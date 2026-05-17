from fastapi import HTTPException, status
from core.app_notifier.app_notifier import AppNotifier
from kardex.repos.v1.integrations import (
    UpdateIntegration,
    IntegrationInDb,
    IntegrationsRepository,
    IntegrationsDataSource,
)

from tools.integration_tool import IntegrationTool
from responses.v1 import ListResponse


class IntegrationsController:
    def __init__(self, integrations_repo: IntegrationsRepository) -> None:
        self.integrations_repo = integrations_repo

    async def get_all_integrations(self) -> ListResponse[IntegrationInDb]:
        integrations = await self.integrations_repo.get_all_integrations()
        return ListResponse(
            count=len(integrations),
            data=integrations,
        )

    async def get_integration_by_id(self, integration_id: str) -> IntegrationInDb:
        integration = await self.integrations_repo.get_integration_by_id(integration_id)
        if integration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )
        return integration

    async def update_integration_by_id(
        self, integration_id: str, body: UpdateIntegration
    ) -> IntegrationInDb:
        updated_integration = await self.integrations_repo.update_integration_by_id(
            integration_id, body
        )
        if updated_integration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        await IntegrationTool().refresh_current_integration()
        return updated_integration

    async def send_telegram_test_message(self) -> None:
        await AppNotifier().notify_test_message()


integrations_controller = IntegrationsController(
    integrations_repo=IntegrationsRepository(
        integrations_ds=IntegrationsDataSource(),
    ),
)
