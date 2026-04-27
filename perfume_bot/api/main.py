from fastapi import FastAPI

from perfume_bot.api.routers import recommendations, favorites, prices

app = FastAPI(title="Perfume Bot API", version="0.1.0")

app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
app.include_router(prices.router, prefix="/prices", tags=["prices"])


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
