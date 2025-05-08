import logging

from internal.bootstrap.abc import AbstractCommand

logger = logging.getLogger()


class AppCommand(AbstractCommand):
    def __init__(self) -> None:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    def execute(self) -> None:
        logger.info("Hello from melcdl-backend!")
