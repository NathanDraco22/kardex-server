import asyncio
from datetime import datetime, timedelta
from typing import Self

from core.scheduler.daily_report_maker import (
    DailyReportMaker,
    WeeklyReportMaker,
    MonthlyReportMaker,
    YearlyReportMaker,
)
from core.scheduler.app_reminder import AppReminder
from tools import TimeTools


class AppScheduler:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    _started = False

    _task: asyncio.Task | None = None

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        self.daily_maker = DailyReportMaker()
        self.weekly_maker = WeeklyReportMaker()
        self.monthly_maker = MonthlyReportMaker()
        self.yearly_maker = YearlyReportMaker()

    async def start_task(self):
        if self._started:
            return

        print("🔄 Scheduler Recovery: Checking for missed reports...")
        now = datetime.now(TimeTools.default_timezone)

        try:
            daily_summary = await self.daily_maker.ensure_daily_report(now)
            if daily_summary is not None:
                await AppReminder.morning_reminder_7am(now, daily_summary)

            await self.weekly_maker.ensure_weekly_report(now)
            # Ensure monthly report (if today is 1st or shortly after)
            await self.monthly_maker.ensure_monthly_report(now)
            # Ensure yearly report (if today is Jan 1st or shortly after)
            await self.yearly_maker.ensure_yearly_report(now)
        except Exception as e:
            print(f"❌ Error during scheduler recovery: {e}")

        self._task = asyncio.create_task(self.run_every_midnight())
        self._started = True
        print("🕒 Scheduler Init")

    async def run_every_midnight(self):
        nic_tz = TimeTools.default_timezone
        while True:
            # 1. Calculate next target execution time (Next Midnight)
            now = datetime.now(nic_tz)
            next_day = now + timedelta(days=1)
            target_time = next_day.replace(hour=0, minute=0, second=0, microsecond=0)

            # 2. Wait until that time
            wait_seconds = (target_time - datetime.now(nic_tz)).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            # 3. Execution with retry loop
            while True:
                try:
                    await self._set_daily_tasks(target_time)
                    break  # Success! Exit retry loop
                except asyncio.CancelledError:
                    print("Scheduler Stopped")
                    return
                except Exception as e:
                    print(
                        f"Error executing daily task at {target_time}, retrying in 60s..."
                    )
                    print(e)
                    await asyncio.sleep(60)

    async def _set_daily_tasks(self, midnight_time: datetime):
        print(f"🚀 Daily Task: {midnight_time}")
        await asyncio.sleep(1)

        daily_summary = await self.daily_maker.ensure_daily_report(midnight_time)

        if daily_summary is not None:
            await AppReminder.morning_reminder_7am(midnight_time, daily_summary)

        if midnight_time.weekday() == 0:
            await self.weekly_maker.ensure_weekly_report(midnight_time)

        # 3. Monthly Report (if 1st of month) - Idempotent
        if midnight_time.day == 1:
            await self.monthly_maker.ensure_monthly_report(midnight_time)

            # 4. Yearly Report (if 1st of January) - Idempotent
            if midnight_time.month == 1:
                await self.yearly_maker.ensure_yearly_report(midnight_time)
