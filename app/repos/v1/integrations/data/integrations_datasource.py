from typing import Any
from services.mongo_collections.v1 import IntegrationsCollection


class IntegrationsDataSource:
    async def create_integration(self, integration: dict[str, Any]) -> dict[str, Any]:
        collection = IntegrationsCollection()
        await collection.create_integration(integration)
        return integration

    async def create_integration_if_absent(
        self, integration: dict[str, Any]
    ) -> dict[str, Any]:
        collection = IntegrationsCollection()
        await collection.create_integration_if_absent(integration)
        return integration

    async def get_all_integrations(self) -> list[dict[str, Any]]:
        collection = IntegrationsCollection()
        return await collection.fetch_all_integrations()

    async def get_integration_by_id(self, integration_id: str) -> dict[str, Any] | None:
        collection = IntegrationsCollection()
        return await collection.fetch_integration_by_id(integration_id)

    async def update_integration_by_id(
        self, integration_id: str, integration: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = IntegrationsCollection()
        return await collection.update_integration_by_id(integration_id, integration)

    async def delete_integration_by_id(
        self, integration_id: str
    ) -> dict[str, Any] | None:
        collection = IntegrationsCollection()
        return await collection.delete_integration_by_id(integration_id)
