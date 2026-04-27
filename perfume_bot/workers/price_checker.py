import asyncio
import logging
from decimal import Decimal

from perfume_bot.workers.app import app

logger = logging.getLogger(__name__)

SCRAPERS: dict = {}  # заполняется при первом вызове


def _get_scrapers() -> dict:
    global SCRAPERS
    if not SCRAPERS:
        from perfume_bot.scrapers.randewoo import RandewooScraper
        from perfume_bot.scrapers.notino import NotinoScraper
        from perfume_bot.scrapers.zolotoe_yabloko import ZolotoeYablokoScraper
        from perfume_bot.scrapers.letuagl import LetuaglScraper
        SCRAPERS = {
            "Randewoo": RandewooScraper(),
            "Notino": NotinoScraper(),
            "Золотое Яблоко": ZolotoeYablokoScraper(),
            "Летуаль": LetuaglScraper(),
        }
    return SCRAPERS


async def _check_prices_async() -> None:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import selectinload

    from perfume_bot.core.config import settings
    from perfume_bot.core.redis import get_redis
    from perfume_bot.models.favorite import Favorite
    from perfume_bot.models.shop import Shop, ShopOffer
    from perfume_bot.models.user import User
    from perfume_bot.services.notification import NotificationService

    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    notification_svc = NotificationService()
    scrapers = _get_scrapers()

    async with Session() as session:
        # Берём все избранные с активными уведомлениями + последним предложением магазина
        result = await session.execute(
            select(Favorite)
            .where(Favorite.notify_on_price_drop == True)  # noqa: E712
            .options(selectinload(Favorite.user), selectinload(Favorite.perfume))
        )
        favorites = result.scalars().all()

        for fav in favorites:
            # Ищем активные предложения для этого парфюма
            offers_result = await session.execute(
                select(ShopOffer, Shop)
                .join(Shop, ShopOffer.shop_id == Shop.id)
                .where(ShopOffer.perfume_id == fav.perfume_id)
                .order_by(ShopOffer.checked_at.desc())
                .limit(10)
            )
            rows = offers_result.all()
            seen_shops: set[int] = set()
            latest_by_shop: dict[int, tuple] = {}
            for offer, shop in rows:
                if offer.shop_id not in seen_shops:
                    latest_by_shop[offer.shop_id] = (offer, shop)
                    seen_shops.add(offer.shop_id)

            for shop_id, (last_offer, shop) in latest_by_shop.items():
                scraper = scrapers.get(shop.name)
                if scraper is None:
                    continue

                # Проверяем circuit breaker
                redis_gen = get_redis()
                redis = await redis_gen.__anext__()
                paused_until = await redis.get(f"scraper:{shop.name}:paused_until")
                if paused_until:
                    logger.warning("Скрапер %s на паузе", shop.name)
                    continue

                try:
                    offer_result = await scraper.fetch_offer(last_offer.url)
                    # Сбрасываем счётчик ошибок
                    await redis.delete(f"scraper:{shop.name}:fail_count")
                except Exception as exc:
                    logger.error("Скрапер %s ошибка: %s", shop.name, exc)
                    fail_count = await redis.incr(f"scraper:{shop.name}:fail_count")
                    await redis.expire(f"scraper:{shop.name}:fail_count", 7200)
                    if int(fail_count) >= 5:
                        await redis.setex(f"scraper:{shop.name}:paused_until", 3600, "1")
                        logger.warning("Circuit breaker сработал для %s", shop.name)
                    continue

                new_price = offer_result.price_rub
                if new_price is None:
                    continue

                # Сохраняем новую запись (append-only)
                new_offer = ShopOffer(
                    perfume_id=fav.perfume_id,
                    shop_id=shop_id,
                    url=last_offer.url,
                    price_rub=new_price,
                    in_stock=offer_result.in_stock,
                )
                session.add(new_offer)

                # Проверяем снижение цены
                if last_offer.price_rub and notification_svc.is_price_drop(
                    last_offer.price_rub, new_price
                ):
                    text = notification_svc.format_notification(
                        perfume_name=fav.perfume.name,
                        brand=fav.perfume.brand,
                        old_price=last_offer.price_rub,
                        new_price=new_price,
                        shop_name=shop.name,
                        shop_url=last_offer.url,
                    )
                    app.send_task(
                        "perfume_bot.workers.notifier.notify_user",
                        args=[fav.user.tg_user_id, text],
                        queue="notifications",
                    )

        await session.commit()
    await engine.dispose()


@app.task(name="perfume_bot.workers.price_checker.check_prices", bind=True, max_retries=3)
def check_prices(self) -> None:
    asyncio.run(_check_prices_async())
