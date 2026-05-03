from typing import Any
from .data.counters_datasource import CountersDataSource
from .models.counter_model import CounterInDb


class CountersRepository:
    def __init__(self, counters_ds: CountersDataSource):
        self.counters_ds = counters_ds

    async def increment_counter(self, counter_name: str, session: Any) -> CounterInDb:
        result = await self.counters_ds.increment_counter(counter_name, session)
        return CounterInDb.model_validate(result)

    async def set_counter(
        self, counter_name: str, value: int, session: Any
    ) -> CounterInDb:
        result = await self.counters_ds.set_counter(counter_name, value, session)
        return CounterInDb.model_validate(result)
