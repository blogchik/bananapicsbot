"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.deps.db import init_database, shutdown_database
from app.infrastructure.logging import get_logger, setup_logging
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.request_id import RequestIdMiddleware
from app.schemas.common import InfoResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting application...")

    await init_database()
    logger.info("Database connected")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    await shutdown_database()
    logger.info("Database disconnected")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Setup logging first
    setup_logging()

    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.cors_origins_list],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Middlewares
    app.add_middleware(RequestIdMiddleware)

    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            rps=settings.rate_limit_rps,
            burst=settings.rate_limit_burst,
        )

    # Exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Root endpoint
    @app.get("/", response_model=InfoResponse)
    async def root_info() -> InfoResponse:
        return InfoResponse(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )

    # Include API routers
    app.include_router(v1_router, prefix=settings.api_prefix)

    return app


app = create_app()
