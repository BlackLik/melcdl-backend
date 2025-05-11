import json
import logging
from enum import Enum
from pathlib import Path

_name_logger = "app"

logger = logging.getLogger(name=_name_logger)


def get_logger() -> logging.Logger:
    return logger


def load_dict_config(file: Path) -> dict:
    if not file.exists():
        raise FileNotFoundError

    return json.loads(file.read_text())


class LoggingLevelEnum(int, Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def set_level(dict_config: dict, level: LoggingLevelEnum) -> None:
    for elem in ["", _name_logger]:
        dict_config["loggers"][elem]["level"] = level.value
