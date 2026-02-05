"""
Subscription model for storing subscription information.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer, JSON


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.strategy import Strategy


class Subscription(Base):
    """Subscription model for storing subscription information."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Subscription info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Subscription type: 'polling' or 'websocket'
    subscription_type: Mapped[str] = mapped_column(String(20), default="polling")

    # Relationships - now references User instead of Client
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("strategies.id"), nullable=True)

    # Filter criteria
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Notification settings
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Last notification tracking
    last_data_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    strategy: Mapped[Optional["Strategy"]] = relationship("Strategy", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, name='{self.name}', user_id={self.user_id})>"
