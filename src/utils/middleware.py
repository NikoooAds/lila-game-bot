import logging
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.enums.chat_type import ChatType
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger("middleware")


class FirewallMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        chat = event.chat if isinstance(event, Message) else event.message.chat
        if chat.type == ChatType.PRIVATE:
            return await handler(event, data)
        else:
            logger.info(f"User #{user_id} call bot not in private chat")
