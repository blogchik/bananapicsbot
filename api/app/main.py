from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.api.v1.api import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.middlewares.request_id import RequestIdMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.schemas.common import InfoResponse


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(title=settings.app_name, version=settings.app_version)

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.cors_origins_list],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(RequestIdMiddleware)

    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            rps=settings.rate_limit_rps,
            burst=settings.rate_limit_burst,
        )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/", response_model=InfoResponse)
    async def root_info() -> InfoResponse:
        return InfoResponse(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )

    app.include_router(v1_router, prefix=settings.api_prefix)

    return app


app = create_app()
