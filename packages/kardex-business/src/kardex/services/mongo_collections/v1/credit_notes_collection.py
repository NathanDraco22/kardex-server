from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection
from kardex.tools import TimeTools


class CreditNotesCollection(BaseMongoCollection):
    collection_name = "CreditNotes"

    async def create_credit_note(self, credit_note: dict) -> None:
        collection = self._collection
        await collection.insert_one(credit_note)

    async def create_credit_note_with_session(
        self, credit_note: dict, session: Any
    ) -> dict[str, Any]:
        collection = self._collection
        await collection.insert_one(credit_note, session=session)
        return credit_note

    async def fetch_all_credit_notes(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        query = {key: value for key, value in kwargs.items() if value is not None}
        cursor = collection.find(query).sort("createdAt", -1)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_all_active_credit_notes(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        query = {key: value for key, value in kwargs.items() if value is not None}
        query["status"] = {"$in": ["confirmed", "open"]}
        cursor = collection.find(query).sort("createdAt", -1)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_credit_notes_by_client_id(
        self, client_id: str, status: str | None = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query: dict[str, Any] = {"clientId": client_id}
        if status is not None:
            query["status"] = status
        cursor = collection.find(query).sort("createdAt", -1)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_credit_notes_by_invoice_id(
        self, invoice_id: str, client_id: str | None = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query: dict[str, Any] = {"originalInvoiceId": invoice_id}
        if client_id is not None:
            query["clientId"] = client_id
        cursor = collection.find(query).sort("createdAt", -1)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_credit_note_by_id(self, credit_note_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": credit_note_id})
        return result

    async def fetch_credit_note_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def update_credit_note_by_id(
        self,
        credit_note_id: str,
        credit_note: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": credit_note_id},
            {"$set": credit_note},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def update_credit_note_status_by_id(
        self,
        credit_note_id: str,
        status: str,
        session: Any = None,
        receipt_id: str | None = None,
        receipt_doc_number: str | None = None,
    ) -> dict[str, Any] | None:
        collection = self._collection
        update_doc: dict[str, Any] = {
            "status": status,
            "updatedAt": TimeTools.get_now_in_milliseconds(),
        }
        if receipt_id is not None:
            update_doc["appliedReceiptId"] = receipt_id
            update_doc["appliedReceiptDocNumber"] = receipt_doc_number or ""
            update_doc["appliedAt"] = TimeTools.get_now_in_milliseconds()

        result = await collection.find_one_and_update(
            {"id": credit_note_id},
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return result

    async def delete_credit_note_by_id(self, credit_note_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": credit_note_id})
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)]),
                IndexModel([("clientId", 1)]),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
                IndexModel([("type", 1)]),
                IndexModel([("status", 1)]),
                IndexModel([("originalInvoiceId", 1)]),
                IndexModel([("createdBy.id", 1)]),
            ]
        )

    async def fetch_history_credit_notes(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        query = {key: value for key, value in kwargs.items() if value is not None}
        if kwargs.get("endDate") is not None:
            query["createdAt"] = {"$lte": kwargs.get("endDate")}
            del query["endDate"]

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)
        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        result = await cursor.to_list(length=None)
        return result
