from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from ..database.promo import get_promo, use_promo, is_promo_valid
from ..database.scores import add_score
from ..database.cooldowns import reset_cooldown
from ..admin_logs.logger import notify_promo_used

router = Router()

@router.message(F.text.lower().startswith(("промо ", "/promo@")))
@router.message(Command("promo"))
async def cmd_promo(message: Message):

    text = message.text.strip()
    if text.startswith("/promo"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ Использование: /promo [код]")
            return
        code = parts[1]
    else:
        code = text[6:].strip()

    if not await is_promo_valid(code):
        await message.answer("❌ Промокод недействителен или исчерпан.")
        return

    user_id = message.from_user.id
    
    from ..database.promo import has_user_used_promo
    if await has_user_used_promo(user_id, code):
        await message.answer("❌ Вы уже активировали этот промокод.")
        return

    promo = await get_promo(code)

    promo = await get_promo(code)
    user_id = message.from_user.id

    if promo["reward_type"] == 1: 
        points = int(promo["reward_value"])
        await add_score(user_id, points)
        result_text = f"✅ Получено {points:,} очков!"
    elif promo["reward_type"] == 2:
        from .homyak import send_homyak_by_name
        print(f" Имя в promo.py {promo['reward_value']}")
        await send_homyak_by_name(message, promo["reward_value"])
        # result_text = f"✅ Промокод активирован" 
    elif promo["reward_type"] == 3: 
        await reset_cooldown(user_id)
        result_text = "✅ Активирован промокод\nВаш приз: Снятие КД\n\nНапишите заново «Хомяк« и откройте карточку"
    elif promo["reward_type"] == 4: 

        result_text = f"✅ +{promo['reward_value']} очков за хомяка на {promo['duration']//60} часов!"

    await notify_promo_used(
        bot=message.bot,
        user_id=user_id,
        username=message.from_user.username,
        full_name=message.from_user.first_name,
        promo_code=code,
        reward_type=promo["reward_type"],
        reward_value=promo["reward_value"],
        creator_id=promo["creator_id"],
        remaining_uses=promo["max_uses"] - promo["used_count"] - 1
    )

    from ..database.promo import record_promo_use
    await record_promo_use(user_id, code)
    await use_promo(code) 
    if promo["reward_type"] != 2:
        await message.answer(result_text)