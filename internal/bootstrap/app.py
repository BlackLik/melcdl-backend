from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import uvicorn
from fastapi import FastAPI

from internal import api, config
from internal.bootstrap.abc import AbstractCommand
from internal.utils import log

if TYPE_CHECKING:
    from internal.config.base import AppSettings

logger = log.get_logger()


class AppCommand(AbstractCommand):
    def __init__(self) -> None:
        self.settings: AppSettings = config.get_config()
        self._app: FastAPI | None = None

    def execute(self) -> None:
        uvicorn.run(
            app="internal.bootstrap.app:_app",
            host=self.settings.HOST,
            port=self.settings.PORT,
            reload=self.settings.APP_RELOAD,
            workers=self.settings.APP_WORKERS,
            log_config=self._get_log_config(),
        )

    @property
    def fastapi_app(self) -> FastAPI:
        if self._app is None:
            self._app = self._init_app()

        return self._app

    def _init_app(self) -> FastAPI:
        app = FastAPI(
            lifespan=self._lifespan,
        )
        app.include_router(api.router)

        return app

    @staticmethod
    @asynccontextmanager
    async def _lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
        logger.info("Start app")
        yield
        logger.info("Stop app")

    def _get_log_config(self) -> dict[str, Any]:
        if not self.settings.APP_CONFIG_LOG.exists():
            raise FileNotFoundError

        dict_log_config: dict[str, Any] = log.load_dict_config(self.settings.APP_CONFIG_LOG)
        level_log = log.LoggingLevelEnum.INFO if self.settings.MODE == "PROD" else log.LoggingLevelEnum.DEBUG
        log.set_level(dict_config=dict_log_config, level=level_log)

        return dict_log_config


_app = AppCommand().fastapi_app
