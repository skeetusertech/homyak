from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from ..database import add_user

class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            await add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        return await handler(event, data)