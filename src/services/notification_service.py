"""
System notification service for internal notifications.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio


class NotificationType(str, Enum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """A system notification."""
    id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    user_id: Optional[int] = None
    read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "metadata": self.metadata
        }


class NotificationService:
    """Service for managing system notifications."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._notifications: Dict[str, Notification] = {}
        self._counter = 0
        self._subscribers: Dict[int, List[Callable]] = {}  # user_id -> callbacks
        self._initialized = True

    def _generate_id(self) -> str:
        self._counter += 1
        return f"NOTIF-{self._counter:08d}"

    def create(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            id=self._generate_id(),
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            user_id=user_id,
            metadata=metadata or {}
        )

        self._notifications[notification.id] = notification
        logger.debug(f"Created notification: {notification.id}")

        # Notify subscribers
        self._notify_subscribers(user_id, notification)

        return notification

    def _notify_subscribers(self, user_id: Optional[int], notification: Notification):
        """Notify subscribed callbacks."""
        if user_id and user_id in self._subscribers:
            for callback in self._subscribers[user_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(notification))
                    else:
                        callback(notification)
                except Exception as e:
                    logger.error(f"Notification callback error: {e}")

    def subscribe(self, user_id: int, callback: Callable):
        """Subscribe to notifications for a user."""
        if user_id not in self._subscribers:
            self._subscribers[user_id] = []
        self._subscribers[user_id].append(callback)

    def unsubscribe(self, user_id: int, callback: Callable):
        """Unsubscribe from notifications."""
        if user_id in self._subscribers:
            self._subscribers[user_id] = [
                cb for cb in self._subscribers[user_id] if cb != callback
            ]

    def get(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID."""
        return self._notifications.get(notification_id)

    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Mark a notification as read."""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.read = True
            notification.read_at = datetime.utcnow()
        return notification

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications for a user as read."""
        count = 0
        for notification in self._notifications.values():
            if notification.user_id == user_id and not notification.read:
                notification.read = True
                notification.read_at = datetime.utcnow()
                count += 1
        return count

    def delete(self, notification_id: str) -> bool:
        """Delete a notification."""
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False

    def list_for_user(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """List notifications for a user."""
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id or n.user_id is None
        ]

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)

        return notifications[:limit]

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user."""
        return sum(
            1 for n in self._notifications.values()
            if (n.user_id == user_id or n.user_id is None) and not n.read
        )

    def cleanup_old(self, days: int = 30) -> int:
        """Remove notifications older than specified days."""
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0)
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=days)

        old_ids = [
            n.id for n in self._notifications.values()
            if n.created_at < cutoff
        ]

        for nid in old_ids:
            del self._notifications[nid]

        return len(old_ids)

    # Convenience methods for different notification types
    def info(self, title: str, message: str, user_id: Optional[int] = None, **kwargs):
        return self.create(title, message, NotificationType.INFO, user_id=user_id, **kwargs)

    def warning(self, title: str, message: str, user_id: Optional[int] = None, **kwargs):
        return self.create(title, message, NotificationType.WARNING,
                          priority=NotificationPriority.HIGH, user_id=user_id, **kwargs)

    def error(self, title: str, message: str, user_id: Optional[int] = None, **kwargs):
        return self.create(title, message, NotificationType.ERROR,
                          priority=NotificationPriority.URGENT, user_id=user_id, **kwargs)

    def success(self, title: str, message: str, user_id: Optional[int] = None, **kwargs):
        return self.create(title, message, NotificationType.SUCCESS, user_id=user_id, **kwargs)


# Global instance
notification_service = NotificationService()
