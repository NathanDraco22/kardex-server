from fastapi import APIRouter, UploadFile, File, Header
from typing import Any

from .imports_controller import imports_controller

imports_router = APIRouter(tags=["importsV1"])


@imports_router.post("/init-inventory")
async def create_import(
    branch_id: str = Header(...),
    file: UploadFile = File(...),
) -> Any:
    return await imports_controller.create_import(branch_id, file)


@imports_router.post("/inventory")
async def create_inventory_import(
    branch_id: str = Header(...),
    file: UploadFile = File(...),
) -> Any:
    return await imports_controller.create_inventory_import(branch_id, file)


@imports_router.post("/clients")
async def create_clients_import(
    branch_id: str = Header(...),
    file: UploadFile = File(...),
) -> Any:
    return await imports_controller.create_clients_import(branch_id, file)
