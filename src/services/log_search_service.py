"""
Log search and management service.
Provides log querying and filtering capabilities.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
from loguru import logger


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """A log entry."""
    id: str
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = ""
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "metadata": self.metadata
        }


@dataclass
class LogSearchQuery:
    """Search query for logs."""
    level: Optional[LogLevel] = None
    source: Optional[str] = None
    user_id: Optional[int] = None
    keyword: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class LogSearchService:
    """Service for searching and managing logs."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._logs: List[LogEntry] = []
        self._counter = 0
        self._max_logs = 10000
        self._initialized = True
    
    def _generate_id(self) -> str:
        self._counter += 1
        return f"LOG-{self._counter:010d}"
    
    def add(
        self,
        level: LogLevel,
        message: str,
        source: str = "",
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        """Add a log entry."""
        entry = LogEntry(
            id=self._generate_id(),
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            source=source,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        self._logs.append(entry)
        
        # Trim old logs
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        return entry
    
    def search(self, query: LogSearchQuery) -> List[LogEntry]:
        """Search logs with filters."""
        results = self._logs.copy()
        
        # Filter by level
        if query.level:
            results = [r for r in results if r.level == query.level]
        
        # Filter by source
        if query.source:
            results = [r for r in results if query.source.lower() in r.source.lower()]
        
        # Filter by user
        if query.user_id:
            results = [r for r in results if r.user_id == query.user_id]
        
        # Filter by keyword
        if query.keyword:
            pattern = re.compile(query.keyword, re.IGNORECASE)
            results = [r for r in results if pattern.search(r.message)]
        
        # Filter by time range
        if query.start_time:
            results = [r for r in results if r.timestamp >= query.start_time]
        if query.end_time:
            results = [r for r in results if r.timestamp <= query.end_time]
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        return results[query.offset:query.offset + query.limit]
    
    def get_by_id(self, log_id: str) -> Optional[LogEntry]:
        """Get a log entry by ID."""
        for log in self._logs:
            if log.id == log_id:
                return log
        return None
    
    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_logs = [l for l in self._logs if l.timestamp >= cutoff]
        
        by_level = {}
        by_source = {}
        
        for log in recent_logs:
            by_level[log.level.value] = by_level.get(log.level.value, 0) + 1
            if log.source:
                by_source[log.source] = by_source.get(log.source, 0) + 1
        
        error_count = by_level.get("ERROR", 0) + by_level.get("CRITICAL", 0)
        
        return {
            "total_logs": len(self._logs),
            "recent_logs": len(recent_logs),
            "by_level": by_level,
            "by_source": dict(sorted(by_source.items(), key=lambda x: -x[1])[:10]),
            "error_count": error_count,
            "hours_analyzed": hours
        }
    
    def cleanup(self, days: int = 7) -> int:
        """Remove logs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(self._logs)
        self._logs = [l for l in self._logs if l.timestamp >= cutoff]
        removed = original_count - len(self._logs)
        logger.info(f"Cleaned up {removed} old log entries")
        return removed
    
    def export_logs(
        self,
        query: Optional[LogSearchQuery] = None,
        format: str = "json"
    ) -> List[Dict[str, Any]]:
        """Export logs as list of dicts."""
        if query:
            logs = self.search(query)
        else:
            logs = sorted(self._logs, key=lambda x: x.timestamp, reverse=True)
        
        return [log.to_dict() for log in logs]
    
    # Convenience methods
    def debug(self, message: str, **kwargs):
        return self.add(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        return self.add(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        return self.add(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        return self.add(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        return self.add(LogLevel.CRITICAL, message, **kwargs)


# Global instance
log_search_service = LogSearchService()
