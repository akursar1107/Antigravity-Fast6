"""FastAPI Application Entry Point - Main Server"""
import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so that both `from backend.X` and bare
# `from backend.database.X` / `from backend.utils.X` imports resolve correctly.
_SRC_DIR = str(Path(__file__).resolve().parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.fastapi_config import settings
from backend.api.rate_limit import limiter
from backend.database.connection import set_db_path
from backend.config import DATABASE_PATH as CONFIG_DATABASE_PATH
from backend.api.routers.fastapi_auth import router as auth_router
from backend.api.routers.fastapi_users import router as users_router
from backend.api.routers.fastapi_picks import router as picks_router
from backend.api.routers.fastapi_results import router as results_router
from backend.api.routers.fastapi_weeks import router as weeks_router
from backend.api.routers.fastapi_leaderboard import router as leaderboard_router
from backend.api.routers.fastapi_analytics import router as analytics_router
from backend.api.routers.fastapi_admin import router as admin_router
from backend.api.routers.fastapi_games import router as games_router
from backend.api.routers.fastapi_rosters import router as rosters_router
from backend.database.migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown"""
    
    # Startup
    logger.info("FastAPI application starting...")

    try:
        # Use env DATABASE_PATH as source of truth for API (see docs/guides/CONFIG_GUIDE.md)
        set_db_path(Path(settings.database_path))
        if str(CONFIG_DATABASE_PATH) != str(settings.database_path):
            logger.warning(
                "Config mismatch: config.json database_path (%s) differs from env DATABASE_PATH (%s). "
                "API uses env value.",
                CONFIG_DATABASE_PATH, settings.database_path
            )
        logger.info("Running database migrations...")
        run_migrations()
        logger.info("Migrations completed")
        
        logger.info("FastAPI application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("FastAPI application shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Fast6 API",
    description="REST API for NFL First Touchdown Scorer Predictions",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers under /api/v1 for versioning (future: /api/v2 for breaking changes)
API_V1_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(picks_router, prefix=API_V1_PREFIX)
app.include_router(results_router, prefix=API_V1_PREFIX)
app.include_router(weeks_router, prefix=API_V1_PREFIX)
app.include_router(leaderboard_router, prefix=API_V1_PREFIX)
app.include_router(analytics_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(games_router, prefix=API_V1_PREFIX)
app.include_router(rosters_router, prefix=API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for monitoring"""
    result = {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }
    try:
        from backend.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT target, season, last_sync_at, status FROM sync_metadata")
        rows = cursor.fetchall()
        conn.close()
        result["sync"] = [{"target": r[0], "season": r[1], "last_sync_at": r[2], "status": r[3]} for r in rows]
    except Exception:
        pass
    return result


# Root endpoint with documentation links
@app.get("/")
async def root() -> dict:
    """API root endpoint with documentation links"""
    return {
        "message": "Fast6 API v1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions. Never expose internal details in production."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.fastapi_app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
