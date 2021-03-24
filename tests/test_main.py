import unittest
from unittest.mock import Mock, MagicMock
from unittest.mock import patch

import pytest
from sdc.rabbit import MessageConsumer
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.exceptions import RetryableError
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from app import settings
from app.gateway import Bridge
from app.gateway import GetHealth
from app.gateway import make_app


class TestBridge:
    """Tests for the Bridge class."""
    bridge = Bridge()

    eq_queue_urls = [
        'amqp://{}:{}@{}:{}/%2f'.format(
            settings.SDX_GATEWAY_EQ_RABBITMQ_USER,
            settings.SDX_GATEWAY_EQ_RABBITMQ_PASSWORD,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
            settings.SDX_GATEWAY_EQ_RABBIT_PORT),
        'amqp://{}:{}@{}:{}/%2f'.format(
            settings.SDX_GATEWAY_EQ_RABBITMQ_USER,
            settings.SDX_GATEWAY_EQ_RABBITMQ_PASSWORD,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2,
            settings.SDX_GATEWAY_EQ_RABBIT_PORT),
    ]

    def test_bridge_settings(self):
        """Test that the Bridge class is instantiating objects using the
           correct attributes from the settings module."""

        #  Rabbit settings
        assert self.bridge._eq_queue_hosts == [
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2,
        ]
        assert self.bridge._eq_queue_port == settings.SDX_GATEWAY_EQ_RABBIT_PORT
        assert self.bridge._eq_queue_user == settings.SDX_GATEWAY_EQ_RABBITMQ_USER
        assert self.bridge._eq_queue_password == settings.SDX_GATEWAY_EQ_RABBITMQ_PASSWORD
        assert self.bridge._eq_queue_urls == self.eq_queue_urls

        #  Consumer settings
        assert isinstance(self.bridge.consumer, MessageConsumer)
        assert self.bridge.consumer._exchange == settings.RABBIT_EXCHANGE
        assert self.bridge.consumer._queue == settings.EQ_QUEUE
        assert self.bridge.consumer._rabbit_urls == self.eq_queue_urls
        assert self.bridge.consumer.quarantine_publisher is self.bridge.quarantine_publisher
        assert self.bridge.consumer.process.__self__ == self.bridge.process.__self__

    @patch('sdc.rabbit.QueuePublisher.publish_message')
    def test_bridge_process_raises_quarantinable_error(self, mock_publisher):
        """Test the process method of the Bridge class."""
        mock_publisher.side_effect = PublishMessageError
        with pytest.raises(RetryableError):
            self.bridge.process("message", tx_id=None)

        mock_publisher.side_effect = Exception
        with pytest.raises(RetryableError):
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
            settings.EQ_RABBITMQ_MONITORING_USER,
            settings.EQ_RABBITMQ_MONITORING_PASSWORD,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
        ),
        'http://{}:{}@{}:15672/api/healthchecks/node'.format(
            settings.EQ_RABBITMQ_MONITORING_USER,
            settings.EQ_RABBITMQ_MONITORING_PASSWORD,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2,
        )
    ]

    def test_get_health_settings(self):
        assert self.get_health._rabbit_hosts == [
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST,
            settings.SDX_GATEWAY_EQ_RABBITMQ_HOST2,
        ]

        assert self.get_health._rabbit_port == settings.SDX_GATEWAY_EQ_RABBIT_PORT
        assert self.get_health._monitoring_user == settings.EQ_RABBITMQ_MONITORING_USER
        assert self.get_health._monitoring_pass == settings.EQ_RABBITMQ_MONITORING_PASSWORD
        assert self.get_health.rabbit_urls == self.urls

    def test_rabbit_status_callback(self):
        """Tests for the rabbit_status_callback function."""

        class NotJSONResponse:
            body = b'not json'

        class GoodResponse:
            body = b'{"status": "ok"}'

        class BadResponse:
            body = b'{"status": "not ok"}'

        with self.assertLogs(level='INFO') as cm:
            self.get_health.rabbit_status_callback(NotJSONResponse())
            self.assertIn('Rabbit status response does not contain valid JSON.', cm.output[-1])

        with self.assertLogs(level='INFO') as cm:
            self.get_health.rabbit_status_callback(BadResponse())
            self.assertIn('Rabbit MQ health check response status=not ok', cm.output[-1])

        with self.assertLogs(level='INFO') as cm:
            self.get_health.rabbit_status_callback(GoodResponse())
            self.assertIn('Rabbit MQ health check response status=ok', cm.output[-1])

    def test_make_app(self):
        app = make_app()
        assert isinstance(app, Application)

class TestHealthCheckApp(AsyncHTTPTestCase):
    """Use tornado AsyncHTTPTestCase to test the HealthCheck application."""
    _healthcheck = '/healthcheck'
    _http_success_code = 200

    registration_handler = Mock()

    def setUp(self):
        AsyncHTTPTestCase.setUp(self)

    def get_app(self):
        return make_app()

    def test_healthcheck_endpoint(self):
        response = self.fetch(self.get_url(self._healthcheck))
        self.assertEqual(self._http_success_code, response.code)
        self.assertEqual(b'{"status": "ok"}', response.body)
