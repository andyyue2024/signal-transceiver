"""
Tests for config manager and log search services.
"""
import pytest
from datetime import datetime, timedelta

from src.core.config_manager import ConfigManager, ConfigType
from src.services.log_search_service import LogSearchService, LogLevel, LogSearchQuery


class TestConfigManager:
    """Tests for ConfigManager."""

    @pytest.fixture
    def manager(self):
        mgr = ConfigManager.__new__(ConfigManager)
        mgr._configs = {}
        mgr._initialized = True
        mgr._init_defaults()
        return mgr

    def test_get_default_config(self, manager):
        """Test getting default configuration."""
        value = manager.get("app.name")
        assert value == "Signal Transceiver"

        value = manager.get("app.debug")
        assert value is False

    def test_get_nonexistent_config(self, manager):
        """Test getting non-existent configuration."""
        value = manager.get("nonexistent.key")
        assert value is None

        value = manager.get("nonexistent.key", "default")
        assert value == "default"

    def test_set_config(self, manager):
        """Test setting configuration."""
        manager.set("test.key", "test_value")
        assert manager.get("test.key") == "test_value"

    def test_set_config_with_type(self, manager):
        """Test setting config with different types."""
        manager.set("test.int", "42", ConfigType.INTEGER)
        assert manager.get("test.int") == 42

        manager.set("test.float", "3.14", ConfigType.FLOAT)
        assert manager.get("test.float") == 3.14

        manager.set("test.bool", "true", ConfigType.BOOLEAN)
        assert manager.get("test.bool") is True

    def test_update_existing_config(self, manager):
        """Test updating existing configuration."""
        original = manager.get("app.version")
        manager.set("app.version", "2.0.0")
        assert manager.get("app.version") == "2.0.0"

    def test_delete_config(self, manager):
        """Test deleting configuration."""
        manager.set("test.delete", "value")
        assert manager.get("test.delete") == "value"

        result = manager.delete("test.delete")
        assert result is True
        assert manager.get("test.delete") is None

        result = manager.delete("nonexistent")
        assert result is False

    def test_list_all(self, manager):
        """Test listing all configurations."""
        configs = manager.list_all()
        assert len(configs) > 0

        # All should be sorted by key
        keys = [c.key for c in configs]
        assert keys == sorted(keys)

    def test_list_with_prefix(self, manager):
        """Test listing configs with prefix."""
        configs = manager.list_all("app.")
        assert all(c.key.startswith("app.") for c in configs)

        configs = manager.list_all("rate_limit.")
        assert all(c.key.startswith("rate_limit.") for c in configs)

    def test_get_by_prefix(self, manager):
        """Test getting configs by prefix as dict."""
        app_config = manager.get_by_prefix("app")
        assert "name" in app_config
        assert "version" in app_config

    def test_export(self, manager):
        """Test exporting configurations."""
        exported = manager.export()
        assert "app.name" in exported
        assert exported["app.name"]["value"] == "Signal Transceiver"

    def test_secret_config(self, manager):
        """Test secret configuration handling."""
        manager.set("test.secret", "secret_value", is_secret=True)

        exported = manager.export(hide_secrets=True)
        assert exported["test.secret"]["value"] == "***"

        exported = manager.export(hide_secrets=False)
        assert exported["test.secret"]["value"] == "secret_value"


class TestLogSearchService:
    """Tests for LogSearchService."""

    @pytest.fixture
    def service(self):
        svc = LogSearchService.__new__(LogSearchService)
        svc._logs = []
        svc._counter = 0
        svc._max_logs = 10000
        svc._initialized = True
        return svc

    def test_add_log(self, service):
        """Test adding log entry."""
        entry = service.add(LogLevel.INFO, "Test message")

        assert entry.id.startswith("LOG-")
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"

    def test_add_log_with_metadata(self, service):
        """Test adding log with metadata."""
        entry = service.add(
            LogLevel.ERROR,
            "Error occurred",
            source="api",
            user_id=1,
            metadata={"error_code": 500}
        )

        assert entry.source == "api"
        assert entry.user_id == 1
        assert entry.metadata["error_code"] == 500

    def test_search_by_level(self, service):
        """Test searching by level."""
        service.add(LogLevel.INFO, "Info message")
        service.add(LogLevel.ERROR, "Error message")
        service.add(LogLevel.INFO, "Another info")

        query = LogSearchQuery(level=LogLevel.ERROR)
        results = service.search(query)

        assert len(results) == 1
        assert results[0].level == LogLevel.ERROR

    def test_search_by_keyword(self, service):
        """Test searching by keyword."""
        service.add(LogLevel.INFO, "User login successful")
        service.add(LogLevel.INFO, "Data uploaded")
        service.add(LogLevel.ERROR, "Login failed")

        query = LogSearchQuery(keyword="login")
        results = service.search(query)

        assert len(results) == 2

    def test_search_by_source(self, service):
        """Test searching by source."""
        service.add(LogLevel.INFO, "Message 1", source="api")
        service.add(LogLevel.INFO, "Message 2", source="worker")
        service.add(LogLevel.INFO, "Message 3", source="api")

        query = LogSearchQuery(source="api")
        results = service.search(query)

        assert len(results) == 2

    def test_search_pagination(self, service):
        """Test search pagination."""
        for i in range(20):
            service.add(LogLevel.INFO, f"Message {i}")

        query = LogSearchQuery(limit=5, offset=0)
        results = service.search(query)
        assert len(results) == 5

        query = LogSearchQuery(limit=5, offset=10)
        results = service.search(query)
        assert len(results) == 5

    def test_get_by_id(self, service):
        """Test getting log by ID."""
        entry = service.add(LogLevel.INFO, "Test")

        result = service.get_by_id(entry.id)
        assert result is not None
        assert result.message == "Test"

        assert service.get_by_id("LOG-999999") is None

    def test_get_stats(self, service):
        """Test getting statistics."""
        service.add(LogLevel.INFO, "Info 1")
        service.add(LogLevel.INFO, "Info 2")
        service.add(LogLevel.ERROR, "Error 1")
        service.add(LogLevel.WARNING, "Warning 1")

        stats = service.get_stats(hours=24)

        assert stats["total_logs"] == 4
        assert stats["by_level"]["INFO"] == 2
        assert stats["by_level"]["ERROR"] == 1
        assert stats["error_count"] == 1

    def test_convenience_methods(self, service):
        """Test convenience logging methods."""
        service.debug("Debug message")
        service.info("Info message")
        service.warning("Warning message")
        service.error("Error message")
        service.critical("Critical message")

        assert len(service._logs) == 5

    def test_to_dict(self, service):
        """Test log entry to_dict."""
        entry = service.add(
            LogLevel.INFO,
            "Test",
            source="test",
            metadata={"key": "value"}
        )

        data = entry.to_dict()
        assert data["level"] == "INFO"
        assert data["message"] == "Test"
        assert data["source"] == "test"
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
