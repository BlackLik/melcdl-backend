import datetime

import pytz

from internal import config


class TimeService:
    @classmethod
    def get_datetime_now(cls, timezone: str | None = None) -> datetime.datetime:
        return datetime.datetime.now(tz=cls.get_time_zone(timezone))

    @classmethod
    def get_time_zone(cls, timezone: str | None = None) -> datetime.tzinfo:
        settings = config.get_config()
        return pytz.timezone(timezone or settings.TZ_NAME)
