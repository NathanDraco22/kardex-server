from typing import List

from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.credit_notes import CreditNoteInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import InvalidOperation, UuidTool, TimeTools
from kardex.services import MongoService


async def approve_credit_note(
    credit_note_id: str,
    approved_by: UserInfo,
) -> CreditNoteInDb:
    """
    Aprueba una nota de crédito formalmente:
    1. Valida que la nota exista y su estado sea 'emitted'.
    2. Si es de tipo devolución ('devolution'):
       - Reingresa los productos al inventario físico (ProductAccount.currentStock).
       - Registra ProductTransaction (type='entry', subtype='credit_note').
    3. Cambia el estado a 'approved' y registra approvedBy y approvedAt.
    """
    credit_note_col = CreditNotesCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    mongo_client = MongoService().client

    raw = await credit_note_col.fetch_credit_note_by_id(credit_note_id)
    if not raw:
        raise ValueError("Nota de crédito no encontrada.")

    credit_note = CreditNoteInDb.model_validate(raw)

    if credit_note.status != "emitted":
        raise InvalidOperation(
            f"Solo se pueden aprobar notas de crédito en estado emitida. Estado actual: {credit_note.status}."
        )

    now_in_milliseconds = TimeTools.get_now_in_milliseconds()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            # 1. Si es devolución, reingresar stock físico y registrar transacciones
            if credit_note.type == "devolution" and credit_note.returnedItems:
                created_transactions: List[ProductTransactionInDb] = []

                for item in credit_note.returnedItems:
                    quantity_to_add = abs(item.quantity)
                    if quantity_to_add == 0:
                        continue

                    updated_account_data = (
                        await prd_account_col.update_product_account_balance_data(
                            product_id=item.product.id,
                            branch_id=credit_note.branchId,
                            add_to_current_stock=quantity_to_add,
                            last_cost=item.cost,
                            session=session,
                        )
                    )
                    updated_account = ProductAccountInDb.model_validate(
                        updated_account_data
                    )

                    new_transaction = ProductTransactionInDb(
                        id=UuidTool.generate_uuid(),
                        documentId=credit_note.id,
                        docNumber=credit_note.docNumber,
                        type="entry",
                        subtype="credit_note",
                        productId=item.product.id,
                        branchId=credit_note.branchId,
                        quantity=quantity_to_add,
                        averageCost=updated_account.averageCost,
                        resultStock=updated_account.currentStock,
                        createdAt=now_in_milliseconds,
                    )
                    created_transactions.append(new_transaction)

                if created_transactions:
                    tx_data = [t.model_dump() for t in created_transactions]
                    await prd_transaction_col.create_many_product_transactions_with_session(
                        tx_data, session=session
                    )

            # 2. Actualizar estado y auditoría de la nota de crédito
            update_data = {
                "status": "approved",
                "approvedBy": approved_by.model_dump(),
                "approvedAt": now_in_milliseconds,
                "updatedAt": now_in_milliseconds,
            }

            await credit_note_col.update_credit_note_fields_by_id(
                credit_note_id, update_data, session=session
            )

    updated_raw = await credit_note_col.fetch_credit_note_by_id(credit_note_id)
    return CreditNoteInDb.model_validate(updated_raw)
