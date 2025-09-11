import asyncio
from fastapi import HTTPException, status

from repos.v1.invoices import (
    CreateInvoice,
    InvoicesRepository,
    InvoicesDataSource,
    InvoiceInDb,
)

from pymongo.errors import OperationFailure

from core.counter_manager.counter_manager import CounterManager

from repos.v1.clients import ClientInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.products import ProductsRepository, ProductsDataSource

from .process_invoice import process_invoice, InsufficientBalanceError


class InvoiceRegister:
    def __init__(self) -> None:
        self.invoices_repo = InvoicesRepository(InvoicesDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.products_repo = ProductsRepository(ProductsDataSource())

    async def regis_invoice(
        self, create_invoice: CreateInvoice
    ) -> tuple[InvoiceInDb, ClientInDb]:
        if len(create_invoice.docNumber) == 0:
            create_invoice.docNumber = await CounterManager().next_invoice_number()

        invoice = await self.invoices_repo.get_invoice_by_doc_number(
            create_invoice.docNumber
        )
        if invoice is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invoice already exists",
            )

        await self._validate_document(create_invoice)

        max_retries = 3

        for _ in range(max_retries):
            try:
                return await process_invoice(create_invoice)

            except InsufficientBalanceError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="INSUFFICIENT_STOCK_FOR_ONE_OR_MORE_PRODUCTS",
                )

            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)

                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing account entry transaction \n" + str(e),
                    )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing account entry transaction",
        )

    async def _validate_document(self, doc: CreateInvoice):
        branch = await self.branches_repo.get_branch_by_id(doc.branchId)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )

        product_ids = list(set(item.product.id for item in doc.saleItems))
        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="PRODUCT_NOT_FOUND"
            )
