from .data.integrations_datasource import IntegrationsDataSource
from .models.integration_model import (
    CreateIntegration,
    UpdateIntegration,
    IntegrationInDb,
)

from tools import TimeTools


class IntegrationsRepository:
    def __init__(self, integrations_ds: IntegrationsDataSource):
        self.integrations_ds = integrations_ds

    async def create_integration_if_absent(
        self, create_integration: CreateIntegration
    ) -> IntegrationInDb:
        new_integration = IntegrationInDb(
            **create_integration.model_dump(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.integrations_ds.create_integration_if_absent(
            new_integration.model_dump()
        )

        return IntegrationInDb.model_validate(new_integration)

    async def get_all_integrations(self) -> list[IntegrationInDb]:
        results = await self.integrations_ds.get_all_integrations()
        models = [IntegrationInDb.model_validate(result) for result in results]
        return models

    async def get_integration_by_id(
        self, integration_id: str
    ) -> IntegrationInDb | None:
        result = await self.integrations_ds.get_integration_by_id(integration_id)

        if result is None:
            return None

        return IntegrationInDb.model_validate(result)

    async def update_integration_by_id(
        self, integration_id: str, integration: UpdateIntegration
    ) -> IntegrationInDb | None:
        update_integration_data = integration.model_dump(exclude_unset=True)

        if not update_integration_data:
            return None

        result = await self.integrations_ds.update_integration_by_id(
            integration_id, update_integration_data
        )

        if result is None:
            return None

        return IntegrationInDb.model_validate(result)

    async def delete_integration_by_id(
        self, integration_id: str
    ) -> IntegrationInDb | None:
        result = await self.integrations_ds.delete_integration_by_id(integration_id)

        if result is None:
            return None

        return IntegrationInDb.model_validate(result)
