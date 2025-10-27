from datetime import datetime, timedelta


class TimeTools:
    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def get_now_in_100days_in_milliseconds() -> int:
        return int((datetime.now() + timedelta(days=100)).timestamp() * 1000)
