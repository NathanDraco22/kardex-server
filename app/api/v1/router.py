from fastapi import APIRouter

from .branches.branches_router import branches_router
from .clients.clients_router import clients_router
from .entry_docs.entry_docs_router import entry_docs_router
from .exit_docs.exit_docs_router import exit_docs_router
from .product_categories.product_categories_router import product_categories_router
from .product_prices.product_prices_router import product_prices_router
from .products.products_router import products_router
from .suppliers.suppliers_router import suppliers_router
from .units.units_router import units_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(clients_router, prefix='/clients')
router_v1.include_router(entry_docs_router, prefix="/entry-docs")
router_v1.include_router(exit_docs_router, prefix="/exit-docs")
router_v1.include_router(product_categories_router, prefix='/product-categories')
router_v1.include_router(product_prices_router, prefix='/product-prices')
router_v1.include_router(products_router, prefix="/products")
router_v1.include_router(suppliers_router, prefix='/suppliers')
router_v1.include_router(units_router, prefix="/units")

