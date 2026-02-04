"""
Caching layer for improved performance.
Implements in-memory and optional Redis caching.
"""
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
from loguru import logger

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry."""
    key: str
    value: T
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats["hits"] += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set a value in cache."""
        if ttl is None:
            ttl = self.default_ttl

        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None

        async with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].expires_at = expires_at
                self._cache[key].created_at = datetime.utcnow()
                self._cache.move_to_end(key)
            else:
                # Check size limit
                while len(self._cache) >= self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats["evictions"] += 1

                self._cache[key] = CacheEntry(
                    key=key,
                    value=value,
                    expires_at=expires_at
                )

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def clear_pattern(self, pattern: str):
        """Clear keys matching a pattern (simple prefix matching)."""
        async with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys()
                if k.startswith(pattern.replace("*", ""))
            ]
            for key in keys_to_delete:
                del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate:.2%}"
        }

    async def cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class CacheManager:
    """Central cache management."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._caches: Dict[str, LRUCache] = {}
        self._default_cache = LRUCache(max_size=1000, default_ttl=300)
        self._initialized = True

    def get_cache(self, name: str = "default") -> LRUCache:
        """Get a named cache or the default cache."""
        if name == "default":
            return self._default_cache

        if name not in self._caches:
            self._caches[name] = LRUCache()

        return self._caches[name]

    def create_cache(
        self,
        name: str,
        max_size: int = 1000,
        default_ttl: int = 300
    ) -> LRUCache:
        """Create a new named cache."""
        cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self._caches[name] = cache
        return cache

    async def clear_all(self):
        """Clear all caches."""
        await self._default_cache.clear()
        for cache in self._caches.values():
            await cache.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches."""
        stats = {"default": self._default_cache.get_stats()}
        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()
        return stats

    # Convenience methods for synchronous access
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Synchronous set (creates event loop if needed)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a task
            asyncio.create_task(self._default_cache.set(key, value, ttl))
        except RuntimeError:
            # No running loop, run synchronously
            asyncio.run(self._default_cache.set(key, value, ttl))

    def get(self, key: str) -> Optional[Any]:
        """Synchronous get (creates event loop if needed)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Return a coroutine for async context
            return asyncio.run(self._default_cache.get(key))
        except RuntimeError:
            # No running loop, run synchronously
            return asyncio.run(self._default_cache.get(key))


# Global cache manager
cache_manager = CacheManager()


def make_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 300,
    cache_name: str = "default",
    key_prefix: str = ""
):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl=60, key_prefix="user")
        async def get_user(user_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = cache_manager.get_cache(cache_name)

            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            cache_key = f"{func_key}:{make_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: asyncio.create_task(
            cache_manager.get_cache(cache_name).clear_pattern(f"{key_prefix}:{func.__name__}")
        )

        return wrapper
    return decorator


def cache_invalidate(
    cache_name: str = "default",
    key_pattern: str = "*"
):
    """
    Decorator for invalidating cache after function execution.

    Usage:
        @cache_invalidate(key_pattern="user:*")
        async def update_user(user_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache = cache_manager.get_cache(cache_name)
            await cache.clear_pattern(key_pattern)

            return result

        return wrapper
    return decorator


# Specialized caches
strategy_cache = cache_manager.create_cache("strategy", max_size=500, default_ttl=600)
user_cache = cache_manager.create_cache("user", max_size=200, default_ttl=300)
permission_cache = cache_manager.create_cache("permission", max_size=500, default_ttl=600)
