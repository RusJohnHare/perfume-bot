from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.core.database import get_db
from perfume_bot.models.shop import ShopOffer, Shop

router = APIRouter()


@router.get("/{perfume_id}")
async def get_prices(perfume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ShopOffer, Shop)
        .join(Shop, ShopOffer.shop_id == Shop.id)
        .where(ShopOffer.perfume_id == perfume_id)
        .order_by(ShopOffer.checked_at.desc())
        .limit(20)
    )
    rows = result.all()
    seen: set[int] = set()
    latest = []
    for offer, shop in rows:
        if offer.shop_id not in seen:
            latest.append({
                "shop": shop.name,
                "price_rub": float(offer.price_rub) if offer.price_rub else None,
                "in_stock": offer.in_stock,
                "url": offer.url,
                "checked_at": offer.checked_at.isoformat(),
            })
            seen.add(offer.shop_id)
    return latest
