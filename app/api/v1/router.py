from fastapi import APIRouter

from .branches.branches_router import branches_router
from .kardex.kardex_router import kardex_router
from .movements.movements_router import movements_router
from .products.products_router import products_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(kardex_router, prefix="/kardex")
router_v1.include_router(movements_router, prefix="/movements")
router_v1.include_router(products_router, prefix="/products")
