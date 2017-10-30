from io import StringIO
import json
import logging
import unittest
from unittest.mock import Mock, MagicMock
from unittest.mock import patch

import pytest
from sdc.rabbit import MessageConsumer
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.exceptions import QuarantinableError
import tornado
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPError
from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPResponse
from tornado.testing import AsyncHTTPTestCase
from tornado.testing import AsyncTestCase
from tornado.web import Application

from app import main
from app import settings
from app.main import Bridge
from app.main import GetHealth
from app.main import make_app


class TestBridge:
    """Tests for the Bridge class."""
    bridge = Bridge()

    urls = [
        'amqp://{}:{}@{}:{}/%2f'.format(
            settings.DEFAULT_USER,
            settings.DEFAULT_PASSWORD,
            settings.RABBIT_HOST,
            settings.RABBIT_PORT),
        'amqp://{}:{}@{}:{}/%2f'.format(
            settings.DEFAULT_USER,
            settings.DEFAULT_PASSWORD,
            settings.RABBIT_HOST2,
            settings.RABBIT_PORT),
    ]

    def test_bridge_settings(self):
        """Test that the Bridge class is instantiating objects using the
           correct attributes from the settings module."""

        #  Rabbit settings
        assert self.bridge._rabbit_hosts == [
            settings.RABBIT_HOST,
            settings.RABBIT_HOST2,
        ]
        assert self.bridge._rabbit_port == settings.RABBIT_PORT
        assert self.bridge._default_user == settings.DEFAULT_USER
        assert self.bridge._default_pass == settings.DEFAULT_PASSWORD
        assert self.bridge._urls == self.urls

        #  Publisher settings
        assert isinstance(self.bridge.publisher, QueuePublisher)
        assert self.bridge.publisher._urls == self.urls
        assert self.bridge.publisher._queue == settings.COLLECT_QUEUE

        #  Quarantine publisher settings
        assert isinstance(self.bridge.quarantine_publisher, QueuePublisher)
        assert self.bridge.quarantine_publisher._urls == self.urls
        assert self.bridge.quarantine_publisher._queue == settings.QUARANTINE_QUEUE

        #  Consumer settings
        assert isinstance(self.bridge.consumer, MessageConsumer)
        assert self.bridge.consumer._exchange == settings.RABBIT_EXCHANGE
        assert self.bridge.consumer._queue == settings.EQ_QUEUE
        assert self.bridge.consumer._rabbit_urls == self.urls
        assert self.bridge.consumer.quarantine_publisher is self.bridge.quarantine_publisher
        assert self.bridge.consumer.process.__self__ == self.bridge.process.__self__

    @patch('sdc.rabbit.QueuePublisher.publish_message')
    def test_bridge_process_raises_quarantinable_error(self, mock_publisher):
        """Test the process method of the Bridge class."""
        mock_publisher.side_effect = PublishMessageError
        with pytest.raises(QuarantinableError):
            self.bridge.process("message", tx_id=None)

    def test_consumer_run_method_called(self):
        """Test that the run method of the MessageConsumer is called."""
        b = Bridge()
        b.consumer.run = MagicMock()
        b.run()
        assert b.consumer.run.called

    def test_consumer_stop_method_called(self):
        """Test that the run method of the MessageConsumer is called."""
        b = Bridge()
        b.consumer.stop = MagicMock()
        b.stop()
        assert b.consumer.stop.called


class TestGetHealth(unittest.TestCase):
    """Tests for the GetHealth class."""

    get_health = GetHealth()

    urls = [
        'http://{}:{}@{}:15672/api/healthchecks/node'.format(
            settings.DEFAULT_USER,
            settings.DEFAULT_PASSWORD,
            settings.RABBIT_HOST,
        ),
        'http://{}:{}@{}:15672/api/healthchecks/node'.format(
            settings.DEFAULT_USER,
            settings.DEFAULT_PASSWORD,
            settings.RABBIT_HOST2,
        ),
    ]

    def test_get_health_settings(self):
        assert self.get_health._rabbit_hosts == [
            settings.RABBIT_HOST,
            settings.RABBIT_HOST2,
        ]

        assert self.get_health._rabbit_port == settings.RABBIT_PORT
        # assert self._default_user == settings.DEFAULT_USER
        assert self.get_health._default_pass == settings.DEFAULT_PASSWORD
        assert self.get_health.rabbit_urls == self.urls

    def test_rabbit_status_callback(self):
        assert self.get_health.rabbit_status == False

        with self.assertRaises(TypeError):
            self.get_health.rabbit_status_callback()

        class NotJSONResponse:
            body = b'not json'

        class GoodResponse:
            body = b'{"status": "ok"}'

        class BadResponse:
            body = b'{"status": "not ok"}'

        assert None == self.get_health.rabbit_status_callback(NotJSONResponse())

        self.get_health.rabbit_status_callback(BadResponse())
        assert self.get_health.rabbit_status == False

        self.get_health.rabbit_status_callback(GoodResponse())
        assert self.get_health.rabbit_status == True

    def test_make_app(self):
        app = make_app()
        assert isinstance(app, Application)


class TestGetHealthCoroutines(AsyncTestCase):
    """Test the GetHealth determine_rabbit_connection_status coroutine."""

    def setUp(self):
        super().setUp()
        self.client = GetHealth()

    class GoodResponse:
        body = b'{"status": "ok"}'

    class BadResponse:
        body = b'{"status": "not ok"}'

    @tornado.testing.gen_test
    def test_connection_status_raises_http_error(self):
        self.client.async_client.fetch = MagicMock(
            side_effect=HTTPError
        )

        result = self.client.determine_rabbit_connection_status()

        self.client.rabbit_status_callback = MagicMock()
        self.client.async_client.fetch = MagicMock(
            return_value=self.GoodResponse()
        )

        assert self.client.rabbit_status_callback.called_with(self.GoodResponse())

        self.client.rabbit_status_callback = MagicMock()
        self.client.async_client.fetch = MagicMock(
            return_value=self.BadResponse()
        )
        assert self.client.rabbit_status_callback.called_with(self.BadResponse())


class TestHealthCheckApp(AsyncHTTPTestCase):
    """Use tornado AsyncHTTPTestCase to test the HealthCheck application."""
    _healthcheck = '/healthcheck'
    _http_success_code = 200

    def setUp(self):
        self._registration_handler = Mock()
        AsyncHTTPTestCase.setUp(self)

    def get_app(self):
        return make_app()

    def test_healthcheck_endpoint(self):
        self.http_client.fetch(self.get_url(self._healthcheck),
                               self.stop)
        response = self.wait()
        self.assertEqual(self._http_success_code, response.code)
        self.assertEqual(b'{"status": "ok"}', response.body)
