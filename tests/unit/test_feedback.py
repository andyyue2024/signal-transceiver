"""
Tests for feedback service.
"""
import pytest
from datetime import datetime

from src.services.feedback_service import (
    FeedbackService, FeedbackType, FeedbackStatus, FeedbackPriority
)


class TestFeedbackService:
    """Tests for FeedbackService."""

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        svc = FeedbackService.__new__(FeedbackService)
        svc._feedbacks = {}
        svc._counter = 0
        svc._initialized = True
        return svc

    def test_submit_feedback(self, service):
        """Test submitting feedback."""
        feedback = service.submit(
            title="Test Bug",
            description="Found a bug in the system",
            feedback_type=FeedbackType.BUG,
            user_id=1,
            priority=FeedbackPriority.HIGH
        )

        assert feedback.id.startswith("FB-")
        assert feedback.title == "Test Bug"
        assert feedback.type == FeedbackType.BUG
        assert feedback.status == FeedbackStatus.OPEN
        assert feedback.priority == FeedbackPriority.HIGH
        assert feedback.user_id == 1

    def test_get_feedback(self, service):
        """Test getting feedback by ID."""
        feedback = service.submit(
            title="Test",
            description="Description"
        )

        result = service.get(feedback.id)
        assert result is not None
        assert result.title == "Test"

        # Non-existent
        assert service.get("FB-999999") is None

    def test_update_status(self, service):
        """Test updating feedback status."""
        feedback = service.submit(
            title="Test",
            description="Description"
        )

        updated = service.update_status(
            feedback.id,
            FeedbackStatus.IN_PROGRESS,
            response="Working on it"
        )

        assert updated.status == FeedbackStatus.IN_PROGRESS
        assert updated.response == "Working on it"

    def test_update_status_resolved(self, service):
        """Test resolving feedback sets resolved_at."""
        feedback = service.submit(
            title="Test",
            description="Description"
        )

        updated = service.update_status(
            feedback.id,
            FeedbackStatus.RESOLVED,
            response="Fixed"
        )

        assert updated.status == FeedbackStatus.RESOLVED
        assert updated.resolved_at is not None

    def test_list_feedbacks(self, service):
        """Test listing feedbacks."""
        service.submit(title="Bug 1", description="Desc", feedback_type=FeedbackType.BUG)
        service.submit(title="Feature 1", description="Desc", feedback_type=FeedbackType.FEATURE_REQUEST)
        service.submit(title="Bug 2", description="Desc", feedback_type=FeedbackType.BUG)

        all_feedbacks = service.list_feedbacks()
        assert len(all_feedbacks) == 3

        bugs_only = service.list_feedbacks(feedback_type=FeedbackType.BUG)
        assert len(bugs_only) == 2

    def test_list_feedbacks_by_status(self, service):
        """Test filtering by status."""
        fb1 = service.submit(title="Open", description="Desc")
        fb2 = service.submit(title="Closed", description="Desc")
        service.update_status(fb2.id, FeedbackStatus.CLOSED)

        open_feedbacks = service.list_feedbacks(status=FeedbackStatus.OPEN)
        assert len(open_feedbacks) == 1
        assert open_feedbacks[0].title == "Open"

    def test_get_stats(self, service):
        """Test getting statistics."""
        service.submit(title="Bug", description="Desc", feedback_type=FeedbackType.BUG)
        service.submit(title="Feature", description="Desc", feedback_type=FeedbackType.FEATURE_REQUEST)
        fb = service.submit(title="Question", description="Desc", feedback_type=FeedbackType.QUESTION)
        service.update_status(fb.id, FeedbackStatus.RESOLVED)

        stats = service.get_stats()

        assert stats["total"] == 3
        assert stats["by_type"]["bug"] == 1
        assert stats["by_type"]["feature_request"] == 1
        assert stats["resolved_count"] == 1

    def test_search(self, service):
        """Test searching feedbacks."""
        service.submit(title="Login bug", description="Can't login")
        service.submit(title="API issue", description="API returns error")
        service.submit(title="Performance", description="Slow login page")

        results = service.search("login")
        assert len(results) == 2

        results = service.search("API")
        assert len(results) == 1

    def test_to_dict(self, service):
        """Test feedback to_dict."""
        feedback = service.submit(
            title="Test",
            description="Description",
            feedback_type=FeedbackType.BUG,
            tags=["urgent", "auth"]
        )

        data = feedback.to_dict()

        assert data["title"] == "Test"
        assert data["type"] == "bug"
        assert data["status"] == "open"
        assert "urgent" in data["tags"]
        assert "created_at" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
