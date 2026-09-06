from datetime import datetime
from kardex.tools import TimeTools
from kardex.repos.v1.daily_summaries import (
    DailySummariesRepository,
    DailySummariesDataSource,
)
from kardex.repos.v1.executive_summaries import (
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
    ExecutiveSummaryInDb,
)
from kardex.repos.v1.receipts import ReceiptsRepository
from kardex.repos.v1.invoices import InvoicesRepository
from kardex.repos.v1.common.models import (
    InventoryBranchDetail,
    CommercialBranchDetail,
)
from kardex.core.report_manager.report_manager import ReportManager

from kardex.repos.v1.common.filter_params import (
    ReportFilterParams,
    TotalsFilterParams,
    InvoiceFilterParams,
    ReceiptFilterParams,
)
from .responses import TotalsResult


class ReportsController:
    def __init__(
        self,
        daily_summaries_repo: DailySummariesRepository,
        executive_summaries_repo: ExecutiveSummariesRepository,
    ):
        self.daily_summaries_repo = daily_summaries_repo
        self.executive_summaries_repo = executive_summaries_repo
        self.report_manager = ReportManager()
        self.receipts_repo = ReceiptsRepository.get_instance()
        self.invoices_repo = InvoicesRepository.get_instance()

    async def get_general_report(
        self, params: ReportFilterParams
    ) -> ExecutiveSummaryInDb:
        # 1. Resumen de facturas y recibos en tiempo real
        invoice_summary = await self.report_manager.get_invoice_summary(
            startDate=params.startDate,
            endDate=params.endDate,
        )

        # 2. Resumen de gastos en tiempo real
        expenses_data = await self.report_manager.get_expenses_summary_in_range(
            params.startDate, params.endDate
        )
        expenses_by_branch = expenses_data.get("branches", {})

        # 3. Resumen de inventario actual de todas las sucursales
        inventory_result = await self.report_manager.get_total_inventory_all_branches()
        inventory_branches = [
            InventoryBranchDetail(
                branchId=branch.id,
                inventoryTotalCost=total,
            )
            for branch, total in inventory_result.results
        ]

        # 4. Resumen de cuentas por cobrar pendientes (CxC)
        pending_branches = (
            await self.report_manager.get_pending_invoice_totals_by_branch()
        )
        total_pending_invoices = sum(b.count for b in pending_branches)

        # 5. Construir lista consolidada de CommercialBranchDetail por sucursal
        all_branches = (
            await self.report_manager.branches_repo.get_all_commerce_branches()
        )

        invoices_dict = (
            {b_id: model for b_id, model in invoice_summary.results}
            if invoice_summary
            else {}
        )
        receipts_dict = (
            {b_id: model for b_id, model in invoice_summary.receiptResults}
            if invoice_summary
            else {}
        )

        commercial_branches = []
        for branch in all_branches:
            inv = invoices_dict.get(branch.id)
            rec = receipts_dict.get(branch.id)
            exp = expenses_by_branch.get(branch.id, {})

            commercial_branches.append(
                CommercialBranchDetail(
                    branchId=branch.id,
                    total=inv.totalSales if inv else 0,
                    totalCost=inv.totalCost if inv else 0,
                    totalPaid=inv.totalPaid if inv else 0,
                    totalOwed=inv.totalOwed if inv else 0,
                    creditSales=inv.creditSales if inv else 0,
                    cashSales=inv.cashSales if inv else 0,
                    totalInvoices=inv.totalInvoices if inv else 0,
                    totalReceiptCash=rec.totalAppliedInvoices if rec else 0,
                    totalReceiptDevolutions=rec.totalAppliedDevolutions if rec else 0,
                    totalReceipts=rec.totalReceipts if rec else 0,
                    receiptCount=rec.receiptCount if rec else 0,
                    expensesTotal=exp.get("expensesTotal", 0),
                    expensesPaid=exp.get("expensesPaid", 0),
                )
            )

        year = datetime.now().year
        month = datetime.now().month

        executive_summary = ExecutiveSummaryInDb(
            id="None",
            dateId="None",
            year=year,
            month=month,
            startDate=params.startDate,
            endDate=params.endDate,
            salesTotal=invoice_summary.totalSales if invoice_summary else 0,
            salesTotalCost=invoice_summary.totalCost if invoice_summary else 0,
            creditSales=invoice_summary.creditSales if invoice_summary else 0,
            cashSales=invoice_summary.cashSales if invoice_summary else 0,
            totalInvoices=invoice_summary.totalInvoices if invoice_summary else 0,
            totalPendingInvoices=total_pending_invoices,
            totalPendingBranches=pending_branches,
            totalReceiptCash=invoice_summary.totalReceiptCash if invoice_summary else 0,
            totalReceiptDevolutions=(
                invoice_summary.totalReceiptDevolutions if invoice_summary else 0
            ),
            totalReceipts=invoice_summary.totalReceipts if invoice_summary else 0,
            receiptCount=invoice_summary.receiptCount if invoice_summary else 0,
            commercialBranches=commercial_branches,
            inventoryTotalCost=inventory_result.total,
            inventoryBranches=inventory_branches,
            expensesTotal=expenses_data.get("expensesTotal", 0),
            expensesPaid=expenses_data.get("expensesPaid", 0),
            type="custom",
            createdAt=TimeTools.get_now_in_milliseconds(),
        )
        return executive_summary

    async def get_total_results_by_date_range(
        self, params: TotalsFilterParams
    ) -> TotalsResult:
        invoices_totals = await self.invoices_repo.get_totals_invoices_by_payment_type(
            params
        )
        receipts = await self.receipts_repo.get_totals_from_receipts_by_payment_method(
            params
        )

        invoice_filter = InvoiceFilterParams(
            branchId=params.branchId,
            startDate=params.startDate,
            endDate=params.endDate,
            createdBy=params.userId,
        )
        receipt_filter = ReceiptFilterParams(
            branchId=params.branchId,
            startDate=params.startDate,
            endDate=params.endDate,
            createdBy=params.userId,
        )
        detail_invoices = await self.invoices_repo.get_all_invoices(invoice_filter)
        detail_receipts = await self.receipts_repo.get_all_receipts(receipt_filter)

        return TotalsResult(
            branchId=params.branchId,
            invoices=invoices_totals,
            receipts=receipts,
            detailInvoices=detail_invoices,
            detailReceipts=detail_receipts,
        )


reports_controller = ReportsController(
    daily_summaries_repo=DailySummariesRepository(
        daily_summaries_ds=DailySummariesDataSource(),
    ),
    executive_summaries_repo=ExecutiveSummariesRepository(
        executive_summaries_ds=ExecutiveSummariesDataSource(),
    ),
)
