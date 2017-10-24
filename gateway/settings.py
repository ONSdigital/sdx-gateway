import os

COLLECT_QUEUE = 'collect'
DEFAULT_USER = os.getenv('SDX_GATEWAY_DEFAULT_USER', 'guest')
LOGGING_FORMAT = '% %(asctime)s. % %(msecs)06dZ | % % (levelname)s: {}: % %(message)s'
LOGGING_LEVEL = 'DEBUG'
DEFAULT_PASSWORD = os.getenv('SDX_GATEWAY_DEFAULT_PASSWORD', 'guest')
QUARANTINE_QUEUE = 'bridge_quarantine'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = 'submit_queue'
RABBIT_HOST = os.getenv('SDX_GATEWAY_RABBIT_HOST', '0.0.0.0')
RABBIT_HOST2 = os.getenv('SDX_GATEWAY_RABBIT_HOST2', '0.0.0.0')
RABBIT_PORT = '5672'
HEALTHCHECK_DELAY_MS = '5000'
