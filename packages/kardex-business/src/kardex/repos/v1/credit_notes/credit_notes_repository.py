from kardex.tools import TimeTools, UuidTool
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.filter_params import CreditNoteFilterParams

from .data.credit_notes_datasource import CreditNotesDataSource
from .models.credit_note_model import (
    CreateCreditNote,
    UpdateCreditNote,
    CreditNoteInDb,
)


class CreditNotesRepository:
    _instance: "CreditNotesRepository | None" = None

    def __init__(self, credit_notes_ds: CreditNotesDataSource):
        self.credit_notes_ds = credit_notes_ds

    @classmethod
    def get_instance(cls) -> "CreditNotesRepository":
        if cls._instance is None:
            cls._instance = CreditNotesRepository(
                credit_notes_ds=CreditNotesDataSource()
            )
        return cls._instance

    async def create_credit_note(
        self, create_credit_note: CreateCreditNote
    ) -> CreditNoteInDb:
        if not create_credit_note.docNumber:
            create_credit_note.docNumber = (
                await CounterManager().next_credit_note_number()
            )
        new_credit_note = CreditNoteInDb(
            **create_credit_note.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.credit_notes_ds.create_credit_note(new_credit_note.model_dump())

        return new_credit_note

    async def get_all_credit_notes(
        self, params: CreditNoteFilterParams | None = None
    ) -> list[CreditNoteInDb]:
        kwargs = params.model_dump(exclude_unset=True) if params else {}
        results = await self.credit_notes_ds.get_all_credit_notes(**kwargs)
        return [CreditNoteInDb.model_validate(result) for result in results]

    async def get_all_active_credit_notes(
        self, params: CreditNoteFilterParams | None = None
    ) -> list[CreditNoteInDb]:
        kwargs = params.model_dump(exclude_unset=True) if params else {}
        results = await self.credit_notes_ds.get_all_active_credit_notes(**kwargs)
        return [CreditNoteInDb.model_validate(result) for result in results]

    async def get_credit_notes_by_client_id(
        self, client_id: str, status: str | None = None
    ) -> list[CreditNoteInDb]:
        results = await self.credit_notes_ds.get_credit_notes_by_client_id(
            client_id, status
        )
        return [CreditNoteInDb.model_validate(r) for r in results]

    async def get_credit_notes_by_invoice_id(
        self, invoice_id: str, client_id: str | None = None
    ) -> list[CreditNoteInDb]:
        results = await self.credit_notes_ds.get_credit_notes_by_invoice_id(
            invoice_id, client_id
        )
        return [CreditNoteInDb.model_validate(r) for r in results]

    async def get_credit_note_by_id(
        self, credit_note_id: str
    ) -> CreditNoteInDb | None:
        result = await self.credit_notes_ds.get_credit_note_by_id(credit_note_id)
        if result is None:
            return None
        return CreditNoteInDb.model_validate(result)

    async def get_credit_note_by_doc_number(
        self, doc_number: str
    ) -> CreditNoteInDb | None:
        result = await self.credit_notes_ds.get_credit_note_by_doc_number(doc_number)
        if result is None:
            return None
        return CreditNoteInDb.model_validate(result)

    async def update_credit_note_by_id(
        self, credit_note_id: str, credit_note: UpdateCreditNote
    ) -> CreditNoteInDb | None:
        updated_data = credit_note.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.credit_notes_ds.update_credit_note_by_id(
            credit_note_id, updated_data
        )
        if result is None:
            return None
        return CreditNoteInDb.model_validate(result)

    async def delete_credit_note_by_id(
        self, credit_note_id: str
    ) -> CreditNoteInDb | None:
        result = await self.credit_notes_ds.delete_credit_note_by_id(credit_note_id)
        if result is None:
            return None
        return CreditNoteInDb.model_validate(result)

    async def get_credit_note_history(self, **kwargs) -> list[CreditNoteInDb]:
        results = await self.credit_notes_ds.get_credit_note_history(**kwargs)
        return [CreditNoteInDb.model_validate(result) for result in results]
