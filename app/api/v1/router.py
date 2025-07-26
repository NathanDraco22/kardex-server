from fastapi import APIRouter


from .branches.branches_router import branches_router

from .entry_docs.entry_docs_router import entry_docs_router
from .exit_docs.exit_docs_router import exit_docs_router

from .products.products_router import products_router
from .units.units_router import units_router

router_v1 = APIRouter(tags=["apiV1"])


router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(entry_docs_router, prefix="/entry-docs")
router_v1.include_router(exit_docs_router, prefix="/exit-docs")
router_v1.include_router(products_router, prefix="/products")
router_v1.include_router(units_router, prefix="/units")
