"""
User model for authentication and user management.
Merged with Client functionality - users can act as both admin users and API clients.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, Integer


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.subscription import Subscription
    from src.models.permission import UserPermission
    from src.models.data import Data
    from src.models.log import Log


class User(Base):
    """
    User model - unified user and client model.
    A user can act as both an admin user (with web UI access) and an API client.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # API Authentication - for web UI and CLI access
    api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    api_key_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Client Credentials - for API client access (data upload, subscriptions)
    client_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    client_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    secret_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Rate limiting for API access
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # requests per minute

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_access_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="user", lazy="selectin")
    data_records: Mapped[List["Data"]] = relationship("Data", back_populates="user", lazy="selectin")
    permissions: Mapped[List["UserPermission"]] = relationship("UserPermission", back_populates="user", lazy="selectin")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
