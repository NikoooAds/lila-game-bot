from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import config
from src.service.user import User, UserStorageService

UserService = UserStorageService()


async def cmd_users(message: Message):
    text = "Пользователи:"
    users: list[User] = await UserService.get_all()
    for u in sorted(users, key=lambda x: x.created_at):
        text += (
            f"\n<code>{u.id}</code> | {u.full_name} ({u.created_at:%d.%m.%Y %H:%M:%S})"
            f"\n ️➜ [{u.start_number}] » {u.dice_numbers}"
        )
    await message.answer(text)


async def cmd_delete_user(message: Message):
    _, *user_ids = message.text.split()
    text = "Удаленные пользователи:"
    for uid in user_ids:
        if uid.isdigit():
            deleted = await UserService.delete(int(uid))
            text += f"\n * {uid} - {'deleted' if deleted else 'not found'}"
        else:
            text += f"\n [x] {uid}"

    await message.answer(text)


def router():
    router = Router()
    router.message.register(cmd_users, Command("users"), F.from_user.id.in_([config.admin_id]))
    router.message.register(cmd_delete_user, Command("delete_user"), F.from_user.id.in_([config.admin_id]))
    return router
