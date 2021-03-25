import os

from app.secret_manager import get_secret

PROJECT_ID = os.getenv('PROJECT_ID', 'ons-sdx-jon')
SURVEY_TOPIC = "survey-topic"

QUARANTINE_QUEUE = 'quarantine-survey-topic'
RABBIT_EXCHANGE = 'exchange'
EQ_QUEUE = os.getenv('RABBIT_GATEWAY_QUEUE', 'survey')
RABBITMQ_HEALTHCHECK_DELAY_MS = os.getenv("RABBITMQ_HEALTHCHECK_DELAY_MS", "60000")

# EQ Rabbit credentials
EQ_RABBITMQ_MONITORING_USER = 'eq-rabbit-user'
EQ_RABBITMQ_MONITORING_PASSWORD = 'eq-rabbit-password'
SDX_GATEWAY_EQ_RABBITMQ_USER = 'eq-rabbit-user'
SDX_GATEWAY_EQ_RABBITMQ_PASSWORD = 'eq-rabbit-password'
SDX_GATEWAY_EQ_RABBITMQ_HOST = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST', 'sdx-rabbit')
SDX_GATEWAY_EQ_RABBITMQ_HOST2 = os.getenv('SDX_GATEWAY_EQ_RABBITMQ_HOST2', 'sdx-rabbit')
SDX_GATEWAY_EQ_RABBIT_PORT = '5672'


def cloud_config():
    eq_rabbit_user = get_secret(PROJECT_ID, 'eq-rabbit-user')
    eq_rabbit_password = get_secret(PROJECT_ID, 'eq-rabbit-password')
    global EQ_RABBITMQ_MONITORING_USER
    EQ_RABBITMQ_MONITORING_USER = eq_rabbit_user
    global EQ_RABBITMQ_MONITORING_PASSWORD
    EQ_RABBITMQ_MONITORING_PASSWORD = eq_rabbit_password
    global SDX_GATEWAY_EQ_RABBITMQ_USER
    SDX_GATEWAY_EQ_RABBITMQ_USER = eq_rabbit_user
    global SDX_GATEWAY_EQ_RABBITMQ_PASSWORD
    SDX_GATEWAY_EQ_RABBITMQ_PASSWORD = eq_rabbit_password
