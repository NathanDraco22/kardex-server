from datetime import datetime, timedelta
from pytz import timezone


class TimeTools:
    ms_day = 86400000

    default_timezone = timezone("America/Managua")

    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def get_now_in_100days_in_milliseconds() -> int:
        return int((datetime.now() + timedelta(days=100)).timestamp() * 1000)
