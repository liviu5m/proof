import asyncio
from collections import defaultdict, deque
import time

from fastapi import HTTPException, Request, status, Depends
from redis.asyncio import Redis
from src.config import settings
from src.models import Users
from src.utils import get_current_user
from typing import Deque, Dict, Optional, Tuple

_redis: Optional[Redis] = None

def _get_redis() -> Optional[Redis]:
    global _redis
    if _redis is None:
        try:
            _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            _redis = None
    return _redis

_request_logs: Dict[str, Deque[float]] = defaultdict(deque)
_active_runs: Dict[int, int] = defaultdict(int)
_lock = asyncio.Lock()

class _SlidingWindow:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit          
        self.window = window_seconds 

    async def check(self, key: str) -> Tuple[bool, Optional[int]]:
        r = _get_redis()
        now = time.time()
        if r is not None:
            try:
                pipe = r.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window)
                results = await pipe.execute()
                count = results[0]

                if count == 1:
                    await r.expire(key, self.window)

                if count > self.limit:
                    ttl = await r.ttl(key)
                    return False, max(int(ttl), 1)

                return True, None
            except Exception:
                pass

_limiter_runs = _SlidingWindow(settings.RATE_LIMIT_RUNS_PER_MIN, 60)
_limiter_datasets = _SlidingWindow(settings.RATE_LIMIT_DATASETS_PER_MIN, 60)

def _client_ip(request: Request) -> str:
    client = request.client
    return client.host if client and client.host else "unknown"

async def _raise_rate_limited(retry_after: Optional[int], message: str) -> None:
    headers = {"Retry-After": str(retry_after)} if retry_after else None
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={"error": message, "code": "rate_limited", "retry_after": retry_after},
        headers=headers,
    )

async def rate_limit_runs(request: Request, user=Depends(get_current_user)) -> None:
    key = f"user:{user.id}" if user else f"ip:{_client_ip(request)}"
    allowed, retry_after = await _limiter_runs.check(f"rate_limit:runs:{key}")
    if not allowed:
        await _raise_rate_limited(retry_after, "Too many requests to /api/runs")


async def rate_limit_datasets(request: Request, user=Depends(get_current_user)) -> None:
    key = f"user:{user.id}" if user else f"ip:{_client_ip(request)}"
    allowed, retry_after = await _limiter_runs.check(f"rate_limit:datasets:{key}")
    if not allowed:
        await _raise_rate_limited(retry_after, "Too many requests to /api/datasets")

async def check_concurrent_run(user_id: int) -> None:
    r = _get_redis()
    key = f"concurrent_runs:user:{user_id}"
    if r is not None:
        try:
            count = await r.incr(key)
            await r.expire(key, 3600)
            if count > settings.MAX_CONCURRENT_RUNS:
                await r.decr(key)
                await _raise_rate_limited(
                    60,
                    f"Concurrent run limit ({settings.MAX_CONCURRENT_RUNS}) reached",
                )
            return
        except Exception:
            pass

    async with _lock:
        if _active_runs.get(user_id, 0) >= settings.MAX_CONCURRENT_RUNS:
            await _raise_rate_limited(
                60,
                f"Concurrent run limit ({settings.MAX_CONCURRENT_RUNS}) reached",
            )
        _active_runs[user_id] = _active_runs.get(user_id, 0) + 1


async def release_concurrent_run(user_id: int) -> None:
    r = _get_redis()
    key = f"concurrent_runs:user:{user_id}"
    if r is not None:
        try:
            await r.decr(key)
            return
        except Exception:
            pass
    async with _lock:
        if _active_runs.get(user_id, 0) > 0:
            _active_runs[user_id] -= 1
