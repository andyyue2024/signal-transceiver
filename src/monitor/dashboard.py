"""
System dashboard for monitoring.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger

from src.monitor.performance import performance_monitor
from src.monitor.alerts import alert_manager, AlertLevel


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    title: str
    type: str  # 'metric', 'chart', 'table', 'alert'
    data_source: str
    refresh_interval: int = 30  # seconds
    config: Dict[str, Any] = None


class SystemDashboard:
    """System monitoring dashboard."""

    def __init__(self):
        self._widgets: List[DashboardWidget] = []
        self._setup_default_widgets()

    def _setup_default_widgets(self):
        """Setup default dashboard widgets."""
        self._widgets = [
            DashboardWidget(
                id="system_health",
                title="系统健康状态",
                type="metric",
                data_source="health"
            ),
            DashboardWidget(
                id="cpu_usage",
                title="CPU 使用率",
                type="chart",
                data_source="cpu"
            ),
            DashboardWidget(
                id="memory_usage",
                title="内存使用率",
                type="chart",
                data_source="memory"
            ),
            DashboardWidget(
                id="request_rate",
                title="请求速率",
                type="chart",
                data_source="requests"
            ),
            DashboardWidget(
                id="error_rate",
                title="错误率",
                type="chart",
                data_source="errors"
            ),
            DashboardWidget(
                id="active_alerts",
                title="活跃告警",
                type="alert",
                data_source="alerts"
            ),
            DashboardWidget(
                id="recent_activity",
                title="最近活动",
                type="table",
                data_source="activity"
            )
        ]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        stats = performance_monitor.get_current_stats()
        warnings = performance_monitor.check_thresholds()
        active_alerts = alert_manager.get_active_alerts()

        # Calculate health score
        health_score = self._calculate_health_score(stats, warnings)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": {
                "score": health_score,
                "status": self._get_health_status(health_score),
                "uptime_hours": stats["uptime_seconds"] / 3600
            },
            "system": {
                "cpu_percent": stats["cpu_percent"],
                "memory_percent": stats["memory_percent"],
                "memory_used_mb": stats["memory_used_mb"],
                "disk_percent": stats["disk_percent"]
            },
            "performance": {
                "requests_per_second": stats["requests_per_second"],
                "avg_response_time_ms": stats["avg_response_time_ms"],
                "error_rate": stats["error_rate"],
                "total_requests": stats["total_requests"],
                "total_errors": stats["total_errors"]
            },
            "alerts": {
                "active_count": len(active_alerts),
                "items": [
                    {
                        "id": a.id,
                        "title": a.title,
                        "level": a.level.value,
                        "timestamp": a.timestamp.isoformat()
                    }
                    for a in active_alerts[-10:]  # Last 10 alerts
                ]
            },
            "warnings": warnings
        }

    def _calculate_health_score(
        self,
        stats: Dict[str, Any],
        warnings: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Deduct for high resource usage
        if stats["cpu_percent"] > 80:
            score -= min(20, (stats["cpu_percent"] - 80) * 2)
        if stats["memory_percent"] > 80:
            score -= min(20, (stats["memory_percent"] - 80) * 2)
        if stats["disk_percent"] > 80:
            score -= min(10, (stats["disk_percent"] - 80))

        # Deduct for performance issues
        if stats["error_rate"] > 0:
            score -= min(30, stats["error_rate"] * 300)
        if stats["avg_response_time_ms"] > 500:
            score -= min(20, (stats["avg_response_time_ms"] - 500) / 50)

        # Deduct for warnings
        for warning in warnings:
            if warning["level"] == "critical":
                score -= 10
            else:
                score -= 5

        return max(0, min(100, score))

    def _get_health_status(self, score: float) -> str:
        """Get health status from score."""
        if score >= 90:
            return "healthy"
        elif score >= 70:
            return "degraded"
        elif score >= 50:
            return "warning"
        else:
            return "critical"

    def get_metrics_history(
        self,
        metric: str,
        minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric."""
        history = performance_monitor.get_history(minutes)

        metric_map = {
            "cpu": "cpu_percent",
            "memory": "memory_percent",
            "requests": "requests_per_second",
            "response_time": "avg_response_time_ms",
            "errors": "error_rate"
        }

        field = metric_map.get(metric, "cpu_percent")

        return [
            {
                "timestamp": h["timestamp"],
                "value": h.get(field, 0)
            }
            for h in history
        ]

    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report."""
        data = self.get_dashboard_data()

        return {
            "report_time": datetime.utcnow().isoformat(),
            "summary": {
                "health_status": data["health"]["status"],
                "health_score": data["health"]["score"],
                "uptime_hours": round(data["health"]["uptime_hours"], 2),
                "total_requests": data["performance"]["total_requests"],
                "error_rate_percent": round(data["performance"]["error_rate"] * 100, 2),
                "avg_response_time_ms": round(data["performance"]["avg_response_time_ms"], 2),
                "active_alerts": data["alerts"]["active_count"]
            },
            "resource_usage": {
                "cpu": f"{data['system']['cpu_percent']:.1f}%",
                "memory": f"{data['system']['memory_percent']:.1f}%",
                "disk": f"{data['system']['disk_percent']:.1f}%"
            },
            "recommendations": self._generate_recommendations(data)
        }

    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current state."""
        recommendations = []

        if data["system"]["cpu_percent"] > 80:
            recommendations.append("考虑增加CPU资源或优化高CPU消耗的操作")

        if data["system"]["memory_percent"] > 80:
            recommendations.append("内存使用率较高，检查是否有内存泄漏或考虑增加内存")

        if data["system"]["disk_percent"] > 80:
            recommendations.append("磁盘空间不足，清理日志文件或扩展存储")

        if data["performance"]["error_rate"] > 0.01:
            recommendations.append("错误率较高，检查应用日志查找问题根源")

        if data["performance"]["avg_response_time_ms"] > 500:
            recommendations.append("响应时间较慢，考虑优化数据库查询或添加缓存")

        if data["alerts"]["active_count"] > 0:
            recommendations.append(f"有 {data['alerts']['active_count']} 个活跃告警需要处理")

        if not recommendations:
            recommendations.append("系统运行正常，无需特别处理")

        return recommendations


# Global dashboard instance
system_dashboard = SystemDashboard()
