from kardex.repos.v1.expense_categories import ExpenseCategoryInDb
from kardex.services.mongo_collections.v1 import ExpenseCategoriesCollection
from kardex.tools import TimeTools, UuidTool

default_categories = [
    "Electricidad",
    "Agua",
    "Telecomunicaciones",
    "Combustible",
    "Transporte",
    "Impuestos",
    "Planilla",
    "Renta",
    "Mantenimiento y Reparaciones",
    "Papelería y Suministros",
    "Publicidad y Mercadeo",
    "Seguros",
    "Servicios Profesionales",
    "Gastos Financieros",
    "Limpieza y Aseo",
    "Seguridad",
    "Viáticos",
]


async def create_default_expense_categories() -> None:
    collection = ExpenseCategoriesCollection.get_instance()

    for category_name in default_categories:
        category_db = ExpenseCategoryInDb(
            id=UuidTool.generate_uuid(),
            name=category_name,
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
        )

        await collection.create_category_if_absent(
            category_name,
            category_db.model_dump(),
        )
