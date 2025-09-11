from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import CountersCollection


class CountersDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def increment_counter(self, counter_name: str) -> dict[str, Any]:
        return await CountersCollection().increment_counter(counter_name)
