import asyncio
from decimal import Decimal

from perfume_bot.core.config import settings


class NotificationService:

    def is_price_drop(self, old_price: Decimal, new_price: Decimal) -> bool:
        if old_price <= 0:
            return False
        drop_ratio = (old_price - new_price) / old_price
        return drop_ratio >= Decimal(str(settings.price_drop_threshold))

    def format_notification(
        self,
        perfume_name: str,
        brand: str,
        old_price: Decimal,
        new_price: Decimal,
        shop_name: str,
        shop_url: str,
    ) -> str:
        drop_pct = int((old_price - new_price) / old_price * 100)
        return (
            f"🎉 <b>Снижение цены!</b>\n\n"
            f"🌸 <b>{perfume_name}</b> — {brand}\n"
            f"💰 Было: {int(old_price)} ₽ → Стало: <b>{int(new_price)} ₽</b> (-{drop_pct}%)\n"
            f"🏪 Магазин: {shop_name}\n"
            f"🛒 <a href='{shop_url}'>Купить</a>"
        )

    async def send(self, tg_user_id: int, text: str) -> None:
        from aiogram import Bot
        bot = Bot(token=settings.telegram_bot_token)
        try:
            await bot.send_message(chat_id=tg_user_id, text=text, parse_mode="HTML")
        finally:
            await bot.session.close()
