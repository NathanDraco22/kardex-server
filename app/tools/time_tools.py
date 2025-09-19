from datetime import datetime


class TimeTools:
    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)
