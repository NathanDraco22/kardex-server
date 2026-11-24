from kardex.repos.v1.common.models.sale_item import ProductType
from kardex.services.mongo_collections.v1 import ProductsCollection
from kardex.tools import InvalidOperation


def _normalize_product_type(raw: object) -> ProductType:
    if raw == "nonInventory":
        return "nonInventory"
    if raw == "service":
        return "service"
    return "item"


async def _fetch_active_products_map(
    product_ids: list[str],
) -> dict[str, dict]:
    """Retorna {productId: documento} solo para productos existentes y no borrados."""
    unique_ids = list({pid for pid in product_ids if pid})
    if not unique_ids:
        return {}
    products_col = ProductsCollection.get_instance()
    docs = await products_col.fetch_product_by_ids(unique_ids)
    return {
        doc["id"]: doc
        for doc in docs
        if "id" in doc and not doc.get("isDeleted")
    }


def calculate_line_amount(
    unit_cents: int,
    base_quantity: int,
    price_unit_factor: int = 1,
) -> int:
    """Calcula un monto en centavos escalado por `price_unit_factor` (default 1).

    Usa aritmética entera con redondeo half-away-from-zero (half-up) para
    coincidir exactamente con `.round()` en Dart y evitar descuadres de 1¢
    respecto al redondeo bancario de Python.
    """
    safe_factor = max(int(price_unit_factor or 1), 1)
    product = unit_cents * base_quantity
    if safe_factor == 1:
        return product
    if product >= 0:
        return (product + safe_factor // 2) // safe_factor
    return -((abs(product) + safe_factor // 2) // safe_factor)


async def fetch_product_types_map(product_ids: list[str]) -> dict[str, ProductType]:
    """Retorna un mapa {productId: productType} desde ProductsCollection (default 'item')."""
    docs_map = await _fetch_active_products_map(product_ids)
    return {
        product_id: _normalize_product_type(doc.get("productType"))
        for product_id, doc in docs_map.items()
    }


async def fetch_product_price_unit_factors_map(
    product_ids: list[str],
) -> dict[str, int]:
    """Retorna un mapa {productId: priceUnitFactor} desde ProductsCollection (default 1)."""
    docs_map = await _fetch_active_products_map(product_ids)
    return {
        product_id: max(int(doc.get("priceUnitFactor") or 1), 1)
        for product_id, doc in docs_map.items()
    }


async def fetch_product_types_and_price_factors_map(
    product_ids: list[str],
) -> tuple[dict[str, ProductType], dict[str, int]]:
    """Consulta `Products` una sola vez y retorna (product_types, price_unit_factors)."""
    docs_map = await _fetch_active_products_map(product_ids)
    types_map = {
        product_id: _normalize_product_type(doc.get("productType"))
        for product_id, doc in docs_map.items()
    }
    factors_map = {
        product_id: max(int(doc.get("priceUnitFactor") or 1), 1)
        for product_id, doc in docs_map.items()
    }
    return types_map, factors_map


async def ensure_inventory_products(
    product_ids: list[str],
    operation_label: str = "esta operación de inventario",
) -> dict[str, int]:
    """Valida que todos los productos existan y sean inventariables (`productType == 'item'`).

    Retorna `{productId: priceUnitFactor}` desde `Products` para evitar una segunda consulta.
    """
    unique_ids = list({pid for pid in product_ids if pid})
    if not unique_ids:
        return {}
    docs_map = await _fetch_active_products_map(unique_ids)

    missing_ids = [pid for pid in unique_ids if pid not in docs_map]
    if missing_ids:
        raise InvalidOperation(
            "PRODUCT_NOT_FOUND: no existen los productos "
            + ", ".join(missing_ids)
            + f" requeridos para {operation_label}"
        )

    non_inventory_names = [
        doc.get("name", doc.get("id", ""))
        for doc in docs_map.values()
        if _normalize_product_type(doc.get("productType")) != "item"
    ]
    if non_inventory_names:
        joined = ", ".join(non_inventory_names)
        raise InvalidOperation(
            f"Los servicios y productos no inventariables no permiten {operation_label}: {joined}"
        )

    return {
        product_id: max(int(doc.get("priceUnitFactor") or 1), 1)
        for product_id, doc in docs_map.items()
    }
