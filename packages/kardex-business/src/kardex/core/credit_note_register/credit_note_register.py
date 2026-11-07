import asyncio
from pymongo.errors import OperationFailure

from kardex.repos.v1.credit_notes import CreateCreditNote, CreditNoteInDb
from kardex.repos.v1.clients import ClientsRepository
from kardex.repos.v1.invoices import InvoicesRepository
from kardex.repos.v1.branches import BranchesRepository
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.tools import InvalidOperation, BranchNotFound, ClientNotFound

from .process_credit_note import process_credit_note


class CreditNoteRegister:
    def __init__(
        self,
        branches_repo: BranchesRepository,
        clients_repo: ClientsRepository,
        invoices_repo: InvoicesRepository,
    ) -> None:
        self.branches_repo = branches_repo
        self.clients_repo = clients_repo
        self.invoices_repo = invoices_repo

    async def register_credit_note(
        self, create_credit_note: CreateCreditNote
    ) -> CreditNoteInDb:
        await self._validate_credit_note(create_credit_note)

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_credit_note(create_credit_note)
            except OperationFailure as e:
                if e.code == 112:  # WriteConflict
                    await asyncio.sleep(0.3)
                else:
                    raise InvalidOperation(f"Database error: {e}")
            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")

    async def _validate_credit_note(self, doc: CreateCreditNote):
        # 1. Validar sucursal
        branch = await self.branches_repo.get_branch_by_id(doc.branchId)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=doc.branchId)

        # 2. Validar cliente (requerido para tipo 'amount')
        if doc.type == "amount":
            if doc.clientId == SALE_CLIENT_ID:
                raise InvalidOperation(
                    "Credit notes by amount require a registered client."
                )
            if doc.amount <= 0:
                raise InvalidOperation("Credit note amount must be greater than 0.")
            if not doc.description.strip():
                raise InvalidOperation(
                    "A detailed reason/description is required for credit notes by amount."
                )

        if doc.clientId != SALE_CLIENT_ID:
            client = await self.clients_repo.get_client_by_id(doc.clientId)
            if client is None:
                raise ClientNotFound("CLIENT_NOT_FOUND", client_id=doc.clientId)

        # 3. Validar tipo 'devolution'
        if doc.type == "devolution":
            if doc.originalInvoiceId:
                invoice = await self.invoices_repo.get_invoice_by_id(
                    doc.originalInvoiceId
                )
                if invoice is None:
                    raise InvalidOperation(
                        f"Original invoice {doc.originalInvoiceId} not found."
                    )
            if not doc.returnedItems:
                raise InvalidOperation(
                    "Devolution credit notes must include returned items."
                )
            if doc.amount <= 0:
                raise InvalidOperation("Credit note total must be greater than 0.")
