from fastapi import HTTPException, status

from responses.v1 import ListResponse

from repos.v1.products import ProductsRepository, ProductsDataSource

from repos.v1.movements import (
    CreateMovement,
    MovementInDb,
    MovementsRepository,
    MovementsDataSource,
)


class MovementsController:
    def __init__(
        self, movements_repo: MovementsRepository, products_repo: ProductsRepository
    ) -> None:
        self.movements_repo = movements_repo
        self.products_repo = products_repo

    async def create_movement(self, body: CreateMovement) -> MovementInDb:
        product = await self.products_repo.get_product_by_id(body.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
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
)
