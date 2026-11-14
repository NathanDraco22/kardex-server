from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.products import ProductsRepository
from kardex.services.mongo_collections.v1 import ProductAccountsCollection
from kardex.tools import BranchNotFound, BranchesTool, InvalidOperation, ProductNotFound

from ..base import PipelineStep
from ..context import AdjustmentRequestContext


class ValidateRequestStep(PipelineStep[AdjustmentRequestContext]):
    """Valida que la solicitud siga pendiente y que el aprobador tenga permiso."""

    async def execute(self, context: AdjustmentRequestContext) -> None:
        request = context.request

        if request.isDeleted:
            raise InvalidOperation("ADJUSTMENT_REQUEST_NOT_FOUND")

        if request.status != "pending":
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_APPROVED")

        if context.approver_role not in ("Admin", "Supervisor"):
            raise InvalidOperation("APPROVAL_REQUIRES_SUPERVISOR_OR_ADMIN")

        if (
            context.approved_by.id == request.createdBy.id
            and context.approver_role != "Admin"
        ):
            raise InvalidOperation("SELF_APPROVAL_NOT_ALLOWED")


class SplitItemsStep(PipelineStep[AdjustmentRequestContext]):
    """Separa los ítems en sobrantes (entrada) y faltantes (salida)."""

    async def execute(self, context: AdjustmentRequestContext) -> None:
        context.entry_items = [
            item for item in context.request.items if item.difference > 0
        ]
        context.exit_items = [
            item for item in context.request.items if item.difference < 0
        ]

        if not context.entry_items and not context.exit_items:
            raise InvalidOperation("ADJUSTMENT_REQUEST_WITHOUT_DIFFERENCES")


class LoadBranchStep(PipelineStep[AdjustmentRequestContext]):
    def __init__(self, branches_tool: BranchesTool | None = None):
        self.branches_tool = branches_tool or BranchesTool()

    async def execute(self, context: AdjustmentRequestContext) -> None:
        branch = self.branches_tool.get_branch_by_id(context.request.branchId)

        if branch is None:
            raise BranchNotFound(
                "BRANCH_NOT_FOUND",
                branch_id=context.request.branchId,
            )

        context.branch = branch


class LoadProductsStep(PipelineStep[AdjustmentRequestContext]):
    def __init__(self, products_repo: ProductsRepository):
        self.products_repo = products_repo

    async def execute(self, context: AdjustmentRequestContext) -> None:
        product_ids = list(
            {
                item.productId
                for item in [*context.entry_items, *context.exit_items]
            }
        )

        if not product_ids:
            return

        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise ProductNotFound("PRODUCT_NOT_FOUND")

        context.product_ids = product_ids


class LoadAccountsStep(PipelineStep[AdjustmentRequestContext]):
    def __init__(self, product_accounts_col: ProductAccountsCollection):
        self.product_accounts_col = product_accounts_col

    async def execute(self, context: AdjustmentRequestContext) -> None:
        if not context.product_ids:
            return

        accounts = await self.product_accounts_col.get_accounts_by_branch_id(
            branch_id=context.request.branchId,
            product_ids=context.product_ids,
            session=context.session,
        )

        context.accounts = {
            account["productId"]: ProductAccountInDb.model_validate(account)
            for account in accounts
        }
