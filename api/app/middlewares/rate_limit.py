import asyncio
import time
from typing import Callable, Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rps: int, burst: int) -> None:
        super().__init__(app)
        self.rps = rps
        self.burst = burst
        self._hits: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        async with self._lock:
            timestamps = self._hits.get(client_ip, [])
            cutoff = now - 1
            timestamps = [t for t in timestamps if t >= cutoff]
            limit = self.burst if self.burst > 0 else self.rps
            if len(timestamps) >= limit:
                request_id = getattr(request.state, "request_id", None)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many requests",
                            "request_id": request_id,
                        }
                    },
                )
            timestamps.append(now)
            self._hits[client_ip] = timestamps
        return await call_next(request)
