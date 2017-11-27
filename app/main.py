#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the sdx-gateway service."""
import json
import logging
import os

import tornado
from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPError

from sdc.rabbit import MessageConsumer
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.exceptions import QuarantinableError

import app.settings
from app import create_and_wrap_logger
from . import settings

logging.basicConfig(format=app.settings.LOGGING_FORMAT,
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    level=app.settings.LOGGING_LEVEL)

logger = create_and_wrap_logger(__name__)

logging.getLogger('sdc.rabbit').setLevel(logging.DEBUG)
logging.getLogger('pika').setLevel(logging.ERROR)


class Bridge:
    """A Bridge object that takes from one queue and publishes to another."""

    def __init__(self):
        """Initialise a Bridge object."""
        self._rabbit_hosts = [
            settings.RABBIT_HOST,
            settings.RABBIT_HOST2
        ]
        self._rabbit_port = settings.RABBIT_PORT
        self._default_user = settings.DEFAULT_USER
        self._default_pass = settings.DEFAULT_PASSWORD
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
            settings.COLLECT_QUEUE,
        )

        self.quarantine_publisher = QueuePublisher(
            urls=self._urls,
            queue=settings.QUARANTINE_QUEUE,
        )

        self.consumer = MessageConsumer(
            durable_queue=True,
            exchange=settings.RABBIT_EXCHANGE,
            exchange_type="topic",
            rabbit_queue=settings.EQ_QUEUE,
            rabbit_urls=self._urls,
            quarantine_publisher=self.quarantine_publisher,
            process=self.process,
        )

    def process(self, message, tx_id=None):
        try:
            self.publisher.publish_message(message, headers={'tx_id': tx_id})
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
            settings.RABBIT_HOST,
            settings.RABBIT_HOST2,
        ]
        self._rabbit_port = settings.RABBIT_PORT
        self._default_user = settings.DEFAULT_USER
        self._default_pass = settings.DEFAULT_PASSWORD
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

        # Application health statuses
        self.rabbit_status = False
        self.app_health = False

        # Async HTTP Client
        self.async_client = AsyncHTTPClient()

    def determine_rabbit_connection_status(self):
        for url in self.rabbit_urls:
            try:
                logger.info("Fetching rabbit health")
                response = yield self.async_client.fetch(url)
            except HTTPError:
                logger.exception("Error receiving rabbit health")
                raise tornado.gen.Return(None)
            except Exception:
                logger.exception("Unknown exception occurred when receiving " +
                                 "rabbit health")
                raise tornado.gen.Return(None)

            logger.error("Setting rabbit status")
            self.rabbit_status_callback(response)

        return

    def rabbit_status_callback(self, response):
        """Sets the rabbit_status attribute on this GetHealth object
        to True if the response passed contains a status of 'ok'. Otherwise
        sets the attribute to False."""
        self.rabbit_status = False
        logger.info("Decoding rabbitmq status")
        resp = response.body.decode()
        print(resp)
        try:
            res = json.loads(resp)
        except ValueError:
            logger.exception("Rabbit status response does not contain valid JSON.")
            return

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
            int(settings.HEALTHCHECK_DELAY_MS),
        )
        sched.start()
        logger.info("Scheduled healthcheck started.")

        # Carry out an initial healthcheck
        loop = tornado.ioloop.IOLoop.current()
        loop.call_later(
            int(settings.HEALTHCHECK_DELAY_MS),
            task.determine_rabbit_connection_status,
        )

        # Run the bridge service
        bridge = Bridge()
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping application.")
        bridge.stop()
        logger.info("Application stopped.")


if __name__ == "__main__":
    main()
