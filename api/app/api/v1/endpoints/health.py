import time

from fastapi import APIRouter, Request

router = APIRouter()

START_TIME = time.monotonic()


@router.get("/health")
async def healthcheck(request: Request) -> dict:
    uptime_seconds = time.monotonic() - START_TIME
    request_id = getattr(request.state, "request_id", None)
    return {
        "status": "ok",
        "uptime_seconds": round(uptime_seconds, 3),
        "request_id": request_id,
    }
