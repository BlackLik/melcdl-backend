from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class BaseRepository[T]:
    """
    Базовый CRUD-репозиторий для асинхронных моделей SQLAlchemy.
    Предполагается, что сессия передается извне и commit/rollback управляется на уровне сервиса или middleware.
    """

    _default_model: type[T]

    def __init__(self, session: AsyncSession, model: type[T] | None = None) -> None:
        self.session: AsyncSession = session
        self.model = model or self._default_model

    async def get(self, pk: Any) -> T | None:  # noqa: ANN401
        """Получить объект по primary key"""
        return await self.session.get(self.model, pk)

    async def filter(self, **params: dict[str, Any]) -> T | None:
        """Получить объект по набору параметров"""
        qs = select(self.model).filter_by(**(params or {}))
        result = await self.session.execute(qs)
        return result.scalar_one_or_none()

    async def list(self, offset: int = 0, limit: int = 1000, **params: dict[str, Any]) -> list[T]:
        """Получить список объектов по пагинации"""
        q = select(self.model).filter_by(**(params or {})).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def create(self, **obj_in: dict[str, Any]) -> T:
        """Создать новый объект и добавить в сессию"""
        obj = self.model(**(obj_in or {}))
        self.session.add(obj)
        # flush позволяет получить сгенерированные БД поля (id и т.д.)
        await self.session.flush()
        return obj

    async def update(self, obj: T, obj_in: dict[str, Any]) -> T:
        """Обновить поля объекта и добавить изменения в сессию"""
        for field, value in obj_in.items():
            setattr(obj, field, value)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: T) -> None:
        """Удалить объект из базы"""
        await self.session.delete(obj)
        await self.session.flush()
