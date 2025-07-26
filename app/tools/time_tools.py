from datetime import datetime, timezone


class TimeTools:
    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def get_now_utc() -> datetime:
        return datetime.now(tz=timezone.utc)
