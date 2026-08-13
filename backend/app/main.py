"""
School Scheduler FastAPI Application Entry Point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    announcements,
    assignments,
    audit,
    auth,
    availability,
    backups,
    classes,
    classrooms,
    courses,
    duties,
    exports,
    imports,
    reports,
    schools,
    settings as settings_api,
    teachers,
    timetables,
    timeslots,
    scheduler as scheduler_api,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis, get_redis

configure_logging(log_level=settings.log_level, log_format=settings.log_format)
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 School Scheduler Application Starting...", version=settings.app_version)
    from app.core.database import engine, Base, is_sqlite, AsyncSessionLocal
    import app.models  # noqa: F401
    from sqlalchemy import select

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Automatic SQLite schema sync for added columns
    if is_sqlite:
        try:
            from scripts.migrate_sqlite import apply_sqlite_migrations
            import os
            db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            if os.path.exists(db_path):
                apply_sqlite_migrations(db_path)
        except Exception as e:
            logger.warning(f"SQLite schema migration check error: {e}")

    # 2. Automatic Seed Data if database has no school
    try:
        from app.models.school import School
        async with AsyncSessionLocal() as session:
            school_exists = (await session.execute(select(School))).scalars().first()
            if not school_exists:
                logger.info("No school found in DB. Executing automatic seed_data()...")
                from scripts.seed import seed_data
                await seed_data()
    except Exception as e:
        logger.warning(f"Auto-seed check error: {e}")

    try:
        await get_redis()
    except Exception:
        logger.warning("Redis not available, falling back to local processing mode.")
    yield
    logger.info("👋 Shutting down application...")
    try:
        await close_redis()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready School Timetable & Scheduling System API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(schools.router, prefix="/api")
app.include_router(teachers.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(classes.router, prefix="/api")
app.include_router(classrooms.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(availability.router, prefix="/api")
app.include_router(timeslots.router, prefix="/api")
app.include_router(timetables.router, prefix="/api")
app.include_router(duties.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(backups.router, prefix="/api")
app.include_router(announcements.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")
app.include_router(scheduler_api.router, prefix="/api")



@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Sunucu tarafında beklenmeyen bir hata oluştu."},
    )
