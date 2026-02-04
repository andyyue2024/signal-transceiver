"""
Alert system for monitoring and notifications.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
import asyncio
from loguru import logger


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data class."""
    id: str
    title: str
    message: str
    level: AlertLevel
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertHandler(ABC):
    """Abstract base class for alert handlers."""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send an alert notification."""
        pass

    @abstractmethod
    def supports_level(self, level: AlertLevel) -> bool:
        """Check if handler supports the given alert level."""
        pass


class ConsoleAlertHandler(AlertHandler):
    """Console alert handler for logging alerts."""

    def __init__(self, min_level: AlertLevel = AlertLevel.INFO):
        self.min_level = min_level
        self._level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

    async def send(self, alert: Alert) -> bool:
        """Log alert to console."""
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(alert.level, logger.info)

        log_func(f"[ALERT] {alert.title}: {alert.message} (source: {alert.source})")
        return True

    def supports_level(self, level: AlertLevel) -> bool:
        return self._level_order[level] >= self._level_order[self.min_level]


class AlertManager:
    """Central alert management system."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._handlers: List[AlertHandler] = []
        self._alerts: List[Alert] = []
        self._alert_counter = 0
        self._rules: List[Dict[str, Any]] = []
        self._initialized = True

    def add_handler(self, handler: AlertHandler):
        """Add an alert handler."""
        self._handlers.append(handler)

    def remove_handler(self, handler: AlertHandler):
        """Remove an alert handler."""
        self._handlers.remove(handler)

    async def trigger(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Trigger a new alert."""
        self._alert_counter += 1
        alert = Alert(
            id=f"alert_{self._alert_counter}",
            title=title,
            message=message,
            level=level,
            source=source,
            metadata=metadata or {}
        )

        self._alerts.append(alert)

        # Send to all handlers
        for handler in self._handlers:
            if handler.supports_level(level):
                try:
                    await handler.send(alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {handler.__class__.__name__}: {e}")

        return alert

    def resolve(self, alert_id: str):
        """Mark an alert as resolved."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                break

    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [a for a in self._alerts if not a.resolved]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get alerts by severity level."""
        return [a for a in self._alerts if a.level == level]

    def add_rule(
        self,
        name: str,
        condition: Callable[[], bool],
        alert_title: str,
        alert_message: str,
        level: AlertLevel = AlertLevel.WARNING,
        check_interval: int = 60
    ):
        """Add an alert rule."""
        self._rules.append({
            "name": name,
            "condition": condition,
            "alert_title": alert_title,
            "alert_message": alert_message,
            "level": level,
            "check_interval": check_interval,
            "last_check": None,
            "triggered": False
        })

    async def check_rules(self):
        """Check all alert rules."""
        now = datetime.utcnow()
        for rule in self._rules:
            last_check = rule.get("last_check")
            if last_check and (now - last_check).seconds < rule["check_interval"]:
                continue

            rule["last_check"] = now

            try:
                if rule["condition"]():
                    if not rule["triggered"]:
                        await self.trigger(
                            title=rule["alert_title"],
                            message=rule["alert_message"],
                            level=rule["level"],
                            source=f"rule:{rule['name']}"
                        )
                        rule["triggered"] = True
                else:
                    rule["triggered"] = False
            except Exception as e:
                logger.error(f"Error checking rule {rule['name']}: {e}")


# Global alert manager instance
alert_manager = AlertManager()
alert_manager.add_handler(ConsoleAlertHandler())
