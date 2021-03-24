import structlog
from google.cloud import pubsub_v1

from app import settings

logger = structlog.get_logger()


class PubSubQuarantine:
    """Writes to a pubsub topic.

    Objects of this class can be used in place of sdc.rabbit.QueuePublisher
    for the quarantine_publisher parameter when creating an instance of
    sdc.rabbit.MessageConsumer. This will allow the MessageConsumer to be used
    with pubsub instead of rabbitmq.
    """

    def __init__(self,):
        self._publisher = pubsub_v1.PublisherClient()
        self._quarantine_topic_path = self._publisher.topic_path(settings.PROJECT_ID, settings.QUARANTINE_QUEUE)

    def publish_message(self, data: bytes, headers: dict = {'tx_id': 'tx_id'}) -> None:
        tx_id = headers['tx_id']
        logger.info(f"Quarantining data with tx_id: {tx_id}")
        future = self._publisher.publish(self._quarantine_topic_path, data, tx_id=tx_id, error="failed in gateway!")
        logger.info(future.result())
