from typing import Any

from pymongo import ReturnDocument
from kardex.services import BaseMongoCollection


class AccountBalancesCollection(BaseMongoCollection):
    collection_name = "AccountBalances"

    async def fetch_account_balance(
        self,
        account_id: str,
        branch_id: str,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {
                "accountId": account_id,
                "branchId": branch_id,
            }
        )
        return result

    async def update_account_balance_by_id(
        self,
        account_balance_id: str,
        account_balance: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": account_balance_id},
            {"$set": account_balance},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_account_balance_by_id(
        self, account_balance_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": account_balance_id})
        return result

    # Mark: Transactions method

    async def update_account_balance_with_session(
        self,
        account_id: str,
        branch_id: str,
        quantity: int,
        updated_at: int,
        session: Any,
    ) -> dict[str, Any]:
        collection = self._collection

        result = await collection.find_one_and_update(
            {
                "accountId": account_id,
                "branchId": branch_id,
            },
            {
                "$inc": {
                    "balance": quantity,
                },
                "$set": {
                    "updatedAt": updated_at,
                },
            },
            session=session,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def subtract_account_balance_with_session(
        self,
        account_id: str,
        branch_id: str,
        quantity: int,
        updated_at: int,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {
                "accountId": account_id,
                "branchId": branch_id,
                "balance": {"$gte": abs(quantity)},
            },
            {
                "$inc": {
                    "balance": quantity,
                },
                "$set": {
                    "updatedAt": updated_at,
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result
