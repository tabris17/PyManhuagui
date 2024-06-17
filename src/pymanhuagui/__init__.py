"""__init__.py"""
import logging
import sys


logger = logging.getLogger(__name__)


def handle_exception(exc_type, exc, tb):
    """handle_exception()"""
    logger.error('An uncaught error occurred: [%s] %s', exc_type.__name__, exc)
    sys.exit(-1)


sys.excepthook = handle_exception
