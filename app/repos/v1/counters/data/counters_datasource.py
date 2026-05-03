from typing import Any
from services.mongo_collections.v1 import CountersCollection


class CountersDataSource:
    async def increment_counter(
        self, counter_name: str, session: Any
    ) -> dict[str, Any]:
        return await CountersCollection().increment_counter(counter_name, session)

    async def set_counter(
        self, counter_name: str, value: int, session: Any
    ) -> dict[str, Any]:
        return await CountersCollection().set_counter(counter_name, value, session)
