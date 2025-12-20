import asyncio
from datetime import datetime, timedelta
from tools import TimeTools


class AppScheduler:
    async def start_task(self):
        asyncio.create_task(self.run_every_midnight())
        print("🕒 Scheduler Init")

    async def run_every_midnight(self):
        nic_tz = TimeTools.default_timezone
        while True:
            try:
                next_day = datetime.now(nic_tz) + timedelta(days=1)
                next_midnight = next_day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                diff_seconds = (next_midnight - datetime.now(nic_tz)).total_seconds()
                await asyncio.sleep(diff_seconds)
                await self._set_daily_tasks(next_midnight)
            except asyncio.CancelledError:
                print("Scheduler Stopped")
                break
            except Exception as e:
                print("Error in run_every_midnight")
                print(e)
                await asyncio.sleep(60)

    async def _set_daily_tasks(self, current_time: datetime):
        print(f"🚀 Daily Task: {current_time}")
        # here the daily tasks will be set
        pass
