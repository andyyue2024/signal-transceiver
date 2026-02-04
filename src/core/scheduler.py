"""
Scheduled tasks for periodic operations.
Implements scheduled report generation, cleanup, and notification tasks.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading
from loguru import logger


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Scheduled task definition."""
    id: str
    name: str
    func: Callable
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)


class Scheduler:
    """Task scheduler for periodic operations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._initialized = True

    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        interval_seconds: int,
        enabled: bool = True,
        **kwargs
    ) -> ScheduledTask:
        """Add a scheduled task."""
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            enabled=enabled,
            next_run=datetime.utcnow() + timedelta(seconds=interval_seconds),
            kwargs=kwargs
        )
        self._tasks[task_id] = task
        logger.info(f"Scheduled task added: {name} (every {interval_seconds}s)")
        return task

    def remove_task(self, task_id: str):
        """Remove a scheduled task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Scheduled task removed: {task_id}")

    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True

    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[ScheduledTask]:
        """List all tasks."""
        return list(self._tasks.values())

    async def _run_task(self, task: ScheduledTask):
        """Run a single task."""
        if not task.enabled:
            return

        task.status = TaskStatus.RUNNING
        task.last_run = datetime.utcnow()

        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func(**task.kwargs)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: task.func(**task.kwargs)
                )

            task.status = TaskStatus.COMPLETED
            task.run_count += 1
            task.last_error = None
            logger.debug(f"Task {task.name} completed successfully")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            logger.error(f"Task {task.name} failed: {e}")

        finally:
            task.next_run = datetime.utcnow() + timedelta(seconds=task.interval_seconds)

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler started")

        while self._running:
            now = datetime.utcnow()

            for task in self._tasks.values():
                if task.enabled and task.next_run and now >= task.next_run:
                    if task.status != TaskStatus.RUNNING:
                        asyncio.create_task(self._run_task(task))

            await asyncio.sleep(1)

        logger.info("Scheduler stopped")

    def start(self):
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._scheduler_loop())

    def stop(self):
        """Stop the scheduler."""
        self._running = False

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "task_count": len(self._tasks),
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "enabled": t.enabled,
                    "status": t.status.value,
                    "interval_seconds": t.interval_seconds,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "next_run": t.next_run.isoformat() if t.next_run else None,
                    "run_count": t.run_count,
                    "error_count": t.error_count
                }
                for t in self._tasks.values()
            ]
        }


# Global scheduler instance
scheduler = Scheduler()


# ============ Predefined Tasks ============

async def task_cleanup_logs(days: int = 7):
    """Clean up old log entries from database."""
    from src.config.database import async_session_maker
    from src.models.log import Log
    from sqlalchemy import delete

    cutoff = datetime.utcnow() - timedelta(days=days)

    async with async_session_maker() as session:
        await session.execute(
            delete(Log).where(Log.created_at < cutoff)
        )
        await session.commit()

    logger.info(f"Cleaned up logs older than {days} days")


async def task_generate_daily_report():
    """Generate and send daily report."""
    from src.config.database import async_session_maker
    from src.models.data import Data
    from src.report.generator import report_service
    from src.monitor.dashboard import system_dashboard
    from sqlalchemy import select, func
    from datetime import date

    async with async_session_maker() as session:
        # Get today's data count
        today = date.today()
        result = await session.execute(
            select(func.count(Data.id)).where(Data.execute_date == today)
        )
        data_count = result.scalar() or 0

    summary = system_dashboard.get_summary_report()

    logger.info(f"Daily report generated: {data_count} records today")

    # Here you would send the report via email/webhook
    # await send_report_notification(summary)


async def task_check_system_health():
    """Check system health and trigger alerts if needed."""
    from src.monitor.performance import performance_monitor
    from src.monitor.alerts import alert_manager, AlertLevel

    warnings = performance_monitor.check_thresholds()

    for warning in warnings:
        if warning["level"] == "critical":
            await alert_manager.trigger(
                title=f"系统告警: {warning['type']}",
                message=warning["message"],
                level=AlertLevel.CRITICAL,
                source="health_check"
            )


async def task_backup_database():
    """Backup SQLite database."""
    import shutil
    import os
    from src.config.settings import settings

    if "sqlite" not in settings.database_url:
        logger.info("Database backup skipped: not using SQLite")
        return

    # Extract database path from URL
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    if not os.path.exists(db_path):
        logger.warning(f"Database file not found: {db_path}")
        return

    # Create backup directory
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"app_backup_{timestamp}.db")

    shutil.copy2(db_path, backup_path)
    logger.info(f"Database backed up to: {backup_path}")

    # Clean old backups (keep last 7)
    backups = sorted([
        f for f in os.listdir(backup_dir)
        if f.startswith("app_backup_") and f.endswith(".db")
    ], reverse=True)

    for old_backup in backups[7:]:
        os.remove(os.path.join(backup_dir, old_backup))
        logger.info(f"Removed old backup: {old_backup}")


def setup_default_tasks():
    """Setup default scheduled tasks."""
    # Log cleanup - every 24 hours
    scheduler.add_task(
        task_id="cleanup_logs",
        name="清理日志",
        func=task_cleanup_logs,
        interval_seconds=86400,  # 24 hours
        days=7
    )

    # Daily report - every 24 hours
    scheduler.add_task(
        task_id="daily_report",
        name="每日报告",
        func=task_generate_daily_report,
        interval_seconds=86400  # 24 hours
    )

    # Health check - every 5 minutes
    scheduler.add_task(
        task_id="health_check",
        name="健康检查",
        func=task_check_system_health,
        interval_seconds=300  # 5 minutes
    )

    # Database backup - every 6 hours
    scheduler.add_task(
        task_id="database_backup",
        name="数据库备份",
        func=task_backup_database,
        interval_seconds=21600  # 6 hours
    )
