from kardex.repos.v1.transfers import TransferInDb, ReceiveTransferIntent

from kardex.repos.v1.product_accounts import ProductAccountInDb

from kardex.repos.v1.product_transactions import ProductTransactionInDb

from kardex.repos.v1.product_sale_profiles import CreateProductSaleProfile

from kardex.repos.v1.product_stats import CreateProductStat


from kardex.tools import UuidTool, TimeTools, BranchesTool


from kardex.services import MongoService

from kardex.services.mongo_collections.v1 import (
    TransfersCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)


async def process_incoming_transfer(
    transfer_id: str,
    intent: ReceiveTransferIntent,
) -> tuple[TransferInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client

    # Colecciones necesarias

    transfers_col = TransfersCollection.get_instance()

    product_account_col = ProductAccountsCollection.get_instance()

    product_stats_col = ProductStatsCollection.get_instance()

    product_prof_col = ProductSaleProfilesCollection.get_instance()

    prd_transaction_col = ProductTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            # 1. OBTENER EL TRASLADO EXISTENTE

            # Necesitamos leer los items y el destination original

            existing_transfer_dict = (
                await transfers_col.fetch_transfer_by_id_with_session(
                    transfer_id, session=session
                )
            )

            if not existing_transfer_dict:
                raise Exception(f"Traslado {transfer_id} no encontrado")

            # Convertimos a objeto para trabajar fácil

            transfer_doc = TransferInDb.model_validate(existing_transfer_dict)

            # (Opcional) Validar que no haya sido recibido ya

            if transfer_doc.status != "inTransit":
                raise Exception("Este traslado ya fue procesado anteriormente")

            destination_branch_in_db = BranchesTool().get_branch_by_id(
                transfer_doc.destination
            )

            if destination_branch_in_db is None:
                raise Exception("Sucursal de Destino no encontrada")

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            destination_branch = transfer_doc.destination

            items_to_receive = transfer_doc.items

            updated_dest_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            sale_profiles: list[CreateProductSaleProfile] = []

            new_product_stats: list[CreateProductStat] = []

            # 2. PROCESAR CADA ITEM (Igual que un Entry Doc)

            for item in items_to_receive:
                # A. Sumar al Stock del DESTINO y Recalcular Costo Promedio

                # Usamos item.cost (que viene del origen) como costo de entrada

                result = await product_account_col.update_product_account_balance_data(
                    product_id=item.id,
                    branch_id=destination_branch,  # <--- IMPORTANTE: Sucursal Destino
                    add_to_current_stock=item.quantity,  # Cantidad Positiva (Entrada)
                    last_cost=item.cost,  # Costo (int/centavos)
                    session=session,
                )

                updated_account = ProductAccountInDb.model_validate(result)

                updated_dest_accounts.append(updated_account)

                # B. Inicializar Perfil de Venta (Si no existe en esta sucursal)

                sale_profile = CreateProductSaleProfile(
                    branchId=destination_branch,
                    productId=item.id,
                    salePrice=0,  # Ojo: Entra con precio 0, alguien deberá ponerle precio luego
                    salePrice2=0,
                    salePrice3=0,
                    salePrice4=0,
                )

                sale_profiles.append(sale_profile)

                if destination_branch_in_db.isCommerce:
                    # C. Inicializar Stats (Si no existe en esta sucursal)

                    product_stats = CreateProductStat(
                        branchId=destination_branch,
                        productId=item.id,
                        startDate=now_in_milliseconds,
                        endDate=now_in_milliseconds,
                        totalUnits=0,
                        totalTransactions=0,
                        daysAnalyzed=0,
                        lastEstimation=now_in_milliseconds,
                    )

                    new_product_stats.append(product_stats)

                # D. Crear Transacción de ENTRADA

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=transfer_doc.id,
                    docNumber=transfer_doc.docNumber,
                    type="entry",  # Tipo Entrada (Suma inventario)
                    subtype="transfer",  # Subtipo específico
                    productId=item.id,
                    branchId=destination_branch,
                    # REGLA: Entrada = Positivo
                    quantity=abs(item.quantity),
                    averageCost=updated_account.averageCost,
                    createdAt=now_in_milliseconds,
                    resultStock=updated_account.currentStock,
                )

                created_transactions.append(new_transaction)

            # 3. ACTUALIZAR EL DOCUMENTO DE TRASLADO

            # Usamos los datos del Intent (fecha, usuario, status)

            update_data = intent.model_dump()

            # Nota: Necesitarás un método update_transfer_with_session en tu colección

            updated_transfer_dict = (
                await transfers_col.update_transfer_status_with_session(
                    transfer_id=transfer_id, update_data=update_data, session=session
                )
            )

            updated_transfer_in_db = TransferInDb.model_validate(updated_transfer_dict)

            # 4. INSERTAR PERFILES DE VENTA EN LOTE

            sale_profiles_raw = [sp.model_dump() for sp in sale_profiles]

            await product_prof_col.bulk_create_product_sale_profiles(
                sale_profiles_raw, session=session
            )

            if destination_branch_in_db.isCommerce:
                # 4. INSERTAR STATS EN LOTE

                new_product_stats_raw = [ps.model_dump() for ps in new_product_stats]

                await product_stats_col.bulk_create_product_stats_if_not_exist(
                    new_product_stats_raw, session=session
                )

            # 4. INSERTAR TRANSACCIONES EN LOTE

            created_transactions_data = [t.model_dump() for t in created_transactions]

            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            return updated_transfer_in_db, updated_dest_accounts
