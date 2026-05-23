from kardex.core.inventory import (
    InventoryExitBatchItem,
    InventoryBatchTransformer,
    InventoryEngine,
)
from kardex.tools import UuidTool, TimeTools, BranchesTool, BranchNotFound
from kardex.repos.v1.exit_docs import ExitDocInDb, CreateExitDoc
from kardex.repos.v1.product_accounts import ProductAccountInDb

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ExitDocsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


async def process_exit_doc(
    create_exit_doc: CreateExitDoc,
) -> ExitDocInDb:
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    product_account_col = ProductAccountsCollection.get_instance()

    branches_tool = BranchesTool()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            current_branch_in_db = branches_tool.get_branch_by_id(
                create_exit_doc.branchId
            )

            if current_branch_in_db is None:
                raise BranchNotFound(
                    "Branch not found in process", branch_id=create_exit_doc.branchId
                )

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            new_exit_doc_generated_id = UuidTool.generate_uuid()

            new_exit_data = create_exit_doc.model_dump()
            new_exit_data["id"] = new_exit_doc_generated_id
            new_exit_data["createdAt"] = now_in_milliseconds

            insert_result = (
                await ExitDocsCollection.get_instance().create_exit_doc_with_session(
                    new_exit_data,
                    session=session,
                )
            )

            new_exit_doc_in_db = ExitDocInDb.model_validate(insert_result)

            batch_items = [
                InventoryExitBatchItem(
                    product_id=item.productId,
                    product_name=item.productName,
                    quantity=item.quantity,
                )
                for item in create_exit_doc.items
            ]

            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=create_exit_doc.branchId,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            batch_result = InventoryBatchTransformer.prepare_exit(
                branch_id=create_exit_doc.branchId,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                document_id=new_exit_doc_in_db.id,
                doc_number=new_exit_doc_in_db.docNumber,
                tx_type="exit",
                tx_subtype="exit",
            )

            await InventoryEngine.execute_exit(
                branch_id=create_exit_doc.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
            )

            return new_exit_doc_in_db
