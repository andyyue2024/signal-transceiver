"""
飞书 (Feishu/Lark) alert integration.
"""
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from src.monitor.alerts import AlertHandler, Alert, AlertLevel


class FeishuAlertHandler(AlertHandler):
    """Feishu webhook alert handler."""

    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
        min_level: AlertLevel = AlertLevel.WARNING
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.min_level = min_level
        self._level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }
        self._level_colors = {
            AlertLevel.INFO: "blue",
            AlertLevel.WARNING: "yellow",
            AlertLevel.ERROR: "red",
            AlertLevel.CRITICAL: "red"
        }

    def _build_card_message(self, alert: Alert) -> Dict[str, Any]:
        """Build Feishu card message."""
        color = self._level_colors.get(alert.level, "blue")

        # Build card content
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**级别:** {alert.level.value.upper()}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**来源:** {alert.source}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**消息:** {alert.message}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**时间:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]

        # Add metadata if present
        if alert.metadata:
            metadata_str = "\n".join([f"- {k}: {v}" for k, v in alert.metadata.items()])
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**详细信息:**\n{metadata_str}"
                }
            })

        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 {alert.title}"
                    },
                    "template": color
                },
                "elements": elements
            }
        }

    async def send(self, alert: Alert) -> bool:
        """Send alert to Feishu webhook."""
        try:
            message = self._build_card_message(alert)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            logger.info(f"Feishu alert sent successfully: {alert.title}")
                            return True
                        else:
                            logger.error(f"Feishu API error: {result}")
                            return False
                    else:
                        logger.error(f"Feishu webhook failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Feishu alert: {e}")
            return False

    def supports_level(self, level: AlertLevel) -> bool:
        return self._level_order[level] >= self._level_order[self.min_level]


class FeishuNotifier:
    """Utility class for sending various Feishu notifications."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_text(self, content: str) -> bool:
        """Send a simple text message."""
        message = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return await self._send(message)

    async def send_markdown(self, title: str, content: str) -> bool:
        """Send a markdown message."""
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
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

        metrics_content = "\n".join([f"• **{k}:** {v}" for k, v in metrics.items()])

        message = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": f"📊 {title}"},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": summary}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": metrics_content}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
        }
        return await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> bool:
        """Send message to Feishu webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send Feishu message: {e}")
            return False
