"""
Rate limiter module for API throttling.
Provides flexible rate limiting configuration.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst: Optional[int] = None  # Allow burst up to this amount

    @property
    def key(self) -> str:
        return f"{self.requests}/{self.window_seconds}s"


@dataclass
class RateLimitState:
    """State for a rate limit bucket."""
    count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)

    def reset(self):
        self.count = 0
        self.window_start = datetime.utcnow()


class RateLimiter:
    """
    Token bucket rate limiter.
    Supports multiple rate limit tiers and custom keys.
    """

    def __init__(self):
        self._buckets: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._configs: Dict[str, RateLimitConfig] = {}
        self._lock = asyncio.Lock()

        # Default rate limits
        self.set_limit("default", RateLimitConfig(requests=100, window_seconds=60))
        self.set_limit("auth", RateLimitConfig(requests=10, window_seconds=60))
        self.set_limit("data_write", RateLimitConfig(requests=50, window_seconds=60))
        self.set_limit("data_read", RateLimitConfig(requests=200, window_seconds=60))
        self.set_limit("admin", RateLimitConfig(requests=30, window_seconds=60))
        self.set_limit("webhook", RateLimitConfig(requests=1000, window_seconds=60))

    def set_limit(self, name: str, config: RateLimitConfig):
        """Set a rate limit configuration."""
        self._configs[name] = config

    def get_limit(self, name: str) -> Optional[RateLimitConfig]:
        """Get a rate limit configuration."""
        return self._configs.get(name)

    def _get_bucket_key(self, identifier: str, limit_name: str) -> str:
        """Generate a unique bucket key."""
        return f"{limit_name}:{identifier}"

    async def check(
        self,
        identifier: str,
        limit_name: str = "default"
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (e.g., API key, IP address)
            limit_name: Name of the rate limit to apply

        Returns:
            Tuple of (allowed: bool, headers: dict with rate limit info)
        """
        config = self._configs.get(limit_name, self._configs["default"])
        bucket_key = self._get_bucket_key(identifier, limit_name)

        async with self._lock:
            bucket = self._buckets[bucket_key]
            now = datetime.utcnow()

            # Check if window has expired
            window_end = bucket.window_start + timedelta(seconds=config.window_seconds)
            if now > window_end:
                bucket.reset()

            # Check if request is allowed
            remaining = config.requests - bucket.count
            allowed = remaining > 0

            if allowed:
                bucket.count += 1
                remaining -= 1

            # Calculate reset time
            reset_time = bucket.window_start + timedelta(seconds=config.window_seconds)
            reset_seconds = max(0, int((reset_time - now).total_seconds()))

            headers = {
                "X-RateLimit-Limit": config.requests,
                "X-RateLimit-Remaining": max(0, remaining),
                "X-RateLimit-Reset": reset_seconds,
                "X-RateLimit-Policy": config.key
            }

            return allowed, headers

    async def consume(
        self,
        identifier: str,
        limit_name: str = "default",
        cost: int = 1
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Consume tokens from the rate limit bucket.

        Args:
            identifier: Unique identifier
            limit_name: Name of the rate limit
            cost: Number of tokens to consume

        Returns:
            Tuple of (allowed, headers)
        """
        config = self._configs.get(limit_name, self._configs["default"])
        bucket_key = self._get_bucket_key(identifier, limit_name)

        async with self._lock:
            bucket = self._buckets[bucket_key]
            now = datetime.utcnow()

            window_end = bucket.window_start + timedelta(seconds=config.window_seconds)
            if now > window_end:
                bucket.reset()

            remaining = config.requests - bucket.count
            allowed = remaining >= cost

            if allowed:
                bucket.count += cost
                remaining -= cost

            reset_time = bucket.window_start + timedelta(seconds=config.window_seconds)
            reset_seconds = max(0, int((reset_time - now).total_seconds()))

            headers = {
                "X-RateLimit-Limit": config.requests,
                "X-RateLimit-Remaining": max(0, remaining),
                "X-RateLimit-Reset": reset_seconds
            }

            return allowed, headers

    def reset(self, identifier: str, limit_name: str = "default"):
        """Reset rate limit for an identifier."""
        bucket_key = self._get_bucket_key(identifier, limit_name)
        if bucket_key in self._buckets:
            self._buckets[bucket_key].reset()

    def reset_all(self):
        """Reset all rate limit buckets."""
        self._buckets.clear()

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        return {
            "active_buckets": len(self._buckets),
            "configured_limits": {
                name: {"requests": c.requests, "window": c.window_seconds}
                for name, c in self._configs.items()
            }
        }

    def get_usage(self, identifier: str, limit_name: str = "default") -> Dict[str, any]:
        """Get current usage for an identifier."""
        config = self._configs.get(limit_name, self._configs["default"])
        bucket_key = self._get_bucket_key(identifier, limit_name)
        bucket = self._buckets.get(bucket_key)

        if not bucket:
            return {
                "used": 0,
                "remaining": config.requests,
                "limit": config.requests,
                "window_seconds": config.window_seconds
            }

        now = datetime.utcnow()
        window_end = bucket.window_start + timedelta(seconds=config.window_seconds)

        if now > window_end:
            return {
                "used": 0,
                "remaining": config.requests,
                "limit": config.requests,
                "window_seconds": config.window_seconds
            }

        return {
            "used": bucket.count,
            "remaining": max(0, config.requests - bucket.count),
            "limit": config.requests,
            "window_seconds": config.window_seconds,
            "resets_in": max(0, int((window_end - now).total_seconds()))
        }


# Global rate limiter instance
rate_limiter = RateLimiter()
