from types import ModuleType

from fastapi import APIRouter


def include_router(include_router: APIRouter, models: list[ModuleType]) -> None:
    for elem in models:
        if (elem_router := getattr(elem, "router", None)) and not isinstance(elem_router, APIRouter):
            raise AttributeError

        include_router.include_router(elem.router)
