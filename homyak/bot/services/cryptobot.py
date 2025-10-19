from aiosend import CryptoPay, TESTNET, MAINNET
from aiogram import Bot
from aiosend.types import Invoice
import logging

logger = logging.getLogger(__name__)

class CryptoBotService:
    def __init__(self, token: str, bot: Bot):
        self.crypto_pay = CryptoPay(token, MAINNET)
        self.bot = bot
        self.on_payment_callback = None
        self._register_handlers()

    def set_payment_callback(self, callback):
        self.on_payment_callback = callback

    def _register_handlers(self):
        @self.crypto_pay.invoice_paid()
        async def handle_payment(invoice: Invoice):
            try:
                payload_parts = invoice.payload.split("|")
                if len(payload_parts) != 3 or payload_parts[0] != "crypto_premium":
                    return

                plan = payload_parts[1]
                user_id = int(payload_parts[2])

                if self.on_payment_callback:
                    await self.on_payment_callback(
                        user_id=user_id,
                        plan=plan,
                        amount=invoice.amount,
                        asset=invoice.asset
                    )

            except Exception as e:
                logger.error(f"error payment 41 :  {e}")

    def _format_display_name(self, plan_key: str) -> str:
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

    async def create_invoice(self, plan: str, user_id: int):
        CRYPTO_PRICES = {
            "1_month": 0.2,
            "3_months": 1.4,
            "6_months": 0.6,
            "1_year": 1.1,
            "lifetime": 2.5,
        }
        amount = CRYPTO_PRICES.get(plan)
        if amount is None:
            raise ValueError(f"error value cryptobot 66 : {plan}")

        try:
            invoice = await self.crypto_pay.create_invoice(
                asset="USDT",
                amount=amount,
                description=f"Premium {self._format_display_name(plan)}",
                payload=f"crypto_premium|{plan}|{user_id}"
            )
            return invoice
        except Exception as e:
            logger.error(f"error create invoice {e}")
            raise

    async def start_polling(self):
        """Запуск обработчика платежей"""
        try:
            await self.crypto_pay.start_polling()
        except Exception as e:
            logger.error(f"error cryptobot cryptobot.py : {e}")
            raise