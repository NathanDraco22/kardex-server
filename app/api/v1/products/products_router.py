from fastapi import APIRouter, Depends
from kardex.repos.v1.products import (
    CreateProduct,
    UpdateProduct,
    ProductInDb,
    ProductInDbInBranch,
    GetProductsInBranchRequest,
)

from responses.v1 import ListResponse

from kardex.repos.v1.common.filter_params import ProductFilterParams
from .products_controller import products_controller


products_router = APIRouter(tags=["productsV1"])


@products_router.post("")
async def create_product(body: CreateProduct) -> ProductInDb:
    return await products_controller.create_product(body)


@products_router.get("")
async def get_all_products() -> ListResponse[ProductInDb]:
    return await products_controller.get_all_products()


@products_router.get("/paginated")
async def get_paginated_products(
    query_params: ProductFilterParams = Depends(),
) -> ListResponse[ProductInDb]:
    return await products_controller.get_paginated_products(
        **query_params.model_dump(exclude_none=True)
    )


@products_router.get("/{product_id}")
async def get_product_by_id(product_id: str) -> ProductInDb:
    return await products_controller.get_product_by_id(product_id)


@products_router.get("/search/{text_query}")
async def search_product_by_text(text_query: str) -> ListResponse[ProductInDb]:
    return await products_controller.search_product_by_text(text_query)


@products_router.get("/branch/{branch_id}/search/{text_query}")
async def search_product_in_branch(
    branch_id: str,
    text_query: str,
) -> ListResponse[ProductInDbInBranch]:
    return await products_controller.search_product_in_branch(branch_id, text_query)


@products_router.post("/branch/{branch_id}/by-ids")
async def get_products_in_branch_by_ids(
    branch_id: str,
    body: GetProductsInBranchRequest,
) -> ListResponse[ProductInDbInBranch]:
    return await products_controller.get_products_in_branch_by_ids(branch_id, body.productIds)


@products_router.get("/branch/{branch_id}")
async def get_all_products_in_branch(
    branch_id: str,
    query: ProductFilterParams = Depends(),
) -> ListResponse[ProductInDbInBranch]:
    query.branchId = branch_id
    return await products_controller.get_all_product_in_branch(query)


@products_router.get("/{product_id}/branch/{branch_id}")
async def get_product_in_branch_by_id(
    product_id: str, branch_id: str
) -> ProductInDbInBranch:
    return await products_controller.get_product_in_branch_by_id(product_id, branch_id)


@products_router.patch("/{product_id}")
async def update_product_by_id(product_id: str, body: UpdateProduct) -> ProductInDb:
    return await products_controller.update_product_by_id(product_id, body)


@products_router.delete("/{product_id}")
async def delete_product_by_id(product_id: str) -> ProductInDb:
    return await products_controller.delete_product_by_id(product_id)
