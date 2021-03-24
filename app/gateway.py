import json
import os

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars
import tornado
from tornado import gen, web
from tornado.httpclient import AsyncHTTPClient, HTTPError

from google.cloud import pubsub_v1

from sdc.rabbit import MessageConsumer
from sdc.rabbit.exceptions import QuarantinableError

from app.settings import PROJECT_ID, SURVEY_TOPIC
from . import settings
from .quarantine import PubSubQuarantine

logger = structlog.get_logger()


class Bridge:
    """A Bridge object that takes from one queue and publishes to another."""

    def __init__(self):
        self._eq_queue_hosts = [
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2
        ]
        self._eq_queue_port = settings.SDX_GATEWAY_EQ_RABBIT_PORT
        self._eq_queue_user = settings.SDX_GATEWAY_EQ_RABBITMQ_USER
        self._eq_queue_password = settings.SDX_GATEWAY_EQ_RABBITMQ_PASSWORD

        self._sdx_publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._sdx_publisher.topic_path(PROJECT_ID, SURVEY_TOPIC)

        self._eq_queue_urls = [
            'amqp://{}:{}@{}:{}/%2f'.format(
                self._eq_queue_user,
                self._eq_queue_password,
                self._eq_queue_hosts[0],
                self._eq_queue_port),
            'amqp://{}:{}@{}:{}/%2f'.format(
                self._eq_queue_user,
                self._eq_queue_password,
                self._eq_queue_hosts[1],
                self._eq_queue_port),
        ]

        self.quarantine_publisher = PubSubQuarantine()

        self.consumer = MessageConsumer(
            durable_queue=True,
            exchange=settings.RABBIT_EXCHANGE,
            exchange_type="topic",
            rabbit_queue=settings.EQ_QUEUE,
            rabbit_urls=self._eq_queue_urls,
            quarantine_publisher=self.quarantine_publisher,
            process=self.process,
        )

    def process(self, message, tx_id=None):
        try:
            bind_contextvars(tx_id=tx_id)
            logger.info("Publishing data to pubsub")
            data = message.encode("utf-8")
            future = self._sdx_publisher.publish(self._topic_path, data, tx_id=tx_id)
            logger.info(future.result())
        except Exception as e:
            logger.exception(str(e))
            raise QuarantinableError()
        finally:
            unbind_contextvars('tx_id')

    def run(self):
        """Run this object's MessageConsumer. Stops on KeyboardInterrupt."""
        logger.info("Starting consumer")
        self.consumer.run()

    def stop(self):
        logger.info("Stopping consumer")
        self.consumer.stop()


class GetHealth:
    """The status of the application is determined by the rabbitmq health.
       This is done by performing a healthcheck on rabbitmq. This check is done
       in the background after a delay. When a GET requst is issued against the
       healthcheck endpoint, the current rabbit status is returned along with
       the app status."""

    def __init__(self):
        """Initialise a GetHealth object."""

        # RabbitMQ vars
        self._rabbit_hosts = [
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2,
        ]
        self._rabbit_port = settings.SDX_GATEWAY_EQ_RABBIT_PORT
        self._monitoring_user = settings.EQ_RABBITMQ_MONITORING_USER
        self._monitoring_pass = settings.EQ_RABBITMQ_MONITORING_PASSWORD
        self.rabbit_urls = [
            'http://{}:{}@{}:15672/api/healthchecks/node'.format(
                self._monitoring_user,
                self._monitoring_pass,
                self._rabbit_hosts[0]),
            'http://{}:{}@{}:15672/api/healthchecks/node'.format(
                self._monitoring_user,
                self._monitoring_pass,
                self._rabbit_hosts[1]),
        ]

    @gen.coroutine
    def determine_rabbit_connection_status(self):
        logger.debug("Starting to check rabbit health")
        for url in self.rabbit_urls:
            try:
                logger.debug("Fetching rabbit health")
                response = yield AsyncHTTPClient().fetch(url)
            except HTTPError:
                logger.exception("Error receiving rabbit health")
                raise tornado.gen.Return(None)
            except Exception:
                logger.exception("Unknown exception occurred when receiving rabbit health")
                raise tornado.gen.Return(None)

            self.rabbit_status_callback(response)

        logger.debug("Finished checking rabbit health")
        return

    def rabbit_status_callback(self, response):
        """Logs the status of the rabbit connection as ok or not ok."""
        logger.debug("Decoding rabbitmq status")
        resp = response.body.decode()
        try:
            res = json.loads(resp)
        except ValueError:
            logger.exception("Rabbit status response does not contain valid JSON.")
            return

        logger.info("Rabbit MQ health check response", status=res.get('status'))


class HealthCheck(web.RequestHandler):
    """Returns a http response with a JSON body of {"status": "ok"}
       if this service is running."""

    def get(self):
        """Writes `{"status": "ok"}` to the output buffer and sets
           the Content-Type of the response to be `application/json`."""
        self.write('{"status": "ok"}')


def make_app():
    """Returns a tornado web application with the following endpoints:
       - /healthcheck (GET)."""
    return web.Application([
        (r"/healthcheck", HealthCheck),
    ])


def main():
    """Run the Bridge application."""
    bind_contextvars(app="SDX-gateway")
    logger.info("Starting")

    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.bind(int(os.getenv("SDX_GATEWAY_PORT", '8087')))
    server.start(1)
    bridge = Bridge()

    try:
        # Create the scheduled healthcheck
        task = GetHealth()
        sched = tornado.ioloop.PeriodicCallback(
            task.determine_rabbit_connection_status,
            int(settings.RABBITMQ_HEALTHCHECK_DELAY_MS),
        )
        sched.start()
        logger.info("Scheduled healthcheck started.")

        # Carry out an initial healthcheck
        loop = tornado.ioloop.IOLoop.current()
        loop.call_later(
            int(settings.RABBITMQ_HEALTHCHECK_DELAY_MS),
            task.determine_rabbit_connection_status,
        )

        # Run the bridge service
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping application.")
        bridge.stop()
        logger.info("Application stopped.")
        clear_contextvars()
