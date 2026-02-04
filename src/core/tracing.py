"""
Simple request tracing for distributed systems.
Provides request ID tracking and span management.
"""
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from contextvars import ContextVar
from loguru import logger


# Context variable for current trace
current_trace: ContextVar[Optional["Trace"]] = ContextVar("current_trace", default=None)
current_span: ContextVar[Optional["Span"]] = ContextVar("current_span", default=None)


class SpanKind(str, Enum):
    """Type of span."""
    SERVER = "server"
    CLIENT = "client"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span execution status."""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class Span:
    """A single span in a trace."""
    span_id: str
    trace_id: str
    name: str
    kind: SpanKind = SpanKind.INTERNAL
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })

    def end(self, status: SpanStatus = SpanStatus.OK):
        """End the span."""
        self.end_time = time.time()
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "kind": self.kind.value,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events
        }


@dataclass
class Trace:
    """A complete trace containing multiple spans."""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_span(self, span: Span):
        self.spans.append(span)

    def get_root_span(self) -> Optional[Span]:
        for span in self.spans:
            if span.parent_span_id is None:
                return span
        return self.spans[0] if self.spans else None

    @property
    def duration_ms(self) -> Optional[float]:
        root = self.get_root_span()
        return root.duration_ms if root else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "created_at": self.created_at.isoformat(),
            "duration_ms": self.duration_ms,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans]
        }


class Tracer:
    """Simple tracer for request tracking."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._traces: Dict[str, Trace] = {}
        self._max_traces = 1000
        self._initialized = True

    def _generate_id(self) -> str:
        return uuid.uuid4().hex[:16]

    def start_trace(self, name: str = "request") -> Trace:
        """Start a new trace."""
        trace_id = self._generate_id()
        trace = Trace(trace_id=trace_id)
        self._traces[trace_id] = trace
        current_trace.set(trace)

        # Create root span
        span = self.start_span(name, kind=SpanKind.SERVER)

        # Cleanup old traces
        if len(self._traces) > self._max_traces:
            self._cleanup_old_traces()

        return trace

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[Span] = None
    ) -> Span:
        """Start a new span."""
        trace = current_trace.get()
        if not trace:
            trace = self.start_trace()

        parent_span = parent or current_span.get()

        span = Span(
            span_id=self._generate_id(),
            trace_id=trace.trace_id,
            name=name,
            kind=kind,
            parent_span_id=parent_span.span_id if parent_span else None
        )

        trace.add_span(span)
        current_span.set(span)

        return span

    def end_span(self, span: Optional[Span] = None, status: SpanStatus = SpanStatus.OK):
        """End a span."""
        span = span or current_span.get()
        if span:
            span.end(status)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_current_trace(self) -> Optional[Trace]:
        """Get the current trace."""
        return current_trace.get()

    def get_current_span(self) -> Optional[Span]:
        """Get the current span."""
        return current_span.get()

    def _cleanup_old_traces(self):
        """Remove old traces."""
        if len(self._traces) <= self._max_traces // 2:
            return

        # Sort by creation time and remove oldest
        sorted_traces = sorted(
            self._traces.items(),
            key=lambda x: x[1].created_at
        )

        to_remove = len(self._traces) - self._max_traces // 2
        for trace_id, _ in sorted_traces[:to_remove]:
            del self._traces[trace_id]

    def list_traces(self, limit: int = 50) -> List[Trace]:
        """List recent traces."""
        traces = sorted(
            self._traces.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return traces[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        traces = list(self._traces.values())

        total_spans = sum(len(t.spans) for t in traces)
        durations = [t.duration_ms for t in traces if t.duration_ms]

        return {
            "total_traces": len(traces),
            "total_spans": total_spans,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0
        }

    def clear(self):
        """Clear all traces."""
        self._traces.clear()
        current_trace.set(None)
        current_span.set(None)


# Global tracer instance
tracer = Tracer()


# Context manager for spans
class SpanContext:
    """Context manager for creating spans."""

    def __init__(self, name: str, kind: SpanKind = SpanKind.INTERNAL):
        self.name = name
        self.kind = kind
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        self.span = tracer.start_span(self.name, self.kind)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            status = SpanStatus.ERROR if exc_type else SpanStatus.OK
            if exc_val:
                self.span.set_attribute("error.message", str(exc_val))
            tracer.end_span(self.span, status)
        return False


# Decorator for tracing functions
def trace(name: Optional[str] = None, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to trace a function."""
    def decorator(func):
        span_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with SpanContext(span_name, kind) as span:
                    span.set_attribute("function", func.__name__)
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with SpanContext(span_name, kind) as span:
                    span.set_attribute("function", func.__name__)
                    return func(*args, **kwargs)
            return sync_wrapper

    return decorator


import asyncio
