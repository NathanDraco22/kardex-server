from repos.v1.users.models.user_model import UserRole


class Modules:
    ALL = "all"
    CLIENTS = "clients"
    SUPPLIERS = "suppliers"
    PRODUCTS = "products"
    COMMERCIAL = "commerical"
    FINANCE = "finance"
    INVENTORY = "inventory"
    SETTINGS = "settings"


class CommercialSubModules:
    ORDERS = "orders"
    CREATE_ORDER = "create_order"
    CREATE_INVOICE = "create_invoice"
    PENDING_INVOICES = "pending_invoices"
    INVOICE_HISTORY = "invoice_history"
    PRICE_SETTING = "price_setting"


default_roles = [
    UserRole(name="admin", access=[Modules.ALL]),
    UserRole(
        name="saler",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.PENDING_INVOICES,
        ],
    ),
]


class RoleManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RoleManager, cls).__new__(cls)
        return cls._instance

    def get_default_roles(self) -> list[UserRole]:
        return default_roles
