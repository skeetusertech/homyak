from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject

class AdminNotifyMiddleware(BaseMiddleware):
    def __init__(self, bot):
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        return await handler(event, data)