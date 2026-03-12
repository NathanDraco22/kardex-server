from typing import Tuple
from services.mongo_collections.v1 import (
    ReceiptsCollection,
    InvoicesCollection,
    ClientTransactionsCollection,
    ClientsCollection,
    DevolutionsCollection,
)
from repos.v1.invoices import InvoiceInDb
from repos.v1.receipts import CreateReceipt, ReceiptInDb
from repos.v1.client_transactions import ClientTransactionInDb
from repos.v1.clients import ClientInDb
from tools import UuidTool, TimeTools
from services import MongoService

from core.counter_manager.counter_manager import CounterManager


async def process_receipt(
    create_receipt: CreateReceipt,
) -> Tuple[ReceiptInDb, ClientInDb]:
    """
    Procesa un recibo, creando transacciones de cliente separadas para
    pagos y para la aplicación de devoluciones (notas de crédito).
    """
    mongo_client = MongoService().client
    receipt_col = ReceiptsCollection()
    invoice_col = InvoicesCollection()
    devolution_col = DevolutionsCollection()
    client_transaction_col = ClientTransactionsCollection()
    client_account_col = ClientsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. Validar Cuadratura de Sumas (Total + Devoluciones == Facturas Aplicadas)
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()
            total_funds = create_receipt.total + sum(
                d.amountApplied for d in create_receipt.appliedDevolutions
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
                # A. Validar que el monto no exceda el saldo pendiente (Overpayment Protection)
                current_invoice_data = (
                    await invoice_col.fetch_invoice_by_id_with_session(
                        invoice_id=applied_invoice.invoiceId, session=session
                    )
                )

                if current_invoice_data is None:
                    # Si no existe, fallará más adelante o aquí mismo.
                    # Asumimos que existe validación previa,
                    # pero por seguridad devolvemos error.
                    raise Exception(f"Invoice {applied_invoice.invoiceId} not found")

                current_invoice = InvoiceInDb.model_validate(current_invoice_data)

                total_amount = current_invoice.total
                amount_paid_so_far = current_invoice.amountPaid
                pending_balance = total_amount - amount_paid_so_far

                # Permitimos un pequeño margen de error por flotantes si fuera necesario,
                # pero aquí trabajamos con enteros (centavos presumably).
                if applied_invoice.amountApplied > pending_balance:
                    raise Exception(
                        f"Overpayment Error: Payment of {applied_invoice.amountApplied} "
                        f"exceeds pending balance of {pending_balance} "
                        f"for Invoice {current_invoice.docNumber}"
                    )

                # B. Aplicar el pago
                await invoice_col.add_to_amount_paid(
                    invoice_id=applied_invoice.invoiceId,
                    amount_paid=applied_invoice.amountApplied,
                    session=session,
                )

            final_client_account = None

            # 3. Procesar CADA DEVOLUCIÓN como una transacción de crédito individual
            for applied_devolution in create_receipt.appliedDevolutions:
                # Marcar la devolución como aplicada para que no se use de nuevo
                await devolution_col.update_devolution_status_by_id(
                    devolution_id=applied_devolution.devolutionId,
                    status="applied",
                    session=session,
                )

                # Actualizar el saldo del cliente
                updated_client_data = (
                    await client_account_col.substract_from_client_balance(
                        client_id=create_receipt.clientId,
                        amount=applied_devolution.amountApplied,
                        session=session,
                        timestamp=now_in_milliseconds,
                    )
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                # Crear la transacción específica para la DEVOLUCIÓN
                devolution_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_receipt.clientId,
                    documentId=applied_devolution.devolutionId,  # Enlaza a la devolución
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

            # 4. Procesar el PAGO MONETARIO como una transacción de crédito separada
            if create_receipt.total > 0:
                # Actualizar el saldo del cliente
                updated_client_data = (
                    await client_account_col.substract_from_client_balance(
                        client_id=create_receipt.clientId,
                        amount=create_receipt.total,
                        session=session,
                        timestamp=now_in_milliseconds,
                    )
                )
                final_client_account = ClientInDb.model_validate(updated_client_data)

                # Crear la transacción específica para el PAGO
                payment_transaction = ClientTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    clientId=create_receipt.clientId,
                    documentId=new_receipt_in_db.id,  # Enlaza al recibo
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

            # Si no hubo pago monetario, necesitamos obtener el estado final del cliente
            if final_client_account is None:
                client_data = await client_account_col.fetch_client_by_id(
                    create_receipt.clientId
                )
                final_client_account = ClientInDb.model_validate(client_data)

            return new_receipt_in_db, final_client_account
