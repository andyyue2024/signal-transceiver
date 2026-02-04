"""
Enhanced health check module.
Provides detailed system health information for load balancers and monitoring.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import psutil
from loguru import logger


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Enhanced health check service."""

    def __init__(self):
        self._start_time = datetime.utcnow()
        self._checks: Dict[str, callable] = {}

    def register_check(self, name: str, check_func: callable):
        """Register a health check function."""
        self._checks[name] = check_func

    @property
    def uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return (datetime.utcnow() - self._start_time).total_seconds()

    @property
    def uptime_human(self) -> str:
        """Get human-readable uptime."""
        seconds = self.uptime_seconds
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if not parts:
            parts.append(f"{int(seconds)}s")

        return " ".join(parts)

    async def check_database(self, db_session) -> ComponentHealth:
        """Check database connectivity."""
        start = datetime.utcnow()
        try:
            # Simple query to test connection
            await db_session.execute("SELECT 1")
            latency = (datetime.utcnow() - start).total_seconds() * 1000

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY if latency < 100 else HealthStatus.DEGRADED,
                message="Database is responsive",
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )

    def check_memory(self) -> ComponentHealth:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        used_percent = memory.percent

        if used_percent < 80:
            status = HealthStatus.HEALTHY
            message = "Memory usage normal"
        elif used_percent < 90:
            status = HealthStatus.DEGRADED
            message = "Memory usage high"
        else:
            status = HealthStatus.UNHEALTHY
            message = "Memory usage critical"

        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            details={
                "used_percent": used_percent,
                "available_mb": round(memory.available / (1024 * 1024), 2),
                "total_mb": round(memory.total / (1024 * 1024), 2)
            }
        )

    def check_disk(self, path: str = "/") -> ComponentHealth:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage(path)
            used_percent = disk.percent

            if used_percent < 80:
                status = HealthStatus.HEALTHY
                message = "Disk usage normal"
            elif used_percent < 90:
                status = HealthStatus.DEGRADED
                message = "Disk usage high"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Disk usage critical"

            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "used_percent": used_percent,
                    "free_gb": round(disk.free / (1024 ** 3), 2),
                    "total_gb": round(disk.total / (1024 ** 3), 2)
                }
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {str(e)}"
            )

    def check_cpu(self) -> ComponentHealth:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=0.1)

        if cpu_percent < 70:
            status = HealthStatus.HEALTHY
            message = "CPU usage normal"
        elif cpu_percent < 90:
            status = HealthStatus.DEGRADED
            message = "CPU usage high"
        else:
            status = HealthStatus.UNHEALTHY
            message = "CPU usage critical"

        return ComponentHealth(
            name="cpu",
            status=status,
            message=message,
            details={
                "used_percent": cpu_percent,
                "cpu_count": psutil.cpu_count()
            }
        )

    async def run_all_checks(self, db_session=None) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        components = []

        # System checks
        components.append(self.check_memory())
        components.append(self.check_disk())
        components.append(self.check_cpu())

        # Database check
        if db_session:
            components.append(await self.check_database(db_session))

        # Run custom checks
        for name, check_func in self._checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                components.append(result)
            except Exception as e:
                components.append(ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}"
                ))

        # Determine overall status
        unhealthy = any(c.status == HealthStatus.UNHEALTHY for c in components)
        degraded = any(c.status == HealthStatus.DEGRADED for c in components)

        if unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": self.uptime_human,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                    "details": c.details
                }
                for c in components
            ]
        }

    def get_liveness(self) -> Dict[str, Any]:
        """
        Liveness probe - is the application running?
        Used by Kubernetes liveness probe.
        """
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_readiness(self) -> Dict[str, Any]:
        """
        Readiness probe - is the application ready to serve traffic?
        Used by Kubernetes readiness probe.
        """
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)

        ready = memory.percent < 95 and cpu < 95

        return {
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "memory_ok": memory.percent < 95,
                "cpu_ok": cpu < 95
            }
        }


# Global health checker instance
health_checker = HealthChecker()
