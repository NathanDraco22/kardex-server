from repos.v1.counters import CountersRepository, CountersDataSource


class CounterManager:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.counters_repository = CountersRepository(CountersDataSource())

    async def next_invoice_number(self) -> str:
        res = await self.counters_repository.increment_counter("invoiceNumber")
        return str(res.value)

    async def next_receipt_number(self) -> str:
        res = await self.counters_repository.increment_counter("receiptNumber")
        return str(res.value)
