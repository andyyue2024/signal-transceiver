"""
钉钉 (DingTalk) alert integration.
"""
import aiohttp
import hmac
import hashlib
import base64
import time
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from src.monitor.alerts import AlertHandler, Alert, AlertLevel


class DingTalkAlertHandler(AlertHandler):
    """DingTalk webhook alert handler."""

    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
        min_level: AlertLevel = AlertLevel.WARNING,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.min_level = min_level
        self.at_mobiles = at_mobiles or []
        self.at_all = at_all
        self._level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

    def _get_signed_url(self) -> str:
        """Generate signed webhook URL if secret is provided."""
        if not self.secret:
            return self.webhook_url

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(
            secret_enc,
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    def _get_level_emoji(self, level: AlertLevel) -> str:
        """Get emoji for alert level."""
        return {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(level, "📢")

    def _build_markdown_message(self, alert: Alert) -> Dict[str, Any]:
        """Build DingTalk markdown message."""
        emoji = self._get_level_emoji(alert.level)

        content_lines = [
            f"## {emoji} {alert.title}",
            "",
            f"**级别:** {alert.level.value.upper()}",
            f"**来源:** {alert.source}",
            f"**时间:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**消息:** {alert.message}"
        ]

        if alert.metadata:
            content_lines.append("")
            content_lines.append("**详细信息:**")
            for key, value in alert.metadata.items():
                content_lines.append(f"- {key}: {value}")

        return {
            "msgtype": "markdown",
            "markdown": {
                "title": alert.title,
                "text": "\n".join(content_lines)
            },
            "at": {
                "atMobiles": self.at_mobiles,
                "isAtAll": self.at_all
            }
        }

    async def send(self, alert: Alert) -> bool:
        """Send alert to DingTalk webhook."""
        try:
            message = self._build_markdown_message(alert)
            url = self._get_signed_url()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("errcode") == 0:
                            logger.info(f"DingTalk alert sent successfully: {alert.title}")
                            return True
                        else:
                            logger.error(f"DingTalk API error: {result}")
                            return False
                    else:
                        logger.error(f"DingTalk webhook failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send DingTalk alert: {e}")
            return False

    def supports_level(self, level: AlertLevel) -> bool:
        return self._level_order[level] >= self._level_order[self.min_level]


class DingTalkNotifier:
    """Utility class for sending various DingTalk notifications."""

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret

    def _get_signed_url(self) -> str:
        """Generate signed webhook URL."""
        if not self.secret:
            return self.webhook_url

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            secret_enc,
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    async def send_text(
        self,
        content: str,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ) -> bool:
        """Send a text message."""
        message = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        }
        return await self._send(message)

    async def send_link(
        self,
        title: str,
        text: str,
        message_url: str,
        pic_url: Optional[str] = None
    ) -> bool:
        """Send a link message."""
        message = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "messageUrl": message_url,
                "picUrl": pic_url or ""
            }
        }
        return await self._send(message)

    async def send_action_card(
        self,
        title: str,
        text: str,
        buttons: List[Dict[str, str]],
        btn_orientation: str = "0"
    ) -> bool:
        """Send an action card message."""
        message = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "btnOrientation": btn_orientation,
                "btns": buttons
            }
        }
        return await self._send(message)

    async def send_report(
        self,
        title: str,
        summary: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Send a formatted report."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        lines = [
            f"## 📊 {title}",
            "",
            summary,
            "",
            "---",
            ""
        ]

        for key, value in metrics.items():
            lines.append(f"**{key}:** {value}")

        lines.extend([
            "",
            "---",
            f"*生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": "\n".join(lines)
            }
        }
        return await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> bool:
        """Send message to DingTalk webhook."""
        try:
            url = self._get_signed_url()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("errcode") == 0
                    return False
        except Exception as e:
            logger.error(f"Failed to send DingTalk message: {e}")
            return False
