from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.kardex_config import kardexCtx
from kardex.repos.v1.product_accounts.models.product_account_model import (
    ProductAccountInDb,
)
from kardex.repos.v1.product_sale_profiles.models.product_sale_profile_model import (
    ProductSaleProfileInDb,
)
from kardex.repos.v1.products.models.product_model import (
    CreateProduct,
    ProductInDb,
    UpdateProduct,
)
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductTransactionsCollection,
    ProductsCollection,
)
from kardex.tools import (
    BranchNotFound,
    BranchesTool,
    InvalidOperation,
    TimeTools,
    UuidTool,
    generate_prefixes,
)


def resolve_required_branch_id(explicit_branch_id: str | None) -> str:
    branch_id = (explicit_branch_id or kardexCtx.get().branchId or "").strip()
    if not branch_id:
        raise InvalidOperation("BRANCH_ID_REQUIRED_FOR_NON_INVENTORY_PRODUCT")
    branch = BranchesTool().get_branch_by_id(branch_id)
    if branch is None:
        raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=branch_id)
    return branch_id


async def create_branch_scoped_product(
    create_product: CreateProduct,
) -> ProductInDb:
    """Crea un producto no inventariable o servicio exclusivamente en la sucursal solicitada."""
    branch_id = resolve_required_branch_id(create_product.branchId)
    create_product.branchId = branch_id

    mongo_client = MongoService().client
    products_col = ProductsCollection.get_instance()
    accounts_col = ProductAccountsCollection.get_instance()
    profiles_col = ProductSaleProfilesCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            if not create_product.code:
                create_product.code = await CounterManager().next_product_number(
                    session
                )

            new_product_id = UuidTool.generate_uuid()
            now_ms = TimeTools.get_now_in_milliseconds()

            new_product = ProductInDb(
                id=new_product_id,
                createdAt=now_ms,
                **create_product.model_dump(),
            )
            new_product_data = new_product.model_dump()
            new_product_data["searchPrefixes"] = generate_prefixes(
                new_product_data["name"]
            )

            new_account = ProductAccountInDb(
                productId=new_product_id,
                branchId=branch_id,
                currentStock=0,
                promiseStock=0,
                averageCost=0,
                lastCost=0,
                maximumCost=0,
                createdAt=now_ms,
            )

            new_profile = ProductSaleProfileInDb(
                branchId=branch_id,
                productId=new_product_id,
                salePrice=0,
                salePrice2=0,
                salePrice3=0,
                salePrice4=0,
                discounts=[],
                updatedAt=now_ms,
            )

            await products_col.create_product_with_session(
                product=new_product_data, session=session
            )
            await accounts_col.create_new_product_account_with_session(
                product_account=new_account.model_dump(), session=session
            )
            await profiles_col.create_product_sale_profile_with_session(
                product_sale_profile=new_profile.model_dump(), session=session
            )

            return new_product


async def update_product_with_type_transition(
    product_id: str,
    product: UpdateProduct,
) -> ProductInDb | None:
    """Actualiza un producto gestionando de forma atómica las transiciones de `productType`.

    La sucursal de un producto no inventariable o servicio es inmutable: se define al
    crearlo y no puede modificarse mediante una actualización.
    """
    products_col = ProductsCollection.get_instance()
    existing = await products_col.fetch_product_by_id(product_id)
    if existing is None:
        return None

    updated_data = product.model_dump(exclude_unset=True)
    updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()
    if "name" in updated_data and updated_data["name"] is not None:
        updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

    prev_type = existing.get("productType", "item")
    next_type = updated_data.get("productType", prev_type)
    is_leaving_inventory = prev_type == "item" and next_type != "item"

    prev_price_unit_factor = max(int(existing.get("priceUnitFactor") or 1), 1)
    next_price_unit_factor = max(
        int(updated_data.get("priceUnitFactor", prev_price_unit_factor) or 1), 1
    )
    if next_price_unit_factor != prev_price_unit_factor and not is_leaving_inventory:
        accounts_col = ProductAccountsCollection.get_instance()
        accounts = await accounts_col.get_product_accounts_by_product(product_id)
        if any(
            int(acc.get("currentStock") or 0) != 0
            or int(acc.get("promiseStock") or 0) > 0
            for acc in accounts
        ):
            raise InvalidOperation(
                "No se puede cambiar el factor de precio (priceUnitFactor) de un producto con stock o stock comprometido."
            )
        tx_col = ProductTransactionsCollection.get_instance()
        if await tx_col.has_transactions_for_product(product_id):
            raise InvalidOperation(
                "No se puede cambiar el factor de precio (priceUnitFactor) de un producto que ya tiene movimientos registrados."
            )

    if prev_type == next_type:
        # La sucursal no se actualiza: el producto permanece donde fue creado.
        updated_data.pop("branchId", None)
        result = await products_col.update_product_by_id(product_id, updated_data)
        return ProductInDb.model_validate(result) if result is not None else None

    now_ms = updated_data["updatedAt"]

    # Transición de servicio / no inventariable -> item (pasa al catálogo global).
    # No se aprovisionan cuentas ni perfiles en otras sucursales: cada una los
    # crea cuando opera el producto.
    if prev_type != "item" and next_type == "item":
        mongo_client = MongoService().client
        accounts_col = ProductAccountsCollection.get_instance()

        async with mongo_client.start_session() as session:
            async with await session.start_transaction():
                await accounts_col.reset_product_accounts_stock_and_cost_with_session(
                    product_id, session=session
                )
                updated_data["branchId"] = None
                result = await products_col.update_product_by_id(
                    product_id, updated_data, session=session
                )

        if result is None:
            return None
        return ProductInDb.model_validate(result)

    # Transición item -> nonInventory / service. Solo se permite sin existencias
    # ni stock comprometido en ninguna sucursal, porque el artículo es global.
    target_branch_id = resolve_required_branch_id(
        updated_data.pop("branchId", None) or existing.get("branchId")
    )
    updated_data["branchId"] = target_branch_id

    mongo_client = MongoService().client
    accounts_col = ProductAccountsCollection.get_instance()
    profiles_col = ProductSaleProfilesCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            accounts = await accounts_col.get_product_accounts_by_product(
                product_id, session=session
            )

            for acc in accounts:
                stock = acc.get("currentStock") or 0
                promise = acc.get("promiseStock") or 0
                if stock != 0 or promise > 0:
                    raise InvalidOperation(
                        "No se puede convertir a servicio o no inventariable porque "
                        "tiene existencias o stock comprometido "
                        f"(stock: {stock}, comprometido: {promise}). Registra una "
                        "salida o ajuste de inventario antes de continuar."
                    )

            await accounts_col.reset_product_accounts_stock_and_cost_with_session(
                product_id, session=session
            )

            await accounts_col.create_product_account_if_not_exist_with_session(
                branch_id=target_branch_id,
                product_id=product_id,
                product_account=ProductAccountInDb(
                    productId=product_id,
                    branchId=target_branch_id,
                    currentStock=0,
                    promiseStock=0,
                    averageCost=0,
                    lastCost=0,
                    maximumCost=0,
                    createdAt=now_ms,
                ).model_dump(),
                session=session,
            )

            await profiles_col.create_product_sale_profile_if_not_exist_with_session(
                branch_id=target_branch_id,
                product_id=product_id,
                product_sale_profile=ProductSaleProfileInDb(
                    branchId=target_branch_id,
                    productId=product_id,
                    salePrice=0,
                    salePrice2=0,
                    salePrice3=0,
                    salePrice4=0,
                    discounts=[],
                    updatedAt=now_ms,
                ).model_dump(),
                session=session,
            )

            result = await products_col.update_product_by_id(
                product_id, updated_data, session=session
            )
            if result is None:
                return None
            return ProductInDb.model_validate(result)
