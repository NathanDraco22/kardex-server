from fastapi import HTTPException, status

from responses.v1 import ListResponse

from repos.v1.products import ProductsRepository, ProductsDataSource
from repos.v1.branches import BranchesRepository, BranchesDataSource

from repos.v1.movements import (
    CreateMovement,
    MovementInDb,
    MovementsRepository,
    MovementsDataSource,
)


class MovementsController:
    def __init__(
        self,
        movements_repo: MovementsRepository,
        products_repo: ProductsRepository,
        branches_repo: BranchesRepository,
    ) -> None:
        self.movements_repo = movements_repo
        self.products_repo = products_repo
        self.branches_repo = branches_repo

    async def create_exit_movement(self, body: CreateMovement) -> MovementInDb:
        product = await self.products_repo.get_product_by_id(body.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        branch = await self.branches_repo.get_branch_by_id(body.branch_id)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )

        if body.type != "out":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movement type must be out",
            )

        if body.quantity >= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be less than 0",
            )

        if body.reference_document_type not in ["exit", "sale"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference document type must be exit or sale",
            )

        return await self.movements_repo.create_movement(body)

    async def create_entry_movement(self, body: CreateMovement) -> MovementInDb:
        product = await self.products_repo.get_product_by_id(body.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        branch = await self.branches_repo.get_branch_by_id(body.branch_id)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )

        if body.type != "in":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movement type must be entry",
            )

        if body.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0",
            )

        if body.cost_at_moment <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cost at moment must be greater than 0",
            )

        if body.reference_document_type not in ["entry", "purchase"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference document type must be entry or purchase",
            )

        return await self.movements_repo.create_movement(body)

    async def get_all_movements(self) -> ListResponse[MovementInDb]:
        movements = await self.movements_repo.get_all_movements()
        return ListResponse(count=len(movements), data=movements)

    async def get_movement_by_id(self, movement_id: str) -> MovementInDb:
        movement = await self.movements_repo.get_movement_by_id(movement_id)
        if movement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movement not found",
            )
        return movement


movements_controller = MovementsController(
    movements_repo=MovementsRepository(
        movements_ds=MovementsDataSource(),
    ),
    products_repo=ProductsRepository(
        products_ds=ProductsDataSource(),
    ),
    branches_repo=BranchesRepository(
        branches_ds=BranchesDataSource(),
    ),
)
