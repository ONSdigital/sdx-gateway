import logging
import os

from app.secret_manager import get_secret

LOGGING_LEVEL = logging.getLevelName(os.getenv("LOGGING_LEVEL", "INFO"))
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-gateway: %(message)s"

PROJECT_ID = os.getenv('PROJECT_ID', 'ons-sdx-jon')
SURVEY_TOPIC = "survey-topic"

QUARANTINE_QUEUE = 'quarantine-survey-topic'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = os.getenv('RABBIT_GATEWAY_QUEUE', 'survey')
RABBITMQ_HEALTHCHECK_DELAY_MS = os.getenv("RABBITMQ_HEALTHCHECK_DELAY_MS", "60000")

# EQ Rabbit credentials
EQ_RABBITMQ_MONITORING_USER = get_secret(PROJECT_ID, 'eq-rabbit-user')
EQ_RABBITMQ_MONITORING_PASSWORD = get_secret(PROJECT_ID, 'eq-rabbit-password')
SDX_GATEWAY_EQ_RABBITMQ_USER = get_secret(PROJECT_ID, 'eq-rabbit-user')
SDX_GATEWAY_EQ_RABBITMQ_PASSWORD = get_secret(PROJECT_ID, 'eq-rabbit-password')
SDX_GATEWAY_EQ_RABBITMQ_HOST = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST', 'sdx-rabbit')
SDX_GATEWAY_EQ_RABBITMQ_HOST2 = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST2', 'sdx-rabbit')
SDX_GATEWAY_EQ_RABBIT_PORT = '5672'
