from __future__ import annotations

from typing import Any, TYPE_CHECKING
from pydantic import BaseModel
from kardex.tools import UuidTool, TimeTools

if TYPE_CHECKING:
    from kardex.repos.v1.clients import ClientInDb

from kardex.repos.v1.client_transactions import (
    ClientTransactionInDb,
    TransactionSubType,
)
from kardex.services.mongo_collections.v1 import (
    ClientsCollection,
    ClientTransactionsCollection,
)


class FinanceTransactionRequest(BaseModel):
    client_id: str
    amount: int  # Usamos int (centavos) según tu función existente
    document_id: str
    doc_number: str
    subtype: TransactionSubType


async def process_client_financial_movement(
    request: FinanceTransactionRequest,
    session: Any,
    client_col: ClientsCollection,
    client_tx_col: ClientTransactionsCollection,
) -> ClientInDb:
    """
    Orquesta el movimiento de saldo y la creación del registro en el Kardex del cliente.
    """
    now = TimeTools.get_now_in_milliseconds()

    # 1. ACTUALIZAR SALDO (Usando TU función existente)
    # Si request.amount es positivo, SUMA (Deuda).
    # Si request.amount es negativo, RESTA (Pago).
    updated_client_data = await client_col.add_to_client_balance(
        client_id=request.client_id,
        amount=request.amount,
        timestamp=now,
        session=session,
    )

    updated_client = ClientInDb.model_validate(updated_client_data)

    # 2. DETERMINAR TIPO DE TRANSACCIÓN
    # Si el monto es positivo (o cero), es un DÉBITO (Cargo a la cuenta)
    # Si el monto es negativo, es un CRÉDITO (Abono a la cuenta)
    tx_type = "debit" if request.amount >= 0 else "credit"

    # 3. CREAR EL REGISTRO HISTÓRICO (KARDEX)
    new_tx = ClientTransactionInDb(
        id=UuidTool.generate_uuid(),
        clientId=request.client_id,
        documentId=request.document_id,
        docNumber=request.doc_number,
        # Guardamos el monto tal cual viene (con signo) o absoluto,
        # dependiendo de cómo prefieras mostrarlo en tu frontend.
        # Aquí lo dejo tal cual para consistencia matemática.
        amount=request.amount,
        type=tx_type,
        subtype=request.subtype,
        createdAt=now,
        resultBalance=updated_client.balance,  # El saldo YA actualizado
    )

    await client_tx_col.create_client_transaction_with_session(
        new_tx.model_dump(), session=session
    )

    return updated_client
