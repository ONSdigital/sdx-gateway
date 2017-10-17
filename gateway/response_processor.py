#!/usr/bin/env python3
#   encoding: UTF-8
"""Implements the ResponseProcessor class for use with sdc-rabbit."""

import os
import logging

from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Consume a message from a queue and publish it to sdx-collect."""

    def __init__(self):
        """Class initialisation."""
        self.publisher = QueuePublisher(
            [os.getenv('RABBIT_URL', '0.0.0.0:5672')],
            'collect',
            confirm_delivery=True,
        )

    def publish(self, msg, **kwargs):
        """Publish a received message to sdx-collect."""
        try:
            self.publisher.publish_message(msg)
        except PublishMessageError:
            logger.exception()
