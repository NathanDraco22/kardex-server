from kardex.repos.v1.bi import (
    BIDetalleVentaItem,
    BIClienteItem,
    BIFlujoCajaItem,
    BIInventarioItem,
    BIRepository,
    BIVentaItem,
)


class BIController:
    def __init__(self, repo: BIRepository | None = None) -> None:
        self.repo = repo or BIRepository.get_instance()

    async def get_invoices(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIVentaItem]:
        return await self.repo.get_bi_invoices(start_date, end_date, branch_id)

    async def get_invoice_items(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIDetalleVentaItem]:
        return await self.repo.get_bi_invoice_items(start_date, end_date, branch_id)

    async def get_cash_flow(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIFlujoCajaItem]:
        return await self.repo.get_bi_cash_flow(start_date, end_date, branch_id)

    async def get_inventory(self, branch_id: str | None = None) -> list[BIInventarioItem]:
        return await self.repo.get_bi_inventory(branch_id)

    async def get_customers(self) -> list[BIClienteItem]:
        return await self.repo.get_bi_customers()
