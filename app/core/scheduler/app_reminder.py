import asyncio
from datetime import datetime
from repos.v1.daily_summaries import DailySummaryInDb
from repos.v1.executive_summaries import ExecutiveSummaryInDb
from core.app_notifier.app_notifier import AppNotifier
from tools import TimeTools


class AppReminder:
    @staticmethod
    async def morning_reminder_7am(
        today_midnight: datetime, daily_summary: DailySummaryInDb
    ) -> None:
        today_morning = today_midnight.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        seconds = (
            today_morning - datetime.now(tz=TimeTools.default_timezone)
        ).total_seconds()

        if seconds <= 0:
            await AppNotifier().notify_daily_report(daily_summary)
            return

        async def inner_action():
            await asyncio.sleep(seconds)
            await AppNotifier().notify_daily_report(daily_summary)
            pass

        asyncio.create_task(inner_action())

    @staticmethod
    async def morning_executive_report_7am(
        today_midnight: datetime, executive_summary: ExecutiveSummaryInDb, delay: int
    ) -> None:
        today_morning = today_midnight.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        seconds = (
            today_morning - datetime.now(tz=TimeTools.default_timezone)
        ).total_seconds()

        if seconds <= 0:
            await AppNotifier().notify_executive_report(executive_summary)
            return

        async def inner_action():
            await asyncio.sleep(seconds + delay)
            await AppNotifier().notify_executive_report(executive_summary)
            pass

        asyncio.create_task(inner_action())
