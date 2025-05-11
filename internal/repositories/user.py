from internal.entities.models import UserModel
from internal.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    _default_model = UserModel
