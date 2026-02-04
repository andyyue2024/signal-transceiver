"""
System configuration management service.
Provides dynamic configuration management.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class ConfigType(str, Enum):
    """Configuration value types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"


@dataclass
class ConfigItem:
    """A configuration item."""
    key: str
    value: Any
    config_type: ConfigType
    description: str = ""
    is_secret: bool = False
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[int] = None

    def to_dict(self, hide_secrets: bool = True) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": "***" if self.is_secret and hide_secrets else self.value,
            "type": self.config_type.value,
            "description": self.description,
            "is_secret": self.is_secret,
            "updated_at": self.updated_at.isoformat()
        }


class ConfigManager:
    """Service for managing system configuration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._configs: Dict[str, ConfigItem] = {}
        self._init_defaults()
        self._initialized = True

    def _init_defaults(self):
        """Initialize default configurations."""
        defaults = [
            ("app.name", "Signal Transceiver", ConfigType.STRING, "Application name"),
            ("app.version", "1.0.0", ConfigType.STRING, "Application version"),
            ("app.debug", False, ConfigType.BOOLEAN, "Debug mode"),
            ("rate_limit.default", 100, ConfigType.INTEGER, "Default rate limit per minute"),
            ("rate_limit.auth", 10, ConfigType.INTEGER, "Auth rate limit per minute"),
            ("cache.ttl", 300, ConfigType.INTEGER, "Default cache TTL in seconds"),
            ("cache.max_size", 1000, ConfigType.INTEGER, "Maximum cache entries"),
            ("backup.enabled", True, ConfigType.BOOLEAN, "Enable automatic backups"),
            ("backup.interval_hours", 6, ConfigType.INTEGER, "Backup interval in hours"),
            ("backup.retention_days", 30, ConfigType.INTEGER, "Backup retention days"),
            ("log.level", "INFO", ConfigType.STRING, "Log level"),
            ("log.retention_days", 7, ConfigType.INTEGER, "Log retention days"),
            ("notification.enabled", True, ConfigType.BOOLEAN, "Enable notifications"),
            ("webhook.timeout", 30, ConfigType.INTEGER, "Webhook timeout seconds"),
            ("webhook.retry_count", 3, ConfigType.INTEGER, "Webhook retry count"),
        ]

        for key, value, config_type, description in defaults:
            self._configs[key] = ConfigItem(
                key=key,
                value=value,
                config_type=config_type,
                description=description
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self._configs.get(key)
        if config:
            return config.value
        return default

    def set(
        self,
        key: str,
        value: Any,
        config_type: ConfigType = ConfigType.STRING,
        description: str = "",
        is_secret: bool = False,
        updated_by: Optional[int] = None
    ) -> ConfigItem:
        """Set a configuration value."""
        # Validate type
        value = self._convert_value(value, config_type)

        if key in self._configs:
            config = self._configs[key]
            config.value = value
            config.updated_at = datetime.utcnow()
            config.updated_by = updated_by
            if description:
                config.description = description
        else:
            config = ConfigItem(
                key=key,
                value=value,
                config_type=config_type,
                description=description,
                is_secret=is_secret,
                updated_by=updated_by
            )
            self._configs[key] = config

        logger.info(f"Config updated: {key}")
        return config

    def _convert_value(self, value: Any, config_type: ConfigType) -> Any:
        """Convert value to specified type."""
        if config_type == ConfigType.INTEGER:
            return int(value)
        elif config_type == ConfigType.FLOAT:
            return float(value)
        elif config_type == ConfigType.BOOLEAN:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', '1', 'yes')
        elif config_type == ConfigType.JSON:
            import json
            if isinstance(value, str):
                return json.loads(value)
            return value
        return str(value)

    def delete(self, key: str) -> bool:
        """Delete a configuration."""
        if key in self._configs:
            del self._configs[key]
            return True
        return False

    def list_all(self, prefix: Optional[str] = None) -> List[ConfigItem]:
        """List all configurations."""
        configs = list(self._configs.values())
        if prefix:
            configs = [c for c in configs if c.key.startswith(prefix)]
        return sorted(configs, key=lambda x: x.key)

    def get_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get all configs with a prefix as a dict."""
        result = {}
        for key, config in self._configs.items():
            if key.startswith(prefix):
                # Remove prefix from key
                short_key = key[len(prefix):].lstrip('.')
                result[short_key] = config.value
        return result

    def export(self, hide_secrets: bool = True) -> Dict[str, Any]:
        """Export all configurations."""
        return {
            key: config.to_dict(hide_secrets)
            for key, config in self._configs.items()
        }

    def import_configs(self, data: Dict[str, Any], updated_by: Optional[int] = None):
        """Import configurations from dict."""
        for key, item in data.items():
            if isinstance(item, dict):
                self.set(
                    key=key,
                    value=item.get("value"),
                    config_type=ConfigType(item.get("type", "string")),
                    description=item.get("description", ""),
                    is_secret=item.get("is_secret", False),
                    updated_by=updated_by
                )
            else:
                self.set(key, item, updated_by=updated_by)


# Global instance
config_manager = ConfigManager()
