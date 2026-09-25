import asyncio
import time
from typing import Callable, Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.deps.telegram_auth import validate_internal_api_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rps: int, burst: int) -> None:
        super().__init__(app)
        self.rps = rps
        self.burst = burst
        self._hits: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _is_internal_request(request: Request) -> bool:
        """Bot traffic for all users comes from one IP, so it is not limited per IP."""
        api_key = request.headers.get("X-Internal-Api-Key")
        if not api_key:
            return False
        bot_token = get_settings().bot_token
        return bool(bot_token) and validate_internal_api_key(api_key, bot_token)

    async def dispatch(self, request: Request, call_next: Callable):
        if self._is_internal_request(request):
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        async with self._lock:
            if len(self._hits) > 10000:
                # Drop IPs with no hits in the current window to bound memory
                self._hits = {ip: ts for ip, ts in self._hits.items() if ts and ts[-1] >= now - 1}
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
