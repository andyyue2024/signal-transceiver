"""
Tests for message queue and tracing modules.
"""
import pytest
import asyncio
from datetime import datetime

from src.core.message_queue import (
    MessageQueue, Task, TaskStatus, TaskPriority
)
from src.core.tracing import (
    Tracer, Span, Trace, SpanKind, SpanStatus, SpanContext
)


class TestMessageQueue:
    """Tests for MessageQueue."""

    @pytest.fixture
    def queue(self):
        q = MessageQueue.__new__(MessageQueue)
        q._queues = {"default": []}
        q._handlers = {}
        q._tasks = {}
        q._running = False
        q._workers = []
        q._initialized = True
        from collections import deque
        q._queues = {"default": deque()}
        return q

    def test_enqueue_task(self, queue):
        """Test enqueuing a task."""
        task = queue.enqueue("test_task", {"key": "value"})

        assert task.id is not None
        assert task.name == "test_task"
        assert task.status == TaskStatus.PENDING
        assert task.payload == {"key": "value"}

    def test_dequeue_task(self, queue):
        """Test dequeuing a task."""
        queue.enqueue("task1", {})
        queue.enqueue("task2", {})

        task = queue.dequeue()
        assert task.name == "task1"

        task = queue.dequeue()
        assert task.name == "task2"

    def test_priority_ordering(self, queue):
        """Test that higher priority tasks are processed first."""
        queue.enqueue("low", {}, priority=TaskPriority.LOW)
        queue.enqueue("high", {}, priority=TaskPriority.HIGH)
        queue.enqueue("normal", {}, priority=TaskPriority.NORMAL)

        # High priority should come first
        task = queue.dequeue()
        assert task.name == "high"

    def test_register_handler(self, queue):
        """Test registering a handler."""
        def handler(payload):
            return "done"

        queue.register_handler("test", handler)
        assert "test" in queue._handlers

    @pytest.mark.asyncio
    async def test_process_task(self, queue):
        """Test processing a task."""
        result_holder = {}

        async def handler(payload):
            result_holder["value"] = payload["value"]
            return {"success": True}

        queue.register_handler("test", handler)
        task = queue.enqueue("test", {"value": 42})

        success = await queue.process_task(task)

        assert success is True
        assert task.status == TaskStatus.COMPLETED
        assert result_holder["value"] == 42

    @pytest.mark.asyncio
    async def test_task_failure_retry(self, queue):
        """Test task retry on failure."""
        call_count = 0

        async def failing_handler(payload):
            nonlocal call_count
            call_count += 1
            raise Exception("Failed!")

        queue.register_handler("fail", failing_handler)
        task = queue.enqueue("fail", {}, max_retries=3)

        await queue.process_task(task)

        assert task.retries == 1
        assert task.status == TaskStatus.PENDING  # Should be re-queued

    def test_get_stats(self, queue):
        """Test getting queue statistics."""
        queue.enqueue("task1", {})
        queue.enqueue("task2", {})

        stats = queue.get_stats()

        assert stats["total_tasks"] == 2
        assert "default" in stats["queues"]

    def test_get_queue_size(self, queue):
        """Test getting queue size."""
        assert queue.get_queue_size() == 0

        queue.enqueue("task1", {})
        queue.enqueue("task2", {})

        assert queue.get_queue_size() == 2


class TestTracer:
    """Tests for Tracer."""

    @pytest.fixture
    def tracer(self):
        t = Tracer.__new__(Tracer)
        t._traces = {}
        t._max_traces = 1000
        t._initialized = True
        return t

    def test_start_trace(self, tracer):
        """Test starting a trace."""
        trace = tracer.start_trace("test")

        assert trace.trace_id is not None
        assert len(trace.spans) == 1  # Root span
        assert trace.spans[0].name == "test"

    def test_start_span(self, tracer):
        """Test starting a span."""
        tracer.start_trace("root")
        span = tracer.start_span("child")

        assert span.span_id is not None
        assert span.name == "child"
        assert span.parent_span_id is not None

    def test_end_span(self, tracer):
        """Test ending a span."""
        tracer.start_trace("test")
        span = tracer.start_span("child")

        tracer.end_span(span, SpanStatus.OK)

        assert span.end_time is not None
        assert span.status == SpanStatus.OK
        assert span.duration_ms is not None

    def test_span_attributes(self, tracer):
        """Test setting span attributes."""
        tracer.start_trace("test")
        span = tracer.start_span("child")

        span.set_attribute("key", "value")
        span.set_attribute("number", 42)

        assert span.attributes["key"] == "value"
        assert span.attributes["number"] == 42

    def test_span_events(self, tracer):
        """Test adding span events."""
        tracer.start_trace("test")
        span = tracer.start_span("child")

        span.add_event("event1", {"detail": "info"})

        assert len(span.events) == 1
        assert span.events[0]["name"] == "event1"

    def test_get_trace(self, tracer):
        """Test getting a trace by ID."""
        trace = tracer.start_trace("test")

        result = tracer.get_trace(trace.trace_id)
        assert result is not None
        assert result.trace_id == trace.trace_id

    def test_list_traces(self, tracer):
        """Test listing traces."""
        tracer.start_trace("trace1")
        tracer.start_trace("trace2")
        tracer.start_trace("trace3")

        traces = tracer.list_traces(limit=2)
        assert len(traces) == 2

    def test_get_stats(self, tracer):
        """Test getting tracer statistics."""
        tracer.start_trace("test")
        tracer.start_span("span1")
        tracer.start_span("span2")

        stats = tracer.get_stats()

        assert stats["total_traces"] >= 1
        assert stats["total_spans"] >= 2

    def test_span_context(self, tracer):
        """Test SpanContext context manager."""
        tracer.start_trace("test")

        with SpanContext("operation") as span:
            span.set_attribute("test", True)

        assert span.status == SpanStatus.OK
        assert span.end_time is not None

    def test_span_to_dict(self, tracer):
        """Test span serialization."""
        tracer.start_trace("test")
        span = tracer.start_span("child")
        span.set_attribute("key", "value")
        tracer.end_span(span)

        data = span.to_dict()

        assert data["name"] == "child"
        assert data["status"] == "ok"
        assert "duration_ms" in data


class TestTask:
    """Tests for Task dataclass."""

    def test_task_to_dict(self):
        """Test task serialization."""
        task = Task(
            id="test-123",
            name="test_task",
            payload={"key": "value"},
            priority=TaskPriority.HIGH
        )

        data = task.to_dict()

        assert data["id"] == "test-123"
        assert data["name"] == "test_task"
        assert data["priority"] == TaskPriority.HIGH.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
