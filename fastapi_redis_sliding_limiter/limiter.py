"""
fastapi-redis-sliding-limiter: Distributed sliding window rate limiter decorator for FastAPI.
Accurate, distributed across multiple worker pods, with in-memory fallback.
"""

import functools
import inspect
import time
from typing import Callable, Optional
from fastapi import HTTPException, Request, Response, status

class SlidingWindowLimiter:
    """Sliding window rate limiter using Redis sorted sets or local memory."""
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_store = {}

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        now = time.time()
        clear_before = now - window_seconds

        # Redis-backed distributed rate limiting (using Sorted Set ZSET)
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds + 5)
            results = await pipe.execute()

            current_count = results[1]
            if current_count >= max_requests:
                # Remove the timestamp we just added since it's rejected
                await self.redis.zrem(key, str(now))
                retry_after = int(window_seconds)
                return False, max_requests - current_count, retry_after

            remaining = max(0, max_requests - current_count - 1)
            return True, remaining, 0

        # In-memory fallback
        if key not in self._memory_store:
            self._memory_store[key] = []

        timestamps = [t for t in self._memory_store[key] if t > clear_before]
        self._memory_store[key] = timestamps

        if len(timestamps) >= max_requests:
            retry_after = int(window_seconds - (now - timestamps[0])) if timestamps else window_seconds
            return False, 0, max(1, retry_after)

        self._memory_store[key].append(now)
        remaining = max_requests - len(self._memory_store[key])
        return True, remaining, 0

_GLOBAL_LIMITER = SlidingWindowLimiter()

def init_limiter(redis_client=None):
    """Initialize the global rate limiter with an optional async redis client."""
    global _GLOBAL_LIMITER
    _GLOBAL_LIMITER = SlidingWindowLimiter(redis_client=redis_client)

def rate_limit(
    requests: int,
    window_seconds: int,
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    Decorator to apply sliding-window rate limiting to a FastAPI endpoint.

    Usage:
        @app.get("/items")
        @rate_limit(requests=5, window_seconds=60)
        async def get_items(request: Request):
            return {"items": []}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break

            if not request:
                raise RuntimeError("Endpoint with @rate_limit decorator must have a 'request: Request' parameter.")

            # Identify client by IP or custom key
            if key_func:
                client_id = key_func(request)
            else:
                client_ip = request.client.host if request.client else "unknown"
                client_id = f"ratelimit:{request.url.path}:{client_ip}"

            allowed, remaining, retry_after = await _GLOBAL_LIMITER.is_allowed(
                key=client_id,
                max_requests=requests,
                window_seconds=window_seconds
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests. Please try again later.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(requests),
                        "X-RateLimit-Remaining": "0"
                    }
                )

            # Call handler
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Attach headers if Response
            if isinstance(result, Response):
                result.headers["X-RateLimit-Limit"] = str(requests)
                result.headers["X-RateLimit-Remaining"] = str(remaining)

            return result

        return wrapper
    return decorator
