import logging

_LOG = None

_DEFAULT_CHECKPOINT = "data/base_checkpoint"

def get_logger() -> logging.Logger:
    global _LOG
    if _LOG is None:
        _LOG = logging.getLogger(__name__)
    return _LOG