"""
Pydantic schemas for health check endpoints
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Basic health status schema"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ComponentHealth(BaseModel):
    """Individual component health schema"""
    name: str = Field(..., description="Component name")
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Component status")
    message: str | None = Field(None, description="Status message")
    response_time_ms: float | None = Field(None, description="Component response time in milliseconds")
    last_check: datetime = Field(..., description="Last health check timestamp")
    error_count: int = Field(0, description="Number of recent errors")


class DatabaseHealth(ComponentHealth):
    """Database health schema"""
    connection_pool_active: int | None = Field(None, description="Active database connections")
    connection_pool_idle: int | None = Field(None, description="Idle database connections")
    query_time_avg_ms: float | None = Field(None, description="Average query time in milliseconds")


class ModelHealth(ComponentHealth):
    """Model health schema"""
    model_id: str = Field(..., description="Model identifier")
    load_status: Literal["loaded", "loading", "unloaded", "error"] = Field(..., description="Model load status")
    memory_usage_mb: float | None = Field(None, description="Model memory usage in MB")
    last_inference_time: datetime | None = Field(None, description="Last inference timestamp")
    inference_count: int = Field(0, description="Total inference count")
    average_inference_time_ms: float | None = Field(None, description="Average inference time in milliseconds")


class SystemHealth(ComponentHealth):
    """System health schema"""
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float | None = Field(None, description="Disk usage percentage")
    gpu_usage_percent: float | None = Field(None, description="GPU usage percentage")
    thermal_state: Literal["nominal", "fair", "serious", "critical"] = Field("nominal", description="Thermal state")
    load_average: list[float] = Field(..., description="System load average")


class MLXHealth(ComponentHealth):
    """MLX framework health schema"""
    version: str = Field(..., description="MLX version")
    metal_available: bool = Field(..., description="Whether Metal is available")
    unified_memory_gb: float | None = Field(None, description="Unified memory available in GB")
    gpu_memory_usage_mb: float | None = Field(None, description="GPU memory usage in MB")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response schema"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")

    # Component health
    components: list[ComponentHealth] = Field(..., description="Component health status")
    system: SystemHealth = Field(..., description="System health")
    models: list[ModelHealth] = Field(..., description="Model health status")
    mlx: MLXHealth | None = Field(None, description="MLX framework health")
    database: DatabaseHealth | None = Field(None, description="Database health")

    # Performance metrics
    requests_per_second: float | None = Field(None, description="Current requests per second")
    average_response_time_ms: float | None = Field(None, description="Average response time in milliseconds")
    error_rate_percent: float | None = Field(None, description="Error rate percentage")

    # Resource limits
    memory_limit_mb: float | None = Field(None, description="Memory limit in MB")
    cpu_limit_percent: float | None = Field(None, description="CPU limit percentage")

    # Health score
    health_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score out of 100")


class ReadinessResponse(BaseModel):
    """Readiness probe response schema"""
    ready: bool = Field(..., description="Whether the service is ready to serve requests")
    timestamp: datetime = Field(..., description="Readiness check timestamp")
    checks: dict[str, bool] = Field(..., description="Individual readiness checks")
    message: str | None = Field(None, description="Readiness message")


class LivenessResponse(BaseModel):
    """Liveness probe response schema"""
    alive: bool = Field(..., description="Whether the service is alive")
    timestamp: datetime = Field(..., description="Liveness check timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")


class HealthMetrics(BaseModel):
    """Health metrics for monitoring schema"""
    timestamp: datetime = Field(..., description="Metrics timestamp")

    # Request metrics
    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    requests_per_minute: float = Field(..., description="Requests per minute")

    # Response time metrics
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    p50_response_time_ms: float = Field(..., description="50th percentile response time")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    p99_response_time_ms: float = Field(..., description="99th percentile response time")

    # Error metrics
    error_rate_percent: float = Field(..., ge=0.0, le=100.0, description="Error rate percentage")
    error_count_5min: int = Field(..., description="Error count in last 5 minutes")

    # Resource metrics
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_usage_percent: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")

    # Model metrics
    loaded_models_count: int = Field(..., description="Number of loaded models")
    total_inferences: int = Field(..., description="Total number of inferences")
    avg_inference_time_ms: float = Field(..., description="Average inference time in milliseconds")

    # Connection metrics
    active_connections: int = Field(..., description="Number of active connections")
    websocket_connections: int = Field(..., description="Number of WebSocket connections")


class AlertRule(BaseModel):
    """Health alert rule schema"""
    name: str = Field(..., description="Alert rule name")
    metric: str = Field(..., description="Metric to monitor")
    threshold: float = Field(..., description="Alert threshold")
    operator: Literal["gt", "lt", "eq", "gte", "lte"] = Field(..., description="Comparison operator")
    severity: Literal["info", "warning", "error", "critical"] = Field(..., description="Alert severity")
    description: str = Field(..., description="Alert description")
    enabled: bool = Field(True, description="Whether the alert rule is enabled")


class Alert(BaseModel):
    """Health alert schema"""
    id: str = Field(..., description="Alert ID")
    rule_name: str = Field(..., description="Alert rule name")
    severity: Literal["info", "warning", "error", "critical"] = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    metric_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Alert threshold")
    timestamp: datetime = Field(..., description="Alert timestamp")
    resolved: bool = Field(False, description="Whether the alert is resolved")
    resolved_at: datetime | None = Field(None, description="Alert resolution timestamp")


class HealthConfiguration(BaseModel):
    """Health check configuration schema"""
    check_interval_seconds: int = Field(30, ge=5, le=300, description="Health check interval in seconds")
    unhealthy_threshold: int = Field(3, ge=1, le=10, description="Number of failed checks before marking unhealthy")
    timeout_seconds: int = Field(10, ge=1, le=60, description="Health check timeout in seconds")

    # Component-specific settings
    check_models: bool = Field(True, description="Whether to check model health")
    check_system: bool = Field(True, description="Whether to check system health")
    check_mlx: bool = Field(True, description="Whether to check MLX health")

    # Alert settings
    enable_alerts: bool = Field(True, description="Whether to enable health alerts")
    alert_rules: list[AlertRule] = Field(default_factory=list, description="List of alert rules")

    # Metrics retention
    metrics_retention_hours: int = Field(24, ge=1, le=168, description="Metrics retention in hours")
