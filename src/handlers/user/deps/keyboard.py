from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup

from src.config import config

from .board import Cell


class Keyboard:

    @staticmethod
    def hi():
        channel_url = f"https://t.me/{config.target_chat}"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [Button(text="Преветственное видео", url=f"{channel_url}/11")],
                [Button(text="Канал Проводника", url=channel_url)],
            ]
        )
    @staticmethod
    def lets_go():
        return InlineKeyboardMarkup(
            inline_keyboard=[[Button(text="Начать", callback_data="~lets_go")]]
        )

    @staticmethod
    def input_prompt():
        return InlineKeyboardMarkup(
            inline_keyboard=[[Button(text="Начать", callback_data="~input_prompt")]]
        )

    @staticmethod
    def dice_kb(cell: Cell, total_six_before: int = 0):
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [Button(text="Бросить  🎲", callback_data=f"{cell.number}~{total_six_before}~dice")]
            ]
        )

    @staticmethod
    def link_to_facilitator ():
        channel_url = f"https://t.me/{config.target_chat}"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [Button(text="Написать Проводнику", url=f"{channel_url}?direct")],
                [Button(text="Канал Проводника", url=channel_url)],
            ]
        )
