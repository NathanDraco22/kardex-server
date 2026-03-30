import random
from typing import Tuple
from dataclasses import dataclass
from tools import UuidTool, TimeTools
from tools.search_tools import generate_prefixes
from core.counter_manager.counter_manager import CounterManager
from core.finance import process_client_financial_movement, FinanceTransactionRequest

from repos.v1.clients import CreateClient, ClientInDb
from repos.v1.invoices import CreateInvoice, InvoiceInDb
from repos.v1.common.models import UserInfo, ClientInfo, SaleItem, ProductItem

from services import MongoService
from services.mongo_collections.v1 import (
    ClientsCollection,
    InvoicesCollection,
    ClientTransactionsCollection,
)


async def process_create_client_with_balance(
    create_client: CreateClient,
    branch_id: str,
) -> Tuple[ClientInDb, InvoiceInDb]:
    """
    Crea un cliente y, si tiene un saldo inicial mayor a 0,
    genera una factura por ese saldo usando una transacción multidocumento.
    """
    mongo_client = MongoService().client

    client_col = ClientsCollection()
    invoice_col = InvoicesCollection()
    client_tx_col = ClientTransactionsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            current_time = TimeTools.get_now_in_milliseconds()

            # ==========================================
            # 1. CREACIÓN DEL CLIENTE
            # ==========================================
            client_number = await CounterManager().next_client_number(session=session)

            client_data_dump = create_client.model_dump(exclude={"initialBalance"})

            new_client_in_db = ClientInDb(
                id=client_number,
                createdAt=current_time,
                **client_data_dump,
            )

            new_client_in_db_data = new_client_in_db.model_dump()
            new_client_in_db_data["searchPrefixes"] = generate_prefixes(
                new_client_in_db.name
            )

            await client_col.create_client_with_session(
                new_client_in_db_data, session=session
            )

            # ==========================================
            # 2. CREACIÓN DE LA FACTURA DE SALDO INICIAL
            # ==========================================
            new_invoice_id = UuidTool.generate_uuid()

            invoice_doc_number = client_number

            client_info = ClientInfo(
                name=new_client_in_db.name,
                phone=new_client_in_db.phone or "",
                address=new_client_in_db.address or "",
                email=new_client_in_db.email or "",
                cardId=new_client_in_db.cardId or "",
            )

            initial_balance_item = SaleItem(
                product=ProductItem(
                    id="INITIAL_BALANCE",
                    name="SALDO INICIAL",
                    unitName="UNIDAD",
                    brandName="SISTEMA",
                    categoryName="SISTEMA",
                    tags=["INITIAL_BALANCE"],
                ),
                selectedPrice=1,
                quantity=1,
                bonQuantity=0,
                cost=create_client.initialBalance,
                price=create_client.initialBalance,
                subTotal=create_client.initialBalance,
                discountPercentage=0,
                totalDiscount=0,
                iva=0,
                total=create_client.initialBalance,
            )

            create_invoice_data = CreateInvoice(
                branchId=branch_id,
                clientId=client_number,
                clientInfo=client_info,
                docNumber=invoice_doc_number,
                saleItems=[initial_balance_item],
                description="Saldo Inicial",
                amountPaid=0,
                status="open",
                paymentType="credit",
                totalCost=create_client.initialBalance,
                total=create_client.initialBalance,
                createdBy=UserInfo(
                    id="system",
                    name="SISTEMA",
                ),
            )

            new_invoice_data = create_invoice_data.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_id,
                    "createdAt": current_time,
                    "paidAt": None,
                }
            )

            await invoice_col.create_invoice_with_session(
                new_invoice_data, session=session
            )
            new_invoice_in_db = InvoiceInDb.model_validate(new_invoice_data)

            # ==========================================
            # 3. GESTIÓN FINANCIERA (Cargo / Deuda)
            # ==========================================
            client = await process_client_financial_movement(
                request=FinanceTransactionRequest(
                    client_id=client_number,
                    amount=new_invoice_in_db.total,
                    document_id=new_invoice_id,
                    doc_number=new_invoice_in_db.docNumber,
                    subtype="invoice",
                ),
                session=session,
                client_col=client_col,
                client_tx_col=client_tx_col,
            )

            return client, new_invoice_in_db


async def create_initial_balance(
    client: ClientInDb, initial_balance: int, branch_id: str, product_name: str
) -> ClientInDb:
    """
    Agrega un saldo inicial a un cliente existente mediante la creación
    de una factura y un movimiento financiero en una transacción de base de datos.
    """
    mongo_client = MongoService().client

    client_col = ClientsCollection()
    invoice_col = InvoicesCollection()
    client_tx_col = ClientTransactionsCollection()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            current_time = TimeTools.get_now_in_milliseconds()

            new_invoice_id = UuidTool.generate_uuid()

            invoice_doc_number = client.id

            client_info = ClientInfo(
                name=client.name,
                phone=client.phone or "",
                address=client.address or "",
                email=client.email or "",
                cardId=client.cardId or "",
            )

            sale_item_name = product_name if product_name else "SALDO INICIAL"

            initial_balance_item = SaleItem(
                product=ProductItem(
                    id="INITIAL_BALANCE",
                    name=sale_item_name,
                    unitName="UNIDAD",
                    brandName="SISTEMA",
                    categoryName="SISTEMA",
                    tags=["INITIAL_BALANCE"],
                ),
                selectedPrice=1,
                quantity=1,
                bonQuantity=0,
                cost=initial_balance,
                price=initial_balance,
                subTotal=initial_balance,
                discountPercentage=0,
                totalDiscount=0,
                iva=0,
                total=initial_balance,
            )

            create_invoice_data = CreateInvoice(
                branchId=branch_id,
                clientId=client.id,
                clientInfo=client_info,
                docNumber=invoice_doc_number,
                saleItems=[initial_balance_item],
                description="APERTURA DE CUENTA",
                amountPaid=0,
                status="open",
                paymentType="credit",
                totalCost=initial_balance,
                total=initial_balance,
                createdBy=UserInfo(
                    id="system",
                    name="SISTEMA",
                ),
            )

            new_invoice_data = create_invoice_data.model_dump()
            new_invoice_data.update(
                {
                    "id": new_invoice_id,
                    "createdAt": current_time,
                    "paidAt": None,
                }
            )

            await invoice_col.create_invoice_with_session(
                new_invoice_data, session=session
            )
            new_invoice_in_db = InvoiceInDb.model_validate(new_invoice_data)

            client = await process_client_financial_movement(
                request=FinanceTransactionRequest(
                    client_id=client.id,
                    amount=new_invoice_in_db.total,
                    document_id=new_invoice_id,
                    doc_number=new_invoice_in_db.docNumber,
                    subtype="invoice",
                ),
                session=session,
                client_col=client_col,
                client_tx_col=client_tx_col,
            )

            return client


class InitialBalanceClient:
    def __init__(
        self,
        client: ClientInDb,
        initial_balance: int,
        branch_id: str,
        product_name: str,
    ):
        self.client = client
        self.initial_balance = initial_balance
        self.branch_id = branch_id
        self.product_name = product_name


async def create_multiple_initial_balance(
    balance_requests: list[InitialBalanceClient],
) -> list[ClientInDb]:
    """
    Agrega un saldo inicial a múltiples clientes existentes mediante la creación
    de facturas y movimientos financieros en una sola transacción de base de datos.
    """
    mongo_client = MongoService().client

    client_col = ClientsCollection()
    invoice_col = InvoicesCollection()
    client_tx_col = ClientTransactionsCollection()

    updated_clients: list[ClientInDb] = []

    # Iniciamos la sesión y la transacción UNA sola vez para todo el lote
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            current_time = TimeTools.get_now_in_milliseconds()

            for req in balance_requests:
                client = req.client
                initial_balance = req.initial_balance
                branch_id = req.branch_id
                product_name = req.product_name

                first_letter = client.name[0].upper()

                suffix = random.randint(0, 1000000)

                new_invoice_id = (
                    first_letter
                    + str(TimeTools.get_now_in_milliseconds())
                    + str(suffix)
                )

                # Nota: Si docNumber tiene un índice único en DB, asegúrate de que
                # client.id no cause colisiones si a un mismo cliente se le
                # aplican dos saldos iniciales distintos en el futuro.
                invoice_doc_number = new_invoice_id

                client_info = ClientInfo(
                    name=client.name,
                    phone=client.phone or "",
                    address=client.address or "",
                    email=client.email or "",
                    cardId=client.cardId or "",
                )

                sale_item_name = product_name if product_name else "SALDO INICIAL"

                initial_balance_item = SaleItem(
                    product=ProductItem(
                        id="INITIAL_BALANCE",
                        name=sale_item_name,
                        unitName="UNIDAD",
                        brandName="SISTEMA",
                        categoryName="SISTEMA",
                        tags=["INITIAL_BALANCE"],
                    ),
                    selectedPrice=1,
                    quantity=1,
                    bonQuantity=0,
                    cost=initial_balance,
                    price=initial_balance,
                    subTotal=initial_balance,
                    discountPercentage=0,
                    totalDiscount=0,
                    iva=0,
                    total=initial_balance,
                )

                create_invoice_data = CreateInvoice(
                    branchId=branch_id,
                    clientId=client.id,
                    clientInfo=client_info,
                    docNumber=invoice_doc_number,
                    saleItems=[initial_balance_item],
                    description="APERTURA DE CUENTA",
                    amountPaid=0,
                    status="open",
                    paymentType="credit",
                    totalCost=initial_balance,
                    total=initial_balance,
                    createdBy=UserInfo(
                        id="system",
                        name="SISTEMA",
                    ),
                )

                new_invoice_data = create_invoice_data.model_dump()
                new_invoice_data.update(
                    {
                        "id": UuidTool.generate_uuid(),
                        "createdAt": current_time,
                        "paidAt": None,
                    }
                )

                # 1. Creamos la factura
                await invoice_col.create_invoice_with_session(
                    new_invoice_data, session=session
                )
                new_invoice_in_db = InvoiceInDb.model_validate(new_invoice_data)

                # 2. Procesamos el movimiento financiero
                updated_client = await process_client_financial_movement(
                    request=FinanceTransactionRequest(
                        client_id=client.id,
                        amount=new_invoice_in_db.total,
                        document_id=new_invoice_id,
                        doc_number=new_invoice_in_db.docNumber,
                        subtype="invoice",
                    ),
                    session=session,
                    client_col=client_col,
                    client_tx_col=client_tx_col,
                )

                # Agregamos el cliente actualizado a nuestra lista de respuesta
                updated_clients.append(updated_client)

        # Si el bloque async with session.start_transaction() termina sin errores,
        # MongoDB hace el "commit" automático de todas las operaciones juntas.

        return updated_clients
