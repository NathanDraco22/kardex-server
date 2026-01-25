from datetime import datetime

from typing import Self, Literal
from services import TelegramService

from tools.integration_tool import IntegrationTool
from repos.v1.daily_summaries import DailySummaryInDb


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

        message = f"⚠️ *Ajuste de Inventario* ⚠️\n📦 *{branch_name}* \n📄 documento: *{document}*\ntipo: *{adjust_type_label}*\nAutor: *{author}*"
        await TelegramService().send_message(adjustments_channel, message)

    async def notify_daily_report(self, daily_summary: DailySummaryInDb) -> None:
        current_integration = await IntegrationTool().get_current_integration()
        telegram = current_integration.telegram

        if not telegram.isActive:
            return

        report_channel = telegram.reportId

        utility = daily_summary.total - daily_summary.totalCost

        datetime_obj = datetime.strptime(daily_summary.dateId, "%Y-%m-%d")

        formatted_datetime = (
            f"{datetime_obj.day} de {month_es[datetime_obj.month]} {datetime_obj.year}"
        )

        message = f"""📊 *Reporte Diario* 📊
📅 *{formatted_datetime}*
💲 Ventas: *C$ {daily_summary.total / 100}*
📈 Costos: *C$ {daily_summary.totalCost / 100}*
💰 Utilidad: *C$ {utility / 100}*
"""

        await TelegramService().send_message(report_channel, message)
