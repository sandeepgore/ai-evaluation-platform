import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.router import api_router
from app.config.settings import settings
from app.db.session import AsyncSessionLocal
from app.services.evaluation.scheduler import EvaluationScheduler
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    queue = EvaluationQueue(
        redis=redis,
        stream=settings.evaluation_queue_stream,
        group=settings.evaluation_queue_group,
    )

    scheduler = EvaluationScheduler(
        queue=queue,
    )

    scheduler_task = asyncio.create_task(
        scheduler.run_forever(),
    )

    app.state.scheduler = scheduler
    app.state.scheduler_task = scheduler_task
    app.state.scheduler_redis = redis

    try:
        yield

    finally:
        scheduler.request_shutdown()

        try:
            await scheduler_task
        except Exception:
            # Scheduler failures should not prevent application shutdown.
            pass

        await redis.aclose()


app = FastAPI(
    title=settings.app_name,
    description="Enterprise platform for evaluating and benchmarking AI systems.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


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
        "healthy" if database_status == "connected" and redis_status == "connected" else "degraded"
    )

    return {
        "status": overall_status,
        "version": settings.app_version,
        "database": database_status,
        "redis": redis_status,
    }
