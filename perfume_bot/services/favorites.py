import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from perfume_bot.models.favorite import Favorite


class FavoritesService:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: uuid.UUID, perfume_id: int) -> Favorite:
        result = await self._session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.perfume_id == perfume_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        fav = Favorite(user_id=user_id, perfume_id=perfume_id)
        self._session.add(fav)
        await self._session.commit()
        return fav

    async def remove(self, favorite_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(Favorite).where(Favorite.id == favorite_id)
        )
        fav = result.scalar_one_or_none()
        if fav:
            await self._session.delete(fav)
            await self._session.commit()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Favorite]:
        result = await self._session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.added_at.desc())
        )
        return list(result.scalars().all())

    async def toggle_notify(self, favorite_id: uuid.UUID) -> Favorite:
        result = await self._session.execute(
            select(Favorite).where(Favorite.id == favorite_id)
        )
        fav = result.scalar_one()
        fav.notify_on_price_drop = not fav.notify_on_price_drop
        await self._session.commit()
        return fav
