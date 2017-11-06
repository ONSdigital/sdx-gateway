import os

COLLECT_QUEUE = 'sdx_gateway_collect'
DEFAULT_USER = os.getenv('SDX_GATEWAY_DEFAULT_USER', 'rabbit')
DEFAULT_PASSWORD = os.getenv('SDX_GATEWAY_DEFAULT_PASSWORD', 'rabbit')
QUARANTINE_QUEUE = 'bridge_quarantine'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = 'submit_queue'
RABBIT_HOST = os.getenv('RABBITMQ_HOST', '0.0.0.0')
RABBIT_HOST2 = os.getenv('RABBITMQ_HOST2', '0.0.0.0')
RABBIT_PORT = '5672'
HEALTHCHECK_DELAY_MS = '5000'
