import asyncio
import logging
from typing import Optional

from aiogram import Bot

from src.config import config

logging.basicConfig(level="INFO",
                    format="%(asctime)s [%(levelname)s]: %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")


class ChatLogger:
    def __init__(
        self, name: str | None = None, chat_id: Optional[int] = None,
    ):
        self.name = name
        self.chat_id = chat_id if chat_id else config.log_chat_id
        self._bot = Bot(token=config.token, parse_mode=None)

    async def _send(self, flag, msg: object, max_length: int = 4096):
        text = f"{flag}" + (f" | {self.name}" if self.name else "") + f" - {msg}"
        attempt_count = 3
        for text in [text[i : i + max_length] for i in range(0, len(text), max_length)]:
            try:
                await self._bot.send_message(chat_id=self.chat_id, text=text)
            except Exception as e:
                logging.exception(f"Send chat log message\n{type(e).__name__}: {e}")

                attempt_count -= 1
                if attempt_count <= 0:
                    break

                await asyncio.sleep(0.15)

    async def info(self, msg: object):
        await self._send("Info", msg)

    async def error(self, msg: object):
        await self._send("Error", msg)
