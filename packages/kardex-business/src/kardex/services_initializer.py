from kardex.services import MongoService


async def init_business_services() -> None:
    """Inicializa el cliente Mongo del proceso.

    Los indices y los datos semilla ya no corren al arrancar: cada tenant se
    aprovisiona y se migra con ``kardex.core.tenant.provision_tenant`` y con
    ``tools/migrate_tenants.py``.
    """

    await MongoService().init_client()
