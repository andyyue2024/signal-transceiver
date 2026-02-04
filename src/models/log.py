"""
Log model for storing access and operation logs.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Log(Base):
    """Log model for storing access and operation logs."""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Log type: 'access', 'operation', 'error', 'security'
    log_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Action information
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Request information
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # User relationship
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    client_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Log content
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Response information
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Severity level: 'debug', 'info', 'warning', 'error', 'critical'
    level: Mapped[str] = mapped_column(String(20), default="info", index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="logs")

    def __repr__(self) -> str:
        return f"<Log(id={self.id}, type='{self.log_type}', action='{self.action}')>"
