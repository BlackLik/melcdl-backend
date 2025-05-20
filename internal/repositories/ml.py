from internal.entities import models

from .base import BaseRepository


class TasksRepository(BaseRepository[models.Tasks]):
    _default_model = models.Tasks


class PredictsRepository(BaseRepository[models.Predicts]):
    _default_model = models.Predicts


class ModelsRepository(BaseRepository[models.Models]):
    _default_model = models.Models


class FilesRepository(BaseRepository[models.Files]):
    _default_model = models.Files
