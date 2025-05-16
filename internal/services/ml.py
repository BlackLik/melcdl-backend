import torch
from async_lru import alru_cache


class MLService:
    @staticmethod
    @alru_cache(maxsize=1)
    async def get_model() -> torch.Module: ...

    @classmethod
    def upload_img(cls) -> None: ...
