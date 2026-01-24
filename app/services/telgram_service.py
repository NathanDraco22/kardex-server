import os
import asyncio
from typing import Self
import httpx


class TelegramService:
    _instance: Self | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.__tlg_token = os.getenv("TELEGRAM_BOT_TOKEN")

    async def send_message(self, chat_id: str, text: str):
        if not self.__tlg_token:
            return
        BASE_URL = f"https://api.telegram.org/bot{self.__tlg_token}/sendMessage"

        if not chat_id:
            return

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(BASE_URL, json=payload, timeout=2.0)
            if response.status_code != 200:
                print(
                    f"Error al enviar alerta a Telegram: {response.status_code} - {response.text}"
                )


async def test_run():
    GROUP_ID = "-5148990143"
    content = "Esto es una *prueba* de _Telegram_"

    await TelegramService().send_message(GROUP_ID, content)


if __name__ == "__main__":
    asyncio.run(test_run())
