"""
Redis connection pool and utility functions.
"""
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

_redis_pool: Redis | None = None


async def get_redis() -> Redis:
    """Get or create the Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


async def set_with_expiry(key: str, value: str, ttl_seconds: int = 3600) -> None:
    r = await get_redis()
    await r.setex(key, ttl_seconds, value)


async def get_value(key: str) -> str | None:
    r = await get_redis()
    return await r.get(key)


async def delete_key(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def publish_progress(channel: str, message: str) -> None:
    """Publish a solver progress message to a Redis pub/sub channel."""
    try:
        r = await get_redis()
        await r.publish(channel, message)
    except Exception:
        pass
