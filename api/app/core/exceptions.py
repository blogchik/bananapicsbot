from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(
    request: Request,
    status_code: int,
    message: str,
    code: str,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=status_code, content=payload)


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error_response(request, exc.status_code, exc.detail, "http_error")


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(request, 422, "Validation error", "validation_error")


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(request, 500, "Internal server error", "internal_error")
