from fastapi import APIRouter, Depends
from kardex.repos.v1.integrations import UpdateIntegration, IntegrationInDb
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .integrations_controller import integrations_controller


integrations_router = APIRouter(
    tags=["integrationsV1"],
    dependencies=[Depends(auth_middleware)],
)


@integrations_router.get("")
async def get_all_integrations() -> ListResponse[IntegrationInDb]:
    return await integrations_controller.get_all_integrations()


@integrations_router.get("/{integration_id}")
async def get_integration_by_id(integration_id: str) -> IntegrationInDb:
    return await integrations_controller.get_integration_by_id(integration_id)


@integrations_router.patch("/{integration_id}")
async def update_integration_by_id(
    integration_id: str, body: UpdateIntegration
) -> IntegrationInDb:
    return await integrations_controller.update_integration_by_id(integration_id, body)


@integrations_router.post("/telegram/test")
async def telegrand_test() -> dict:
    await integrations_controller.send_telegram_test_message()
    return {"status": "ok"}
