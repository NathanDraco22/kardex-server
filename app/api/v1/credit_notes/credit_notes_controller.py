from fastapi import HTTPException, status

from kardex.core.credit_note_register import CreditNoteRegister, reverse_credit_note
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.clients import ClientsRepository, ClientsDataSource
from kardex.repos.v1.invoices import InvoicesRepository, InvoicesDataSource
from kardex.repos.v1.credit_notes import (
    CreateCreditNote,
    CreditNoteInDb,
    CreditNotesRepository,
    CreditNotesDataSource,
)
from kardex.repos.v1.common.filter_params import CreditNoteFilterParams
from responses.v1 import ListResponse


class CreditNotesController:
    def __init__(self, credit_notes_repo: CreditNotesRepository) -> None:
        self.credit_notes_repo = credit_notes_repo
        self.credit_note_register = CreditNoteRegister(
            branches_repo=BranchesRepository(BranchesDataSource()),
            clients_repo=ClientsRepository(ClientsDataSource()),
            invoices_repo=InvoicesRepository(InvoicesDataSource()),
        )

    async def create_credit_note(self, body: CreateCreditNote) -> CreditNoteInDb:
        try:
            return await self.credit_note_register.register_credit_note(body)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    async def get_all_credit_notes(
        self, params: CreditNoteFilterParams
    ) -> ListResponse[CreditNoteInDb]:
        credit_notes = await self.credit_notes_repo.get_all_credit_notes(params)
        return ListResponse(count=len(credit_notes), data=credit_notes)

    async def get_all_active_credit_notes(
        self, params: CreditNoteFilterParams
    ) -> ListResponse[CreditNoteInDb]:
        credit_notes = await self.credit_notes_repo.get_all_active_credit_notes(params)
        return ListResponse(count=len(credit_notes), data=credit_notes)

    async def get_credit_notes_by_client_id(
        self, client_id: str, status: str | None = None
    ) -> ListResponse[CreditNoteInDb]:
        credit_notes = await self.credit_notes_repo.get_credit_notes_by_client_id(
            client_id, status
        )
        return ListResponse(count=len(credit_notes), data=credit_notes)

    async def get_credit_notes_by_invoice_id(
        self, invoice_id: str, client_id: str | None = None
    ) -> ListResponse[CreditNoteInDb]:
        credit_notes = await self.credit_notes_repo.get_credit_notes_by_invoice_id(
            invoice_id, client_id
        )
        return ListResponse(count=len(credit_notes), data=credit_notes)

    async def get_credit_note_by_id(self, credit_note_id: str) -> CreditNoteInDb:
        credit_note = await self.credit_notes_repo.get_credit_note_by_id(credit_note_id)
        if credit_note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CreditNote not found",
            )
        return credit_note

    async def get_credit_note_by_doc_number(
        self, doc_number: str
    ) -> CreditNoteInDb:
        credit_note = await self.credit_notes_repo.get_credit_note_by_doc_number(
            doc_number
        )
        if credit_note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CreditNote not found",
            )
        return credit_note

    async def get_credit_note_history(
        self, **kwargs
    ) -> ListResponse[CreditNoteInDb]:
        credit_notes = await self.credit_notes_repo.get_credit_note_history(**kwargs)
        return ListResponse(count=len(credit_notes), data=credit_notes)

    async def delete_credit_note_by_id(self, credit_note_id: str) -> CreditNoteInDb:
        try:
            return await reverse_credit_note(credit_note_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )


credit_notes_controller = CreditNotesController(
    credit_notes_repo=CreditNotesRepository(CreditNotesDataSource()),
)
