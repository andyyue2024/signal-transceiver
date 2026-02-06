"""
Prometheus metrics for monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time

# Application info
app_info = Info('signal_transceiver', 'Application information')
app_info.info({
    'version': '1.0.0',
    'framework': 'fastapi'
})

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Business metrics
data_uploads_total = Counter(
    'data_uploads_total',
    'Total number of data uploads',
    ['user_id', 'strategy_id', 'type']
)

subscriptions_active = Gauge(
    'subscriptions_active',
    'Number of active subscriptions',
    ['subscription_type']
)

websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['operation']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['result']  # success, failure
)

api_key_validations_total = Counter(
    'api_key_validations_total',
    'Total API key validations',
    ['result']
)


def track_request_metrics(method: str, endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                errors_total.labels(error_type=type(e).__name__, endpoint=endpoint).inc()
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        return wrapper
    return decorator


def get_metrics():
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_metrics_content_type():
    """Get content type for metrics response."""
    return CONTENT_TYPE_LATEST
