import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from .board import BOARD, Cell

logger = logging.getLogger("user.tools")


async def set_my_commands(bot: Bot, user_id: int):
    try:
        return await bot.set_my_commands(
            [BotCommand(command="start", description="Начать игру")],
            scope=BotCommandScopeChat(chat_id=user_id),
        )
    except Exception as e:
        logger.error(f"Set commands for user #{user_id} failed\n"
                     f"{type(e).__name__}: {e}")
    return False


def calculate_cell(init_number: int, dice_numbers: list[int]) -> tuple[Cell, int]:
    cell = BOARD[init_number]
    if cell.offset != 0:
        cell = BOARD[cell.offset]

    count_six = 0
    for number in dice_numbers:
        if number == 6:
            count_six += 1
            continue

        if count_six == 3:
            count_six = 0

        if count_six != 0:
            for _ in range(0, count_six):
                if cell.number + 6 <= 72:
                    cell = BOARD[cell.number + 6]
                    if cell.offset != 0:
                        cell = BOARD[cell.offset]
            count_six = 0

        if cell.number + number > 72:
            continue
        else:
            cell = BOARD[cell.number + number]
            if cell.offset != 0:
                cell = BOARD[cell.offset]

    return cell, count_six


def calculate_user_way(init_number: int, dice_numbers: list[int]) -> str:
    def mark(cell: Cell):
        return '🐍' if cell.number > cell.offset else '🏹'

    cell = BOARD[init_number]
    if cell.offset == 0:
        way = f"[{cell.number}]"
    else:
        way = f"[{cell.number} {mark(cell)} {cell.offset}]"
        cell = BOARD[cell.offset]

    count_six = 0
    for n in dice_numbers:

        if n == 6:
            count_six += 1
            continue

        if count_six == 3:
            way += " (6x3=🔥)"
            count_six = 0

        if count_six != 0:
            for _ in range(0, count_six):
                way += f" (+{6})"
                if cell.number + 6 <= 72:
                    cell = BOARD[cell.number + 6]
                    way += f" » {cell.number} "
                    if cell.offset != 0:
                        m = mark(cell)
                        cell = BOARD[cell.offset]
                        way += f" {m} {cell.number} "
                else:
                    way += " ✖️"

            count_six = 0

        way += f" (+{n})"

        if cell.number + n > 72:
            way += " ✖️"
        else:
            cell = BOARD[cell.number + n]
            way += f" » {cell.number}"
            if cell.offset != 0:
                m = mark(cell)
                cell = BOARD[cell.offset]
                way += f" {m} {cell.number}"
    return way


def convert_until2str(frozen_until: datetime) -> str:
    now = datetime.now()

    time_left = frozen_until - now
    if time_left.total_seconds() < 0:
        return "меньше секунды"

    text = ""
    days = time_left.days
    if days and days > 0:
        text += f"{days} дн. "

    hours = time_left.seconds // 3600
    if hours and hours > 0:
        text += f"{hours:2d} ч. "

    minutes = (time_left.seconds % 3600) // 60
    if minutes and minutes > 0:
        text += f"{minutes:2d} мин. "

    seconds = time_left.seconds % 60
    if seconds and seconds > 0:
        text += f"{seconds:2d} сек. "

    if not text:
        return "меньше секунды"
    return text
