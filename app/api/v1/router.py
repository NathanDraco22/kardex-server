from fastapi import APIRouter

from .products.products_router import products_router

router_v1 = APIRouter(tags=["apiV1"])


router_v1.include_router(products_router, prefix="/products")
