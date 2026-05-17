from datetime import datetime, timedelta
from pytz import timezone


class TimeTools:
    ms_day = 86400000

    default_timezone = timezone("America/Managua")

    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def seconds_until_next_midnight() -> int:
        now = datetime.now(TimeTools.default_timezone)

        next_midnight = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        seconds_until_next_midnight = (next_midnight - now).total_seconds()

        return int(seconds_until_next_midnight)

    @staticmethod
    def get_now_in_100days_in_milliseconds() -> int:
        return int((datetime.now() + timedelta(days=100)).timestamp() * 1000)
