from typing import Any

from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.filter_params import AdjustmentRequestFilterParams
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.products import ProductsDataSource, ProductsRepository
from kardex.services.mongo_collections.v1 import ProductAccountsCollection
from kardex.tools import (
    BranchNotFound,
    BranchesTool,
    InvalidOperation,
    ProductNotFound,
    TimeTools,
    UuidTool,
)

from .data.adjustment_requests_datasource import AdjustmentRequestsDataSource
from .models.adjustment_request_model import (
    AdjustmentRequestInDb,
    AdjustmentRequestItem,
    CreateAdjustmentRequest,
    CreateAdjustmentRequestItem,
    UpdateAdjustmentRequest,
)


class AdjustmentRequestsRepository:
    _instance: "AdjustmentRequestsRepository|None" = None

    def __init__(self, adjustment_requests_ds: AdjustmentRequestsDataSource):
        self.adjustment_requests_ds = adjustment_requests_ds

    @classmethod
    def get_instance(cls) -> "AdjustmentRequestsRepository":
        if cls._instance is None:
            cls._instance = cls(AdjustmentRequestsDataSource())
        return cls._instance

    async def create_adjustment_request(
        self, create_adjustment_request: CreateAdjustmentRequest
    ) -> AdjustmentRequestInDb:
        self._validate_items(create_adjustment_request.items)

        items = await self._build_items(
            create_adjustment_request.branchId,
            create_adjustment_request.items,
        )
        entry_total, exit_total = self._calculate_totals(items)

        doc_number = create_adjustment_request.docNumber.strip()
        if not doc_number:
            doc_number = await CounterManager().next_adjustment_request_number(None)

        new_adjustment_request = AdjustmentRequestInDb(
            id=UuidTool.generate_uuid(),
            docNumber=doc_number,
            branchId=create_adjustment_request.branchId,
            description=create_adjustment_request.description,
            items=items,
            createdBy=create_adjustment_request.createdBy,
            status="pending",
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            isDeleted=False,
            entryTotal=entry_total,
            exitTotal=exit_total,
        )

        await self.adjustment_requests_ds.create_adjustment_request(
            new_adjustment_request.model_dump()
        )

        return new_adjustment_request

    async def get_all_adjustment_requests(
        self, params: AdjustmentRequestFilterParams
    ) -> list[AdjustmentRequestInDb]:
        results = await self.adjustment_requests_ds.get_all_adjustment_requests(
            **params.model_dump(exclude_none=True)
        )
        models = [AdjustmentRequestInDb.model_validate(result) for result in results]
        return models

    async def get_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> AdjustmentRequestInDb | None:
        result = await self.adjustment_requests_ds.get_adjustment_request_by_id(
            adjustment_request_id
        )

        if result is None:
            return None

        return AdjustmentRequestInDb.model_validate(result)

    async def update_adjustment_request_by_id(
        self,
        adjustment_request_id: str,
        adjustment_request: UpdateAdjustmentRequest,
    ) -> AdjustmentRequestInDb | None:
        existing = await self.get_adjustment_request_by_id(adjustment_request_id)

        if existing is None:
            return None

        if existing.status != "pending":
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_UPDATED")

        updated_data: dict[str, Any] = {
            key: value
            for key, value in adjustment_request.model_dump(
                exclude_unset=True
            ).items()
            if value is not None
        }

        if adjustment_request.items is not None:
            self._validate_items(adjustment_request.items)

            items = await self._build_items(
                existing.branchId,
                adjustment_request.items,
            )
            entry_total, exit_total = self._calculate_totals(items)

            updated_data["items"] = [item.model_dump() for item in items]
            updated_data["entryTotal"] = entry_total
            updated_data["exitTotal"] = exit_total

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.adjustment_requests_ds.update_adjustment_request_by_id(
            adjustment_request_id, updated_data
        )

        if result is None:
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_UPDATED")

        return AdjustmentRequestInDb.model_validate(result)

    async def delete_adjustment_request_by_id(
        self, adjustment_request_id: str
    ) -> AdjustmentRequestInDb | None:
        existing = await self.get_adjustment_request_by_id(adjustment_request_id)

        if existing is None:
            return None

        if existing.status != "pending":
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_DELETED")

        result = await self.adjustment_requests_ds.delete_adjustment_request_by_id(
            adjustment_request_id
        )

        if result is None:
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_DELETED")

        return AdjustmentRequestInDb.model_validate(result)

    async def cancel_adjustment_request(
        self,
        adjustment_request_id: str,
        cancelled_by: UserInfo,
        reason: str | None = None,
    ) -> AdjustmentRequestInDb:
        now = TimeTools.get_now_in_milliseconds()

        result = await self.adjustment_requests_ds.cancel_adjustment_request(
            adjustment_request_id,
            {
                "status": "cancelled",
                "cancelledBy": cancelled_by.model_dump(),
                "cancelledAt": now,
                "cancellationReason": reason,
                "updatedAt": now,
            },
        )

        if result is None:
            raise InvalidOperation("ONLY_PENDING_REQUESTS_CAN_BE_CANCELLED")

        return AdjustmentRequestInDb.model_validate(result)

    def _validate_items(self, items: list[CreateAdjustmentRequestItem]) -> None:
        if not items:
            raise InvalidOperation("ADJUSTMENT_REQUEST_ITEMS_REQUIRED")

        product_ids = [item.productId for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise InvalidOperation("DUPLICATED_PRODUCT_IDS")

        for item in items:
            if item.countedQuantity < 0:
                raise InvalidOperation("INVALID_COUNTED_QUANTITY")

    async def _build_items(
        self,
        branch_id: str,
        create_items: list[CreateAdjustmentRequestItem],
    ) -> list[AdjustmentRequestItem]:
        branch = BranchesTool().get_branch_by_id(branch_id)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=branch_id)

        product_ids = [item.productId for item in create_items]

        products = await ProductsRepository(
            products_ds=ProductsDataSource()
        ).get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise ProductNotFound("PRODUCT_NOT_FOUND")

        products_by_id = {product.id: product for product in products}

        accounts = await ProductAccountsCollection.get_instance().get_accounts_by_branch_id(
            branch_id=branch_id,
            product_ids=product_ids,
            session=None,
        )
        accounts_by_product = {account["productId"]: account for account in accounts}

        items: list[AdjustmentRequestItem] = []

        for create_item in create_items:
            product = products_by_id.get(create_item.productId)
            if product is None:
                raise ProductNotFound("PRODUCT_NOT_FOUND")

            account = accounts_by_product.get(create_item.productId)
            system_stock = int(account.get("currentStock") or 0) if account else 0
            average_cost = int(account.get("averageCost") or 0) if account else 0

            difference = create_item.countedQuantity - system_stock
            cost = create_item.cost

            if cost <= 0 and difference > 0:
                cost = average_cost

            if difference > 0 and cost <= 0:
                raise InvalidOperation("SURPLUS_COST_REQUIRED")

            subtotal = abs(difference) * cost

            items.append(
                AdjustmentRequestItem(
                    **create_item.model_dump(),
                    image=product.image,
                    systemStock=system_stock,
                    difference=difference,
                    subtotal=subtotal,
                )
            )

        return items

    def _calculate_totals(
        self, items: list[AdjustmentRequestItem]
    ) -> tuple[int, int]:
        if not any(item.difference != 0 for item in items):
            raise InvalidOperation("ADJUSTMENT_REQUEST_WITHOUT_DIFFERENCES")

        entry_total = sum(item.subtotal for item in items if item.difference > 0)
        exit_total = sum(item.subtotal for item in items if item.difference < 0)

        return entry_total, exit_total
