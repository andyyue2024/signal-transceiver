"""
Internationalization (i18n) support module.
Provides multi-language support and timezone handling.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from enum import Enum
import json
from pathlib import Path
from loguru import logger


class Language(str, Enum):
    """Supported languages."""
    ZH_CN = "zh-CN"  # 简体中文
    ZH_TW = "zh-TW"  # 繁体中文
    EN_US = "en-US"  # English (US)
    JA_JP = "ja-JP"  # 日本語


class Timezone(str, Enum):
    """Common timezones."""
    UTC = "UTC"
    ASIA_SHANGHAI = "Asia/Shanghai"
    ASIA_TOKYO = "Asia/Tokyo"
    AMERICA_NEW_YORK = "America/New_York"
    EUROPE_LONDON = "Europe/London"


# Timezone offsets in hours
TIMEZONE_OFFSETS = {
    Timezone.UTC: 0,
    Timezone.ASIA_SHANGHAI: 8,
    Timezone.ASIA_TOKYO: 9,
    Timezone.AMERICA_NEW_YORK: -5,
    Timezone.EUROPE_LONDON: 0,
}


# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        # Common
        "success": "成功",
        "error": "错误",
        "warning": "警告",
        "info": "信息",

        # Auth
        "login_success": "登录成功",
        "login_failed": "登录失败",
        "logout_success": "登出成功",
        "invalid_credentials": "无效的凭证",
        "token_expired": "令牌已过期",
        "permission_denied": "权限不足",

        # Data
        "data_created": "数据创建成功",
        "data_updated": "数据更新成功",
        "data_deleted": "数据删除成功",
        "data_not_found": "数据未找到",

        # Subscription
        "subscription_created": "订阅创建成功",
        "subscription_cancelled": "订阅已取消",
        "subscription_active": "订阅激活中",

        # Validation
        "required_field": "必填字段",
        "invalid_format": "格式无效",
        "value_too_long": "值过长",
        "value_too_short": "值过短",

        # System
        "system_healthy": "系统运行正常",
        "system_degraded": "系统性能下降",
        "system_error": "系统错误",
        "backup_success": "备份成功",
        "backup_failed": "备份失败",
    },

    "en-US": {
        # Common
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "info": "Info",

        # Auth
        "login_success": "Login successful",
        "login_failed": "Login failed",
        "logout_success": "Logout successful",
        "invalid_credentials": "Invalid credentials",
        "token_expired": "Token expired",
        "permission_denied": "Permission denied",

        # Data
        "data_created": "Data created successfully",
        "data_updated": "Data updated successfully",
        "data_deleted": "Data deleted successfully",
        "data_not_found": "Data not found",

        # Subscription
        "subscription_created": "Subscription created successfully",
        "subscription_cancelled": "Subscription cancelled",
        "subscription_active": "Subscription active",

        # Validation
        "required_field": "Required field",
        "invalid_format": "Invalid format",
        "value_too_long": "Value too long",
        "value_too_short": "Value too short",

        # System
        "system_healthy": "System healthy",
        "system_degraded": "System degraded",
        "system_error": "System error",
        "backup_success": "Backup successful",
        "backup_failed": "Backup failed",
    },

    "ja-JP": {
        # Common
        "success": "成功",
        "error": "エラー",
        "warning": "警告",
        "info": "情報",

        # Auth
        "login_success": "ログイン成功",
        "login_failed": "ログイン失敗",
        "logout_success": "ログアウト成功",
        "invalid_credentials": "無効な認証情報",
        "token_expired": "トークンの有効期限切れ",
        "permission_denied": "権限がありません",

        # Data
        "data_created": "データを作成しました",
        "data_updated": "データを更新しました",
        "data_deleted": "データを削除しました",
        "data_not_found": "データが見つかりません",

        # Subscription
        "subscription_created": "サブスクリプションを作成しました",
        "subscription_cancelled": "サブスクリプションをキャンセルしました",
        "subscription_active": "サブスクリプション有効",

        # Validation
        "required_field": "必須項目",
        "invalid_format": "形式が無効です",
        "value_too_long": "値が長すぎます",
        "value_too_short": "値が短すぎます",

        # System
        "system_healthy": "システム正常",
        "system_degraded": "システム低下",
        "system_error": "システムエラー",
        "backup_success": "バックアップ成功",
        "backup_failed": "バックアップ失敗",
    },
}


class I18n:
    """Internationalization handler."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._default_language = Language.ZH_CN
        self._default_timezone = Timezone.ASIA_SHANGHAI
        self._translations = TRANSLATIONS.copy()
        self._initialized = True

    def set_default_language(self, language: Language):
        """Set the default language."""
        self._default_language = language

    def set_default_timezone(self, tz: Timezone):
        """Set the default timezone."""
        self._default_timezone = tz

    def translate(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        """
        Translate a key to the specified language.

        Args:
            key: Translation key
            language: Target language (uses default if None)
            **kwargs: Format arguments

        Returns:
            Translated string
        """
        lang = language or self._default_language
        lang_code = lang.value if isinstance(lang, Language) else lang

        # Get translation
        translations = self._translations.get(lang_code, {})
        text = translations.get(key, key)

        # Format with kwargs
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def t(self, key: str, language: Optional[Language] = None, **kwargs) -> str:
        """Shorthand for translate."""
        return self.translate(key, language, **kwargs)

    def add_translation(self, language: str, key: str, value: str):
        """Add a translation."""
        if language not in self._translations:
            self._translations[language] = {}
        self._translations[language][key] = value

    def load_translations(self, filepath: str):
        """Load translations from JSON file."""
        path = Path(filepath)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for lang, translations in data.items():
                    if lang not in self._translations:
                        self._translations[lang] = {}
                    self._translations[lang].update(translations)
            logger.info(f"Loaded translations from {filepath}")


class TimezoneHelper:
    """Helper for timezone conversions."""

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    @staticmethod
    def to_timezone(dt: datetime, tz: Timezone) -> datetime:
        """Convert datetime to specified timezone."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        offset_hours = TIMEZONE_OFFSETS.get(tz, 0)
        target_tz = timezone(timedelta(hours=offset_hours))

        return dt.astimezone(target_tz)

    @staticmethod
    def from_timezone(dt: datetime, tz: Timezone) -> datetime:
        """Convert datetime from specified timezone to UTC."""
        offset_hours = TIMEZONE_OFFSETS.get(tz, 0)
        source_tz = timezone(timedelta(hours=offset_hours))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=source_tz)

        return dt.astimezone(timezone.utc)

    @staticmethod
    def format_datetime(
        dt: datetime,
        tz: Timezone = Timezone.UTC,
        format_str: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """Format datetime for display."""
        localized = TimezoneHelper.to_timezone(dt, tz)
        return localized.strftime(format_str)

    @staticmethod
    def get_timezone_offset(tz: Timezone) -> str:
        """Get timezone offset string (e.g., '+08:00')."""
        hours = TIMEZONE_OFFSETS.get(tz, 0)
        sign = '+' if hours >= 0 else '-'
        return f"{sign}{abs(hours):02d}:00"


# Global instances
i18n = I18n()
tz_helper = TimezoneHelper()


def _(key: str, language: Optional[Language] = None, **kwargs) -> str:
    """Shorthand function for translation."""
    return i18n.translate(key, language, **kwargs)
