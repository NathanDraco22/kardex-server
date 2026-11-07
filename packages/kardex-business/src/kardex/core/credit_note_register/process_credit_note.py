from typing import List

from kardex.repos.v1.credit_notes import CreateCreditNote, CreditNoteInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.tools import UuidTool, TimeTools
from kardex.services import MongoService


async def process_credit_note(
    create_credit_note: CreateCreditNote,
) -> CreditNoteInDb:
    """
    Procesa la creación de una nota de crédito de forma atómica:
    1. Si type == 'devolution':
       - Reingresa los items al inventario (ProductAccount).
       - Registra ProductTransaction (type='entry', subtype='credit_note').
    2. Si type == 'amount':
       - Solo registra el documento de crédito por el monto establecido (sin tocar inventario).
    3. Asigna número de documento correlativo si no viene especificado.
    4. Guarda la nota de crédito en MongoDB con status='confirmed'.
    """
    mongo_client = MongoService().client
    credit_note_col = CreditNotesCollection.get_instance()
    prd_account_col = ProductAccountsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            credit_note_id = UuidTool.generate_uuid()

            if not create_credit_note.docNumber:
                create_credit_note.docNumber = (
                    await CounterManager().next_credit_note_number(session=session)
                )

            # 1. Si es de tipo devolución de productos, reingresamos stock a la sucursal
            if create_credit_note.type == "devolution" and create_credit_note.returnedItems:
                created_product_transactions: List[ProductTransactionInDb] = []

                for item in create_credit_note.returnedItems:
                    quantity_to_add = abs(item.quantity)
                    if quantity_to_add == 0:
                        continue

                    updated_account_data = (
                        await prd_account_col.update_product_account_balance_data(
                            product_id=item.product.id,
                            branch_id=create_credit_note.branchId,
                            add_to_current_stock=quantity_to_add,
                            last_cost=item.cost,
                            session=session,
                        )
                    )
                    updated_product_account = ProductAccountInDb.model_validate(
                        updated_account_data
                    )

                    new_prod_transaction = ProductTransactionInDb(
                        id=UuidTool.generate_uuid(),
                        documentId=credit_note_id,
                        docNumber=create_credit_note.docNumber,
                        type="entry",
                        subtype="credit_note",
                        productId=item.product.id,
                        branchId=create_credit_note.branchId,
                        quantity=quantity_to_add,
                        averageCost=updated_product_account.averageCost,
                        resultStock=updated_product_account.currentStock,
                        createdAt=now_in_milliseconds,
                    )
                    created_product_transactions.append(new_prod_transaction)

                if created_product_transactions:
                    product_transactions_data = [
                        t.model_dump() for t in created_product_transactions
                    ]
                    await prd_transaction_col.create_many_product_transactions_with_session(
                        product_transactions_data, session=session
                    )

            # 2. Crear el documento de la nota de crédito
            new_credit_note_data = create_credit_note.model_dump()
            new_credit_note_data["id"] = credit_note_id
            new_credit_note_data["status"] = "confirmed"
            new_credit_note_data["createdAt"] = now_in_milliseconds
            new_credit_note_data["updatedAt"] = None

            await credit_note_col.create_credit_note_with_session(
                new_credit_note_data, session=session
            )

            return CreditNoteInDb.model_validate(new_credit_note_data)
