import asyncio
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from src.config import IMAGES
from ..handlers.user.deps.board import BOARD, Cell

logger = logging.getLogger(__name__)


async def load_env(bot: Bot, chat_id: int, load_numbers: list[int] = []):
    pairs = {}
    load_certain = True if load_numbers else False
    for path in IMAGES.glob("*.jpg"):
        file_number = path.name.split(".", maxsplit=1)[0]
        if not file_number.isdigit():
            continue

        if load_certain and int(file_number) not in load_numbers:
            continue

        for i in range(0, 3):
            try:
                message = await bot.send_photo(chat_id, photo=FSInputFile(path))
            except Exception as e:
                await asyncio.sleep(0.15)
            else:
                if message and message.photo:
                    pairs[int(file_number)] = message.photo[-1].file_id
                    break
        else:
            logger.error(f"Load {file_number!r} failed")

        await asyncio.sleep(0.05)

    text = "Update board"
    text += "\nBOARD = {"
    for i, c in BOARD.items():
        if load_certain:
            if i in load_numbers:
                file_id = v if (v := pairs.get(i)) else ""
            else:
                file_id = c.file_id
        else:
            file_id = v if (v := pairs.get(i)) else ""
        t = (
            f'{i}: Cell({c.number},\n'
            f'{c.offset},\n'
            f'"{c.title}",\n'
            f'"{c.sanskrit}",\n'
            f'{repr(c.description).replace("'", "\"")},\n'
            f'"{file_id}"),'
        )
        text += f"\n{t}"
    text += "\n}"

    logger.info(text)
