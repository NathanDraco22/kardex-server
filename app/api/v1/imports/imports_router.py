from fastapi import APIRouter, Depends, File, UploadFile

from app_middleware import auth_middleware
from api.v1.depends import get_branch_id

from .imports_controller import imports_controller
from .responses import ImportResponse


imports_router = APIRouter(tags=["importsV1"], dependencies=[Depends(auth_middleware)])


@imports_router.post("/init-inventory", response_model=ImportResponse)
async def create_import(
    branch_id: str = Depends(get_branch_id),
    file: UploadFile = File(...),
) -> ImportResponse:
    return await imports_controller.create_import(branch_id, file)


@imports_router.post("/inventory", response_model=ImportResponse)
async def create_inventory_import(
    branch_id: str = Depends(get_branch_id),
    file: UploadFile = File(...),
) -> ImportResponse:
    return await imports_controller.create_inventory_import(branch_id, file)


@imports_router.post("/clients", response_model=ImportResponse)
async def create_clients_import(
    branch_id: str = Depends(get_branch_id),
    file: UploadFile = File(...),
) -> ImportResponse:
    return await imports_controller.create_clients_import(branch_id, file)


@imports_router.post("/suppliers", response_model=ImportResponse)
async def create_suppliers_import(
    file: UploadFile = File(...),
) -> ImportResponse:
    return await imports_controller.create_suppliers_import(file)
