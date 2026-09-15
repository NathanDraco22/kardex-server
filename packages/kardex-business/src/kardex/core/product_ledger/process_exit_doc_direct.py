from kardex.tools import UuidTool, TimeTools, BranchesTool, BranchNotFound
from kardex.repos.v1.exit_docs import ExitDocInDb, CreateExitDoc
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ExitDocsCollection,
    ProductAccountsCollection,
)


async def process_exit_doc_direct(
    create_exit_doc: CreateExitDoc,
) -> ExitDocInDb:
    mongo_client = MongoService().client
    product_account_col = ProductAccountsCollection.get_instance()
    exit_docs_col = ExitDocsCollection.get_instance()

    branches_tool = BranchesTool()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            current_branch_in_db = branches_tool.get_branch_by_id(
                create_exit_doc.branchId
            )

            if current_branch_in_db is None:
                raise BranchNotFound(
                    "Branch not found in process", branch_id=create_exit_doc.branchId
                )

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            new_exit_doc_generated_id = UuidTool.generate_uuid()

            product_ids = [item.productId for item in create_exit_doc.items]

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

            for item in create_exit_doc.items:
                if item.cost is None:
                    account = accounts_dict.get(item.productId)
                    item.cost = account.averageCost if account else 0

            new_exit_data = create_exit_doc.model_dump()
            new_exit_data["id"] = new_exit_doc_generated_id
            new_exit_data["createdAt"] = now_in_milliseconds

            insert_result = await exit_docs_col.create_exit_doc_with_session(
                new_exit_data,
                session=session,
            )
            new_exit_doc_in_db = ExitDocInDb.model_validate(insert_result)

            items_data = [
                {
                    "productId": item.productId,
                    "quantity": item.quantity,
                }
                for item in create_exit_doc.items
            ]

            await product_account_col.bulk_substract_product_accounts_direct(
                branch_id=create_exit_doc.branchId,
                items=items_data,
                session=session,
            )

            return new_exit_doc_in_db
