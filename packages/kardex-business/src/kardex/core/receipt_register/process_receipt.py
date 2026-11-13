from typing import Tuple
from kardex.services.mongo_collections.v1 import (
    ReceiptsCollection,
    InvoicesCollection,
    ClientTransactionsCollection,
    ClientsCollection,
    DevolutionsCollection,
    CreditNotesCollection,
)
from kardex.repos.v1.invoices import InvoiceInDb
from kardex.repos.v1.receipts import CreateReceipt, ReceiptInDb
from kardex.repos.v1.client_transactions import ClientTransactionInDb
from kardex.repos.v1.clients import ClientInDb
from kardex.tools import UuidTool, TimeTools
from kardex.services import MongoService

from kardex.core.counter_manager.counter_manager import CounterManager


async def process_receipt(
    create_receipt: CreateReceipt,
) -> Tuple[ReceiptInDb, ClientInDb]:
    """
    Procesa un recibo, creando transacciones de cliente separadas para
    pagos, devoluciones y notas de crédito aplicadas.
    """
    mongo_client = MongoService().client
    receipt_col = ReceiptsCollection.get_instance()
    invoice_col = InvoicesCollection.get_instance()
    devolution_col = DevolutionsCollection.get_instance()
    credit_note_col = CreditNotesCollection.get_instance()
    client_transaction_col = ClientTransactionsCollection.get_instance()
    client_account_col = ClientsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            # 1. Validar Cuadratura de Sumas (Total + Devoluciones + Notas de Crédito == Facturas Aplicadas)
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            total_funds = (
                create_receipt.total
                + sum(d.amountApplied for d in create_receipt.appliedDevolutions)
                + sum(c.amountApplied for c in create_receipt.appliedCreditNotes)
            )
            total_applied = sum(i.amountApplied for i in create_receipt.appliedInvoices)

            if not create_receipt.docNumber:
                create_receipt.docNumber = await CounterManager().next_receipt_number(
                    session
                )

            if total_funds != total_applied:
                raise Exception(
                    f"Discrepancy Error: Total Funds ({total_funds}) "
                    f"does not match Total Applied to Invoices ({total_applied})."
                )

            # Validar que cada nota de crédito esté aprobada
            for applied_credit_note in create_receipt.appliedCreditNotes:
                cn_data = await credit_note_col.fetch_credit_note_by_id(
                    applied_credit_note.creditNoteId
                )
                if not cn_data:
                    raise Exception(
                        f"Nota de crédito {applied_credit_note.creditNoteId} no encontrada."
                    )
                if cn_data.get("status") not in ("approved", "confirmed"):
                    raise Exception(
                        f"La nota de crédito #{cn_data.get('docNumber', '')} no está aprobada (estado: {cn_data.get('status')})."
                    )

            # 2. Crear el documento de recibo
            new_receipt_data = create_receipt.model_dump()
            new_receipt_data["id"] = UuidTool.generate_uuid()
            new_receipt_data["createdAt"] = now_in_milliseconds

            insert_result = await receipt_col.create_receipt_with_session(
                new_receipt_data, session=session
            )
            new_receipt_in_db = ReceiptInDb.model_validate(insert_result)

            # 3. Aplicar el pago a cada factura involucrada
            for applied_invoice in create_receipt.appliedInvoices:
                current_invoice_data = (
                    await invoice_col.fetch_invoice_by_id_with_session(
                        invoice_id=applied_invoice.invoiceId, session=session
                    )
                )

                if current_invoice_data is None:
                    raise Exception(f"Invoice {applied_invoice.invoiceId} not found")

                current_invoice = InvoiceInDb.model_validate(current_invoice_data)

                total_amount = current_invoice.total
                amount_paid_so_far = current_invoice.amountPaid
                pending_balance = total_amount - amount_paid_so_far

                if applied_invoice.amountApplied > pending_balance:
                    raise Exception(
                        f"Overpayment Error: Payment of {applied_invoice.amountApplied} "
                        f"exceeds pending balance of {pending_balance} "
                        f"for Invoice {current_invoice.docNumber}"
                    )

                await invoice_col.add_to_amount_paid(
                    invoice_id=applied_invoice.invoiceId,
                    amount_paid=applied_invoice.amountApplied,
                    session=session,
                )

            final_client_account = None

            # 4. Procesar CADA DEVOLUCIÓN como una transacción de crédito individual
            for applied_devolution in create_receipt.appliedDevolutions:
                await devolution_col.update_devolution_status_by_id(
                    devolution_id=applied_devolution.devolutionId,
                    status="applied",
                    session=session,
                )

                updated_client_data = (
                    await client_account_col.substract_from_client_balance(
                        client_id=create_receipt.clientId,
                        amount=applied_devolution.amountApplied,
                        session=session,
                        timestamp=now_in_milliseconds,
                    )
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                devolution_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_receipt.clientId,
                    documentId=applied_devolution.devolutionId,
                    docNumber=applied_devolution.docNumber,
                    amount=-abs(applied_devolution.amountApplied),
                    type="credit",
                    subtype="devolution",
                    resultBalance=final_client_account.balance,
                    createdAt=now_in_milliseconds,
                )
                await client_transaction_col.create_client_transaction_with_session(
                    devolution_transaction.model_dump(), session=session
                )

            # 5. Procesar CADA NOTA DE CRÉDITO como una transacción de crédito individual
            for applied_credit_note in create_receipt.appliedCreditNotes:
                await credit_note_col.update_credit_note_status_by_id(
                    credit_note_id=applied_credit_note.creditNoteId,
                    status="applied",
                    session=session,
                    receipt_id=new_receipt_in_db.id,
                    receipt_doc_number=new_receipt_in_db.docNumber,
                )

                updated_client_data = (
                    await client_account_col.substract_from_client_balance(
                        client_id=create_receipt.clientId,
                        amount=applied_credit_note.amountApplied,
                        session=session,
                        timestamp=now_in_milliseconds,
                    )
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                credit_note_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_receipt.clientId,
                    documentId=applied_credit_note.creditNoteId,
                    docNumber=applied_credit_note.docNumber,
                    amount=-abs(applied_credit_note.amountApplied),
                    type="credit",
                    subtype="credit_note",
                    resultBalance=final_client_account.balance,
                    createdAt=now_in_milliseconds,
                )
                await client_transaction_col.create_client_transaction_with_session(
                    credit_note_transaction.model_dump(), session=session
                )

            # 6. Procesar el PAGO MONETARIO como una transacción de crédito separada
            if create_receipt.total > 0:
                updated_client_data = (
                    await client_account_col.substract_from_client_balance(
                        client_id=create_receipt.clientId,
                        amount=create_receipt.total,
                        session=session,
                        timestamp=now_in_milliseconds,
                    )
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                payment_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_receipt.clientId,
                    documentId=new_receipt_in_db.id,
                    docNumber=create_receipt.docNumber,
                    amount=-abs(create_receipt.total),
                    type="credit",
                    subtype="receipt",
                    resultBalance=final_client_account.balance,
                    createdAt=now_in_milliseconds,
                )
                await client_transaction_col.create_client_transaction_with_session(
                    payment_transaction.model_dump(), session=session
                )

            if final_client_account is None:
                client_data = await client_account_col.fetch_client_by_id(
                    create_receipt.clientId
                )
                final_client_account = ClientInDb.model_validate(client_data)

            return new_receipt_in_db, final_client_account
