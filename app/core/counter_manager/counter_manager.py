from typing import Any
from repos.v1.counters import CountersRepository, CountersDataSource


class CounterManager:
    _instance: "CounterManager|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.counters_repository = CountersRepository(CountersDataSource())

    async def next_invoice_number(self, session: Any) -> str:
        res = await self.counters_repository.increment_counter("invoiceNumber", session)
        return str(res.value)

    async def next_receipt_number(self, session: Any) -> str:
        res = await self.counters_repository.increment_counter("receiptNumber", session)
        return str(res.value)

    async def next_order_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("orderNumber", session)
        return str(res.value)

    async def next_devolution_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter(
            "devolutionNumber", session
        )
        return str(res.value)

    async def next_product_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("productNumber", session)
        formatted = str(res.value).zfill(5)
        return formatted

    async def next_user_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("userNumber", session)
        formatted = str(res.value).zfill(4)
        return formatted

    async def next_client_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("clientNumber", session)
        formatted = str(res.value).zfill(4)
        return formatted

    async def next_tranfer_number(self, session: Any) -> str:
        res = await self.counters_repository.increment_counter(
            "transferNumber", session
        )
        formatted = str(res.value)
        return formatted

    async def next_adjust_number(self, session: Any) -> str:
        res = await self.counters_repository.increment_counter("adjustNumber", session)
        formatted = str(res.value)
        return formatted
