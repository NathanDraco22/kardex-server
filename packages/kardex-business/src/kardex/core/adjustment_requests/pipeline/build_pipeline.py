from kardex.repos.v1.products import ProductsDataSource, ProductsRepository
from kardex.services.mongo_collections.v1 import (
    AdjustEntriesCollection,
    AdjustExitsCollection,
    AdjustmentRequestsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import BranchesTool

from .base import Pipeline
from .context import AdjustmentRequestContext
from .steps.entry_steps import (
    ExecuteEntryStep,
    PersistEntryDocumentStep,
    PrepareEntryStep,
)
from .steps.exit_steps import (
    ExecuteExitStep,
    PersistExitDocumentStep,
    PrepareExitStep,
)
from .steps.finalize_steps import ApproveRequestStep, BuildResultStep
from .steps.request_steps import (
    LoadAccountsStep,
    LoadBranchStep,
    LoadProductsStep,
    SplitItemsStep,
    ValidateRequestStep,
)


def build_adjustment_request_pipeline() -> Pipeline[AdjustmentRequestContext]:
    """Construye el pipeline de aprobación de una solicitud de ajuste.

    El orden es intencional:
    1. Validar y separar los ítems.
    2. Cargar sucursal, productos y cuentas.
    3. Preparar/ejecutar/persistir la salida (si hay faltantes).
    4. Preparar/ejecutar/persistir la entrada (si hay sobrantes).
    5. Aprobar la solicitud y construir el resultado.

    Los steps de salida o entrada se omiten automáticamente con
    `should_execute` cuando la solicitud no tiene ítems de ese tipo.
    """

    product_accounts_col = ProductAccountsCollection.get_instance()
    product_transactions_col = ProductTransactionsCollection.get_instance()

    return Pipeline(
        [
            ValidateRequestStep(),
            SplitItemsStep(),
            LoadBranchStep(BranchesTool()),
            LoadProductsStep(
                ProductsRepository(products_ds=ProductsDataSource())
            ),
            LoadAccountsStep(product_accounts_col),
            PrepareExitStep(),
            ExecuteExitStep(product_accounts_col, product_transactions_col),
            PersistExitDocumentStep(AdjustExitsCollection.get_instance()),
            PrepareEntryStep(),
            ExecuteEntryStep(
                product_accounts_col,
                ProductSaleProfilesCollection.get_instance(),
                ProductStatsCollection.get_instance(),
                product_transactions_col,
            ),
            PersistEntryDocumentStep(AdjustEntriesCollection.get_instance()),
            ApproveRequestStep(AdjustmentRequestsCollection.get_instance()),
            BuildResultStep(),
        ]
    )
