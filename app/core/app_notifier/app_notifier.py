from datetime import datetime

from typing import Self, Literal
from services import TelegramService

from tools.integration_tool import IntegrationTool
from repos.v1.daily_summaries import DailySummaryInDb
from repos.v1.executive_summaries import ExecutiveSummaryInDb


AdjusmentType = Literal["in", "out"]

month_es = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


class AppNotifier:
    _instance: Self | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def notify_test_message(self) -> None:
        current_integration = await IntegrationTool().get_current_integration()
        telegram = current_integration.telegram

        if not telegram.isActive:
            return

        test_channel = telegram.reportId

        message = """Hola 👋, soy un bot 🤖
mi deber es enviarte mensajes, darte informacion y alertas
sera un placer trabajar contigo.
"""

        await TelegramService().send_message(test_channel, message)

    async def notify_adjustments(
        self, branch_name: str, document: str, type: AdjusmentType, author: str
    ) -> None:
        current_integration = await IntegrationTool().get_current_integration()
        telegram = current_integration.telegram

        if not telegram.isActive:
            return

        adjustments_channel = telegram.adjustmentId

        adjust_type_label: str

        match type:
            case "in":
                adjust_type_label = "Entrada ↙️"
            case "out":
                adjust_type_label = "Salida ↗️"

        message = f"⚠️ *Ajuste de Inventario* ⚠️\n\n📦 *{branch_name}* \n📄 documento: *{document}*\ntipo: *{adjust_type_label}*\nAutor: *{author}*"
        await TelegramService().send_message(adjustments_channel, message)

    async def notify_daily_report(self, daily_summary: DailySummaryInDb) -> None:
        current_integration = await IntegrationTool().get_current_integration()
        telegram = current_integration.telegram

        if not telegram.isActive:
            return

        report_channel = telegram.reportId

        utility = daily_summary.total - daily_summary.totalCost
        ingreso_caja = daily_summary.cashSales + daily_summary.totalReceiptCash

        datetime_obj = datetime.strptime(daily_summary.dateId, "%Y-%m-%d")

        formatted_datetime = (
            f"{datetime_obj.day} {month_es[datetime_obj.month]} {datetime_obj.year}"
        )

        message = f"""📊 *Reporte Diario* 📊
Resultados para {formatted_datetime}

📝 Facturas: {daily_summary.totalInvoices}
💲 Ventas Totales: {(daily_summary.total / 100):,.2f}
  ├ Contado: {(daily_summary.cashSales / 100):,.2f}
  └ Crédito: {(daily_summary.creditSales / 100):,.2f}
📈 Costo de Ventas: {(daily_summary.totalCost / 100):,.2f}
-----------------------------------------------
💰 Utilidad Bruta: {(utility / 100):,.2f}

📥 *RECAUDACIÓN DETALLADA* 📥
💵 Ingresos a Caja: {(ingreso_caja / 100):,.2f}
  ├ Contado: {(daily_summary.cashSales / 100):,.2f}
  └ Abonos: {(daily_summary.totalReceiptCash / 100):,.2f}

🔙 Devoluciones: {(daily_summary.totalReceiptDevolutions / 100):,.2f}

⚠️ Nuevas Cuentas por Cobrar: {(daily_summary.totalOwed / 100):,.2f}
"""

        await TelegramService().send_message(report_channel, message)

    async def notify_executive_report(
        self, executive_summary: ExecutiveSummaryInDb
    ) -> None:
        current_integration = await IntegrationTool().get_current_integration()
        telegram = current_integration.telegram

        if not telegram.isActive:
            return

        title_type: str

        match executive_summary.type:
            case "weekly":
                title_type = "Semanal 📄"
            case "monthly":
                title_type = "Mensual 📅"
            case "yearly":
                title_type = "Anual ⭐"
            case "custom":
                title_type = "Personalizado"

        start_date = datetime.fromtimestamp(executive_summary.startDate / 1000)
        end_date = datetime.fromtimestamp(executive_summary.endDate / 1000)

        date_range = f"{start_date.day}/{month_es[start_date.month]} - {end_date.day}/{month_es[end_date.month]}"

        utility = executive_summary.salesTotal - executive_summary.salesTotalCost
        ingreso_caja = executive_summary.cashSales + executive_summary.totalReceiptCash

        report_channel = telegram.reportId

        message = f"""*Reporte {title_type}*
Periodo: {date_range}

📦 Inventario: {(executive_summary.inventoryTotalCost / 100):,.2f}
⚠️ Cuentas por Cobrar: {(executive_summary.totalPendingInvoices / 100):,.2f}

📝 Facturas: {executive_summary.totalInvoices}
💲 Ventas Totales: {(executive_summary.salesTotal / 100):,.2f}
  ├ Contado: {(executive_summary.cashSales / 100):,.2f}
  └ Crédito: {(executive_summary.creditSales / 100):,.2f}
📈 Costo de Ventas: {(executive_summary.salesTotalCost / 100):,.2f}
---------------------------------------------
💰 Utilidad: {(utility / 100):,.2f}

📥 *RECAUDACIÓN DETALLADA* 📥
💵 Ingresos a Caja: {(ingreso_caja / 100):,.2f}
  ├ Contado: {(executive_summary.cashSales / 100):,.2f}
  └ Abonos: {(executive_summary.totalReceiptCash / 100):,.2f}

🔙 Devoluciones: {(executive_summary.totalReceiptDevolutions / 100):,.2f}
"""

        await TelegramService().send_message(report_channel, message)
