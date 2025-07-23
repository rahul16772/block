import logging
import socket

_DATA_DIR = "data"
_DEFAULT_CHECKPOINT = f"{_DATA_DIR}/base_checkpoint"

_LOG = None


def get_logger() -> logging.Logger:
    global _LOG
    if _LOG is None:
        _LOG = logging.getLogger(__name__)
    return _LOG


def get_identifier() -> str:
    """Return identifier based on uname and IP address."""
    hostname = socket.gethostname()
    return f"{hostname}_{socket.gethostbyname(hostname)}"