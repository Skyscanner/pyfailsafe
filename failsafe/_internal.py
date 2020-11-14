import logging

logger = logging.getLogger(__name__)


def _do_nothing(*args):
    pass


def _safe_call(callable):
    try:
        callable()
    except Exception:
        logger.exception("Exception caught!")
