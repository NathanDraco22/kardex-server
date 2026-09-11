from kardex.tools import UuidTool, TimeTools, BranchesTool, BranchNotFound
from kardex.repos.v1.entry_docs.models.entry_doc_model import CreateEntryDoc
from kardex.repos.v1.entry_docs import EntryDocInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    EntryDocsCollection,
    ProductAccountsCollection,
)


async def process_entry_doc_direct(
    entry_doc: CreateEntryDoc,
) -> EntryDocInDb:
    mongo_client = MongoService().client

    # Colecciones
    product_account_col = ProductAccountsCollection.get_instance()
    entry_docs_col = EntryDocsCollection.get_instance()

    # Tools
    branches_tool = BranchesTool()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            current_branch_in_db = branches_tool.get_branch_by_id(entry_doc.branchId)

            if current_branch_in_db is None:
                raise BranchNotFound("Branch not found in process")

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            new_entry_data = entry_doc.model_dump()
            new_entry_data["id"] = UuidTool.generate_uuid()
            new_entry_data["createdAt"] = now_in_milliseconds

            insert_result = await entry_docs_col.create_entry_doc_with_session(
                new_entry_data,
                session=session,
            )
            new_entry_doc_in_db = EntryDocInDb.model_validate(insert_result)

            items_data = [
                {
                    "productId": item.productId,
                    "quantity": item.quantity,
                    "cost": item.cost,
                }
                for item in entry_doc.items
            ]

            await product_account_col.bulk_add_product_accounts_direct(
                branch_id=entry_doc.branchId,
                items=items_data,
                session=session,
            )

            return new_entry_doc_in_db
