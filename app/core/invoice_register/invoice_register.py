import asyncio
from typing import Callable, Coroutine
from fastapi import HTTPException, status
from tools import BranchesTool

from repos.v1.invoices import (
    CreateInvoice,
    InvoicesRepository,
    InvoicesDataSource,
    InvoiceInDb,
)

from pymongo.errors import OperationFailure

from core.counter_manager.counter_manager import CounterManager
from core.default_values import SALE_CLIENT_ID

from repos.v1.clients import ClientInDb
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.products import ProductsRepository, ProductsDataSource

from .process_invoice import (
    process_invoice,
    InsufficientBalanceError,
    process_anon_invoice,
)


class InvoiceRegister:
    def __init__(self) -> None:
        self.invoices_repo = InvoicesRepository(InvoicesDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.products_repo = ProductsRepository(ProductsDataSource())

    async def _register_transaction(
        self,
        create_invoice: CreateInvoice,
        process_function: Callable[[CreateInvoice], Coroutine],
    ):
        if len(create_invoice.docNumber) == 0:
            create_invoice.docNumber = await CounterManager().next_invoice_number()

        invoice = await self.invoices_repo.get_invoice_by_doc_number(
            create_invoice.docNumber
        )
        if invoice is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invoice with this document number already exists",
            )

        await self._validate_document(create_invoice)

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_function(create_invoice)
            except InsufficientBalanceError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"INSUFFICIENT_STOCK: {e}",
                )
            except OperationFailure as _:
                await asyncio.sleep(0.3)
                continue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, please try again later",
        )

    async def regis_invoice(
        self, create_invoice: CreateInvoice
    ) -> tuple[InvoiceInDb, ClientInDb]:
        if create_invoice.clientId == SALE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use the anonymous invoice endpoint for this client.",
            )
        return await self._register_transaction(create_invoice, process_invoice)

    async def regis_anon_invoice(
        self, create_invoice: CreateInvoice
    ) -> tuple[InvoiceInDb, list[ProductAccountInDb]]:
        if create_invoice.clientId != SALE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID for anonymous invoice.",
            )
        return await self._register_transaction(create_invoice, process_anon_invoice)

    async def _validate_document(self, doc: CreateInvoice):
        branch = BranchesTool().get_branch_by_id(doc.branchId)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )
