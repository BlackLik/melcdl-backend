import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Self

import uvicorn
from fastapi import FastAPI, Request, Response

from internal import api, config
from internal.bootstrap.abc import AbstractCommand
from internal.config.kafka import get_kafka_consumer
from internal.services.ml.base import MLService
from internal.utils import errors, log

if TYPE_CHECKING:
    from internal.config.base import AppSettings

logger = log.get_logger()


class AppCommand(AbstractCommand):
    _instance: Self | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self.settings: AppSettings = config.get_config()
        self._app: FastAPI | None = None
        self.background_tasks = set()

    def execute(self) -> None:
        uvicorn.run(
            app="internal.bootstrap.app:_app",
            host=self.settings.HOST,
            port=self.settings.PORT,
            reload=self.settings.APP_RELOAD,
            workers=self.settings.APP_WORKERS,
            log_config=self.get_log_config(),
        )

    @property
    def fastapi_app(self) -> FastAPI:
        if self._app is None:
            self._app = self._init_app()

        return self._app

    def _init_app(self) -> FastAPI:
        app = FastAPI(
            lifespan=self._lifespan,
            exception_handlers=self._exception_handlers(),
        )
        app.include_router(api.router)

        self.consumer = get_kafka_consumer()
        self.consumer.include_action(api.kafka.actions)

        return app

    def _exception_handlers(self) -> dict[int | type[Exception], Callable[[Request, Any], Awaitable[Response]]]:
        return errors.get_exception_handlers()

    @asynccontextmanager
    async def _lifespan(self, _: FastAPI) -> AsyncGenerator[None, Any]:
        logging.getLogger("sqlalchemy.engine.Engine").disabled = True
        logger.info("Start app")
        await MLService.start_all_jobs()
        tasks_start = [self.consumer.start]

        for elem in tasks_start:
            task = asyncio.create_task(elem())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        yield

        logger.info("Stop app")

    def get_log_config(self) -> dict[str, Any]:
        if not self.settings.APP_CONFIG_LOG.exists():
            raise FileNotFoundError

        dict_log_config: dict[str, Any] = log.load_dict_config(self.settings.APP_CONFIG_LOG)
        level_log = log.LoggingLevelEnum.INFO if self.settings.MODE == "PROD" else log.LoggingLevelEnum.DEBUG
        log.set_level(dict_config=dict_log_config, level=level_log)

        return dict_log_config


_app = AppCommand().fastapi_app
