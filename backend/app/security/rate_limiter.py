import time
import threading
from typing import Dict, List
from fastapi import HTTPException
from app.config import settings

class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter for authenticated AI requests.
    Tracks timestamps per user_id and enforces per-minute and per-day limits.
    """
    def __init__(self):
        self._lock = threading.Lock()
        # user_id -> list of float timestamps
        self._user_requests: Dict[str, List[float]] = {}

    def check_rate_limit(self, user_id: str, endpoint: str = "chat") -> None:
        """
        Validates whether the user is within rate limits.
        Raises HTTPException(429) if exceeded.
        """
        if not user_id or user_id in ("guest_user", "anonymous"):
            # Guests use strict fallback limit
            max_per_minute = min(settings.CHAT_RATE_LIMIT_PER_MINUTE, 5)
            max_per_day = min(settings.CHAT_DAILY_LIMIT, 20)
        else:
            max_per_minute = settings.CHAT_RATE_LIMIT_PER_MINUTE
            max_per_day = settings.CHAT_DAILY_LIMIT

        now = time.time()
        one_minute_ago = now - 60.0
        one_day_ago = now - 86400.0

        with self._lock:
            timestamps = self._user_requests.get(user_id, [])
            
            # Prune timestamps older than 24 hours
            recent_timestamps = [t for t in timestamps if t > one_day_ago]
            
            # Check 1-minute window
            last_minute_requests = [t for t in recent_timestamps if t > one_minute_ago]
            if len(last_minute_requests) >= max_per_minute:
                retry_after = int(60.0 - (now - last_minute_requests[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"تم تجاوز الحد المسموح للطلبات بالدقيقة ({max_per_minute} طلب/دقيقة). يرجى المحاولة بعد {retry_after} ثانية.",
                    headers={"Retry-After": str(max(1, retry_after))}
                )
            
            # Check 24-hour window
            if len(recent_timestamps) >= max_per_day:
                raise HTTPException(
                    status_code=429,
                    detail=f"تم استهلاك الحد اليومي المسموح للأسئلة الذكية ({max_per_day} طلب/يوم). يرجى المحاولة غداً.",
                    headers={"Retry-After": "3600"}
                )
            
            # Record this request
            recent_timestamps.append(now)
            self._user_requests[user_id] = recent_timestamps

    def clear(self):
        """Clears all in-memory rate limit logs (used in unit tests)."""
        with self._lock:
            self._user_requests.clear()

# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()

def check_user_rate_limit(user_id: str, endpoint: str = "chat"):
    """Convenience function to check rate limit for a user."""
    rate_limiter.check_rate_limit(user_id, endpoint=endpoint)
