import pytest

from kardex.core.adjustment_requests.pipeline import (
    AdjustmentRequestContext,
    AdjustmentRequestPipelineResult,
    Pipeline,
    PipelineResult,
    PipelineStep,
)
from kardex.core.adjustment_requests.pipeline.steps import (
    BuildResultStep,
    SplitItemsStep,
    ValidateRequestStep,
)
from kardex.repos.v1.adjustment_requests import (
    AdjustmentRequestInDb,
    AdjustmentRequestItem,
    AdjustmentRequestStatus,
)
from kardex.repos.v1.common.models import UserInfo
from kardex.tools import InvalidOperation

CREATOR = UserInfo(id="user-1", name="Creator")
APPROVER = UserInfo(id="user-2", name="Approver")


def _make_request(
    *,
    status: AdjustmentRequestStatus = "pending",
    is_deleted: bool = False,
    differences: tuple[int, ...] = (5, -3, 0),
    created_by: UserInfo | None = None,
) -> AdjustmentRequestInDb:
    items = [
        AdjustmentRequestItem(
            productId=f"product-{index}",
            productName=f"Product {index}",
            countedQuantity=10,
            cost=100,
            systemStock=10 - difference,
            difference=difference,
            subtotal=abs(difference) * 100,
        )
        for index, difference in enumerate(differences)
    ]

    return AdjustmentRequestInDb(
        id="request-1",
        docNumber="0001",
        branchId="branch-1",
        description="Test request",
        status=status,
        items=items,
        createdBy=created_by or CREATOR,
        createdAt=1,
        isDeleted=is_deleted,
    )


def _make_context(
    request: AdjustmentRequestInDb | None = None,
    approved_by: UserInfo | None = None,
    approver_role: str = "Supervisor",
) -> AdjustmentRequestContext:
    return AdjustmentRequestContext(
        request=request or _make_request(),
        approved_by=approved_by or APPROVER,
        approver_role=approver_role,
        session=None,
    )


class _RecordingStep(PipelineStep[list[str]]):
    def __init__(self, label: str, run: bool = True):
        self.label = label
        self.run = run

    @property
    def name(self) -> str:
        return self.label

    def should_execute(self, context: list[str]) -> bool:
        return self.run

    async def execute(self, context: list[str]) -> None:
        context.append(self.label)


@pytest.mark.asyncio
async def test_pipeline_executes_and_skips_steps():
    context: list[str] = []
    pipeline = Pipeline(
        [
            _RecordingStep("validate"),
            _RecordingStep("exit", run=False),
            _RecordingStep("entry"),
        ]
    )

    result = await pipeline.run(context)

    assert context == ["validate", "entry"]
    assert result.executed_steps == ["validate", "entry"]
    assert result.skipped_steps == ["exit"]
    assert isinstance(result, PipelineResult)
    assert result.context is context


@pytest.mark.asyncio
async def test_split_items_step_separates_surplus_and_shortage():
    context = _make_context()

    await SplitItemsStep().execute(context)

    assert [item.difference for item in context.entry_items] == [5]
    assert [item.difference for item in context.exit_items] == [-3]


@pytest.mark.asyncio
async def test_split_items_step_rejects_request_without_differences():
    context = _make_context(_make_request(differences=(0, 0)))

    with pytest.raises(
        InvalidOperation,
        match="ADJUSTMENT_REQUEST_WITHOUT_DIFFERENCES",
    ):
        await SplitItemsStep().execute(context)


@pytest.mark.asyncio
async def test_validate_request_step_allows_another_user():
    await ValidateRequestStep().execute(_make_context())


@pytest.mark.asyncio
async def test_validate_request_step_rejects_operator_role():
    context = _make_context(approver_role="Operador")

    with pytest.raises(
        InvalidOperation,
        match="APPROVAL_REQUIRES_SUPERVISOR_OR_ADMIN",
    ):
        await ValidateRequestStep().execute(context)


@pytest.mark.asyncio
async def test_validate_request_step_allows_admin_self_approval():
    context = _make_context(approved_by=CREATOR, approver_role="Admin")

    await ValidateRequestStep().execute(context)


@pytest.mark.asyncio
async def test_validate_request_step_rejects_supervisor_self_approval():
    context = _make_context(approved_by=CREATOR, approver_role="Supervisor")

    with pytest.raises(InvalidOperation, match="SELF_APPROVAL_NOT_ALLOWED"):
        await ValidateRequestStep().execute(context)


@pytest.mark.asyncio
async def test_validate_request_step_rejects_non_pending_request():
    context = _make_context(_make_request(status="approved"))

    with pytest.raises(
        InvalidOperation,
        match="ONLY_PENDING_REQUESTS_CAN_BE_APPROVED",
    ):
        await ValidateRequestStep().execute(context)


@pytest.mark.asyncio
async def test_validate_request_step_rejects_deleted_request():
    context = _make_context(_make_request(is_deleted=True))

    with pytest.raises(InvalidOperation, match="ADJUSTMENT_REQUEST_NOT_FOUND"):
        await ValidateRequestStep().execute(context)


@pytest.mark.asyncio
async def test_build_result_step_sets_pipeline_result():
    context = _make_context()
    context.updated_request = context.request

    await BuildResultStep().execute(context)

    assert isinstance(context.result, AdjustmentRequestPipelineResult)
    assert context.result.request.id == context.request.id
    assert context.result.adjust_entry is None
    assert context.result.adjust_exit is None
