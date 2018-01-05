import logging
import os

LOGGING_LEVEL = logging.getLevelName(os.getenv("LOGGING_LEVEL", "DEBUG"))
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-gateway: %(message)s"

COLLECT_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE', 'sdx_gateway_collect')
DEFAULT_USER = os.getenv('SDX_GATEWAY_DEFAULT_USER', 'rabbit')
DEFAULT_PASSWORD = os.getenv('SDX_GATEWAY_DEFAULT_PASSWORD', 'rabbit')
QUARANTINE_QUEUE = 'bridge_quarantine'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = os.getenv('RABBIT_GATEWAY_QUEUE', 'survey')
RABBIT_HOST = os.getenv('RABBITMQ_HOST', '0.0.0.0')
RABBIT_HOST2 = os.getenv('RABBITMQ_HOST2', '0.0.0.0')
RABBIT_PORT = '5672'
HEALTHCHECK_DELAY_MS = '5000'
HEARTBEAT_INTERVAL = "?heartbeat_interval=5"
