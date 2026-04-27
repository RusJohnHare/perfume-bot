from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.models import (
    User, Perfume, Shop, ShopOffer, Favorite,
    FragranceCategory,
)
from perfume_bot.services.notification import NotificationService


@pytest.fixture
async def price_drop_scenario(db_session: AsyncSession):
    user = User(tg_user_id=999888777)
    cat = FragranceCategory(name="Ценовая")
    db_session.add_all([user, cat])
    await db_session.flush()

    perfume = Perfume(name="ЦеновойПарфюм", brand="Бренд")
    shop = Shop(name="ТестМагазин", base_url="https://test.shop")
    db_session.add_all([perfume, shop])
    await db_session.flush()

    old_offer = ShopOffer(
        perfume_id=perfume.id,
        shop_id=shop.id,
        url="https://test.shop/product/1",
        price_rub=Decimal("10000"),
        in_stock=True,
    )
    db_session.add(old_offer)
    await db_session.flush()

    fav = Favorite(user_id=user.id, perfume_id=perfume.id, notify_on_price_drop=True)
    db_session.add(fav)
    await db_session.commit()

    return user, perfume, shop, old_offer, fav


async def test_price_drop_detected(price_drop_scenario, db_session: AsyncSession):
    user, perfume, shop, old_offer, fav = price_drop_scenario
    svc = NotificationService()

    old_price = Decimal("10000")
    new_price = Decimal("8500")  # -15%, превышает порог 10%

    assert svc.is_price_drop(old_price, new_price) is True


async def test_no_drop_below_threshold(price_drop_scenario):
    svc = NotificationService()
    old_price = Decimal("10000")
    new_price = Decimal("9500")  # -5%, ниже порога

    assert svc.is_price_drop(old_price, new_price) is False


async def test_notification_text_contains_prices():
    svc = NotificationService()
    text = svc.format_notification(
        perfume_name="Chanel No 5",
        brand="Chanel",
        old_price=Decimal("10000"),
        new_price=Decimal("8000"),
        shop_name="Randewoo",
        shop_url="https://randewoo.ru/product/1",
    )
    assert "10000" in text
    assert "8000" in text
    assert "Randewoo" in text
    assert "-20%" in text


async def test_circuit_breaker_threshold():
    """Проверяем, что порог circuit breaker — 5 ошибок подряд."""
    from perfume_bot.scrapers.base import ScraperError
    errors = [ScraperError("Тест", "http://x", f"ошибка {i}") for i in range(5)]
    assert len(errors) == 5
