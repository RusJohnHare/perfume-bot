import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.models import User, Perfume, FragranceCategory, Favorite
from perfume_bot.services.favorites import FavoritesService


@pytest.fixture
async def user_and_perfume(db_session: AsyncSession):
    user = User(tg_user_id=123456789)
    cat = FragranceCategory(name="Фикстурная")
    db_session.add_all([user, cat])
    await db_session.flush()

    perfume = Perfume(name="ТестПарфюм", brand="ТестБренд")
    db_session.add(perfume)
    await db_session.commit()
    return user, perfume


async def test_add_to_favorites(user_and_perfume, db_session: AsyncSession):
    user, perfume = user_and_perfume
    service = FavoritesService(db_session)
    fav = await service.add(user.id, perfume.id)
    assert fav.user_id == user.id
    assert fav.perfume_id == perfume.id
    assert fav.notify_on_price_drop is True


async def test_deduplication(user_and_perfume, db_session: AsyncSession):
    user, perfume = user_and_perfume
    service = FavoritesService(db_session)
    fav1 = await service.add(user.id, perfume.id)
    fav2 = await service.add(user.id, perfume.id)
    assert fav1.id == fav2.id


async def test_remove_from_favorites(user_and_perfume, db_session: AsyncSession):
    user, perfume = user_and_perfume
    service = FavoritesService(db_session)
    fav = await service.add(user.id, perfume.id)
    await service.remove(fav.id)
    result = await service.list_for_user(user.id)
    assert all(f.id != fav.id for f in result)


async def test_toggle_notifications(user_and_perfume, db_session: AsyncSession):
    user, perfume = user_and_perfume
    service = FavoritesService(db_session)
    fav = await service.add(user.id, perfume.id)
    assert fav.notify_on_price_drop is True
    updated = await service.toggle_notify(fav.id)
    assert updated.notify_on_price_drop is False
    restored = await service.toggle_notify(fav.id)
    assert restored.notify_on_price_drop is True
