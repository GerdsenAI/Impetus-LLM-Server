"""
Metal GPU Performance Monitoring for Apple Silicon
Provides real-time GPU utilization, memory bandwidth, and performance metrics
"""

import subprocess
import re
import json
import time
import threading
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from collections import deque
from loguru import logger
import psutil

# Try to import MLX for Metal memory stats
try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False


@dataclass
class MetalMetrics:
    """Metal GPU metrics"""
    timestamp: float
    gpu_utilization: float  # 0-100%
    gpu_frequency_mhz: float
    memory_used_gb: float
    memory_total_gb: float
    memory_bandwidth_utilization: float  # 0-100%
    compute_units_active: int
    temperature_celsius: Optional[float]
    power_watts: Optional[float]


class MetalMonitor:
    """Monitor Metal GPU performance on Apple Silicon"""
    
    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[MetalMetrics], None]] = []
        
        # Check if we're on macOS
        if not self._is_macos():
            logger.warning("Metal monitoring is only available on macOS")
    
    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        import platform
        return platform.system() == 'Darwin'
    
    def _run_command(self, cmd: List[str]) -> Optional[str]:
        """Run a shell command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Command {' '.join(cmd)} failed: {e}")
            return None
    
    def _get_gpu_stats_ioreg(self) -> Dict[str, float]:
        """Get GPU stats using ioreg (requires no special permissions)"""
        stats = {
            'gpu_utilization': 0.0,
            'gpu_frequency_mhz': 0.0,
            'memory_bandwidth_utilization': 0.0
        }
        
        # Try to get GPU utilization from ioreg
        output = self._run_command(['ioreg', '-r', '-c', 'IOAccelerator'])
        if output:
            # Parse GPU utilization if available
            utilization_match = re.search(r'"Device Utilization %"\s*=\s*(\d+)', output)
            if utilization_match:
                stats['gpu_utilization'] = float(utilization_match.group(1))
            
            # Parse GPU frequency if available
            freq_match = re.search(r'"GPU Core Frequency\(MHz\)"\s*=\s*(\d+)', output)
            if freq_match:
                stats['gpu_frequency_mhz'] = float(freq_match.group(1))
        
        return stats
    
    def _get_metal_memory_stats(self) -> Dict[str, float]:
        """Get Metal memory stats using MLX if available"""
        stats = {
            'memory_used_gb': 0.0,
            'memory_total_gb': 0.0
        }
        
        if MLX_AVAILABLE:
            try:
                # Get Metal memory usage from MLX
                memory_info = mx.metal.get_memory_info()
                stats['memory_used_gb'] = memory_info['current_allocated_size'] / (1024 ** 3)
                stats['memory_total_gb'] = memory_info['peak_allocated_size'] / (1024 ** 3)
                
                # Also get cache info
                cache_info = mx.metal.get_cache_memory()
                logger.debug(f"Metal cache memory: {cache_info / (1024 ** 3):.2f} GB")
            except Exception as e:
                logger.debug(f"Failed to get MLX memory info: {e}")
        
        # Fallback: estimate from system memory
        if stats['memory_total_gb'] == 0:
            memory = psutil.virtual_memory()
            # Unified memory - estimate GPU can use up to 75% of total
            stats['memory_total_gb'] = memory.total * 0.75 / (1024 ** 3)
            # Estimate current GPU usage based on process memory
            stats['memory_used_gb'] = memory.used * 0.3 / (1024 ** 3)  # Rough estimate
        
        return stats
    
    def _estimate_bandwidth_utilization(self, metrics: MetalMetrics) -> float:
        """Estimate memory bandwidth utilization based on GPU activity"""
        # This is a rough estimate based on GPU utilization and memory usage
        # Real bandwidth monitoring would require powermetrics or Instruments
        
        if len(self.metrics_history) < 2:
            return 0.0
        
        # Calculate memory throughput based on memory changes
        prev_metrics = self.metrics_history[-1]
        time_delta = metrics.timestamp - prev_metrics.timestamp
        
        if time_delta <= 0:
            return prev_metrics.memory_bandwidth_utilization
        
        # Estimate based on GPU utilization and frequency
        # Higher GPU utilization typically means higher bandwidth usage
        bandwidth_estimate = (
            metrics.gpu_utilization * 0.7 +  # GPU util contributes 70%
            (metrics.gpu_frequency_mhz / 1500) * 30  # Frequency contributes 30%
        )
        
        return min(100.0, bandwidth_estimate)
    
    def _get_thermal_info(self) -> Optional[float]:
        """Get GPU temperature if available"""
        # Try to get temperature from SMC
        output = self._run_command(['sysctl', '-n', 'machdep.xcpm.gpu_thermal_level'])
        if output:
            try:
                # Convert thermal level to approximate temperature
                thermal_level = int(output)
                # Rough conversion: 0 = 40°C, 100 = 100°C
                return 40 + (thermal_level * 0.6)
            except:
                pass
        return None
    
    def get_current_metrics(self) -> MetalMetrics:
        """Get current Metal GPU metrics"""
        # Get GPU stats
        gpu_stats = self._get_gpu_stats_ioreg()
        memory_stats = self._get_metal_memory_stats()
        
        # Create metrics object
        metrics = MetalMetrics(
            timestamp=time.time(),
            gpu_utilization=gpu_stats['gpu_utilization'],
            gpu_frequency_mhz=gpu_stats['gpu_frequency_mhz'],
            memory_used_gb=memory_stats['memory_used_gb'],
            memory_total_gb=memory_stats['memory_total_gb'],
            memory_bandwidth_utilization=0.0,  # Will be calculated
            compute_units_active=0,  # Not available without powermetrics
            temperature_celsius=self._get_thermal_info(),
            power_watts=None  # Not available without powermetrics
        )
        
        # Estimate bandwidth utilization
        metrics.memory_bandwidth_utilization = self._estimate_bandwidth_utilization(metrics)
        
        # Add to history
        self.metrics_history.append(metrics)
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in Metal monitor callback: {e}")
        
        return metrics
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous monitoring"""
        if self.monitoring:
            logger.warning("Metal monitoring already started")
            return
        
        if not self._is_macos():
            logger.error("Metal monitoring requires macOS")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.get_current_metrics()
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Error in Metal monitoring loop: {e}")
                    time.sleep(5)  # Back off on error
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started Metal GPU monitoring")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped Metal GPU monitoring")
    
    def add_callback(self, callback: Callable[[MetalMetrics], None]):
        """Add a callback for metrics updates"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[MetalMetrics], None]):
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_average_metrics(self, window_seconds: float = 60) -> Optional[MetalMetrics]:
        """Get average metrics over a time window"""
        if not self.metrics_history:
            return None
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Filter metrics within window
        window_metrics = [m for m in self.metrics_history if m.timestamp >= window_start]
        
        if not window_metrics:
            return self.metrics_history[-1]
        
        # Calculate averages
        avg_metrics = MetalMetrics(
            timestamp=current_time,
            gpu_utilization=sum(m.gpu_utilization for m in window_metrics) / len(window_metrics),
            gpu_frequency_mhz=sum(m.gpu_frequency_mhz for m in window_metrics) / len(window_metrics),
            memory_used_gb=sum(m.memory_used_gb for m in window_metrics) / len(window_metrics),
            memory_total_gb=window_metrics[-1].memory_total_gb,  # Use latest
            memory_bandwidth_utilization=sum(m.memory_bandwidth_utilization for m in window_metrics) / len(window_metrics),
            compute_units_active=0,
            temperature_celsius=sum(m.temperature_celsius for m in window_metrics if m.temperature_celsius) / len([m for m in window_metrics if m.temperature_celsius]) if any(m.temperature_celsius for m in window_metrics) else None,
            power_watts=None
        )
        
        return avg_metrics
    
    def get_peak_metrics(self) -> Optional[MetalMetrics]:
        """Get peak metrics from history"""
        if not self.metrics_history:
            return None
        
        # Find peak GPU utilization
        peak_metric = max(self.metrics_history, key=lambda m: m.gpu_utilization)
        return peak_metric


# Singleton instance
metal_monitor = MetalMonitor()


if __name__ == "__main__":
    # Test Metal monitoring
    monitor = MetalMonitor()
    
    def print_metrics(metrics: MetalMetrics):
        print(f"\nMetal GPU Metrics:")
        print(f"  GPU Utilization: {metrics.gpu_utilization:.1f}%")
        print(f"  GPU Frequency: {metrics.gpu_frequency_mhz:.0f} MHz")
        print(f"  Memory Used: {metrics.memory_used_gb:.2f} GB / {metrics.memory_total_gb:.2f} GB")
        print(f"  Memory Bandwidth: {metrics.memory_bandwidth_utilization:.1f}%")
        if metrics.temperature_celsius:
            print(f"  Temperature: {metrics.temperature_celsius:.1f}°C")
    
    monitor.add_callback(print_metrics)
    monitor.start_monitoring(interval_seconds=2.0)
    
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring()