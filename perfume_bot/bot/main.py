import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from perfume_bot.bot.handlers import favorites, notes, recommendations, start
from perfume_bot.core.config import settings
from perfume_bot.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Middleware: передаём db-сессию в хендлеры
    from aiogram import BaseMiddleware
    from typing import Any, Callable, Awaitable
    from aiogram.types import TelegramObject

    class DbSessionMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
        ) -> Any:
            async with AsyncSessionLocal() as session:
                data["db"] = session
                return await handler(event, data)

    dp.update.middleware(DbSessionMiddleware())

    dp.include_routers(
        start.router,
        notes.router,
        recommendations.router,
        favorites.router,
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
