"""
Tests for health check and rate limiter modules.
"""
import pytest
from datetime import datetime

from src.core.health import HealthChecker, HealthStatus, ComponentHealth
from src.core.rate_limiter import RateLimiter, RateLimitConfig


class TestHealthChecker:
    """Tests for HealthChecker."""

    def test_uptime(self):
        """Test uptime calculation."""
        checker = HealthChecker()

        # Uptime should be positive
        assert checker.uptime_seconds >= 0
        assert len(checker.uptime_human) > 0

    def test_check_memory(self):
        """Test memory check."""
        checker = HealthChecker()
        result = checker.check_memory()

        assert result.name == "memory"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.details is not None
        assert "used_percent" in result.details
        assert "available_mb" in result.details

    def test_check_cpu(self):
        """Test CPU check."""
        checker = HealthChecker()
        result = checker.check_cpu()

        assert result.name == "cpu"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.details is not None
        assert "used_percent" in result.details
        assert "cpu_count" in result.details

    def test_check_disk(self):
        """Test disk check."""
        checker = HealthChecker()
        result = checker.check_disk()

        assert result.name == "disk"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

    def test_liveness_probe(self):
        """Test liveness probe."""
        checker = HealthChecker()
        result = checker.get_liveness()

        assert result["status"] == "alive"
        assert "timestamp" in result

    def test_readiness_probe(self):
        """Test readiness probe."""
        checker = HealthChecker()
        result = checker.get_readiness()

        assert result["status"] in ["ready", "not_ready"]
        assert "checks" in result

    def test_register_custom_check(self):
        """Test registering custom health check."""
        checker = HealthChecker()

        def custom_check():
            return ComponentHealth(
                name="custom",
                status=HealthStatus.HEALTHY,
                message="Custom check passed"
            )

        checker.register_check("custom", custom_check)
        assert "custom" in checker._checks


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_basic_rate_limit(self):
        """Test basic rate limiting."""
        limiter = RateLimiter()
        limiter.set_limit("test", RateLimitConfig(requests=5, window_seconds=60))

        # First 5 requests should succeed
        for i in range(5):
            allowed, headers = await limiter.check("user1", "test")
            assert allowed is True
            assert headers["X-RateLimit-Remaining"] == 4 - i

        # 6th request should fail
        allowed, headers = await limiter.check("user1", "test")
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == 0

    @pytest.mark.asyncio
    async def test_different_identifiers(self):
        """Test that different identifiers have separate limits."""
        limiter = RateLimiter()
        limiter.set_limit("test", RateLimitConfig(requests=2, window_seconds=60))

        # User1 uses 2 requests
        await limiter.check("user1", "test")
        await limiter.check("user1", "test")

        # User2 should still have full limit
        allowed, headers = await limiter.check("user2", "test")
        assert allowed is True
        assert headers["X-RateLimit-Remaining"] == 1

    @pytest.mark.asyncio
    async def test_consume_multiple(self):
        """Test consuming multiple tokens."""
        limiter = RateLimiter()
        limiter.set_limit("test", RateLimitConfig(requests=10, window_seconds=60))

        # Consume 5 at once
        allowed, headers = await limiter.consume("user1", "test", cost=5)
        assert allowed is True
        assert headers["X-RateLimit-Remaining"] == 5

        # Try to consume 6 more (should fail)
        allowed, headers = await limiter.consume("user1", "test", cost=6)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test resetting rate limit."""
        limiter = RateLimiter()
        limiter.set_limit("test", RateLimitConfig(requests=2, window_seconds=60))

        # Use up limit
        await limiter.check("user1", "test")
        await limiter.check("user1", "test")

        allowed, _ = await limiter.check("user1", "test")
        assert allowed is False

        # Reset
        limiter.reset("user1", "test")

        # Should be allowed again
        allowed, _ = await limiter.check("user1", "test")
        assert allowed is True

    def test_get_stats(self):
        """Test getting rate limiter stats."""
        limiter = RateLimiter()
        stats = limiter.get_stats()

        assert "active_buckets" in stats
        assert "configured_limits" in stats
        assert "default" in stats["configured_limits"]

    @pytest.mark.asyncio
    async def test_get_usage(self):
        """Test getting usage for an identifier."""
        limiter = RateLimiter()
        limiter.set_limit("test", RateLimitConfig(requests=10, window_seconds=60))

        # Initial usage
        usage = limiter.get_usage("user1", "test")
        assert usage["used"] == 0
        assert usage["remaining"] == 10

        # After some usage
        await limiter.check("user1", "test")
        await limiter.check("user1", "test")

        usage = limiter.get_usage("user1", "test")
        assert usage["used"] == 2
        assert usage["remaining"] == 8

    def test_default_limits(self):
        """Test default rate limits are configured."""
        limiter = RateLimiter()

        assert limiter.get_limit("default") is not None
        assert limiter.get_limit("auth") is not None
        assert limiter.get_limit("data_write") is not None
        assert limiter.get_limit("data_read") is not None
        assert limiter.get_limit("admin") is not None


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_config_key(self):
        """Test rate limit config key generation."""
        config = RateLimitConfig(requests=100, window_seconds=60)
        assert config.key == "100/60s"

        config2 = RateLimitConfig(requests=1000, window_seconds=3600)
        assert config2.key == "1000/3600s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
