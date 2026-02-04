"""
Data model for storing client-reported data.
"""
from datetime import datetime, date
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.client import Client
    from src.models.strategy import Strategy


class Data(Base):
    """Data model for storing client-reported data."""

    __tablename__ = "data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Data content
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    execute_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional data
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Source information
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    strategy_id: Mapped[int] = mapped_column(Integer, ForeignKey("strategies.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    processed: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="data_records")
    client: Mapped["Client"] = relationship("Client", back_populates="data_records")

    def __repr__(self) -> str:
        return f"<Data(id={self.id}, type='{self.type}', symbol='{self.symbol}')>"
