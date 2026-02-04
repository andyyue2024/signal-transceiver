"""
Tests for new functionality: scheduler, cache, validation, compliance.
"""
import pytest
from datetime import datetime, date

# Import test modules
from src.core.scheduler import Scheduler, ScheduledTask, TaskStatus
from src.core.cache import LRUCache, CacheManager, make_cache_key
from src.core.validation import DataValidator, ValidationLevel
from src.core.compliance import TargetCompliance, ComplianceStatus, ComplianceCategory


class TestScheduler:
    """Tests for the scheduler module."""

    def test_scheduler_singleton(self):
        """Test scheduler is a singleton."""
        s1 = Scheduler()
        s2 = Scheduler()
        assert s1 is s2

    def test_add_task(self):
        """Test adding a scheduled task."""
        scheduler = Scheduler()

        # Clear any existing tasks
        scheduler._tasks.clear()

        async def dummy_task():
            pass

        task = scheduler.add_task(
            task_id="test_task",
            name="Test Task",
            func=dummy_task,
            interval_seconds=60
        )

        assert task.id == "test_task"
        assert task.name == "Test Task"
        assert task.interval_seconds == 60
        assert task.enabled is True
        assert task.status == TaskStatus.PENDING

    def test_disable_enable_task(self):
        """Test disabling and enabling tasks."""
        scheduler = Scheduler()
        scheduler._tasks.clear()

        async def dummy_task():
            pass

        scheduler.add_task("test_task", "Test", dummy_task, 60)

        scheduler.disable_task("test_task")
        assert scheduler._tasks["test_task"].enabled is False

        scheduler.enable_task("test_task")
        assert scheduler._tasks["test_task"].enabled is True

    def test_get_status(self):
        """Test getting scheduler status."""
        scheduler = Scheduler()
        scheduler._tasks.clear()

        status = scheduler.get_status()

        assert "running" in status
        assert "task_count" in status
        assert "tasks" in status


class TestCache:
    """Tests for the cache module."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test setting and getting cache values."""
        cache = LRUCache(max_size=100, default_ttl=300)

        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUCache()

        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting cache entries."""
        cache = LRUCache()

        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")

        assert deleted is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3, default_ttl=300)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")  # Should evict key1

        assert await cache.get("key1") is None
        assert await cache.get("key4") == "value4"

    def test_make_cache_key(self):
        """Test cache key generation."""
        key1 = make_cache_key("arg1", "arg2", foo="bar")
        key2 = make_cache_key("arg1", "arg2", foo="bar")
        key3 = make_cache_key("arg1", "arg3", foo="bar")

        assert key1 == key2  # Same args should produce same key
        assert key1 != key3  # Different args should produce different key

    def test_cache_manager_singleton(self):
        """Test cache manager is a singleton."""
        m1 = CacheManager()
        m2 = CacheManager()
        assert m1 is m2


class TestValidation:
    """Tests for the validation module."""

    def test_valid_data(self):
        """Test validation of valid data."""
        validator = DataValidator()

        data = {
            "type": "signal",
            "symbol": "AAPL",
            "execute_date": date.today(),
            "strategy_id": "strategy_001"
        }

        assert validator.is_valid(data) is True

    def test_missing_required_field(self):
        """Test validation fails for missing required field."""
        validator = DataValidator()

        data = {
            "type": "signal",
            "symbol": "AAPL"
            # Missing execute_date and strategy_id
        }

        errors = validator.get_errors(data)
        assert len(errors) > 0

    def test_invalid_type_format(self):
        """Test validation fails for invalid type format."""
        validator = DataValidator()

        data = {
            "type": "123invalid",  # Type should start with a letter
            "symbol": "AAPL",
            "execute_date": date.today(),
            "strategy_id": "strategy_001"
        }

        errors = validator.get_errors(data)
        type_errors = [e for e in errors if e.field == "type"]
        assert len(type_errors) > 0


class TestCompliance:
    """Tests for the compliance module."""

    def test_compliance_check_compliant_data(self):
        """Test compliance check on valid data."""
        compliance = TargetCompliance()

        data = {
            "type": "signal",
            "symbol": "AAPL",
            "execute_date": date.today(),
            "strategy_id": "strategy_001",
            "description": "Test signal"
        }

        results = compliance.check(data)
        assert len(results) > 0

        # Should have mostly compliant results
        compliant = [r for r in results if r.status == ComplianceStatus.COMPLIANT]
        assert len(compliant) > 0

    def test_compliance_check_missing_fields(self):
        """Test compliance check detects missing fields."""
        compliance = TargetCompliance()

        data = {
            "type": "signal"
            # Missing required fields
        }

        results = compliance.check(data, [ComplianceCategory.DATA_QUALITY])
        non_compliant = [r for r in results if r.status == ComplianceStatus.NON_COMPLIANT]

        assert len(non_compliant) > 0

    def test_compliance_is_compliant(self):
        """Test is_compliant method."""
        compliance = TargetCompliance()

        valid_data = {
            "type": "signal",
            "symbol": "AAPL",
            "execute_date": date.today(),
            "strategy_id": "strategy_001"
        }

        invalid_data = {
            "type": "signal"
        }

        # Valid data should be compliant
        assert compliance.is_compliant(valid_data) is True
        # Invalid data should not be compliant
        assert compliance.is_compliant(invalid_data) is False

    def test_compliance_summary(self):
        """Test compliance summary generation."""
        compliance = TargetCompliance()

        data = {
            "type": "signal",
            "symbol": "AAPL",
            "execute_date": date.today(),
            "strategy_id": "strategy_001"
        }

        results = compliance.check(data)
        summary = compliance.get_summary(results)

        assert "total_checks" in summary
        assert "compliant" in summary
        assert "non_compliant" in summary
        assert "compliance_rate" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
