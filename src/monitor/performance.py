"""
Performance monitoring utilities.
"""
import time
import asyncio
import psutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
from loguru import logger

from src.monitor.metrics import (
    http_request_duration_seconds,
    db_query_duration_seconds,
    errors_total
)


@dataclass
class PerformanceSnapshot:
    """Performance metrics snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    active_connections: int = 0
    requests_per_second: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0


class PerformanceMonitor:
    """System performance monitoring."""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self._snapshots: deque = deque(maxlen=history_size)
        self._request_times: deque = deque(maxlen=10000)
        self._error_count = 0
        self._total_requests = 0
        self._start_time = datetime.utcnow()

    def record_request(self, duration_ms: float, is_error: bool = False):
        """Record a request for performance tracking."""
        self._request_times.append({
            "timestamp": datetime.utcnow(),
            "duration_ms": duration_ms,
            "is_error": is_error
        })
        self._total_requests += 1
        if is_error:
            self._error_count += 1

    def take_snapshot(self) -> PerformanceSnapshot:
        """Take a performance snapshot."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Calculate request metrics
        now = datetime.utcnow()
        recent_requests = [
            r for r in self._request_times
            if (now - r["timestamp"]).seconds < 60
        ]

        rps = len(recent_requests) / 60.0 if recent_requests else 0
        avg_response_time = (
            sum(r["duration_ms"] for r in recent_requests) / len(recent_requests)
            if recent_requests else 0
        )
        error_rate = (
            sum(1 for r in recent_requests if r["is_error"]) / len(recent_requests)
            if recent_requests else 0
        )

        snapshot = PerformanceSnapshot(
            timestamp=now,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_percent=disk.percent,
            requests_per_second=rps,
            avg_response_time_ms=avg_response_time,
            error_rate=error_rate
        )

        self._snapshots.append(snapshot)
        return snapshot

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        snapshot = self.take_snapshot()
        uptime = datetime.utcnow() - self._start_time

        return {
            "uptime_seconds": uptime.total_seconds(),
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "memory_used_mb": snapshot.memory_used_mb,
            "disk_percent": snapshot.disk_percent,
            "requests_per_second": snapshot.requests_per_second,
            "avg_response_time_ms": snapshot.avg_response_time_ms,
            "error_rate": snapshot.error_rate,
            "total_requests": self._total_requests,
            "total_errors": self._error_count
        }

    def get_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get performance history for the specified duration."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "cpu_percent": s.cpu_percent,
                "memory_percent": s.memory_percent,
                "requests_per_second": s.requests_per_second,
                "avg_response_time_ms": s.avg_response_time_ms,
                "error_rate": s.error_rate
            }
            for s in self._snapshots
            if s.timestamp > cutoff
        ]

    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check performance thresholds and return warnings."""
        warnings = []
        stats = self.get_current_stats()

        if stats["cpu_percent"] > 80:
            warnings.append({
                "type": "cpu",
                "level": "warning" if stats["cpu_percent"] < 90 else "critical",
                "message": f"High CPU usage: {stats['cpu_percent']:.1f}%"
            })

        if stats["memory_percent"] > 80:
            warnings.append({
                "type": "memory",
                "level": "warning" if stats["memory_percent"] < 90 else "critical",
                "message": f"High memory usage: {stats['memory_percent']:.1f}%"
            })

        if stats["disk_percent"] > 80:
            warnings.append({
                "type": "disk",
                "level": "warning" if stats["disk_percent"] < 90 else "critical",
                "message": f"High disk usage: {stats['disk_percent']:.1f}%"
            })

        if stats["error_rate"] > 0.05:
            warnings.append({
                "type": "error_rate",
                "level": "warning" if stats["error_rate"] < 0.1 else "critical",
                "message": f"High error rate: {stats['error_rate']*100:.1f}%"
            })

        if stats["avg_response_time_ms"] > 1000:
            warnings.append({
                "type": "response_time",
                "level": "warning" if stats["avg_response_time_ms"] < 2000 else "critical",
                "message": f"Slow response time: {stats['avg_response_time_ms']:.0f}ms"
            })

        return warnings


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.start_time = None
        self.is_error = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.is_error = exc_type is not None
        self.monitor.record_request(duration_ms, self.is_error)
        return False


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
