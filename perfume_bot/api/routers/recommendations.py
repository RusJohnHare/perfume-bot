from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.core.database import get_db
from perfume_bot.services.recommendation import RecommendationService

router = APIRouter()


@router.get("/")
async def get_recommendations(note_ids: str, db: AsyncSession = Depends(get_db)):
    ids = [int(i) for i in note_ids.split(",") if i.strip().isdigit()]
    service = RecommendationService(db)
    results = await service.get_recommendations(ids)
    return [
        {
            "id": r.perfume.id,
            "name": r.perfume.name,
            "brand": r.perfume.brand,
            "score": round(r.score, 3),
            "is_exact": r.is_exact,
        }
        for r in results
    ]
