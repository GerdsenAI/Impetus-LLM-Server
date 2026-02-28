"""
Pydantic schemas for hardware monitoring endpoints
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PerformanceModeRequest(BaseModel):
    """Performance mode request schema"""
    mode: Literal["efficiency", "balanced", "performance"] = Field(..., description="Performance mode to set")

    @classmethod
    @field_validator('mode')
    def validate_mode(cls, v):
        valid_modes = ["efficiency", "balanced", "performance"]
        if v not in valid_modes:
            raise ValueError(f"Mode must be one of: {', '.join(valid_modes)}")
        return v


class CPUInfo(BaseModel):
    """CPU information schema"""
    brand: str = Field(..., description="CPU brand/model")
    architecture: str = Field(..., description="CPU architecture")
    performance_cores: int = Field(..., description="Number of performance cores")
    efficiency_cores: int = Field(..., description="Number of efficiency cores")
    total_cores: int = Field(..., description="Total number of cores")
    base_frequency_ghz: float | None = Field(None, description="Base frequency in GHz")
    max_frequency_ghz: float | None = Field(None, description="Maximum frequency in GHz")


class MemoryInfo(BaseModel):
    """Memory information schema"""
    total_gb: float = Field(..., description="Total memory in GB")
    available_gb: float = Field(..., description="Available memory in GB")
    used_gb: float = Field(..., description="Used memory in GB")
    usage_percent: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    swap_total_gb: float | None = Field(None, description="Total swap memory in GB")
    swap_used_gb: float | None = Field(None, description="Used swap memory in GB")


class GPUInfo(BaseModel):
    """GPU information schema"""
    name: str = Field(..., description="GPU name")
    vendor: str = Field(..., description="GPU vendor")
    memory_gb: float | None = Field(None, description="GPU memory in GB")
    compute_units: int | None = Field(None, description="Number of compute units")
    metal_support: bool = Field(False, description="Whether Metal is supported")
    unified_memory: bool = Field(False, description="Whether unified memory is used")


class ThermalInfo(BaseModel):
    """Thermal information schema"""
    cpu_temperature_c: float | None = Field(None, description="CPU temperature in Celsius")
    gpu_temperature_c: float | None = Field(None, description="GPU temperature in Celsius")
    thermal_state: Literal["nominal", "fair", "serious", "critical"] = Field("nominal", description="Thermal state")
    fan_speed_rpm: int | None = Field(None, description="Fan speed in RPM")
    throttling: bool = Field(False, description="Whether thermal throttling is active")


class PowerInfo(BaseModel):
    """Power information schema"""
    battery_level_percent: float | None = Field(None, ge=0.0, le=100.0, description="Battery level percentage")
    is_charging: bool | None = Field(None, description="Whether device is charging")
    power_adapter_connected: bool | None = Field(None, description="Whether power adapter is connected")
    cpu_power_watts: float | None = Field(None, description="CPU power consumption in watts")
    gpu_power_watts: float | None = Field(None, description="GPU power consumption in watts")
    total_power_watts: float | None = Field(None, description="Total power consumption in watts")


class HardwareInfo(BaseModel):
    """Complete hardware information schema"""
    chip_type: str = Field(..., description="Chip type (e.g., M1, M2, M3, M4)")
    chip_variant: str | None = Field(None, description="Chip variant (Pro, Max, Ultra)")
    cpu: CPUInfo = Field(..., description="CPU information")
    memory: MemoryInfo = Field(..., description="Memory information")
    gpu: GPUInfo = Field(..., description="GPU information")
    thermal: ThermalInfo = Field(..., description="Thermal information")
    power: PowerInfo | None = Field(None, description="Power information")
    os_version: str = Field(..., description="Operating system version")
    mlx_version: str | None = Field(None, description="MLX framework version")
    python_version: str = Field(..., description="Python version")


class CPUMetrics(BaseModel):
    """CPU metrics schema"""
    usage_percent: float = Field(..., ge=0.0, le=100.0, description="Overall CPU usage percentage")
    performance_core_usage: list[float] = Field(..., description="Per-core usage for performance cores")
    efficiency_core_usage: list[float] = Field(..., description="Per-core usage for efficiency cores")
    frequency_ghz: list[float] = Field(..., description="Current frequency per core in GHz")
    load_average: list[float] = Field(..., description="System load average (1, 5, 15 minutes)")


class MetalMetrics(BaseModel):
    """Metal GPU metrics schema"""
    gpu_utilization_percent: float = Field(..., ge=0.0, le=100.0, description="GPU utilization percentage")
    memory_used_mb: float = Field(..., description="GPU memory used in MB")
    memory_total_mb: float = Field(..., description="Total GPU memory in MB")
    memory_usage_percent: float = Field(..., ge=0.0, le=100.0, description="GPU memory usage percentage")
    compute_units_active: int | None = Field(None, description="Number of active compute units")
    shader_utilization_percent: float | None = Field(None, ge=0.0, le=100.0, description="Shader utilization")
    bandwidth_utilization_percent: float | None = Field(None, ge=0.0, le=100.0, description="Memory bandwidth utilization")


class ProcessMetrics(BaseModel):
    """Process-level metrics schema"""
    pid: int = Field(..., description="Process ID")
    cpu_percent: float = Field(..., ge=0.0, description="Process CPU usage percentage")
    memory_mb: float = Field(..., description="Process memory usage in MB")
    memory_percent: float = Field(..., ge=0.0, le=100.0, description="Process memory usage percentage")
    threads: int = Field(..., description="Number of threads")
    file_descriptors: int = Field(..., description="Number of open file descriptors")
    uptime_seconds: float = Field(..., description="Process uptime in seconds")


class SystemMetrics(BaseModel):
    """Complete system metrics schema"""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryInfo = Field(..., description="Memory metrics")
    thermal: ThermalInfo = Field(..., description="Thermal metrics")
    power: PowerInfo | None = Field(None, description="Power metrics")
    metal: MetalMetrics | None = Field(None, description="Metal GPU metrics")
    process: ProcessMetrics = Field(..., description="Process metrics")
    disk_usage_percent: float | None = Field(None, ge=0.0, le=100.0, description="Disk usage percentage")
    network_io: dict[str, float] | None = Field(None, description="Network I/O statistics")


class OptimizationRecommendation(BaseModel):
    """Hardware optimization recommendation schema"""
    category: Literal["memory", "thermal", "performance", "power"] = Field(..., description="Recommendation category")
    priority: Literal["low", "medium", "high", "critical"] = Field(..., description="Recommendation priority")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation description")
    action: str | None = Field(None, description="Suggested action to take")
    impact: str | None = Field(None, description="Expected impact of the recommendation")
    automated: bool = Field(False, description="Whether this can be automated")


class OptimizationResponse(BaseModel):
    """Hardware optimization response schema"""
    recommendations: list[OptimizationRecommendation] = Field(..., description="List of recommendations")
    overall_health: Literal["excellent", "good", "fair", "poor", "critical"] = Field(..., description="Overall system health")
    performance_score: float = Field(..., ge=0.0, le=100.0, description="Performance score out of 100")
    thermal_score: float = Field(..., ge=0.0, le=100.0, description="Thermal health score out of 100")
    memory_score: float = Field(..., ge=0.0, le=100.0, description="Memory health score out of 100")
    estimated_performance_gain: float | None = Field(None, description="Estimated performance gain percentage")


class PerformanceModeInfo(BaseModel):
    """Performance mode information schema"""
    current_mode: Literal["efficiency", "balanced", "performance"] = Field(..., description="Current performance mode")
    available_modes: list[str] = Field(..., description="Available performance modes")
    mode_descriptions: dict[str, str] = Field(..., description="Description of each mode")
    auto_switching_enabled: bool = Field(False, description="Whether automatic mode switching is enabled")
    thermal_throttling_active: bool = Field(False, description="Whether thermal throttling is currently active")


class HardwareCapabilities(BaseModel):
    """Hardware capabilities schema"""
    mlx_support: bool = Field(..., description="Whether MLX is supported")
    metal_support: bool = Field(..., description="Whether Metal is supported")
    unified_memory: bool = Field(..., description="Whether unified memory architecture is available")
    neural_engine: bool = Field(False, description="Whether Neural Engine is available")
    max_model_size_gb: float = Field(..., description="Maximum recommended model size in GB")
    recommended_worker_count: int = Field(..., description="Recommended number of workers")
    optimal_batch_size: int = Field(..., description="Optimal batch size for inference")
