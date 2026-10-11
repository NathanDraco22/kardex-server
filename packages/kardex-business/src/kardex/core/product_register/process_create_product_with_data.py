from kardex.tools import UuidTool, TimeTools
from kardex.tools.search_tools import generate_prefixes
from kardex.core.counter_manager.counter_manager import CounterManager

from kardex.repos.v1.products.models.product_model import (
    CreateProductWithData,
    ProductInDb,
    ProductInDbInBranch,
)
from kardex.repos.v1.product_accounts.models.product_account_model import (
    ProductAccountInDb,
)
from kardex.repos.v1.product_sale_profiles.models.product_sale_profile_model import (
    ProductSaleProfileInDb,
)
from kardex.repos.v1.product_transactions.models.product_transaction_model import (
    ProductTransactionInDb,
)
from kardex.repos.v1.product_stats.models.product_stat_model import (
    CreateProductStat,
)
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ProductsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductTransactionsCollection,
    ProductStatsCollection,
)


async def process_create_product_with_data(
    data: CreateProductWithData,
) -> ProductInDbInBranch:
    mongo_client = MongoService().client

    products_col = ProductsCollection.get_instance()
    accounts_col = ProductAccountsCollection.get_instance()
    profiles_col = ProductSaleProfilesCollection.get_instance()
    transactions_col = ProductTransactionsCollection.get_instance()
    stats_col = ProductStatsCollection.get_instance()

    branches_repo = BranchesRepository(BranchesDataSource())
    all_branches = await branches_repo.get_all_branches()

    create_product = data.createProduct
    branch_id = data.branchId
    inventory_info = data.inventoryInfo

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            if not create_product.code:
                create_product.code = await CounterManager().next_product_number(
                    session
                )

            new_product_id = UuidTool.generate_uuid()
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            new_product = ProductInDb(
                id=new_product_id,
                createdAt=now_in_milliseconds,
                **create_product.model_dump(),
            )

            new_product_data = new_product.model_dump()
            new_product_data["searchPrefixes"] = generate_prefixes(
                new_product_data["name"]
            )

            new_accounts = []
            new_profiles = []
            target_account: ProductAccountInDb | None = None
            target_profile: ProductSaleProfileInDb | None = None
            target_branch = None

            for branch in all_branches:
                is_target = branch.id == branch_id
                if is_target:
                    target_branch = branch

                current_stock = inventory_info.quantity if is_target else 0
                cost = inventory_info.cost if is_target else 0
                sale_price = inventory_info.price if is_target else 0

                new_account = ProductAccountInDb(
                    productId=new_product_id,
                    branchId=branch.id,
                    currentStock=current_stock,
                    promiseStock=0,
                    averageCost=cost,
                    lastCost=cost,
                    maximumCost=cost,
                    createdAt=now_in_milliseconds,
                )

                new_profile = ProductSaleProfileInDb(
                    branchId=branch.id,
                    productId=new_product_id,
                    salePrice=sale_price,
                    salePrice2=0,
                    salePrice3=0,
                    salePrice4=0,
                    discounts=[],
                    updatedAt=now_in_milliseconds,
                )

                if is_target:
                    target_account = new_account
                    target_profile = new_profile

                new_accounts.append(new_account.model_dump())
                new_profiles.append(new_profile.model_dump())

            # Si branch_id no estaba en all_branches, agregarlo explícitamente
            if target_account is None:
                target_account = ProductAccountInDb(
                    productId=new_product_id,
                    branchId=branch_id,
                    currentStock=inventory_info.quantity,
                    promiseStock=0,
                    averageCost=inventory_info.cost,
                    lastCost=inventory_info.cost,
                    maximumCost=inventory_info.cost,
                    createdAt=now_in_milliseconds,
                )
                target_profile = ProductSaleProfileInDb(
                    branchId=branch_id,
                    productId=new_product_id,
                    salePrice=inventory_info.price,
                    salePrice2=0,
                    salePrice3=0,
                    salePrice4=0,
                    discounts=[],
                    updatedAt=now_in_milliseconds,
                )
                new_accounts.append(target_account.model_dump())
                new_profiles.append(target_profile.model_dump())

            # 1. Guardar producto
            await products_col.create_product_with_session(
                product=new_product_data, session=session
            )

            # 2. Guardar cuentas de inventario para todas las sucursales
            await accounts_col.create_many_product_accounts(
                product_accounts=new_accounts, session=session
            )

            # 3. Guardar perfiles de venta para todas las sucursales
            await profiles_col.bulk_create_product_sale_profiles(
                product_sale_profiles=new_profiles, session=session
            )

            # 4. Registrar transacción inicial de kárdex si quantity > 0
            if inventory_info.quantity > 0:
                initial_tx = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId="0000",
                    docNumber="0000",
                    type="entry",
                    subtype="adjustment",
                    productId=new_product_id,
                    branchId=branch_id,
                    quantity=inventory_info.quantity,
                    averageCost=inventory_info.cost,
                    resultStock=inventory_info.quantity,
                    createdAt=now_in_milliseconds,
                )
                await transactions_col.create_many_product_transactions_with_session(
                    [initial_tx.model_dump()], session=session
                )

            # 5. Crear stats si la sucursal es comercial
            if target_branch is not None and target_branch.isCommerce:
                product_stat = CreateProductStat(
                    branchId=branch_id,
                    productId=new_product_id,
                    startDate=now_in_milliseconds,
                    endDate=now_in_milliseconds,
                    totalUnits=0,
                    totalTransactions=0,
                    daysAnalyzed=0,
                    lastEstimation=now_in_milliseconds,
                )
                await stats_col.bulk_create_product_stats_if_not_exist(
                    [product_stat.model_dump()], session=session
                )

            assert target_account is not None
            assert target_profile is not None

            return ProductInDbInBranch(
                **new_product.model_dump(),
                account=target_account,
                saleProfile=target_profile,
            )
