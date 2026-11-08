import asyncio

from kardex.repos.v1.common.filter_params import DevolutionFilterParams
from kardex.repos.v1.credit_notes import CreditNotesDataSource, CreditNotesRepository
from kardex.repos.v1.devolutions import DevolutionsDataSource, DevolutionsRepository
from kardex.repos.v1.invoices import InvoicesDataSource, InvoicesRepository

from .composite_models import (
    ClientPendingInvoicesCompositeResponse,
    PendingCheckoutSummary,
)


class CompositeController:
    def __init__(
        self,
        invoices_repo: InvoicesRepository,
        devolutions_repo: DevolutionsRepository,
        credit_notes_repo: CreditNotesRepository,
    ) -> None:
        self.invoices_repo = invoices_repo
        self.devolutions_repo = devolutions_repo
        self.credit_notes_repo = credit_notes_repo

    async def get_client_pending_invoices(
        self, client_id: str, branch_id: str
    ) -> ClientPendingInvoicesCompositeResponse:
        dev_params = DevolutionFilterParams(clientId=client_id, branchId=branch_id)

        invoices_task = self.invoices_repo.get_pending_to_paid_invoices(client_id)
        devolutions_task = self.devolutions_repo.get_all_active_devolutions(dev_params)
        credit_notes_task = self.credit_notes_repo.get_credit_notes_by_client_id(
            client_id=client_id, status="confirmed"
        )

        invoices, devolutions, credit_notes = await asyncio.gather(
            invoices_task, devolutions_task, credit_notes_task
        )

        total_invoices = sum(max(0, inv.total - inv.amountPaid) for inv in invoices)
        total_devolutions = sum(dev.total for dev in devolutions)
        total_credit_notes = sum(cn.amount for cn in credit_notes)
        net_total = max(0, total_invoices - total_devolutions - total_credit_notes)

        return ClientPendingInvoicesCompositeResponse(
            invoices=invoices,
            devolutions=devolutions,
            creditNotes=credit_notes,
            summary=PendingCheckoutSummary(
                totalInvoices=total_invoices,
                totalDevolutions=total_devolutions,
                totalCreditNotes=total_credit_notes,
                netTotalPayable=net_total,
            ),
        )


composite_controller = CompositeController(
    invoices_repo=InvoicesRepository(InvoicesDataSource()),
    devolutions_repo=DevolutionsRepository(DevolutionsDataSource()),
    credit_notes_repo=CreditNotesRepository(CreditNotesDataSource()),
)
