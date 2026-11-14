from kardex.repos.v1.user_roles.models.user_role_model import (
    BaseUserRole,
    ModuleItem,
    ModulesCatalogResponse,
    SubModuleItem,
)


class Modules:
    ALL = "all"
    COMMERCIAL = "commercial"
    SUPPLIERS = "suppliers"
    CLIENTS = "clients"
    PRODUCTS = "products"
    INVENTORY = "inventory"
    PENDING_INVOICES = "pendingInvoices"
    FINANCE = "finance"
    SETTINGS = "settings"
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

    @staticmethod
    def get_default_role_ids() -> set[str]:
        return {role.name for role in default_roles}

    @staticmethod
    def is_default_role(role_id: str) -> bool:
        return role_id in {role.name for role in default_roles}

    @staticmethod
    def get_modules_catalog() -> ModulesCatalogResponse:
        return ModulesCatalogResponse(
            allAccessKey=Modules.ALL,
            modules=[
                ModuleItem(
                    key=Modules.CLIENTS,
                    name="Clientes",
                    description="Directorio, saldos iniciales, mapas y grupos de clientes",
                ),
                ModuleItem(
                    key=Modules.SUPPLIERS,
                    name="Proveedores",
                    description="Catálogo y gestión de proveedores",
                ),
                ModuleItem(
                    key=Modules.PRODUCTS,
                    name="Productos",
                    description="Catálogo de productos, categorías, unidades y escalas",
                ),
                ModuleItem(
                    key=Modules.COMMERCIAL,
                    name="Comercial",
                    description="Ventas, facturación, órdenes, devoluciones y notas de crédito",
                    submodules=[
                        SubModuleItem(
                            key=CommercialSubModules.CREATE_INVOICE,
                            name="Facturación y Caja",
                            description="Emitir facturas, recibos, terminal de venta y reportes diarios",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.ORDERS,
                            name="Ver Órdenes",
                            description="Consultar órdenes de venta y demanda vs stock",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.CREATE_ORDER,
                            name="Crear Órdenes y Proformas",
                            description="Registrar órdenes de venta y proformas",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.PENDING_INVOICES,
                            name="Facturas Pendientes (Comercial)",
                            description="Consultar y gestionar cuentas pendientes desde Comercial",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.INVOICE_HISTORY,
                            name="Historial de Facturas",
                            description="Consultar historial completo de facturas emitidas",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.PRICE_SETTING,
                            name="Configuración de Precios",
                            description="Ajustar precios y márgenes de productos",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.CREATE_DEVOLUTION,
                            name="Crear Devolución",
                            description="Registrar devoluciones de clientes y anónimas",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.DEVOLUTION_HISTORY,
                            name="Historial de Devoluciones",
                            description="Consultar devoluciones registradas",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.PROCESS_DEVOLUTION,
                            name="Procesar Devoluciones",
                            description="Aprobar o procesar devoluciones pendientes",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.CREATE_CREDIT_NOTE,
                            name="Crear Nota de Crédito",
                            description="Emitir notas de crédito a partir de devoluciones",
                        ),
                        SubModuleItem(
                            key=CommercialSubModules.CREDIT_NOTE_HISTORY,
                            name="Historial de Notas de Crédito",
                            description="Consultar, aprobar o rechazar notas de crédito",
                        ),
                    ],
                ),
                ModuleItem(
                    key=Modules.PENDING_INVOICES,
                    name="Cuentas Pendientes",
                    description="Gestión de cobros, saldos vencidos y abonos",
                ),
                ModuleItem(
                    key=Modules.INVENTORY,
                    name="Inventario",
                    description="Existencias, entradas, salidas, traslados y ajustes",
                ),
                ModuleItem(
                    key=Modules.EXPENSES,
                    name="Gastos",
                    description="Gastos operativos, pagos a proveedores y categorías",
                ),
                ModuleItem(
                    key=Modules.FINANCE,
                    name="Finanzas",
                    description="Cuentas de clientes, resúmenes ejecutivos y reportes financieros",
                ),
                ModuleItem(
                    key=Modules.ADVANCED_TOOLS,
                    name="Herramientas Avanzadas",
                    description="Estadísticas de productos y proyecciones de venta",
                ),
                ModuleItem(
                    key=Modules.SETTINGS,
                    name="Configuraciones",
                    description="Usuarios, roles, sucursales, integraciones y reglas globales",
                ),
            ],
        )
