from tools import UuidTool, TimeTools
from tools.search_tools import generate_prefixes
from core.counter_manager.counter_manager import CounterManager

from repos.v1.products import CreateProduct, ProductInDb
from repos.v1.product_accounts.models.product_account_model import ProductAccountInDb
from repos.v1.product_sale_profiles.models.product_sale_profile_model import ProductSaleProfileInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource

from services import MongoService
from services.mongo_collections.v1 import (
    ProductsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
)


async def process_create_product(
    create_product: CreateProduct,
) -> ProductInDb:
    mongo_client = MongoService().client

    products_col = ProductsCollection()
    accounts_col = ProductAccountsCollection()
    profiles_col = ProductSaleProfilesCollection()

    branches_repo = BranchesRepository(BranchesDataSource())

    all_branches = await branches_repo.get_all_branches()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # 1. Preparar datos del Producto base
            if not create_product.code:
                create_product.code = await CounterManager().next_product_number(session)

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

            for branch in all_branches:
                # 2. Inicializar ProductAccount in 0
                new_account = ProductAccountInDb(
                    productId=new_product_id,
                    branchId=branch.id,
                    currentStock=0,
                    promiseStock=0,
                    averageCost=0,
                    lastCost=0,
                    maximumCost=0,
                    createdAt=now_in_milliseconds,
                )

                # 3. Inicializar ProductSaleProfile in 0
                new_profile = ProductSaleProfileInDb(
                    branchId=branch.id,
                    productId=new_product_id,
                    salePrice=0,
                    salePrice2=0,
                    salePrice3=0,
                    discounts=[],
                )

                new_accounts.append(new_account.model_dump())
                new_profiles.append(new_profile.model_dump())

            # 4. Inserción Transaccional Múltiple (Bulk)
            await products_col.create_product_with_session(
                product=new_product_data, session=session
            )

            await accounts_col.create_many_product_accounts(
                product_accounts=new_accounts, session=session
            )

            await profiles_col.bulk_create_product_sale_profiles(
                product_sale_profiles=new_profiles, session=session
            )

            

            return new_product
