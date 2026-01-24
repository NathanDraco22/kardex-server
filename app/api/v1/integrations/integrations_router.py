from fastapi import APIRouter

from repos.v1.integrations import UpdateIntegration, IntegrationInDb
from responses.v1 import ListResponse

from .integrations_controller import integrations_controller


integrations_router = APIRouter(tags=["integrationsV1"])


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
