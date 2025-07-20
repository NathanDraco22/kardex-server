from fastapi import HTTPException, status


from responses.v1 import ListResponse

from core.kardex import ProcessEntry, ProcessExit

from repos.v1.products import ProductsRepository, ProductsDataSource
from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.branch_stocks import BranchStocksRepository, BranchStocksDataSource

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
        branches_stocks_repo: BranchStocksRepository,
    ) -> None:
        self.movements_repo = movements_repo
        self.products_repo = products_repo
        self.branches_repo = branches_repo
        self.branches_stocks_repo = branches_stocks_repo

    async def create_exit_movement(self, body: CreateMovement) -> MovementInDb:
        process_exit = ProcessExit(
            branch_stocks_repo=self.branches_stocks_repo,
            products_repo=self.products_repo,
            branches_repo=self.branches_repo,
            movements_repo=self.movements_repo,
        )

        return await process_exit.process_exit(body)

    async def create_entry_movement(self, body: CreateMovement) -> MovementInDb:
        process_entry = ProcessEntry(
            branch_stocks_repo=self.branches_stocks_repo,
            products_repo=self.products_repo,
            branches_repo=self.branches_repo,
            movements_repo=self.movements_repo,
        )

        return await process_entry.process_entry(body)

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
    branches_stocks_repo=BranchStocksRepository(
        branch_stocks_ds=BranchStocksDataSource(),
    ),
)
