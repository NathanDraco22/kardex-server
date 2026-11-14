from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.credit_notes import CreditNoteInDb
from kardex.services.mongo_collections.v1 import CreditNotesCollection
from kardex.tools import InvalidOperation, TimeTools


async def reject_credit_note(
    credit_note_id: str,
    rejected_by: UserInfo,
    reason: str,
) -> CreditNoteInDb:
    """
    Rechaza una nota de crédito formalmente:
    1. Valida que la nota exista y su estado sea 'emitted'.
    2. Registra el motivo de rechazo y los datos de auditoría (rejectedBy, rejectedAt).
    3. Cambia el estado a 'rejected'. No toca inventario físico.
    """
    credit_note_col = CreditNotesCollection.get_instance()

    raw = await credit_note_col.fetch_credit_note_by_id(credit_note_id)
    if not raw:
        raise ValueError("Nota de crédito no encontrada.")

    credit_note = CreditNoteInDb.model_validate(raw)

    if credit_note.status != "emitted":
        raise InvalidOperation(
            f"Solo se pueden rechazar notas de crédito en estado emitida. Estado actual: {credit_note.status}."
        )

    now_in_milliseconds = TimeTools.get_now_in_milliseconds()

    update_data = {
        "status": "rejected",
        "rejectedBy": rejected_by.model_dump(),
        "rejectedAt": now_in_milliseconds,
        "rejectionReason": reason.strip(),
        "updatedAt": now_in_milliseconds,
    }

    updated_raw = await credit_note_col.update_credit_note_fields_by_id(
        credit_note_id, update_data
    )
    return CreditNoteInDb.model_validate(updated_raw)
