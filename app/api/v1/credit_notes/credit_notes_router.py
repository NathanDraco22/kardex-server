from fastapi import APIRouter, Depends
from kardex.repos.v1.credit_notes import (
    CreateCreditNote,
    ApproveCreditNote,
    RejectCreditNote,
    CreditNoteInDb,
)
from kardex.repos.v1.common.filter_params import CreditNoteFilterParams
from responses.v1 import ListResponse

from app_middleware import auth_middleware
from .credit_notes_controller import credit_notes_controller

credit_notes_router = APIRouter(
    tags=["credit_notesV1"], dependencies=[Depends(auth_middleware)]
)


@credit_notes_router.post("")
async def create_credit_note(body: CreateCreditNote) -> CreditNoteInDb:
    return await credit_notes_controller.create_credit_note(body)


@credit_notes_router.post("/{credit_note_id}/approve")
async def approve_credit_note(
    credit_note_id: str, body: ApproveCreditNote
) -> CreditNoteInDb:
    return await credit_notes_controller.approve_credit_note(credit_note_id, body)


@credit_notes_router.post("/{credit_note_id}/reject")
async def reject_credit_note(
    credit_note_id: str, body: RejectCreditNote
) -> CreditNoteInDb:
    return await credit_notes_controller.reject_credit_note(credit_note_id, body)


@credit_notes_router.get("")
async def get_all_credit_notes(
    params: CreditNoteFilterParams = Depends(),
) -> ListResponse[CreditNoteInDb]:
    return await credit_notes_controller.get_all_credit_notes(params)


@credit_notes_router.get("/all/active")
async def get_all_active_credit_notes(
    params: CreditNoteFilterParams = Depends(),
) -> ListResponse[CreditNoteInDb]:
    return await credit_notes_controller.get_all_active_credit_notes(params)


@credit_notes_router.get("/client/{client_id}")
async def get_credit_notes_by_client_id(
    client_id: str, status: str | None = None
) -> ListResponse[CreditNoteInDb]:
    return await credit_notes_controller.get_credit_notes_by_client_id(
        client_id, status
    )


@credit_notes_router.get("/invoice/{invoice_id}")
async def get_credit_notes_by_invoice_id(
    invoice_id: str, client_id: str | None = None
) -> ListResponse[CreditNoteInDb]:
    return await credit_notes_controller.get_credit_notes_by_invoice_id(
        invoice_id, client_id
    )


@credit_notes_router.get("/doc/{doc_number}")
async def get_credit_note_by_doc_number(doc_number: str) -> CreditNoteInDb:
    return await credit_notes_controller.get_credit_note_by_doc_number(doc_number)


@credit_notes_router.get("/{credit_note_id}")
async def get_credit_note_by_id(credit_note_id: str) -> CreditNoteInDb:
    return await credit_notes_controller.get_credit_note_by_id(credit_note_id)


@credit_notes_router.delete("/{credit_note_id}")
async def delete_credit_note_by_id(credit_note_id: str) -> CreditNoteInDb:
    return await credit_notes_controller.delete_credit_note_by_id(credit_note_id)
