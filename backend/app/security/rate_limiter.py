"""
Application-Level Rate Limiter & Concurrency Guard (SIH26117).
Protects the local sovereign machine against excessive external/public traffic
without external cloud SaaS dependencies.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Any
from fastapi import Request, HTTPException, status
from app.config import settings


class SovereignRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter and concurrent task limiter.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._ip_history: Dict[str, List[float]] = defaultdict(list)
        self._active_tasks: Dict[str, int] = defaultdict(int)

    def _get_client_ip(self, request: Request) -> str:
        """Extracts client IP safely, prioritizing Cloudflare connecting IP when available."""
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            ip = cf_ip.strip()
            if ip:
                return ip
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            if ip:
                return ip
        return request.client.host if request.client else "127.0.0.1"

    def check_rate_limit(
        self,
        request_or_ip: Any,
        max_requests: Optional[int] = None,
        window_seconds: float = 60.0,
        raise_exception: bool = True
    ) -> bool:
        """
        Validates request rate against rate limit window.
        Supports FastAPI Request object or raw IP string.
        """
        if isinstance(request_or_ip, str):
            ip = request_or_ip
        else:
            ip = self._get_client_ip(request_or_ip)

        max_rpm = max_requests if max_requests is not None else settings.PUBLIC_MAX_REQUESTS_PER_MINUTE
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Purge timestamps older than sliding window
            self._ip_history[ip] = [t for t in self._ip_history[ip] if t > window_start]

            if len(self._ip_history[ip]) >= max_rpm:
                if raise_exception:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: Maximum {max_rpm} requests per minute. Please wait before retrying.",
                        headers={"Retry-After": "10"}
                    )
                return False

            self._ip_history[ip].append(now)

        return True

    def acquire_task_slot(self, user_id: str) -> bool:
        """
        Enforces maximum concurrent task limit per user or IP.
        Raises HTTP 429 if limit is exceeded.
        """
        max_tasks = settings.PUBLIC_MAX_CONCURRENT_TASKS
        with self._lock:
            current = self._active_tasks[user_id]
            if current >= max_tasks:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many concurrent tasks: Maximum {max_tasks} active tasks allowed per user. Please wait for previous tasks to complete."
                )
            self._active_tasks[user_id] = current + 1
        return True

    def release_task_slot(self, user_id: str) -> None:
        """Releases an active task slot for a user."""
        with self._lock:
            if user_id in self._active_tasks:
                self._active_tasks[user_id] = max(0, self._active_tasks[user_id] - 1)
                if self._active_tasks[user_id] == 0:
                    del self._active_tasks[user_id]

    def reset(self) -> None:
        """Resets all tracking state (used in testing)."""
        with self._lock:
            self._ip_history.clear()
            self._active_tasks.clear()


rate_limiter = SovereignRateLimiter()
