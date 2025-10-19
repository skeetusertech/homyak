from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..database.scores import get_top_scores_in_chat

router = Router()


@router.message(Command("top"))
async def cmd_top(message: Message):
    chat = message.chat

    if chat.type == "private":
        await message.answer("Команда доступна только в групповых чатах.")
        return

    top_scores = await get_top_scores_in_chat(chat.id, limit=10)

    if not top_scores:
        await message.answer("🏆 Пока нет участников с очками в этом чате.")
        return

    lines = ["🏆 Топ участников по очкам:"]
    for position, (user_id, score, first_name, username) in enumerate(top_scores, start=1):
        display_name = escape(first_name) if first_name else "Без имени"
        if username:
            display = f"@{username}"
        else:
            display = f"<a href=\"tg://user?id={user_id}\">{display_name}</a>"
        lines.append(f"{position}. {display} — {score:,} очков")

    await message.answer("\n".join(lines))
