from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, LabeledPrice
from aiosend.enums import InvoiceStatus
from datetime import timedelta, datetime
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..database.premium import set_premium
from ..config import ADMIN_CHAT_ID, CRYPTO_BOT_TOKEN
from bot.services.cryptobot import CryptoBotService
from bot.services import crypto_service
from ..database.premium import get_premium
import logging

logger = logging.getLogger(__name__)
router = Router()

_bot_instance: Bot | None = None

def set_bot_instance(bot: Bot):
    global _bot_instance
    _bot_instance = bot


PRICE_PLANS = {
    "1_month": 8,
    "3_months": 30,
    "6_months": 50,
    "1_year": 90,
    "lifetime": 200
}

def format_display_name(plan_key: str) -> str:
    name = plan_key.replace("_", " ")
    if "month" in name:
        name = name.replace("month", "месяц")
        if not name.startswith("1 "):
            name = name.replace("месяц", "месяца")
    elif "year" in name:
        name = name.replace("year", "год")
    elif "lifetime" in name:
        name = "навсегда"
    return name.title()

async def notify_user_about_payment(user_id: int, plan: str, amount: float, asset: str):
    if _bot_instance is None:
        logger.error("bot instance")
        return

    try:

        from ..database.premium import set_premium
        if plan == "lifetime":
            await set_premium(user_id, is_lifetime=True)
        elif plan == "1_year":
            await set_premium(user_id, days=365)
        else:
            months = int(plan.split("_")[0])
            await set_premium(user_id, days=months * 30)

        display_name = format_display_name(plan)
        await _bot_instance.send_message(
            user_id,
            f"✅ Premium активирован!\n"
            f"Срок: {'Навсегда' if plan == 'lifetime' else f'{months * 30} дней'}"
        )
    except Exception as e:
        logger.error(f"error by set premium 69 : {e}")

global_bot = None

@router.message(Command("premium"))
async def cmd_premium(message: Message):
    from ..database.premium import get_premium
    premium_info = await get_premium(message.from_user.id)
    
    if premium_info and premium_info.get("is_lifetime"):
        description = (
            "👑 У вас активен Premium (навсегда)!\n\n"
            "💵 Ваши привилегии:\n"
            "КД 12 часов вместо 24\n"
            "+5% шанс на редкие хомяки\n"
            "+1000 очков за каждого хомяка"
        )
        await message.answer(description, parse_mode="HTML")
        return

    status_text = ""
    if premium_info and premium_info.get("expires_at"):
        from datetime import datetime
        expires_date = datetime.fromisoformat(premium_info["expires_at"]).strftime("%d.%m.%Y")
        status_text = f"👑 Premium активен до {expires_date}!\n\n"

    description = (
        f"{status_text}"
        "🌟Premium-подписка даёт:\n"
        "КД 12 часов вместо 24\n"
        "+5% шанс на редкие хомяки\n"
        "+1000 очков за каждого хомяка\n\n"
        "Выберите способ оплаты:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="pay_stars"),
        InlineKeyboardButton(text="💰 CryptoBot", callback_data="pay_cryptobot")
    )
    await message.answer(description, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(lambda c: c.data == "pay_stars")
async def pay_stars(callback_query: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for plan_key in PRICE_PLANS.keys():
        stars = PRICE_PLANS[plan_key]
        display_name = format_display_name(plan_key)
        builder.add(InlineKeyboardButton(
            text=f"📅 {display_name} - {stars} Stars",
            callback_data=f"stars_{plan_key}"
        ))
    builder.adjust(1)
    await callback_query.message.edit_text("🌟 Выберите тариф:", reply_markup=builder.as_markup())
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith("stars_"))
async def stars_plan_selected(callback_query: CallbackQuery):
    plan = "_".join(callback_query.data.split("_")[1:])
    if plan not in PRICE_PLANS:
        await callback_query.answer("❌ Неверный тариф", show_alert=True)
        return

    amount = PRICE_PLANS[plan]
    display_name = format_display_name(plan)
    prices = [LabeledPrice(label=f"Premium ({display_name})", amount=amount)]
    await callback_query.message.answer_invoice(
        title="Homyak Premium",
        description=f"Premium на {display_name}",
        payload=f"premium|{plan}|{callback_query.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=prices,
        need_name=False,
        need_email=False,
        need_phone_number=False,
        need_shipping_address=False,
        is_flexible=False,
    )
    await callback_query.answer()

@router.pre_checkout_query()
async def pre_checkout_query(query):
    await query.bot.answer_pre_checkout_query(query.id, ok=True)

@router.message(lambda m: m.successful_payment)
async def on_successful_payment(message: Message):
    payment = message.successful_payment
    user_id = message.from_user.id

    payload_parts = payment.invoice_payload.split("|")
    if len(payload_parts) != 3 or payload_parts[0] != "premium":
        await message.answer("❌ Неизвестный платеж.")
        return

    plan = payload_parts[1]
    buyer_id = int(payload_parts[2])
    if buyer_id != user_id:
        await message.answer("❌ Платёж не ваш.")
        return

    display_name = format_display_name(plan)
    if plan == "lifetime":
        await set_premium(user_id, is_lifetime=True)
    elif plan == "1_year":
        await set_premium(user_id, days=365)
    else:
        months = int(plan.split("_")[0])
        await set_premium(user_id, days=months * 30)

    await message.answer(f"✅ Вам выдан Premium на {display_name}!\nСпасибо за поддержку!")
    
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID {user_id}"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or "Без имени"
    text = (
        f"✅ Оплата произведена \n"
        f"Покупатель: {full_name} ({username})\n"
        f"ID: {buyer_id}\n"
        f"Покупка: Premium {display_name}\n"
        f"Стоимость: {payment.total_amount}\n"
        f"ID операции: {payment.telegram_payment_charge_id}"
    )
    try:
        await message.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, message_thread_id=102)
    except Exception as e:
        logger.error(f"cant send log 194 premium: {e}")

@router.callback_query(lambda c: c.data == "pay_cryptobot")
async def pay_cryptobot_menu(callback_query: CallbackQuery):

    builder = InlineKeyboardBuilder()
    CRYPTO_PRICES = {"1_month": 0.2, "3_months": 0.4, "6_months": 0.6, "1_year": 1.1, "lifetime": 2.5}
    for plan_key in CRYPTO_PRICES.keys():
        usdt = CRYPTO_PRICES[plan_key]
        display_name = format_display_name(plan_key)
        builder.add(InlineKeyboardButton(
            text=f"📅 {display_name} - {usdt} USDT",
            callback_data=f"crypto_{plan_key}"
        ))
    builder.adjust(1)
    await callback_query.message.edit_text("💰 Выберите премиум для оплаты в USDT:", reply_markup=builder.as_markup())
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith("crypto_"))
async def crypto_plan_selected(callback_query: CallbackQuery):
    if not CRYPTO_BOT_TOKEN:
        await callback_query.answer("cb non work", show_alert=True)
        return

    plan = callback_query.data[7:]
    CRYPTO_PRICES = {"1_month": 0.2, "3_months": 0.4, "6_months": 0.6, "1_year": 1.1, "lifetime": 2.5}
    if plan not in CRYPTO_PRICES:
        await callback_query.answer("❌ Неверный выбор", show_alert=True)
        return

    try:
        service = crypto_service.service
        if service is None:
            raise ValueError("кб нон ворк")
        
        invoice = await service.create_invoice(plan, callback_query.from_user.id)
        
        display_name = format_display_name(plan)
        amount = CRYPTO_PRICES[plan]
        
        caption = (
            f"🛒 <b>Покупка Premium: {display_name}</b>\n\n"
            f"💰 <b>Стоимость:</b> {amount} USDT\n"
            f"💳 <b>Способ оплаты:</b> CryptoBot \n\n"
            f"Нажмите кнопку ниже, чтобы перейти к оплате!"
        )
        
        pay_button = InlineKeyboardButton(
            text="💵 Оплатить",
            url=invoice.bot_invoice_url
        )
        check_button = InlineKeyboardButton(
            text="🔍 Проверить оплату",
            callback_data=f"check_crypto_{invoice.invoice_id}_{callback_query.from_user.id}_{plan}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[pay_button], [check_button]])
        
        await callback_query.message.answer(
            caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"cb ошибка 261 premium: {e}")
        await callback_query.message.answer("❌ Ошибка создания оплаты.")

@router.callback_query(lambda c: c.data.startswith("check_crypto_"))
async def check_crypto_payment(callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    if len(parts) < 5:
        await callback_query.answer("❌ Неверные данные.", show_alert=True)
        return
        
    invoice_id = parts[2]
    try:
        user_id = int(parts[3])
        plan = parts[4]
    except (ValueError, IndexError):
        await callback_query.answer("❌ Ошибка данных.", show_alert=True)
        return

    try:
        service = crypto_service.service
        if service is None:
            await callback_query.answer("❌ Оплата временно недоступна.", show_alert=True)
            return

        invoice_info = await service.crypto_pay.get_invoice(invoice_id)
        
        if invoice_info.status == InvoiceStatus.PAID:
            from ..database.premium import set_premium
            if plan == "lifetime":
                await set_premium(user_id, is_lifetime=True)
            elif plan == "1_year":
                await set_premium(user_id, days=365)
            else:
                months = int(plan.split("_")[0])
                await set_premium(user_id, days=months * 30)
            
            user = await callback_query.bot.get_chat(user_id)
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
            username = f"@{user.username}" if user.username else "нет"
            display_name = format_display_name(plan)
            CRYPTO_PRICES = {"1_month": 0.2, "3_months": 0.4, "6_months": 2.0, "1_year": 1.1, "lifetime": 2.5}
            amount = CRYPTO_PRICES.get(plan, 0)

            oplata = (
                f"✅ CryptoBot\n\n"
                f"👤 Покупатель: {full_name} ({username})\n"
                f"🆔 ID: {user_id}\n"
                f"📅 Тариф: {display_name}\n"
                f"💰 Сумма: {amount} USDT\n"
                f"🧾 Инвойс ID: {invoice_id}"
            )
            await callback_query.bot.send_message(ADMIN_CHAT_ID, oplata, parse_mode="HTML")
            
            await callback_query.message.edit_text(f"✅ Спасибо за покупку!\nВаш Premium активирован на {display_name} месяц")
        else:
            await callback_query.answer(
                "⏳ Оплата не найдена. Попробуйте через 10 секунд.",
                show_alert=True
            )
            
    except Exception as e:
        logger.error(f"Error checking payment 322 premium.py :{e}")
        await callback_query.answer("❌ Ошибка проверки оплаты.", show_alert=True)

async def is_premium_active(user_id: int) -> bool:
    premium = await get_premium(user_id)
    if not premium:
        return False
    if premium["is_lifetime"]:
        return True
    if premium["expires_at"]:
        from datetime import datetime
        return datetime.fromisoformat(premium["expires_at"]) > datetime.now()
    return False