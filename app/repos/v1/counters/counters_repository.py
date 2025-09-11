from .data.counters_datasource import CountersDataSource
from .models.counter_model import CounterInDb


class CountersRepository:
    def __init__(self, counters_ds: CountersDataSource):
        self.counters_ds = counters_ds

    async def increment_counter(self, counter_name: str) -> CounterInDb:
        result = await self.counters_ds.increment_counter(counter_name)
        return CounterInDb.model_validate(result)
