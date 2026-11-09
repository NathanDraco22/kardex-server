from kardex.repos.v1.unit_scales import CreateUnitScale, UnitScaleInDb
from kardex.repos.v1.products.models.product_model import ExtraUnit
from kardex.services.mongo_collections.v1 import UnitScalesCollection
from kardex.tools import TimeTools, UuidTool

# Escalas viejas (base gramo/mililitro/centímetro/segundo). Se eliminan de las
# semillas porque la unidad base ahora es la fracción comercial mínima. Solo se
# borran si coinciden nombre y base, para no eliminar escalas personalizadas.
OLD_DEFAULT_SCALES: list[tuple[str, str]] = [
    ("Peso", "Gramo"),
    ("Volumen", "Mililitro"),
    ("Longitud", "Centímetro"),
    ("Tiempo", "Segundo"),
]


def _pack_label(pack_name: str, units_per_pack: int) -> str:
    if pack_name.strip().lower() == "docena":
        return "Docena"
    return f"{pack_name} x{units_per_pack}"


def build_fraction_pack_scale(
    pack_name: str,
    units_per_pack: int,
) -> CreateUnitScale | None:
    """Construye una escala fraccionada para un empaque de N unidades.

    - N % 4 == 0: base un cuarto del empaque (factor 4 al empaque).
    - N % 2 == 0: base media parte del empaque (factor 2 al empaque).
    - N impar: no existe una fracción exacta; se usa empaque completo o pack.
    """
    if units_per_pack <= 1:
        return None

    label = _pack_label(pack_name, units_per_pack)

    if units_per_pack % 4 == 0:
        quarter_units = units_per_pack // 4
        half_units = units_per_pack // 2

        return CreateUnitScale(
            name=f"{label} - Fracción",
            scaleType="fractionPack",
            baseUnit=f"Cuarto de {label} ({quarter_units} u)",
            units=[
                ExtraUnit(
                    name=f"Media {label} ({half_units} u)",
                    conversionFactor=2,
                ),
                ExtraUnit(
                    name=f"{label} ({units_per_pack} u)",
                    conversionFactor=4,
                ),
            ],
            defaultUnitIndex=2,
            wholesaleUnitIndex=2,
        )

    if units_per_pack % 2 == 0:
        half_units = units_per_pack // 2

        return CreateUnitScale(
            name=f"{label} - Fracción",
            scaleType="fractionPack",
            baseUnit=f"Media {label} ({half_units} u)",
            units=[
                ExtraUnit(
                    name=f"{label} ({units_per_pack} u)",
                    conversionFactor=2,
                ),
            ],
            defaultUnitIndex=1,
            wholesaleUnitIndex=1,
        )

    return None


# Escalas continuas: la base es un cuarto de la unidad principal y el default
# es la unidad comercial (Libra/Litro/Metro).
default_unit_scales: list[CreateUnitScale] = [
    CreateUnitScale(
        name="Libra",
        scaleType="weight",
        baseUnit="Cuarto de Libra",
        units=[
            ExtraUnit(name="Libra", conversionFactor=4),
            ExtraUnit(name="Arroba (25 lb)", conversionFactor=100),
            ExtraUnit(name="Quintal (100 lb)", conversionFactor=400),
        ],
        defaultUnitIndex=1,
        wholesaleUnitIndex=3,
    ),
    CreateUnitScale(
        name="Litro",
        scaleType="volume",
        baseUnit="Cuarto de Litro",
        units=[
            ExtraUnit(name="Litro", conversionFactor=4),
            ExtraUnit(name="Bidón 5 L", conversionFactor=20),
            ExtraUnit(name="Bidón 20 L", conversionFactor=80),
        ],
        defaultUnitIndex=1,
        wholesaleUnitIndex=3,
    ),
    CreateUnitScale(
        name="Metro",
        scaleType="length",
        baseUnit="Cuarto de Metro",
        units=[
            ExtraUnit(name="Metro", conversionFactor=4),
            ExtraUnit(name="Rollo 50 m", conversionFactor=200),
            ExtraUnit(name="Rollo 100 m", conversionFactor=400),
        ],
        defaultUnitIndex=1,
        wholesaleUnitIndex=3,
    ),
]

# Empaques fraccionados. `pack` no se siembra: queda disponible para escalas
# creadas por el usuario. `time` queda pendiente para servicios.
for pack_name, units_per_pack in [
    ("Caja", 10),
    ("Caja", 12),
    ("Caja", 20),
    ("Caja", 24),
    ("Caja", 30),
    ("Caja", 50),
    ("Caja", 60),
    ("Caja", 100),
    ("Docena", 12),
]:
    fraction_pack_scale = build_fraction_pack_scale(pack_name, units_per_pack)
    if fraction_pack_scale is not None:
        default_unit_scales.append(fraction_pack_scale)


async def create_default_unit_scales() -> None:
    collection = UnitScalesCollection.get_instance()

    # Las escalas viejas se borran porque todavía no hay producción; si algún
    # día la hay, esta limpieza debe convertirse en una migración versionada.
    await collection.delete_unit_scales_by_name_and_base_unit(OLD_DEFAULT_SCALES)

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
