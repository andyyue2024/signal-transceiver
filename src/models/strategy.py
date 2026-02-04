"""
Strategy model for storing strategy information.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.data import Data
    from src.models.subscription import Subscription


class Strategy(Base):
    """Strategy model for storing strategy related information."""

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Strategy type and category
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="default")
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Configuration
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Version control
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    data_records: Mapped[List["Data"]] = relationship("Data", back_populates="strategy", lazy="selectin")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="strategy", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, strategy_id='{self.strategy_id}', name='{self.name}')>"
