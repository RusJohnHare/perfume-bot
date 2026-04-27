import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.core.database import get_db
from perfume_bot.services.favorites import FavoritesService

router = APIRouter()


@router.get("/{user_id}")
async def list_favorites(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = FavoritesService(db)
    favorites = await service.list_for_user(user_id)
    return [
        {
            "id": str(f.id),
            "perfume_id": f.perfume_id,
            "notify_on_price_drop": f.notify_on_price_drop,
            "added_at": f.added_at.isoformat(),
        }
        for f in favorites
    ]


@router.post("/{user_id}/{perfume_id}")
async def add_favorite(user_id: uuid.UUID, perfume_id: int, db: AsyncSession = Depends(get_db)):
    service = FavoritesService(db)
    fav = await service.add(user_id, perfume_id)
    return {"id": str(fav.id), "perfume_id": fav.perfume_id}


@router.delete("/{favorite_id}")
async def remove_favorite(favorite_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = FavoritesService(db)
    await service.remove(favorite_id)
    return {"status": "deleted"}
