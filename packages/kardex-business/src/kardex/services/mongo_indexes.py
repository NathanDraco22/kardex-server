import asyncio
import os

from kardex.services import BaseMongoCollection
from kardex.services.mongo_collections.v1 import (
    ProductsCollection,
    CountersCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    SuppliersCollection,
    ProductCategoriesCollection,
    ProductPricesCollection,
    EntryDocsCollection,
    ExitDocsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductTransactionsCollection,
    InvoicesCollection,
    OrdersCollection,
    ExpirationLogsCollection,
    DevolutionsCollection,
    DailySummariesCollection,
    ExecutiveSummariesCollection,
    ProductStatsCollection,
    TransfersCollection,
    AdjustEntriesCollection,
    AdjustExitsCollection,
    AdjustmentRequestsCollection,
    ExpensesCollection,
    ExpenseCategoriesCollection,
    ApiKeysCollection,
    CreditNotesCollection,
    ReceiptsCollection,
    UsersCollection,
    UserRolesCollection,
    CoreSettingsCollection,
    MetaCollection,
)
from kardex.services.mongo_collections.v1.meta_collection import (
    write_tenant_meta_document,
)

# Se sube en el mismo PR que cambia una definicion de indice.
CURRENT_INDEX_VERSION = 1

# 31 colecciones que definen ``create_indexes``. El runner y el
# aprovisionamiento las ejecutan en paralelo por tenant.
INDEXED_COLLECTIONS: tuple[type[BaseMongoCollection], ...] = (
    ProductsCollection,
    CountersCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    SuppliersCollection,
    ProductCategoriesCollection,
    ProductPricesCollection,
    EntryDocsCollection,
    ExitDocsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductTransactionsCollection,
    InvoicesCollection,
    CreditNotesCollection,
    OrdersCollection,
    ExpirationLogsCollection,
    DevolutionsCollection,
    DailySummariesCollection,
    ExecutiveSummariesCollection,
    ProductStatsCollection,
    TransfersCollection,
    AdjustEntriesCollection,
    AdjustExitsCollection,
    AdjustmentRequestsCollection,
    ExpensesCollection,
    ExpenseCategoriesCollection,
    ApiKeysCollection,
    ReceiptsCollection,
    UsersCollection,
    UserRolesCollection,
    CoreSettingsCollection,
)


def get_target_indexes_version() -> int:
    """Version de indices objetivo, con override de emergencia por entorno."""

    return int(os.getenv("INDEXES_VERSION", str(CURRENT_INDEX_VERSION)))


async def create_tenant_indexes(nickname: str) -> None:
    """Aplica los indices de todas las colecciones en la base del tenant."""

    async def _apply(collection_class: type[BaseMongoCollection]) -> None:
        collection = collection_class.get_instance(nickname)
        await collection.create_indexes()

    await asyncio.gather(*(_apply(collection) for collection in INDEXED_COLLECTIONS))


async def ensure_indexes_for_tenant(nickname: str) -> str:
    """Compara ``Meta.indexesVersion`` con la version objetivo y aplica.

    Devuelve la accion ejecutada: ``skipped``, ``skipped-newer`` o
    ``updated``. Nunca degrada indices: si la base esta mas adelantada que el
    codigo, solo advierte.
    """

    meta = await MetaCollection.get_instance(nickname).read_tenant_meta()
    stored = int(meta.get("indexesVersion", 0)) if meta else 0
    target = get_target_indexes_version()

    if stored == target:
        return "skipped"

    if stored > target:
        print(
            f"WARN tenant={nickname}: indices stored={stored} > target={target}. "
            "Servidor mas viejo que los datos; no se toca."
        )
        return "skipped-newer"

    await create_tenant_indexes(nickname)
    await write_tenant_meta_document(
        nickname,
        is_provisioned=True,
        indexes_version=target,
    )
    return "updated"
