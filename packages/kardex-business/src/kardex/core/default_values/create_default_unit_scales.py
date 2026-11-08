from kardex.repos.v1.unit_scales import CreateUnitScale, UnitScaleInDb
from kardex.repos.v1.products.models.product_model import ExtraUnit
from kardex.services.mongo_collections.v1 import UnitScalesCollection
from kardex.tools import TimeTools, UuidTool

default_unit_scales: list[CreateUnitScale] = [
    CreateUnitScale(
        name="Peso",
        baseUnit="Gramo",
        units=[
            ExtraUnit(name="Onza", conversionFactor=28),
            ExtraUnit(name="Libra", conversionFactor=454),
            ExtraUnit(name="Kilogramo", conversionFactor=1000),
            ExtraUnit(name="Quintal", conversionFactor=45400),
        ],
        defaultUnitIndex=0,
        wholesaleUnitIndex=0,
    ),
    CreateUnitScale(
        name="Volumen",
        baseUnit="Mililitro",
        units=[
            ExtraUnit(name="Litro", conversionFactor=1000),
            ExtraUnit(name="Galón", conversionFactor=3785),
        ],
        defaultUnitIndex=0,
        wholesaleUnitIndex=0,
    ),
    CreateUnitScale(
        name="Longitud",
        baseUnit="Centímetro",
        units=[
            ExtraUnit(name="Metro", conversionFactor=100),
            ExtraUnit(name="Yarda", conversionFactor=91),
        ],
        defaultUnitIndex=0,
        wholesaleUnitIndex=0,
    ),
    CreateUnitScale(
        name="Tiempo",
        baseUnit="Segundo",
        units=[
            ExtraUnit(name="Minuto", conversionFactor=60),
            ExtraUnit(name="Hora", conversionFactor=3600),
            ExtraUnit(name="Día", conversionFactor=86400),
        ],
        defaultUnitIndex=0,
        wholesaleUnitIndex=0,
    ),
]


async def create_default_unit_scales() -> None:
    collection = UnitScalesCollection.get_instance()

    for item in default_unit_scales:
        scale_db = UnitScaleInDb(
            id=UuidTool.generate_uuid(),
            **item.model_dump(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
        )

        await collection.create_unit_scale_if_absent(
            item.name,
            scale_db.model_dump(),
        )
