from typing import Self
from repos.v1.integrations import (
    IntegrationsRepository,
    IntegrationsDataSource,
    IntegrationInDb,
)


class IntegrationTool:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    __current_integration: IntegrationInDb | None = None

    def __init__(self) -> None:
        pass

    async def get_current_integration(self) -> IntegrationInDb:
        if self.__current_integration is None:
            integration_repo = IntegrationsRepository(
                integrations_ds=IntegrationsDataSource()
            )
            all_integrations = await integration_repo.get_all_integrations()
            self.__current_integration = all_integrations[0]
        return self.__current_integration

    async def refresh_current_integration(self) -> None:
        integration_repo = IntegrationsRepository(
            integrations_ds=IntegrationsDataSource()
        )
        all_integrations = await integration_repo.get_all_integrations()
        self.__current_integration = all_integrations[0]
