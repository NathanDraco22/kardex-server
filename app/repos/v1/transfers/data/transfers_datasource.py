from typing import Any
from services.mongo_collections.v1 import TransfersCollection


class TransfersDataSource:
    async def create_transfer(self, transfer: dict[str, Any]) -> dict[str, Any]:
        collection = TransfersCollection()
        await collection.create_transfer(transfer)
        return transfer

    async def get_all_transfers(self, **kwargs) -> list[dict[str, Any]]:
        collection = TransfersCollection()
        return await collection.fetch_all_transfers(**kwargs)

    async def get_transfer_by_id(self, transfer_id: str) -> dict[str, Any] | None:
        collection = TransfersCollection()
        return await collection.fetch_transfer_by_id(transfer_id)

    async def get_transfer_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = TransfersCollection()
        return await collection.fetch_tranfer_by_doc_number(doc_number)

    async def update_transfer_by_id(
        self, transfer_id: str, transfer: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = TransfersCollection()
        return await collection.update_transfer_by_id(transfer_id, transfer)

    async def delete_transfer_by_id(self, transfer_id: str) -> dict[str, Any] | None:
        collection = TransfersCollection()
        return await collection.delete_transfer_by_id(transfer_id)
