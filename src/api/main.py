"""FastAPI application main entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html

from ..infrastructure.config import get_config
from ..infrastructure.persistence.database import create_tables, init_database
from .middleware.error_handler import register_exception_handlers
from .routes import health_router, projects_router, tasks_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup and shutdown)."""
    # Startup
    logger.info("Initializing database...")
    init_database()
    create_tables()
    logger.info("Database initialized successfully")
    logger.info(f"Application started - {config.API_TITLE} v{config.API_VERSION}")

    yield

    # Shutdown
    logger.info("Application shutting down...")


# Create FastAPI application with lifespan
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    docs_url="/docs",
    redoc_url=None,  # Disable default ReDoc (using custom endpoint below)
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(projects_router)


@app.get("/", include_in_schema=False)
def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "Task Management API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation with working CDN URL."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{config.API_TITLE} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )
