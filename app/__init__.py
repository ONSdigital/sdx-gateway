import logging

from structlog import wrap_logger

__version__ = '1.6.1'


def create_and_wrap_logger(logger_name):
    logger = wrap_logger(logging.getLogger(logger_name))
    logger.info("START", version=__version__)
    return logger
