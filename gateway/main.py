"""SDX Gateway service."""

import asyncio
import logging
import os
from aiohttp import web

from sdc.rabbit import AsyncioConsumer
from sdc.rabbit import QueuePublisher

from . import __version__
from . import logger_initial_config
from .response_processor import ResponseProcessor


logger_initial_config(__name__)
logger = logging.getLogger('__name__')

logging.getLogger("sdc.rabbit").setLevel(logging.DEBUG)


async def run():
    """Run the response processor."""
    response_processor = ResponseProcessor()

    quarantine_publisher = QueuePublisher(
        urls=os.getenv('RABBIT_URLS'),
        queue=os.getenv('gateway-quarantine'),
    )

    message_consumer = AsyncioConsumer(
        durable_queue=True,
        exchange=os.getenv('EXCHANGE'),
        exchange_type="topic",
        rabbit_queue=os.getenv('RABBIT_QUEUE'),
        rabbit_urls=os.getenv('RABBIT_URLS'),
        quarantine_publisher=quarantine_publisher,
        process=response_processor.publish
    )

    try:
        await message_consumer.run()
    except asyncio.CancelledError:
        logger.info("Stopping message consumer.")
        message_consumer.stop()


def start_background_tasks(app):
    """Background tasks to run."""
    app['rabbit_consumer'] = app.loop.create_task(run())


async def cleanup_background_tasks(app):
    """Stop background tasks cleanly."""
    app['rabbit_consumer'].cancel()
    await app['rabbit_consumer']


async def healthcheck(session):
    """Healthcheck endpoint for returning app status."""
    return web.json_response({'status': 'ok'})


def init(loop=None):
    """Initialise the web app."""
    logger.info(f"Starting sdx-rabbit-monitor version={__version__}")
    app = web.Application(loop=loop)
    app.router.add_get('/healthcheck', healthcheck)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


if __name__ == "__main__":
    """Run when imported as a module."""
    loop = asyncio.get_event_loop()
    web.run_app(init(), port=os.getenv('PORT', 5000), loop=loop)
