from kardex.repos.v1.credit_notes import CreditNoteInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.services import MongoService


async def reverse_credit_note(credit_note_id: str) -> CreditNoteInDb:
    """
    Revierte y elimina una nota de crédito de forma atómica:
    - Valida que la nota exista.
    - Valida que su estado no sea 'applied' (si ya fue aplicada en un recibo, no se puede eliminar).
    - Si fue por devolución ('devolution') y tiene items reingresados:
        - Descuenta los items del inventario físico (ProductAccount.currentStock).
        - Elimina las transacciones de Kárdex generadas (ProductTransaction con documentId == credit_note_id).
    - Elimina el documento de la nota de crédito.
    """
    credit_note_col = CreditNotesCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    mongo_client = MongoService().client

    raw_credit_note = await credit_note_col.fetch_credit_note_by_id(credit_note_id)
    if not raw_credit_note:
        raise ValueError("Nota de crédito no encontrada.")

    credit_note = CreditNoteInDb.model_validate(raw_credit_note)

    if credit_note.status == "applied":
        raise ValueError(
            "No se puede eliminar una nota de crédito que ya fue aplicada en un recibo de pago."
        )

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            # 1. Si estaba aprobada/confirmada y fue devolución, revertimos el stock
            if (
                credit_note.status in ("approved", "confirmed")
                and credit_note.type == "devolution"
                and credit_note.returnedItems
            ):
                for item in credit_note.returnedItems:
                    quantity_to_remove = abs(item.quantity)
                    if quantity_to_remove == 0:
                        continue

                    # Restar del stock reingresado
                    await prd_account_col.substract_product_account_data(
                        product_id=item.product.id,
                        branch_id=credit_note.branchId,
                        substract_to_current_stock=quantity_to_remove,
                        session=session,
                        allow_negative=True,
                    )

                # Eliminar las transacciones de entrada generadas por esta nota
                await prd_transaction_col.delete_transactions_by_document_id_with_session(
                    document_id=credit_note_id, session=session
                )

            # 2. Eliminar la nota de crédito
            await credit_note_col.delete_credit_note_by_id_with_session(
                credit_note_id=credit_note_id, session=session
            )

    return credit_note
