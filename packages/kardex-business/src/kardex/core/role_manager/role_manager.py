from kardex.repos.v1.user_roles import BaseUserRole


class Modules:
    ALL = "all"
    COMMERCIAL = "commercial"
    SUPPLIERS = "suppliers"
    CLIENTS = "clients"
    PRODUCTS = "products"
    INVENTORY = "inventory"
    USERS = "users"
    ROLES = "roles"
    ADVANCED_TOOLS = "advancedTools"
    EXPENSES = "expenses"


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
    CREATE_CREDIT_NOTE = "createCreditNote"
    CREDIT_NOTE_HISTORY = "creditNoteHistory"


default_roles = [
    BaseUserRole(name="Admin", access=[Modules.ALL]),
    BaseUserRole(
        name="Pre-Venta",
        access=[
            Modules.COMMERCIAL,
            CommercialSubModules.CREATE_INVOICE,
            CommercialSubModules.ORDERS,
            CommercialSubModules.CREATE_ORDER,
            CommercialSubModules.INVOICE_HISTORY,
            CommercialSubModules.CREATE_DEVOLUTION,
            CommercialSubModules.DEVOLUTION_HISTORY,
            CommercialSubModules.CREATE_CREDIT_NOTE,
            CommercialSubModules.CREDIT_NOTE_HISTORY,
        ],
    ),
    BaseUserRole(
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
            CommercialSubModules.CREATE_CREDIT_NOTE,
            CommercialSubModules.CREDIT_NOTE_HISTORY,
        ],
    ),
    BaseUserRole(
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
            CommercialSubModules.CREATE_CREDIT_NOTE,
            CommercialSubModules.CREDIT_NOTE_HISTORY,
            Modules.SUPPLIERS,
            Modules.CLIENTS,
            Modules.PRODUCTS,
            Modules.INVENTORY,
            Modules.EXPENSES,
        ],
    ),
    BaseUserRole(
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
            CommercialSubModules.CREATE_CREDIT_NOTE,
            CommercialSubModules.CREDIT_NOTE_HISTORY,
            Modules.SUPPLIERS,
            Modules.CLIENTS,
            Modules.PRODUCTS,
            Modules.INVENTORY,
            Modules.ADVANCED_TOOLS,
            Modules.EXPENSES,
        ],
    ),
]


class RoleManager:
    @staticmethod
    def get_default_roles() -> list[BaseUserRole]:
        return default_roles
