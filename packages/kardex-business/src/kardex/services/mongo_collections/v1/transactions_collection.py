from typing import Any
from kardex.services import BaseMongoCollection


class TransactionsCollection(BaseMongoCollection):
    collection_name = "Transactions"

    async def create_transaction(self, transaction: dict) -> None:
        collection = self._collection
        await collection.insert_one(transaction)

    async def fetch_all_transactions(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_transaction_by_id(
        self, transaction_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": transaction_id})
        return result

    # MARK - Mongo Transaction Methods

    async def create_transaction_with_session(
        self,
        transaction_data: dict,
        session: Any,
    ) -> None:
        collection = self._collection
        await collection.insert_one(
            transaction_data,
            session=session,
        )

    async def create_many_transactions_with_session(
        self,
        transactions_data: list[dict],
        session: Any,
    ) -> None:
        collection = self._collection
        await collection.insert_many(
            transactions_data,
            session=session,
        )
