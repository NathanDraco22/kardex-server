from fastapi import APIRouter

from .auths.auths_router import auths_router
from .branches.branches_router import branches_router
from .client_transactions.client_transactions_router import client_transactions_router
from .clients.clients_router import clients_router
from .core_settings.core_settings_router import core_settings_router
from .entry_docs.entry_docs_router import entry_docs_router
from .entry_histories.entry_histories_router import entry_histories_router
from .exit_docs.exit_docs_router import exit_docs_router
from .exit_histories.exit_histories_router import exit_histories_router
from .expiration_logs.expiration_logs_router import expiration_logs_router
from .inventories.inventories_router import inventories_router
from .invoices.invoices_router import invoices_router
from .orders.orders_router import orders_router
from .product_accounts.product_accounts_router import product_accounts_router
from .product_categories.product_categories_router import product_categories_router
from .product_prices.product_prices_router import product_prices_router
from .product_sale_profiles.product_sale_profiles_router import product_sale_profiles_router
from .product_transactions.product_transactions_router import product_transactions_router
from .products.products_router import products_router
from .receipts.receipts_router import receipts_router
from .suppliers.suppliers_router import suppliers_router
from .units.units_router import units_router
from .user_roles.user_roles_router import user_roles_router
from .users.users_router import users_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(auths_router, prefix="/auths")
router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(client_transactions_router, prefix="/client-transactions")
router_v1.include_router(clients_router, prefix="/clients")
router_v1.include_router(core_settings_router, prefix="/core-settings")
router_v1.include_router(entry_docs_router, prefix="/entry-docs")
router_v1.include_router(entry_histories_router, prefix="/entry-histories")
router_v1.include_router(exit_docs_router, prefix="/exit-docs")
router_v1.include_router(exit_histories_router, prefix="/exit-histories")
router_v1.include_router(expiration_logs_router, prefix='/expiration-logs')
router_v1.include_router(inventories_router, prefix="/inventories")
router_v1.include_router(invoices_router, prefix="/invoices")
router_v1.include_router(orders_router, prefix="/orders")
router_v1.include_router(product_accounts_router, prefix="/product-accounts")
router_v1.include_router(product_categories_router, prefix="/product-categories")
router_v1.include_router(product_prices_router, prefix="/product-prices")
router_v1.include_router(product_sale_profiles_router, prefix="/product-sale-profiles")
router_v1.include_router(product_transactions_router, prefix="/product-transactions")
router_v1.include_router(products_router, prefix="/products")
router_v1.include_router(receipts_router, prefix="/receipts")
router_v1.include_router(suppliers_router, prefix="/suppliers")
router_v1.include_router(units_router, prefix="/units")
router_v1.include_router(user_roles_router, prefix="/user-roles")
router_v1.include_router(users_router, prefix="/users")

