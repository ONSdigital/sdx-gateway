import logging
import os

LOGGING_LEVEL = logging.getLevelName(os.getenv("LOGGING_LEVEL", "INFO"))
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-gateway: %(message)s"

PROJECT_ID = os.getenv('PROJECT_ID', 'ons-sdx-jon')
SURVEY_TOPIC = "survey-topic"

QUARANTINE_QUEUE = 'quarantine-survey-topic'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = os.getenv('RABBIT_GATEWAY_QUEUE', 'survey')
RABBITMQ_HEALTHCHECK_DELAY_MS = os.getenv("RABBITMQ_HEALTHCHECK_DELAY_MS", "60000")

# EQ Rabbit credentials
EQ_RABBITMQ_MONITORING_USER = os.getenv('EQ_RABBITMQ_MONITORING_USER', 'user')
EQ_RABBITMQ_MONITORING_PASSWORD = os.getenv('EQ_RABBITMQ_MONITORING_PASSWORD', 'iHnGnTqtMo')
SDX_GATEWAY_EQ_RABBITMQ_USER = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_USER', 'user')
SDX_GATEWAY_EQ_RABBITMQ_PASSWORD = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_PASSWORD', 'iHnGnTqtMo')
SDX_GATEWAY_EQ_RABBITMQ_HOST = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST', '127.0.0.1')
SDX_GATEWAY_EQ_RABBITMQ_HOST2 = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST2', '127.0.0.1')
SDX_GATEWAY_EQ_RABBIT_PORT = '5672'
