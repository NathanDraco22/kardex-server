from repos.v1.users.models.user_model import UserRole


class Modules:
    ALL = "all"
    CLIENTS = "clients"
    SUPPLIERS = "suppliers"
    PRODUCTS = "products"
    COMMERCIAL = "commercial"
    FINANCE = "finance"
    INVENTORY = "inventory"
    SETTINGS = "settings"


class CommercialSubModules:
    ORDERS = "orders"
    CREATE_ORDER = "createOrder"
    CREATE_INVOICE = "createInvoice"
    PENDING_INVOICES = "pendingInvoices"
    INVOICE_HISTORY = "invoiceHistory"
    PRICE_SETTING = "priceSetting"


default_roles = [
    UserRole(name="Admin", access=[Modules.ALL]),
    UserRole(
        name="Vendedor",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.PENDING_INVOICES,
        ],
    ),
    UserRole(
        name="Operador",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.CREATE_INVOICE,
            CommercialSubModules.PENDING_INVOICES,
            CommercialSubModules.INVOICE_HISTORY,
            CommercialSubModules.PRICE_SETTING,
            Modules.SUPPLIERS,
            Modules.CLIENTS,
            Modules.PRODUCTS,
            Modules.INVENTORY,
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
