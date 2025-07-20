from fastapi import HTTPException, status
from repos.v1.branch_stocks import (
    BranchStocksRepository,
)
from repos.v1.products import ProductsRepository
from repos.v1.branches import BranchesRepository
from repos.v1.movements import MovementsRepository, CreateMovement, MovementInDb

from services.mongo_collections.v1 import BranchStocksCollection

from tools import TimeTools


class ProcessEntry:
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

    async def process_entry(self, create_movement: CreateMovement) -> MovementInDb:
        if create_movement.type != "in":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movement type must be entry",
            )

        if create_movement.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0",
            )

        if create_movement.cost_at_moment <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cost at moment must be greater than 0",
            )

        if create_movement.reference_document_type not in ["entry", "purchase"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference document type must be entry or purchase",
            )

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

        try:
            filter_doc = {
                "product_id": create_movement.product_id,
                "branch_id": create_movement.branch_id,
            }

            update_pipeline = create_update_pipeline(create_movement)

            await BranchStocksCollection().update_branch_stock_with_pipeline(
                filter_doc, update_pipeline
            )

            return await self.movements_repo.create_movement(create_movement)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


def create_update_pipeline(create_movement: CreateMovement):
    # El pipeline de agregación ahora es mucho más directo.
    # Toda la lógica de cálculo ocurre en un solo paso dentro de la base de datos.
    update_pipeline = [
        {
            # Etapa 1: Preparar los campos. Usamos $ifNull para manejar el caso
            # en que el documento no exista (la primera entrada de un producto).
            "$set": {
                "current_stock": {"$ifNull": ["$current_stock", 0]},
                "average_cost": {"$ifNull": ["$average_cost", 0]},
            }
        },
        {
            # Etapa 2: Realizar los cálculos y actualizar los campos finales.
            "$set": {
                # Calculamos el nuevo costo promedio directamente.
                "average_cost": {
                    "$divide": [
                        {
                            "$add": [
                                {
                                    "$multiply": [
                                        "$current_stock",
                                        "$average_cost",
                                    ]
                                },
                                {
                                    "$multiply": [
                                        create_movement.quantity,
                                        create_movement.cost_at_moment,
                                    ]
                                },
                            ]
                        },
                        {"$add": ["$current_stock", create_movement.quantity]},
                    ]
                },
                # Incrementamos el stock y actualizamos el último costo.
                "current_stock": {"$add": ["$current_stock", create_movement.quantity]},
                "last_cost": create_movement.cost_at_moment,
                "updated_at": TimeTools.get_now_in_milliseconds(),
            }
        },
    ]

    return update_pipeline
