"""
Client model for storing client application information.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.subscription import Subscription
    from src.models.permission import ClientPermission
    from src.models.data import Data


class Client(Base):
    """Client model for storing client application information."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    client_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    client_secret: Mapped[str] = mapped_column(String(128), nullable=False)

    # Owner relationship
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Client information
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # requests per minute

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_access_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="clients")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="client", lazy="selectin")
    permissions: Mapped[List["ClientPermission"]] = relationship("ClientPermission", back_populates="client", lazy="selectin")
    data_records: Mapped[List["Data"]] = relationship("Data", back_populates="client", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}')>"
