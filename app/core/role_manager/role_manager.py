from repos.v1.users.models.user_model import UserRole


class Modules:
    ALL = "all"
    CLIENTS = "clients"
    PRODUCTS = "products"
    COMMERCIAL = "commercial"
    FINANCE = "finance"
    INVENTORY = "inventory"
    ADVANCED_TOOLS = "advancedTools"
    SETTINGS = "settings"


class CommercialSubModules:
    ORDERS = "orders"
    CREATE_ORDER = "createOrder"
    CREATE_INVOICE = "createInvoice"
    PENDING_INVOICES = "pendingInvoices"
    INVOICE_HISTORY = "invoiceHistory"
    PRICE_SETTING = "priceSetting"
    CREATE_DEVOLUTION = "createDevolution"
    DEVOLUTION_HISTORY = "devolutionHistory"
    PROCESS_DEVOLUTION = "processDevolution"


default_roles = [
    UserRole(name="Admin", access=[Modules.ALL]),
    UserRole(
        name="Vendedor",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.CREATE_INVOICE,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.PENDING_INVOICES,
            CommercialSubModules.INVOICE_HISTORY,
            CommercialSubModules.CREATE_DEVOLUTION,
            CommercialSubModules.DEVOLUTION_HISTORY,
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
            CommercialSubModules.CREATE_DEVOLUTION,
            CommercialSubModules.DEVOLUTION_HISTORY,
            CommercialSubModules.PROCESS_DEVOLUTION,
            Modules.CLIENTS,
            Modules.PRODUCTS,
            Modules.INVENTORY,
        ],
    ),
    UserRole(
        name="Supervisor",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.CREATE_INVOICE,
            CommercialSubModules.PENDING_INVOICES,
            CommercialSubModules.INVOICE_HISTORY,
            CommercialSubModules.PRICE_SETTING,
            CommercialSubModules.CREATE_DEVOLUTION,
            CommercialSubModules.DEVOLUTION_HISTORY,
            CommercialSubModules.PROCESS_DEVOLUTION,
            Modules.CLIENTS,
            Modules.PRODUCTS,
            Modules.INVENTORY,
            Modules.ADVANCED_TOOLS,
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
