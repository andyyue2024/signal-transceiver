"""
User feedback service for collecting and managing user feedback.
Provides technical support channel for users.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class FeedbackType(str, Enum):
    """Types of user feedback."""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUESTION = "question"
    IMPROVEMENT = "improvement"
    OTHER = "other"


class FeedbackStatus(str, Enum):
    """Status of feedback."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


class FeedbackPriority(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Feedback:
    """User feedback record."""
    id: str
    user_id: Optional[int]
    type: FeedbackType
    title: str
    description: str
    status: FeedbackStatus = FeedbackStatus.OPEN
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    response: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "response": self.response,
            "tags": self.tags,
            "metadata": self.metadata
        }


class FeedbackService:
    """Service for managing user feedback."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._feedbacks: Dict[str, Feedback] = {}
        self._counter = 0
        self._initialized = True

    def _generate_id(self) -> str:
        self._counter += 1
        return f"FB-{self._counter:06d}"

    def submit(
        self,
        title: str,
        description: str,
        feedback_type: FeedbackType = FeedbackType.OTHER,
        user_id: Optional[int] = None,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """Submit new feedback."""
        feedback = Feedback(
            id=self._generate_id(),
            user_id=user_id,
            type=feedback_type,
            title=title,
            description=description,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {}
        )

        self._feedbacks[feedback.id] = feedback
        logger.info(f"New feedback submitted: {feedback.id} - {title}")

        return feedback

    def get(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID."""
        return self._feedbacks.get(feedback_id)

    def update_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
        response: Optional[str] = None
    ) -> Optional[Feedback]:
        """Update feedback status."""
        feedback = self._feedbacks.get(feedback_id)
        if not feedback:
            return None

        feedback.status = status
        feedback.updated_at = datetime.utcnow()

        if response:
            feedback.response = response

        if status == FeedbackStatus.RESOLVED:
            feedback.resolved_at = datetime.utcnow()

        logger.info(f"Feedback {feedback_id} updated: {status.value}")
        return feedback

    def list_feedbacks(
        self,
        status: Optional[FeedbackStatus] = None,
        feedback_type: Optional[FeedbackType] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Feedback]:
        """List feedbacks with filters."""
        feedbacks = list(self._feedbacks.values())

        if status:
            feedbacks = [f for f in feedbacks if f.status == status]
        if feedback_type:
            feedbacks = [f for f in feedbacks if f.type == feedback_type]
        if user_id:
            feedbacks = [f for f in feedbacks if f.user_id == user_id]

        # Sort by created_at descending
        feedbacks.sort(key=lambda x: x.created_at, reverse=True)

        return feedbacks[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        feedbacks = list(self._feedbacks.values())

        by_status = {}
        by_type = {}
        by_priority = {}

        for f in feedbacks:
            by_status[f.status.value] = by_status.get(f.status.value, 0) + 1
            by_type[f.type.value] = by_type.get(f.type.value, 0) + 1
            by_priority[f.priority.value] = by_priority.get(f.priority.value, 0) + 1

        # Calculate resolution time
        resolved = [f for f in feedbacks if f.resolved_at]
        avg_resolution_hours = 0
        if resolved:
            total_hours = sum(
                (f.resolved_at - f.created_at).total_seconds() / 3600
                for f in resolved
            )
            avg_resolution_hours = total_hours / len(resolved)

        return {
            "total": len(feedbacks),
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "resolved_count": len(resolved),
            "avg_resolution_hours": round(avg_resolution_hours, 2),
            "open_count": by_status.get("open", 0)
        }

    def search(self, query: str, limit: int = 20) -> List[Feedback]:
        """Search feedbacks by title or description."""
        query_lower = query.lower()
        results = [
            f for f in self._feedbacks.values()
            if query_lower in f.title.lower() or query_lower in f.description.lower()
        ]
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]


# Global instance
feedback_service = FeedbackService()
