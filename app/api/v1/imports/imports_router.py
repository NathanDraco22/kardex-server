from fastapi import APIRouter, Depends, File, Header, Query, UploadFile

from app_middleware import auth_middleware
from api.v1.depends import get_branch_id

from .imports_controller import imports_controller
from .responses import ImportPreviewResponse, ImportResponse


imports_router = APIRouter(tags=["importsV1"], dependencies=[Depends(auth_middleware)])


@imports_router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    type: str = Query(
        ...,
        description=(
            "Tipo de importación: initialInventory, inventory, clients, suppliers"
        ),
    ),
    x_branch: str | None = Header(default=None, alias="X-Branch"),
    branch_id: str | None = Header(default=None, alias="branch-id"),
    file: UploadFile = File(...),
) -> ImportPreviewResponse:
    effective_branch = (x_branch or branch_id or "").strip() or None
    return await imports_controller.preview_import(type, effective_branch, file)


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
