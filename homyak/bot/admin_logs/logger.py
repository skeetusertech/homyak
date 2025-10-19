from aiogram import Bot
from aiogram.types import User
from ..config import ADMIN_CHAT_ID
import logging

logger = logging.getLogger(__name__)

async def notify_new_user(bot: Bot, user: User):
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = f"@{user.username}" if user.username else "нет"
    text = (
        f"🆕 Новый пользователь!\n"
        f"ID: {user.id}\n"
        f"Имя: {full_name}\n"
        f"Юзернейм: {username}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"cant send log found new user: {e}")

async def notify_homyak_found(bot: Bot, user: User, homyak_name: str, chat_type: str):
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = f"@{user.username}" if user.username else "нет"
    text = (
        f"🐹 Выпадение хомяка\n"
        f"Пользователь: {full_name} ({username})\n"
        f"ID: {user.id}\n"
        f"Хомяк: {homyak_name}\n"
        f"Источник: {chat_type}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"cant send log found homyak: {e}")

async def notify_promo_used(bot, user_id, username, full_name, promo_code, reward_type, reward_value, creator_id, remaining_uses):
    reward_names = {
        1: "Очки",
        2: "Хомяк",
        3: "Снятие КД",
        4: "Множитель очков"
    }
    reward_text = reward_names.get(reward_type, "Неизвестно")
    if reward_type == 1:
        reward_text += f" ({reward_value} очков)"
    elif reward_type == 2:
        reward_text += f" ({reward_value})"
    elif reward_type == 4:
        reward_text += f" (+{reward_value} очков)"

    text = (
        f"🎟️ <b>Активация промокода</b>\n"
        f"👤 Пользователь: {full_name} (@{username})\n"
        f"🆔 ID: {user_id}\n"
        f"🎫 Промокод: {promo_code}\n"
        f"🎁 Выдалось: {reward_text}\n"
        f"🔄 Осталось активаций: {remaining_uses}\n"
        f"🛠️ Создал: {creator_id} (ID)"
    )
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"cant send log promo:  {e}")