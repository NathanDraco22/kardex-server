from kardex.repos.v1.clients import ClientsRepository
from kardex.repos.v1.common.filter_params import (
    ClientFilterParams,
    ExpensesFilterParams,
    InvoiceFilterParams,
    ReceiptFilterParams,
)
from kardex.repos.v1.expenses import ExpensesRepository
from kardex.repos.v1.inventories import InventoriesRepository
from kardex.repos.v1.invoices import InvoicesRepository
from kardex.repos.v1.receipts import ReceiptsRepository
from kardex.repos.v1.branches import BranchesRepository

from .models.bi_models import (
    BIClienteItem,
    BIDetalleVentaItem,
    BIFlujoCajaItem,
    BIInventarioItem,
    BIVentaItem,
    timestamp_to_date_id,
    timestamp_to_iso,
)

END_DATE_DEFAULT = 4_102_444_800_000  # 2100-01-01T00:00:00Z


class BIRepository:
    _instance: "BIRepository | None" = None

    def __init__(
        self,
        invoices_repo: InvoicesRepository | None = None,
        receipts_repo: ReceiptsRepository | None = None,
        expenses_repo: ExpensesRepository | None = None,
        inventories_repo: InventoriesRepository | None = None,
        clients_repo: ClientsRepository | None = None,
        branches_repo: BranchesRepository | None = None,
    ) -> None:
        self.invoices_repo = invoices_repo or InvoicesRepository.get_instance()
        self.receipts_repo = receipts_repo or ReceiptsRepository.get_instance()
        self.expenses_repo = expenses_repo or ExpensesRepository.get_instance()
        self.inventories_repo = inventories_repo or InventoriesRepository.get_instance()
        self.clients_repo = clients_repo or ClientsRepository.get_instance()
        self.branches_repo = branches_repo or BranchesRepository.get_instance()

    @classmethod
    def get_instance(cls) -> "BIRepository":
        if cls._instance is None:
            cls._instance = BIRepository()
        return cls._instance

    async def get_bi_invoices(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIVentaItem]:
        start, end = self._normalize_date_range(start_date, end_date)
        invoices = await self.invoices_repo.get_all_invoices(
            InvoiceFilterParams(startDate=start, endDate=end, branchId=branch_id, limit=0)
        )
        branch_map = await self._get_branch_map()

        items: list[BIVentaItem] = []
        for inv in invoices:
            items.append(
                BIVentaItem(
                    invoiceId=inv.id,
                    invoiceDocNumber=inv.docNumber,
                    fechaISO=timestamp_to_iso(inv.createdAt),
                    dateId=timestamp_to_date_id(inv.createdAt),
                    branchId=inv.branchId,
                    branchName=branch_map.get(inv.branchId, "Sucursal"),
                    clientId=inv.clientId,
                    clientName=inv.clientInfo.name,
                    paymentType=inv.paymentType,
                    subtotal=round(sum(i.subTotal for i in inv.saleItems) / 100.0, 2),
                    tax=round(sum(i.iva for i in inv.saleItems) / 100.0, 2),
                    discount=round(sum(i.totalDiscount for i in inv.saleItems) / 100.0, 2),
                    total=round(inv.total / 100.0, 2),
                    status=inv.status,
                )
            )
        return items

    async def get_bi_invoice_items(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIDetalleVentaItem]:
        start, end = self._normalize_date_range(start_date, end_date)
        invoices = await self.invoices_repo.get_all_invoices(
            InvoiceFilterParams(startDate=start, endDate=end, branchId=branch_id, limit=0)
        )
        branch_map = await self._get_branch_map()

        items: list[BIDetalleVentaItem] = []
        for inv in invoices:
            for item in inv.saleItems:
                qty = float(item.quantity or 0)
                total_sales_cent = item.subTotal - item.totalDiscount
                if not total_sales_cent:
                    total_sales_cent = item.total
                total_cost_cent = item.cost * qty

                items.append(
                    BIDetalleVentaItem(
                        invoiceId=inv.id,
                        invoiceDocNumber=inv.docNumber,
                        fechaISO=timestamp_to_iso(inv.createdAt),
                        branchName=branch_map.get(inv.branchId, "Sucursal"),
                        productId=item.product.id,
                        productCode=item.product.code or "",
                        productName=item.product.name,
                        categoryName=item.product.categoryName or "",
                        quantity=qty,
                        unitPrice=round(item.price / 100.0, 2),
                        unitCost=round(item.cost / 100.0, 2),
                        totalSales=round(total_sales_cent / 100.0, 2),
                        totalCost=round(total_cost_cent / 100.0, 2),
                        grossProfit=round((total_sales_cent - total_cost_cent) / 100.0, 2),
                    )
                )
        return items

    async def get_bi_cash_flow(
        self,
        start_date: int | None = None,
        end_date: int | None = None,
        branch_id: str | None = None,
    ) -> list[BIFlujoCajaItem]:
        start, end = self._normalize_date_range(start_date, end_date)
        receipts = await self.receipts_repo.get_all_receipts(
            ReceiptFilterParams(startDate=start, endDate=end, branchId=branch_id, limit=0)
        )
        expenses = await self.expenses_repo.get_all_expenses(
            ExpensesFilterParams(
                offset=0,
                limit=0,
                startDate=start,
                endDate=end,
                branchId=branch_id,
            )
        )
        branch_map = await self._get_branch_map()

        items: list[BIFlujoCajaItem] = []

        for rec in receipts:
            items.append(
                BIFlujoCajaItem(
                    movementId=rec.id,
                    type="receipt_payment",
                    receiptDocNumber=rec.docNumber,
                    expenseDocNumber="",
                    fechaISO=timestamp_to_iso(rec.createdAt),
                    dateId=timestamp_to_date_id(rec.createdAt),
                    branchName=branch_map.get(rec.branchId, "Sucursal"),
                    clientName=rec.clientInfo.name,
                    category="Abono a Cuenta",
                    income=round(rec.total / 100.0, 2),
                    expense=0.0,
                    paymentMethod=rec.paymentMethod,
                )
            )

        for exp in expenses:
            items.append(
                BIFlujoCajaItem(
                    movementId=exp.id,
                    type="expense",
                    receiptDocNumber="",
                    expenseDocNumber=exp.docNumber,
                    fechaISO=timestamp_to_iso(exp.createdAt),
                    dateId=timestamp_to_date_id(exp.createdAt),
                    branchName=branch_map.get(exp.branchId, "Sucursal"),
                    clientName=exp.supplierName or "N/A",
                    category=exp.category,
                    income=0.0,
                    expense=round(exp.amount / 100.0, 2),
                    paymentMethod="cash",
                )
            )

        items.sort(key=lambda x: x.fechaISO, reverse=True)
        return items

    async def get_bi_inventory(
        self, branch_id: str | None = None
    ) -> list[BIInventarioItem]:
        branch_map = await self._get_branch_map()
        if branch_id:
            branch_ids = [branch_id]
        else:
            branch_ids = list(branch_map.keys())

        items: list[BIInventarioItem] = []
        for b_id in branch_ids:
            async for inv in self.inventories_repo.get_all_inventories_by_branch(b_id):
                items.append(
                    BIInventarioItem(
                        productId=inv.product.id,
                        productCode=inv.product.code or "",
                        productName=inv.product.name,
                        categoryName=inv.product.categoryName or "",
                        branchId=inv.branchId,
                        branchName=branch_map.get(inv.branchId, "Sucursal"),
                        currentStock=float(inv.currentStock),
                        averageCost=round(inv.averageCost / 100.0, 2),
                        totalInventoryValue=round(
                            (inv.currentStock * inv.averageCost) / 100.0, 2
                        ),
                    )
                )
        return items

    async def get_bi_customers(self) -> list[BIClienteItem]:
        clients = await self.clients_repo.get_all_clients(ClientFilterParams())
        items: list[BIClienteItem] = []

        for cli in clients:
            items.append(
                BIClienteItem(
                    clientId=cli.id,
                    clientName=cli.name,
                    phone=cli.phone or "",
                    currentDebt=round(cli.balance / 100.0, 2),
                    totalPurchasesCount=0,
                    hasOverdueBalance=cli.balance > 0,
                )
            )
        return items

    async def _get_branch_map(self) -> dict[str, str]:
        branches = await self.branches_repo.get_all_branches()
        return {b.id: b.name for b in branches}

    @staticmethod
    def _normalize_date_range(
        start_date: int | None, end_date: int | None
    ) -> tuple[int, int]:
        return start_date or 0, end_date or END_DATE_DEFAULT
