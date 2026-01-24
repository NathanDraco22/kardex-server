from typing import Self, Literal
from services import TelegramService

from tools.integration_tool import IntegrationTool


AdjusmentType = Literal["in", "out"]


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
