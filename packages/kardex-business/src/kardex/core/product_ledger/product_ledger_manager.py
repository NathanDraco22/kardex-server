import asyncio
from fastapi import HTTPException, status

from kardex.repos.v1.entry_docs import (
    EntryDocsRepository,
    EntryDocsDataSource,
    CreateEntryDoc,
    EntryDocInDb,
)

from kardex.repos.v1.exit_docs import (
    ExitDocsRepository,
    ExitDocsDataSource,
    CreateExitDoc,
    ExitDocInDb,
)

from pymongo.errors import OperationFailure

from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountsDataSource,
)
from kardex.repos.v1.products import ProductsRepository, ProductsDataSource

from kardex.tools import BranchesTool


from .process_entry_doc import process_entry_doc
from .process_exit_doc import process_exit_doc
from kardex.tools import InsufficientBalanceError


class ProductLedgerManager:
    def __init__(self, follow_transactions: bool = True) -> None:
        self.entry_docs_repo = EntryDocsRepository(entry_docs_ds=EntryDocsDataSource())
        self.exit_docs_repo = ExitDocsRepository(exit_docs_ds=ExitDocsDataSource())
        self.branches_repo = BranchesRepository(
            branches_ds=BranchesDataSource(),
        )
        self.product_accounts_repo = ProductAccountsRepository(
            product_accounts_ds=ProductAccountsDataSource(),
        )
        self.products_repo = ProductsRepository(
            products_ds=ProductsDataSource(),
        )

        self.follow_transactions = follow_transactions

    async def regis_entry_doc(self, create_entry_doc: CreateEntryDoc) -> EntryDocInDb:
        entry_doc = await self.entry_docs_repo.get_entry_doc_by_doc_number_and_supplier(
            supplier_id=create_entry_doc.supplierId,
            doc_number=create_entry_doc.docNumber,
        )

        if entry_doc is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DOCUMENT_EXISTS",
            )

        await self._validate_document(create_entry_doc)

        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_entry_doc(
                    create_entry_doc,
                    self.follow_transactions,
                )
                return result

            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)

                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing account entry transaction \n" + str(e),
                    )

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing account entry transaction \n" + str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, try again later",
        )

    async def regis_exit_doc(self, create_exit_doc: CreateExitDoc) -> ExitDocInDb:
        exit_doc = await self.exit_docs_repo.get_exit_doc_by_doc_number_and_client(
            client_id=create_exit_doc.clientId, doc_number=create_exit_doc.docNumber
        )

        if exit_doc is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DOCUMENT_EXISTS",
            )

        await self._validate_document(create_exit_doc)

        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_exit_doc(
                    create_exit_doc, self.follow_transactions
                )
                return result

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
                        detail="Error processing account exit transaction \n" + str(e),
                    )

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing account exit transaction \n" + str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, try again later",
        )

    async def _validate_document(self, doc):
        branch = BranchesTool().get_branch_by_id(doc.branchId)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )

        product_ids = list(set(item.productId for item in doc.items))
        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="PRODUCT_NOT_FOUND"
            )
