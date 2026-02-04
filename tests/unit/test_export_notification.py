"""
Tests for export and notification services.
"""
import pytest
from datetime import datetime

from src.services.export_service import DataExportService, ExportFormat
from src.services.notification_service import (
    NotificationService, NotificationType, NotificationPriority
)


class TestDataExportService:
    """Tests for DataExportService."""

    @pytest.fixture
    def service(self):
        return DataExportService()

    @pytest.fixture
    def sample_data(self):
        return [
            {"id": 1, "name": "Test 1", "value": 100, "date": datetime(2024, 1, 1)},
            {"id": 2, "name": "Test 2", "value": 200, "date": datetime(2024, 1, 2)},
        ]

    def test_export_to_json(self, service, sample_data):
        """Test JSON export."""
        result = service.export_to_json(sample_data, "test")

        assert result.format == ExportFormat.JSON
        assert result.filename.startswith("test_")
        assert result.filename.endswith(".json")
        assert result.record_count == 2
        assert b'"data"' in result.content

    def test_export_to_csv(self, service, sample_data):
        """Test CSV export."""
        result = service.export_to_csv(sample_data, "test")

        assert result.format == ExportFormat.CSV
        assert result.filename.endswith(".csv")
        assert result.record_count == 2
        # Check header
        content = result.content.decode('utf-8-sig')
        assert "id" in content
        assert "name" in content

    def test_export_to_jsonl(self, service, sample_data):
        """Test JSONL export."""
        result = service.export_to_jsonl(sample_data, "test")

        assert result.format == ExportFormat.JSONL
        assert result.filename.endswith(".jsonl")
        lines = result.content.decode('utf-8').strip().split('\n')
        assert len(lines) == 2

    def test_export_empty_data(self, service):
        """Test exporting empty data."""
        result = service.export_to_csv([], "test")
        assert result.record_count == 0

    def test_export_with_columns(self, service, sample_data):
        """Test CSV export with specific columns."""
        result = service.export_to_csv(sample_data, "test", columns=["id", "name"])
        content = result.content.decode('utf-8-sig')
        assert "id" in content
        assert "name" in content

    def test_generic_export(self, service, sample_data):
        """Test generic export method."""
        result = service.export(sample_data, ExportFormat.JSON)
        assert result.format == ExportFormat.JSON

        result = service.export(sample_data, ExportFormat.CSV)
        assert result.format == ExportFormat.CSV


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def service(self):
        svc = NotificationService.__new__(NotificationService)
        svc._notifications = {}
        svc._counter = 0
        svc._subscribers = {}
        svc._initialized = True
        return svc

    def test_create_notification(self, service):
        """Test creating a notification."""
        notification = service.create(
            title="Test",
            message="Test message",
            notification_type=NotificationType.INFO,
            user_id=1
        )

        assert notification.id.startswith("NOTIF-")
        assert notification.title == "Test"
        assert notification.type == NotificationType.INFO
        assert notification.read is False

    def test_get_notification(self, service):
        """Test getting notification by ID."""
        notification = service.create("Test", "Message", user_id=1)

        result = service.get(notification.id)
        assert result is not None
        assert result.title == "Test"

        assert service.get("NOTIF-999999") is None

    def test_mark_as_read(self, service):
        """Test marking notification as read."""
        notification = service.create("Test", "Message", user_id=1)
        assert notification.read is False

        service.mark_as_read(notification.id)

        assert notification.read is True
        assert notification.read_at is not None

    def test_mark_all_as_read(self, service):
        """Test marking all notifications as read."""
        service.create("Test 1", "Message", user_id=1)
        service.create("Test 2", "Message", user_id=1)
        service.create("Test 3", "Message", user_id=2)

        count = service.mark_all_as_read(1)
        assert count == 2

    def test_list_for_user(self, service):
        """Test listing notifications for user."""
        service.create("Test 1", "Message", user_id=1)
        service.create("Test 2", "Message", user_id=1)
        service.create("Test 3", "Message", user_id=2)

        notifications = service.list_for_user(1)
        assert len(notifications) == 2

    def test_list_unread_only(self, service):
        """Test listing only unread notifications."""
        n1 = service.create("Test 1", "Message", user_id=1)
        service.create("Test 2", "Message", user_id=1)

        service.mark_as_read(n1.id)

        unread = service.list_for_user(1, unread_only=True)
        assert len(unread) == 1

    def test_get_unread_count(self, service):
        """Test getting unread count."""
        service.create("Test 1", "Message", user_id=1)
        service.create("Test 2", "Message", user_id=1)

        count = service.get_unread_count(1)
        assert count == 2

    def test_delete_notification(self, service):
        """Test deleting notification."""
        notification = service.create("Test", "Message", user_id=1)

        assert service.delete(notification.id) is True
        assert service.get(notification.id) is None
        assert service.delete("NOTIF-999999") is False

    def test_convenience_methods(self, service):
        """Test convenience notification methods."""
        info = service.info("Info", "Info message", user_id=1)
        assert info.type == NotificationType.INFO

        warning = service.warning("Warning", "Warning message", user_id=1)
        assert warning.type == NotificationType.WARNING
        assert warning.priority == NotificationPriority.HIGH

        error = service.error("Error", "Error message", user_id=1)
        assert error.type == NotificationType.ERROR
        assert error.priority == NotificationPriority.URGENT

        success = service.success("Success", "Success message", user_id=1)
        assert success.type == NotificationType.SUCCESS

    def test_to_dict(self, service):
        """Test notification to_dict method."""
        notification = service.create(
            title="Test",
            message="Message",
            notification_type=NotificationType.WARNING,
            user_id=1
        )

        data = notification.to_dict()
        assert data["title"] == "Test"
        assert data["type"] == "warning"
        assert data["read"] is False
        assert "created_at" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
