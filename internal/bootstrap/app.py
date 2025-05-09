import logging

import uvicorn
from fastapi import FastAPI

from internal import api, config
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
        settings = config.get_config()

        return uvicorn.run(
            app="internal.bootstrap.app:_app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.APP_RELOAD,
            workers=settings.APP_WORKERS,
        )

    def get_app(self) -> FastAPI:
        app = FastAPI()
        app.include_router(api.router)

        return app


_app = AppCommand().get_app()
