"""
Simple message queue for async task processing.
Provides in-memory queue with optional persistence.
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from loguru import logger


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Task:
    """A task in the queue."""
    id: str
    name: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retries": self.retries
        }


class MessageQueue:
    """In-memory message queue with async processing."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._queues: Dict[str, deque] = {"default": deque()}
        self._handlers: Dict[str, Callable] = {}
        self._tasks: Dict[str, Task] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._initialized = True

    def create_queue(self, name: str):
        """Create a named queue."""
        if name not in self._queues:
            self._queues[name] = deque()

    def register_handler(self, task_name: str, handler: Callable):
        """Register a handler for a task type."""
        self._handlers[task_name] = handler
        logger.info(f"Registered handler for task: {task_name}")

    def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        queue_name: str = "default",
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3
    ) -> Task:
        """Add a task to the queue."""
        task = Task(
            id=str(uuid.uuid4()),
            name=task_name,
            payload=payload,
            priority=priority,
            max_retries=max_retries
        )

        self._tasks[task.id] = task

        if queue_name not in self._queues:
            self._queues[queue_name] = deque()

        # Insert by priority (higher priority first)
        queue = self._queues[queue_name]
        inserted = False
        for i, existing_id in enumerate(queue):
            existing = self._tasks.get(existing_id)
            if existing and task.priority.value > existing.priority.value:
                queue.insert(i, task.id)
                inserted = True
                break

        if not inserted:
            queue.append(task.id)

        logger.debug(f"Enqueued task {task.id}: {task_name}")
        return task

    def dequeue(self, queue_name: str = "default") -> Optional[Task]:
        """Get the next task from the queue."""
        if queue_name not in self._queues or not self._queues[queue_name]:
            return None

        task_id = self._queues[queue_name].popleft()
        return self._tasks.get(task_id)

    async def process_task(self, task: Task) -> bool:
        """Process a single task."""
        handler = self._handlers.get(task.name)
        if not handler:
            logger.warning(f"No handler for task: {task.name}")
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for {task.name}"
            return False

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task.payload)
            else:
                result = handler(task.payload)

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} completed")
            return True

        except Exception as e:
            task.retries += 1
            task.error = str(e)

            if task.retries < task.max_retries:
                task.status = TaskStatus.PENDING
                # Re-queue
                self._queues["default"].append(task.id)
                logger.warning(f"Task {task.id} failed, retry {task.retries}/{task.max_retries}")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.id} failed permanently: {e}")

            return False

    async def worker(self, queue_name: str = "default"):
        """Worker coroutine that processes tasks."""
        while self._running:
            task = self.dequeue(queue_name)
            if task:
                await self.process_task(task)
            else:
                await asyncio.sleep(0.1)

    async def start(self, num_workers: int = 2, queue_name: str = "default"):
        """Start queue workers."""
        if self._running:
            return

        self._running = True
        for i in range(num_workers):
            worker_task = asyncio.create_task(self.worker(queue_name))
            self._workers.append(worker_task)

        logger.info(f"Started {num_workers} queue workers")

    async def stop(self):
        """Stop all workers."""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        self._workers.clear()
        logger.info("Stopped queue workers")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_queue_size(self, queue_name: str = "default") -> int:
        """Get queue size."""
        return len(self._queues.get(queue_name, []))

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        by_status = {}
        for task in self._tasks.values():
            by_status[task.status.value] = by_status.get(task.status.value, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "by_status": by_status,
            "queues": {name: len(q) for name, q in self._queues.items()},
            "workers": len(self._workers),
            "running": self._running
        }

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """Clear completed tasks older than specified hours."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        to_remove = [
            tid for tid, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            and task.completed_at and task.completed_at < cutoff
        ]

        for tid in to_remove:
            del self._tasks[tid]

        return len(to_remove)


# Global instance
message_queue = MessageQueue()


# Common task handlers
async def send_email_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Example email sending task."""
    logger.info(f"Sending email to {payload.get('to')}")
    # Simulate email sending
    await asyncio.sleep(0.1)
    return {"sent": True, "to": payload.get("to")}


async def generate_report_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Example report generation task."""
    logger.info(f"Generating report: {payload.get('type')}")
    await asyncio.sleep(0.5)
    return {"generated": True, "type": payload.get("type")}


async def webhook_delivery_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Webhook delivery task."""
    import aiohttp
    url = payload.get("url")
    data = payload.get("data")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, timeout=30) as response:
            return {"status_code": response.status, "success": response.status < 400}


# Register default handlers
message_queue.register_handler("send_email", send_email_task)
message_queue.register_handler("generate_report", generate_report_task)
message_queue.register_handler("webhook_delivery", webhook_delivery_task)
