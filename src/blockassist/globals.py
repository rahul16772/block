import logging
import socket

_DATA_DIR = "data"
_DEFAULT_CHECKPOINT = f"{_DATA_DIR}/base_checkpoint"

# S3 Configuration
_DEFAULT_S3_BUCKET = "blockassist-episodes"
_DEFAULT_HF_MODEL_TMPL = "blockassist/model"

_LOG = None


def get_logger() -> logging.Logger:
    global _LOG
    if _LOG is None:
        _LOG = logging.getLogger(__name__)
    return _LOG

def get_hostname() -> str:
    return socket.gethostname()

def get_ip(hostname = get_hostname()) -> str:
    return socket.gethostbyname(hostname)

def get_identifier() -> str:
    """Return identifier based on uname and IP address."""
    return f"{get_hostname()}_{get_ip()}"