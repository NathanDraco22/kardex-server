from responses.v1 import ListResponse
from repos.v1.movements import MovementsRepository, MovementsDataSource, MovementInDb


class KardexController:
    def __init__(self, movements_repo: MovementsRepository) -> None:
        self.movements_repo = movements_repo
        pass

    async def get_product_kardex(
        self, product_id: str, branch_id: str, start_date: int, end_date: int
    ) -> ListResponse[MovementInDb]:
        result = await self.movements_repo.get_movements_by_product_and_branch(
            product_id, branch_id, start_date, end_date
        )

        return ListResponse(count=len(result), data=result)


kardex_controller = KardexController(
    movements_repo=MovementsRepository(MovementsDataSource())
)
