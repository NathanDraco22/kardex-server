from repos.v1.integrations import (
    IntegrationsRepository,
    IntegrationsDataSource,
    CreateIntegration,
)


async def create_default_integration() -> None:
    create_integration = CreateIntegration()

    integrations_repo = IntegrationsRepository(
        integrations_ds=IntegrationsDataSource(),
    )

    await integrations_repo.create_integration_if_absent(create_integration)
