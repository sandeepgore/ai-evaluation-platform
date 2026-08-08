from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy import text

from app.config.settings import settings
from app.db.session import AsyncSessionLocal


app = FastAPI(
    title=settings.app_name,
    description="Enterprise platform for evaluating and benchmarking AI systems.",
    version=settings.app_version,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    database_status = "unavailable"
    redis_status = "unavailable"

    # Check PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            database_status = "connected"
    except Exception:
        database_status = "unavailable"

    # Check Redis
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        await redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unavailable"
    finally:
        await redis.aclose()

    overall_status = (
        "healthy"
        if database_status == "connected"
        and redis_status == "connected"
        else "degraded"
    )

    return {
        "status": overall_status,
        "version": settings.app_version,
        "database": database_status,
        "redis": redis_status,
    }