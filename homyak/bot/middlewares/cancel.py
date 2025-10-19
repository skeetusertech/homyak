from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext
from typing import Callable, Dict, Any, Awaitable

class FSMCancelMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            state: FSMContext = data["state"]
            current_state = await state.get_state()
            

            if current_state is None:
                return await handler(event, data)
                
            if event.text.startswith("/"):
                return await handler(event, data)
                
            # await state.clear()
            # await event.answer("❌ Ошибка, попробуйте заново (cancel by middleware)")
            # return

        return await handler(event, data)