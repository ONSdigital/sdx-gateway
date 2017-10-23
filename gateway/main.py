#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the sdx-gateway service."""
import configparser
import jsons
import logging
import os

import tornado
from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPError

from sdc.rabbit import MessageConsumer
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.exceptions import QuarantinableError

config = configparser.SafeConfigParser()

if not os.getenv('SDX_DEV_MODE'):
    config.read('./dev_config.ini')
else:
    config.read('dev_config.ini')

logging.basicConfig(
    format=config['default']['LOGGING_FORMAT'],
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=config['default']['LOGGING_LEVEL'],
)

logger = logging.getLogger('__name__')

logging.getLogger('sdc.rabbit').setLevel(logging.DEBUG)
logging.getLogger('pika').setLevel(logging.ERROR)


class Bridge:
    """A Bridge object that takes from one queue and publishes to another."""

    def __init__(self):
        """Initialise a Bridge object."""
        self._rabbit_hosts = [
            config['default']['RABBIT_HOST'],
            config['default']['RABBIT_HOST2']
        ]
        self._rabbit_port = config['default']['RABBIT_PORT']
        self._default_user = config['default']['DEFAULT_USER']
        self._default_pass = config['default']['DEFAULT_PASSWORD']
        self._urls = [
            'amqp://{}:{}@{}:{}/%2f'.format(
                self._default_user,
                self._default_pass,
                self._rabbit_hosts[0],
                self._rabbit_port),
            'amqp://{}:{}@{}:{}/%2f'.format(
                self._default_user,
                self._default_pass,
                self._rabbit_hosts[1],
                self._rabbit_port),
        ]

        self.publisher = QueuePublisher(
            self._urls,
            config['default']['COLLECT_QUEUE'],
        )

        self.quarantine_publisher = QueuePublisher(
            urls=self._urls,
            queue=config['default']['QUARANTINE_QUEUE'],
        )

        self.consumer = MessageConsumer(
            durable_queue=True,
            exchange=config['default']['RABBIT_EXCHANGE'],
            exchange_type="topic",
            rabbit_queue=config['default']['EQ_QUEUE'],
            rabbit_urls=self._urls,
            quarantine_publisher=self.quarantine_publisher,
            process=self.process,
        )

    def process(self, message, tx_id=None):
        try:
            self.publisher.publish_message(message)
        except PublishMessageError:
            logger.exception('Unsuccesful publish. tx_id={}'.format(tx_id))
            raise QuarantinableError

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
        """Initialise a Bridge object."""

        # RabbitMQ vars
        self._rabbit_hosts = [
            config['default']['RABBIT_HOST'],
            config['default']['RABBIT_HOST2']
        ]
        self._rabbit_port = config['default']['RABBIT_PORT']
        self._default_user = config['default']['DEFAULT_USER']
        self._default_pass = config['default']['DEFAULT_PASSWORD']
        self.rabbit_urls = [
            'http://{}:{}@{}:{}/api/healthchecks/node'.format(
                self._default_user,
                self._default_pass,
                self._rabbit_hosts[0],
                15672),
            'http://{}:{}@{}:{}/api/healthchecks/node'.format(
                self._default_user,
                self._default_pass,
                self._rabbit_hosts[1],
                15672),
        ]

        logger.info(self.rabbit_urls)

        # Application health statuses
        self.rabbit_status = False
        self.app_health = False

        # Carry out an initial check of connection statuses
        self.determine_rabbit_connection_status()

    @tornado.gen.coroutine
    def determine_rabbit_connection_status(self):
        for url in self.rabbit_urls:
            try:
                response = yield AsyncHTTPClient().fetch(url)
                self.rabbit_status_callback(response)
            except HTTPError:
                logger.exception("Error receiving rabbit health")
                raise tornado.gen.Return(None)
            except Exception:
                logger.exception("Unknown exception occurred when receiving " +
                                 "rabbit health")
                raise tornado.gen.Return(None)
        return

    def rabbit_status_callback(self, response):
        self.rabbit_status = False
        if response:
            resp = response.body.decode()
            logger.error(resp)
            res = json.loads(resp)
            status = res.get('status')
            logger.info("Rabbit MQ health check response {}".format(status))
            if status == "ok":
                logger.info('Setting status now')
                self.rabbit_status = True


class HealthCheck(web.RequestHandler):
    """Returns a http response with a JSON body of {"status": "ok"}
       if this service is running."""

    def initialize(self):
        self.set_health = GetHealth()

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
    logger.info("Starting SDX Bridge service.")

    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.bind(int(os.getenv("SDX_GATEWAY_PORT", '8080')))
    server.start(1)

    try:
        # Create the scheduled healthcheck
        task = GetHealth()
        sched = tornado.ioloop.PeriodicCallback(
            task.determine_rabbit_connection_status,
            int(config['default']['HEALTHCHECK_DELAY_MS']))
        sched.start()
        logger.info("Scheduled healthcheck started.")

        # Carry out an initial healthcheck
        loop = tornado.ioloop.IOLoop.current()
        loop.call_later(
            int(config['default']['HEALTHCHECK_DELAY_MS']),
            task.determine_rabbit_connection_status
        )

        # Run the bridge service
        bridge = Bridge()
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping application.")
        bridge.stop()
        logger.info("ApplicatiSOon stopped.")


if __name__ == "__main__":
    main()
