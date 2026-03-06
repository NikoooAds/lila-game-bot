import asyncio
import logging
from datetime import datetime, timedelta

import aiocron
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import FSInputFile

from src.config import IMAGES, config
from src.handlers import link
from src.handlers.user.deps import Keyboard as UserK
from src.handlers.user.deps import calculate_cell
from src.service.user import User, UserStorageService
from src.utils.middleware import FirewallMiddleware
from src.utils.tools import load_env

UserService = UserStorageService()

logger = logging.getLogger(__name__)


async def main():
    await UserService.init_db()

    bot = Bot(token=config.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    @aiocron.crontab('*/1 * * * *')
    async def job_1():
        users = await UserService.get_frozen_users()
        if users:
            unlocked_count = 0
            for user in users:
                if user.is_frozen and user.frozen_until < datetime.now() + timedelta(seconds=1):
                    is_ok = await UserService.unlock_user(user.id)
                    await UserService.add_more_rolls(user.id)
                    unlocked_count += 1
                    logger.info(f"Unfreez user #{user.id} - {user.full_name}. Ok: {is_ok}")

                    cell, six_count = calculate_cell(user.start_number, user.dice_numbers)
                    for _ in (1, 2, 3):
                        try:
                            await bot.send_message(chat_id=user.id,
                                                   text="Вы можете продолжить свой путь",
                                                   reply_markup=UserK.dice_kb(cell, six_count))
                        except Exception as e:
                            logger.error(f"Notify #{user.id} failed. Retry after 0.15 sec\n{type(e).__name__}: {e}")
                            await asyncio.sleep(0.15)
                        else:
                            break
                    else:
                        logger.error(f"Not notified user #{user.id}")

            logger.info(f"Still locked {len(users) - unlocked_count}-users. "
                        f"Freed: {unlocked_count}")

    dp = Dispatcher()

    dp.message.outer_middleware(FirewallMiddleware())
    dp.callback_query.outer_middleware(FirewallMiddleware())

    link(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Pooling")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("")
