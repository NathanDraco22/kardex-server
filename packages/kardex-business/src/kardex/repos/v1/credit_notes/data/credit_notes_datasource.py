from typing import Any
from kardex.services.mongo_collections.v1 import CreditNotesCollection


class CreditNotesDataSource:
    async def create_credit_note(self, credit_note: dict[str, Any]) -> dict[str, Any]:
        collection = CreditNotesCollection.get_instance()
        await collection.create_credit_note(credit_note)
        return credit_note

    async def get_all_credit_notes(self, **kwargs) -> list[dict[str, Any]]:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_all_credit_notes(**kwargs)

    async def get_all_active_credit_notes(self, **kwargs) -> list[dict[str, Any]]:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_all_active_credit_notes(**kwargs)

    async def get_credit_notes_by_client_id(
        self, client_id: str, status: str | None = None
    ) -> list[dict[str, Any]]:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_credit_notes_by_client_id(client_id, status)

    async def get_credit_notes_by_invoice_id(
        self, invoice_id: str, client_id: str | None = None
    ) -> list[dict[str, Any]]:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_credit_notes_by_invoice_id(invoice_id, client_id)

    async def get_credit_note_by_id(self, credit_note_id: str) -> dict[str, Any] | None:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_credit_note_by_id(credit_note_id)

    async def get_credit_note_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_credit_note_by_doc_number(doc_number)

    async def update_credit_note_by_id(
        self, credit_note_id: str, credit_note: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CreditNotesCollection.get_instance()
        return await collection.update_credit_note_by_id(credit_note_id, credit_note)

    async def delete_credit_note_by_id(self, credit_note_id: str) -> dict[str, Any] | None:
        collection = CreditNotesCollection.get_instance()
        return await collection.delete_credit_note_by_id(credit_note_id)

    async def get_credit_note_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = CreditNotesCollection.get_instance()
        return await collection.fetch_history_credit_notes(**kwargs)
