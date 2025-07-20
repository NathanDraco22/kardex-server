from fastapi import HTTPException, status
from repos.v1.branch_stocks import BranchStocksRepository
from repos.v1.products import ProductsRepository
from repos.v1.branches import BranchesRepository
from repos.v1.movements import MovementsRepository, CreateMovement, MovementInDb

from services.mongo_collections.v1 import BranchStocksCollection

from tools import TimeTools


class ProcessExit:
    def __init__(
        self,
        branch_stocks_repo: BranchStocksRepository,
        products_repo: ProductsRepository,
        branches_repo: BranchesRepository,
        movements_repo: MovementsRepository,
    ):
        self.branch_stocks_repo = branch_stocks_repo
        self.products_repo = products_repo
        self.branches_repo = branches_repo
        self.movements_repo = movements_repo

    async def process_exit(self, create_movement: CreateMovement) -> MovementInDb:
        product = await self.products_repo.get_product_by_id(create_movement.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        branch = await self.branches_repo.get_branch_by_id(create_movement.branch_id)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )

        if create_movement.type != "out":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movement type must be out",
            )

        if create_movement.quantity >= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be less than 0",
            )

        if create_movement.reference_document_type not in ["exit", "sale"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference document type must be exit or sale",
            )

        branck_stock_product = (
            await self.branch_stocks_repo.get_branch_stock_by_branch_and_product_id(
                create_movement.product_id,
                create_movement.branch_id,
            )
        )

        if branck_stock_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No entry for this product not found",
            )

        quantity_to_remove = abs(create_movement.quantity)

        filter_doc = {
            "product_id": create_movement.product_id,
            "branch_id": create_movement.branch_id,
            "current_stock": {"$gte": quantity_to_remove},
        }

        update_doc = {
            "$inc": {
                "current_stock": create_movement.quantity,
            },
            "$set": {
                "updated_at": TimeTools.get_now_in_milliseconds(),
            },
        }

        res = await BranchStocksCollection().update_branch_stock_with_params(
            filter_doc, update_doc
        )

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Stock found for this product",
            )

        create_movement.cost_at_moment = res.get("average_cost", 0.0)

        return await self.movements_repo.create_movement(create_movement)
