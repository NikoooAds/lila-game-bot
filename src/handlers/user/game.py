import asyncio
import logging
import random
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.service.user import User, UserService
from src.config import config
from src.utils.logger import ChatLogger

from .deps import BOARD, Cell
from .deps import Keyboard as K
from .deps import (Prompt, calculate_cell, calculate_user_way,
                   convert_until2str, set_my_commands)

logger = logging.getLogger(__name__)
chat_logger = ChatLogger()


async def send_card(cb: CallbackQuery, cell: Cell, reply_markup: Any | None = None):
    caption = f"<b>{cell.title} ({cell.sanskrit})</b>"
    if ":" in cell.description:
        name, desc = cell.description.split(':', maxsplit=1)
        caption += f"\n\n<b>{name}:</b> {desc}"

    if cell.number == 68:
        await cb.message.answer_photo(photo=cell.file_id, caption=caption)

        user_id = cb.from_user.id
        user = await UserService.get(user_id)
        way = calculate_user_way(user.start_number, user.dice_numbers)

        await cb.message.answer(
            "🎉 Игра пройдена!\n\n"
            f'Ваш запрос: "{user.prompt}"\n'
            f"Ваша подсказка через игру лила: {way}\n"
            "Посмотрите внимательно на картинки, что чувствуете?\n"
            "Прочитайте описание, есть ли подсказка?\n"
            "Если хотите обратную связь от проводника нажмите кнопку ниже"
            "и перешлите это сообщение",
            reply_markup=K.link_to_facilitator(),
        )
        is_ok, frozen_until = await UserService.lock_user(user_id)
        logger.info(f"Lock user #{user_id} until {frozen_until:%d.%m.%y %H:%M:%S}, because won")
        return

    if cell.offset != 0:
        caption += "\n\n"
        if cell.number > cell.offset:
            caption += f"🐍 Змея. Вы спускаетесь с {cell.number} на клетку {cell.offset}"
        else:
            caption += f"🏹 Стрела. Вы поднимаетесь с {cell.number} в клетку {cell.offset}"

    await cb.message.answer_photo(
        photo=cell.file_id, caption=caption, reply_markup=reply_markup
    )


async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user = await UserService.get(user_id)
    if not user:
        await UserService.create_user(user_id, message.from_user.full_name)
        await set_my_commands(message.bot, user_id)
        await message.answer(
            (
                "Рада приветствовать тебя в <b>Лила-боте</b> 😊\n\n"
                "❔что умеет этот бот?\n\n"
                "как только ты отправишь запрос, написав его сообщением боту, начнется твой путь Лила-подсказки с карты\n\n"
                'дальше ты будешь бросать кубик и "ходить" по полю Лилы '
                'как будешь "ходить" по полю, в боте ты не увидишь 🫣 '
                "но все внутри сделано так, что ты будешь ходить по всем правилам Лилы💜\n\n"
                "что будешь видеть ты? 👀\n\n"
                "ты будешь видеть карту с номером клетки на которую ты попадаешь, с картинкой и описанием\n\n"
                "карты с описанием - это детская колода карт Омкара ✨\n"
                "она очень нежная и бережная, передает сообщение мягко\n\n"
                "всего у тебя будет <b>5 шагов</b>\n\n"
                "❕карт возможно будет больше, т.к. на поле могут встречаться стрелы 🏹 и змеи 🐍\n"
                "❕а может и меньше, т.к. если ты с любого хода попал на 68 клетку\n"
                "поздравляю🥳 ты точно знаешь ответ на свой вопрос✨\n\n"
                "после бот выдаст сообщение с пройденным путем💫\n\n"
                "просмотри еще раз картинки, почитай описание, "
                "о чем твоя подсказка? 🤓\n\n"
                "если захочешь комментарий от меня,\n"
                "можешь отправить сообщение с путем\n"
                "через кнопку Отправить проводнику\n"
                "сразу попрошу разрешение отвечать голосовым сообщением,"
                "так быстрее😉\n\n"
                "❕бот выдает подсказку 1 раз в неделю, сделан для знакомства с Лилой,  для помощи тебе в волнующих вопросах\n\n"
                "я всегда буду рада помочь и прокомментировать твой путь🤗\n"
                "пользуйся🫶"

            ),
            reply_markup=K.hi()
        )
        await asyncio.sleep(2)
        await message.answer("Введите свой запрос")
        await state.set_state(Prompt.text)
    else:
        if not user.prompt:
            await state.set_state(Prompt.text)

        if (st := await state.get_state()) and st.startswith("Prompt"):
            await message.answer("Введи свой запрос")
            return

        if user.remaining_rolls == 0:
            await message.answer(f"Начать новую игру можно через {convert_until2str(user.frozen_until)}")
        else:
            cell, six_count = calculate_cell(user.start_number, user.dice_numbers)
            await message.answer(
                "Бросай кубик и продолжай игру",
                reply_markup=K.dice_kb(cell, six_count),
            )


async def cb_input_prompt(cb: CallbackQuery, state: FSMContext):
    await cb.answer()

    await cb.message.edit_text("Введите запрос", reply_markup=None)

    await state.set_state(Prompt.text)


async def parse_input_prompt(message: Message, state: FSMContext):
    if text := message.text:
        for c, alias in (('>', '»'), ('<','«')):
            if c in text:
                text = text.replace(c, alias)

        if text := text.strip():
            await state.clear()
            user_id = message.from_user.id
            await UserService.set_prompt(user_id, text)

            await message.answer(
                f'Ваш запрос «{text}»\nДальше Вы получите по нему подсказку',
                reply_markup=K.lets_go(),
            )
            return

    await message.answer("Введите запрос с которым пришли в игру")


async def cb_lets_go(cb: CallbackQuery):
    await cb.answer()
    await cb.message.delete_reply_markup()

    user_id = cb.from_user.id
    cell_number = random.randint(1, 72)
    cell = BOARD[cell_number]

    await UserService.set_start_number(user_id, cell.number)

    if cell.offset != 0:
        await send_card(cb, cell)

        cell = BOARD[cell.offset]

        await asyncio.sleep(config.card_delay)

    await send_card(cb, cell, K.dice_kb(cell))


async def cb_roll_dice(cb: CallbackQuery):
    await cb.answer()

    await cb.message.delete_reply_markup()

    number, six_count, *_ = cb.data.split("~")
    cell, six_count = BOARD[int(number)], int(six_count)

    user_id = cb.from_user.id
    user = await UserService.get(user_id)
    if not (user.remaining_rolls > 0):
        way = calculate_user_way(user.start_number, user.dice_numbers)
        await cb.message.answer(
            f'Ваш запрос «{user.prompt}»\n'
            f"Ваша подсказка через игру лила: {way}\n\n"
            "Посмотрите внимательно на картинки, что чувствуете?\n\n"
            "Прочитайте описание, есть ли подсказка?\n\n"
            "Если хотите обратную связь от проводника нажмите кнопку ниже"
            "и перешлите это сообщение.",
            reply_markup=K.link_to_facilitator(),
        )
        is_ok, frozen_until = await UserService.lock_user(user_id)
        logger.info(f"Lock user #{user_id} - {user.full_name!r} until {frozen_until:%d.%m.%y %H:%M:%S}, because spent attemps")
        return

    message = await cb.message.answer_dice(emoji="🎲")
    if not message.dice:
        logger.info(f"Not have dice in message for user:{user_id}")
        return

    await asyncio.sleep(config.dice_delay)

    dice_number = message.dice.value
    await UserService.take_dice(user_id, dice_number)
    if dice_number == 6:
        await cb.message.answer(
            "🔮 Шестерка это всегда ещё один бросок",
            reply_markup=K.dice_kb(cell, six_count + 1),
        )
        return

    if six_count == 3:
        await cb.message.answer("🔥 Три шестерки подряд сгорают")
    elif six_count != 0:
        for _ in range(0, six_count):
            if cell.number + 6 <= 72:
                cell = BOARD[cell.number + 6]

                await send_card(cb, cell)
                await asyncio.sleep(config.card_delay)

                if cell.offset != 0:
                    cell = BOARD[cell.offset]
                    await send_card(cb, cell)

                    await asyncio.sleep(config.card_delay)

    if cell.number + dice_number > 72:
        await cb.message.answer(
            "Это число на кубике не работает, бросайте ещё",
            reply_markup=K.dice_kb(cell),
        )
        return

    cell = BOARD[cell.number + dice_number]
    if cell.offset != 0:
        await send_card(cb, cell)

        cell = BOARD[cell.offset]

        await asyncio.sleep(config.card_delay)

    await send_card(cb, cell, K.dice_kb(cell))


def router():
    router = Router()
    router.message.register(cmd_start, Command("start"))
    router.callback_query.register(cb_input_prompt, F.data.endswith("~input_prompt"))
    router.message.register(parse_input_prompt, Prompt.text)
    router.callback_query.register(cb_lets_go, F.data.endswith("~lets_go"))
    router.callback_query.register(cb_roll_dice, F.data.endswith("~dice"))
    return router
