import logging

from aiogram import Dispatcher

from src.utils.logger import ChatLogger

from . import admin
from .user import game

logger = logging.getLogger(__name__)
chat_logger = ChatLogger()


async def startup():
    logger.info("Started...")
    await chat_logger.info("Let's go! \U0001F680")


async def shutdown():
    logger.info("...Shutdown")


def attach_routers(dp: Dispatcher):
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    dp.include_routers(game.router(), admin.router())
