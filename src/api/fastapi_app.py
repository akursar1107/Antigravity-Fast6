"""FastAPI Application Entry Point - Main Server"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.fastapi_config import settings
from src.api.routers.fastapi_auth import router as auth_router
from src.api.routers.fastapi_users import router as users_router
from src.api.routers.fastapi_picks import router as picks_router
from src.api.routers.fastapi_results import router as results_router
from src.api.routers.fastapi_weeks import router as weeks_router
from src.api.routers.fastapi_leaderboard import router as leaderboard_router
from src.api.routers.fastapi_analytics import router as analytics_router
from src.api.routers.fastapi_admin import router as admin_router
from src.database.migrations import run_migrations
from src.services.data_sync.roster_ingestion import sync_rosters
from src.services.data_sync.game_sync import sync_games_for_season

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
        # Run database migrations
        logger.info("Running database migrations...")
        run_migrations()
        logger.info("Migrations completed")
        
        # Sync roster data
        logger.info(f"Syncing roster data for season {settings.current_season}...")
        sync_rosters(settings.current_season)
        logger.info("Roster sync completed")
        
        # Sync game data
        logger.info(f"Syncing games for season {settings.current_season}...")
        sync_games_for_season(settings.current_season)
        logger.info("Game sync completed")
        
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(picks_router)
app.include_router(results_router)
app.include_router(weeks_router)
app.include_router(leaderboard_router)
app.include_router(analytics_router)
app.include_router(admin_router)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


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
    """Handle unhandled exceptions"""
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
        "src.api.fastapi_app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
