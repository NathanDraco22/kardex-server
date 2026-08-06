from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.app_middleware.depends.auth_middleware import auth_middleware
from kardex.repos.v1.api_keys import (
    ApiKeyInDb,
    CreateApiKey,
    CreatedApiKeyResponse,
)

from .api_keys_controller import ApiKeysController

api_keys_router = APIRouter(
    prefix="/api-keys",
    tags=["API Keys"],
    dependencies=[Depends(auth_middleware)],
)


class ToggleApiKeyRequest(BaseModel):
    isActive: bool


@api_keys_router.get("", response_model=list[ApiKeyInDb])
async def get_all_api_keys():
    controller = ApiKeysController()
    return await controller.get_all_api_keys()


@api_keys_router.post("", response_model=CreatedApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(create_dto: CreateApiKey):
    controller = ApiKeysController()
    return await controller.create_api_key(create_dto)


@api_keys_router.patch("/{key_id}/toggle", response_model=ApiKeyInDb)
async def toggle_api_key_status(key_id: str, body: ToggleApiKeyRequest):
    controller = ApiKeysController()
    result = await controller.toggle_api_key_status(key_id, body.isActive)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Llave de API no encontrada",
        )
    return result


@api_keys_router.delete("/{key_id}", response_model=ApiKeyInDb)
async def delete_api_key(key_id: str):
    controller = ApiKeysController()
    result = await controller.delete_api_key(key_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Llave de API no encontrada",
        )
    return result
