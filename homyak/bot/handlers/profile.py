from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import timedelta, datetime
from ..database.premium import get_premium
from ..database.scores import get_score
from ..database.cards import get_user_cards, get_total_cards_count
from ..database.admins import is_admin

router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = message.from_user
    user_id = user.id

    total_score, last_homyak = await get_score(user_id)
    total_score = total_score or 0
    name = user.first_name or "Error to get name"
    user_cards = await get_user_cards(user_id)
    total_cards = await get_total_cards_count()
    opened_cards = len(user_cards)

    admin_status = " Administrator" if await is_admin(user_id) else ""

    premium_info = await get_premium(user_id)
    premium_text = ""
    if premium_info:
        if premium_info["is_lifetime"]:
            premium_text = "\n👑 Premium: Навсегда"
        elif premium_info["expires_at"]:
            expires_date = datetime.fromisoformat(premium_info["expires_at"]).strftime("%d.%m.%Y")
            premium_text = f"\n👑 Premium до: {expires_date}"

    photos = await message.bot.get_user_profile_photos(user_id, limit=1)
    photo_file_id = None
    if photos.photos:
        photo_file_id = photos.photos[0][-1].file_id

    last_homyak_text = last_homyak if last_homyak else "ещё не было"
    text = (
        f"👋 Привет, {name}!{premium_text}\n\n"
        f"✨ Очки: {total_score:,}\n"
        f"🃏 Карточек: {opened_cards} / {total_cards}\n"
        f"🐹 Последний хомяк: {last_homyak_text}\n"
        f"🎁 Открывай хомяков каждый день и собирай свою коллекцию!\n\n"
        f"{admin_status}"
    )

    if photo_file_id:
        await message.answer_photo(photo=photo_file_id, caption=text)
    else:
        await message.answer(text)