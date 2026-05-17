from __future__ import annotations

from typing import Any
from pydantic import BaseModel
from kardex.tools import UuidTool, TimeTools

from kardex.repos.v1.clients.models.client_model import ClientInDb

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
    amount: int
    document_id: str
    doc_number: str
    subtype: TransactionSubType


class ClientFinanceEngine:
    @staticmethod
    async def process_movement(
        request: FinanceTransactionRequest,
        session: Any,
        client_col: ClientsCollection,
        client_tx_col: ClientTransactionsCollection,
    ) -> ClientInDb:
        now = TimeTools.get_now_in_milliseconds()

        updated_client_data = await client_col.add_to_client_balance(
            client_id=request.client_id,
            amount=request.amount,
            timestamp=now,
            session=session,
        )

        updated_client = ClientInDb.model_validate(updated_client_data)

        tx_type = "debit" if request.amount >= 0 else "credit"

        new_tx = ClientTransactionInDb(
            id=UuidTool.generate_uuid(),
            clientId=request.client_id,
            documentId=request.document_id,
            docNumber=request.doc_number,
            amount=request.amount,
            type=tx_type,
            subtype=request.subtype,
            createdAt=now,
            resultBalance=updated_client.balance,
        )

        await client_tx_col.create_client_transaction_with_session(
            new_tx.model_dump(), session=session
        )

        return updated_client
