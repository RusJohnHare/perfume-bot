from redis.asyncio import Redis
from collections.abc import AsyncGenerator

from perfume_bot.core.config import settings

_redis: Redis | None = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    yield _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
