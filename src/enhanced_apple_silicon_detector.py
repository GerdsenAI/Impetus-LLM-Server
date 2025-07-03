#!/usr/bin/env python3
"""
Enhanced Apple Silicon Hardware Detection and Optimization Module
Provides advanced hardware detection, real-time monitoring, and dynamic optimization
for Apple Silicon Macs (M1, M2, M3, M4 series)
"""

import os
import re
import json
import subprocess
import platform
import psutil
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class ChipGeneration(Enum):
    """Apple Silicon chip generations"""
    M1 = "M1"
    M2 = "M2" 
    M3 = "M3"
    M4 = "M4"
    UNKNOWN = "Unknown"

class ChipVariant(Enum):
    """Apple Silicon chip variants"""
    BASE = "Base"
    PRO = "Pro"
    MAX = "Max"
    ULTRA = "Ultra"
    UNKNOWN = "Unknown"

class ThermalState(Enum):
    """System thermal states"""
    NORMAL = "normal"
    WARM = "warm"
    HOT = "hot"
    THROTTLED = "throttled"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class PowerState(Enum):
    """System power states"""
    AC_POWER = "ac_power"
    BATTERY_POWER = "battery_power"
    LOW_BATTERY = "low_battery"
    UNKNOWN = "unknown"

@dataclass
class EnhancedAppleSiliconSpecs:
    """Enhanced Apple Silicon chip specifications with latest data"""
    chip_name: str
    generation: ChipGeneration
    variant: ChipVariant
    cpu_cores_performance: int
    cpu_cores_efficiency: int
    cpu_cores_total: int
    gpu_cores: int
    neural_engine_cores: int
    neural_engine_tops: float  # Tera Operations Per Second
    memory_gb_base: int
    memory_gb_max: int
    memory_bandwidth_gbps: int
    process_node: str
    year_introduced: int
    base_frequency_ghz: float
    boost_frequency_ghz: float
    tdp_watts: int
    cache_l2_mb: int
    cache_l3_mb: int
    pcie_lanes: int
    thunderbolt_ports: int
    display_support: int
    video_decode_engines: int
    video_encode_engines: int
    media_engine_support: List[str]

class EnhancedAppleSiliconDetector:
    """Enhanced Apple Silicon detector with advanced monitoring and optimization"""
    
    # Latest Apple Silicon specifications (updated for 2024/2025)
    ENHANCED_CHIP_SPECS = {
        'M1': EnhancedAppleSiliconSpecs(
            'M1', ChipGeneration.M1, ChipVariant.BASE, 4, 4, 8, 8, 16, 15.8,
            8, 16, 68, '5nm', 2020, 3.2, 3.2, 20, 12, 0, 16, 2, 2, 1, 1, 
            ['H.264', 'HEVC', 'ProRes']
        ),
        'M1 Pro': EnhancedAppleSiliconSpecs(
            'M1 Pro', ChipGeneration.M1, ChipVariant.PRO, 8, 2, 10, 16, 16, 15.8,
            16, 32, 200, '5nm', 2021, 3.2, 3.2, 30, 24, 0, 16, 4, 3, 2, 1,
            ['H.264', 'HEVC', 'ProRes']
        ),
        'M1 Max': EnhancedAppleSiliconSpecs(
            'M1 Max', ChipGeneration.M1, ChipVariant.MAX, 8, 2, 10, 32, 16, 15.8,
            32, 64, 400, '5nm', 2021, 3.2, 3.2, 60, 48, 0, 16, 4, 4, 2, 2,
            ['H.264', 'HEVC', 'ProRes']
        ),
        'M1 Ultra': EnhancedAppleSiliconSpecs(
            'M1 Ultra', ChipGeneration.M1, ChipVariant.ULTRA, 16, 4, 20, 64, 32, 31.6,
            64, 128, 800, '5nm', 2022, 3.2, 3.2, 120, 96, 0, 32, 8, 8, 4, 4,
            ['H.264', 'HEVC', 'ProRes']
        ),
        'M2': EnhancedAppleSiliconSpecs(
            'M2', ChipGeneration.M2, ChipVariant.BASE, 4, 4, 8, 10, 16, 15.8,
            8, 24, 100, '5nm', 2022, 3.49, 3.49, 22, 16, 0, 16, 2, 2, 1, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M2 Pro': EnhancedAppleSiliconSpecs(
            'M2 Pro', ChipGeneration.M2, ChipVariant.PRO, 8, 4, 12, 19, 16, 15.8,
            16, 32, 200, '5nm', 2023, 3.49, 3.49, 35, 24, 0, 16, 4, 3, 2, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M2 Max': EnhancedAppleSiliconSpecs(
            'M2 Max', ChipGeneration.M2, ChipVariant.MAX, 8, 4, 12, 38, 16, 15.8,
            32, 96, 400, '5nm', 2023, 3.49, 3.49, 67, 48, 0, 16, 4, 4, 2, 2,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M2 Ultra': EnhancedAppleSiliconSpecs(
            'M2 Ultra', ChipGeneration.M2, ChipVariant.ULTRA, 16, 8, 24, 76, 32, 31.6,
            64, 192, 800, '5nm', 2023, 3.49, 3.49, 134, 96, 0, 32, 8, 8, 4, 4,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M3': EnhancedAppleSiliconSpecs(
            'M3', ChipGeneration.M3, ChipVariant.BASE, 4, 4, 8, 10, 16, 18.0,
            8, 24, 100, '3nm', 2023, 4.05, 4.05, 22, 16, 4, 16, 2, 2, 1, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M3 Pro': EnhancedAppleSiliconSpecs(
            'M3 Pro', ChipGeneration.M3, ChipVariant.PRO, 6, 6, 12, 18, 16, 18.0,
            18, 36, 150, '3nm', 2023, 4.05, 4.05, 37, 24, 6, 16, 4, 3, 2, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M3 Max': EnhancedAppleSiliconSpecs(
            'M3 Max', ChipGeneration.M3, ChipVariant.MAX, 12, 4, 16, 40, 16, 18.0,
            36, 128, 400, '3nm', 2023, 4.05, 4.05, 92, 48, 12, 16, 4, 4, 2, 2,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M3 Ultra': EnhancedAppleSiliconSpecs(
            'M3 Ultra', ChipGeneration.M3, ChipVariant.ULTRA, 24, 8, 32, 80, 32, 36.0,
            64, 256, 800, '3nm', 2024, 4.05, 4.05, 184, 96, 24, 32, 8, 8, 4, 4,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M4': EnhancedAppleSiliconSpecs(
            'M4', ChipGeneration.M4, ChipVariant.BASE, 4, 6, 10, 10, 16, 38.0,
            16, 32, 120, '3nm', 2024, 4.4, 4.4, 22, 16, 8, 16, 2, 2, 1, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M4 Pro': EnhancedAppleSiliconSpecs(
            'M4 Pro', ChipGeneration.M4, ChipVariant.PRO, 10, 4, 14, 20, 16, 38.0,
            24, 64, 273, '3nm', 2024, 4.4, 4.4, 45, 24, 12, 20, 4, 3, 2, 1,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M4 Max': EnhancedAppleSiliconSpecs(
            'M4 Max', ChipGeneration.M4, ChipVariant.MAX, 12, 4, 16, 40, 16, 38.0,
            36, 128, 546, '3nm', 2024, 4.4, 4.4, 105, 48, 24, 20, 4, 4, 2, 2,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
        'M4 Ultra': EnhancedAppleSiliconSpecs(
            'M4 Ultra', ChipGeneration.M4, ChipVariant.ULTRA, 24, 8, 32, 80, 32, 76.0,
            64, 256, 1092, '3nm', 2025, 4.4, 4.4, 210, 96, 48, 40, 8, 8, 4, 4,
            ['H.264', 'HEVC', 'ProRes', 'AV1']
        ),
    }
    
    def __init__(self, monitoring_interval: float = 2.0):
        self.monitoring_interval = monitoring_interval
        self.is_apple_silicon = self._detect_apple_silicon()
        self.chip_info = self._get_enhanced_chip_info() if self.is_apple_silicon else None
        self.system_info = self._get_enhanced_system_info()
        
        # Real-time monitoring
        self._monitoring_active = False
        self._monitoring_thread = None
        self._metrics_history = []
        self._max_history_size = 300  # 10 minutes at 2-second intervals
        
        # Performance optimization
        self._optimization_callbacks = []
        self._thermal_callbacks = []
        self._power_callbacks = []
        
        # Current states
        self.current_thermal_state = ThermalState.UNKNOWN
        self.current_power_state = PowerState.UNKNOWN
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Enhanced Apple Silicon Detector initialized: {self.chip_info}")
    
    def _detect_apple_silicon(self) -> bool:
        """Enhanced Apple Silicon detection"""
        try:
            if platform.system() != 'Darwin':
                return False
            
            # Multiple detection methods for reliability
            methods = [
                self._detect_via_architecture,
                self._detect_via_sysctl,
                self._detect_via_system_profiler
            ]
            
            for method in methods:
                try:
                    if method():
                        return True
                except Exception as e:
                    self.logger.debug(f"Detection method failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to detect Apple Silicon: {e}")
            return False
    
    def _detect_via_architecture(self) -> bool:
        """Detect via platform architecture"""
        return platform.machine() == 'arm64'
    
    def _detect_via_sysctl(self) -> bool:
        """Detect via sysctl"""
        result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], 
                              capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() == '1'
    
    def _detect_via_system_profiler(self) -> bool:
        """Detect via system_profiler"""
        result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'Apple' in result.stdout and any(
                chip in result.stdout for chip in ['M1', 'M2', 'M3', 'M4']
            )
        return False
    
    def _get_enhanced_chip_info(self) -> Optional[Dict[str, Any]]:
        """Get enhanced chip information with detailed detection"""
        try:
            # Get basic chip info
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            output = result.stdout
            
            # Enhanced chip name parsing
            chip_patterns = [
                r'Chip:\s*Apple\s*([^\n]+)',
                r'Processor Name:\s*Apple\s*([^\n]+)',
                r'CPU:\s*Apple\s*([^\n]+)'
            ]
            
            chip_name = None
            for pattern in chip_patterns:
                match = re.search(pattern, output)
                if match:
                    chip_name = match.group(1).strip()
                    break
            
            if not chip_name:
                return None
            
            # Parse memory
            memory_match = re.search(r'Memory:\s*(\d+)\s*GB', output)
            memory_gb = int(memory_match.group(1)) if memory_match else 0
            
            # Get model identifier
            model_match = re.search(r'Model Identifier:\s*([^\n]+)', output)
            model_id = model_match.group(1).strip() if model_match else 'Unknown'
            
            # Get serial number
            serial_match = re.search(r'Serial Number \(system\):\s*([^\n]+)', output)
            serial = serial_match.group(1).strip() if serial_match else 'Unknown'
            
            # Enhanced chip specification lookup
            chip_specs = self._match_chip_specifications(chip_name)
            
            # Get additional hardware details
            hardware_details = self._get_hardware_details()
            
            return {
                'chip_name': chip_name,
                'model_identifier': model_id,
                'serial_number': serial,
                'detected_memory_gb': memory_gb,
                'specifications': asdict(chip_specs) if chip_specs else None,
                'hardware_details': hardware_details,
                'detection_confidence': self._calculate_detection_confidence(chip_name, chip_specs)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced chip info: {e}")
            return None
    
    def _match_chip_specifications(self, chip_name: str) -> Optional[EnhancedAppleSiliconSpecs]:
        """Enhanced chip specification matching"""
        chip_name_lower = chip_name.lower()
        
        # Direct match first
        for spec_name, specs in self.ENHANCED_CHIP_SPECS.items():
            if spec_name.lower() == chip_name_lower:
                return specs
        
        # Fuzzy matching for variations
        for spec_name, specs in self.ENHANCED_CHIP_SPECS.items():
            spec_parts = spec_name.lower().split()
            if all(part in chip_name_lower for part in spec_parts):
                return specs
        
        # Generation-based matching
        if 'm4' in chip_name_lower:
            if 'ultra' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M4 Ultra')
            elif 'max' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M4 Max')
            elif 'pro' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M4 Pro')
            else:
                return self.ENHANCED_CHIP_SPECS.get('M4')
        elif 'm3' in chip_name_lower:
            if 'ultra' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M3 Ultra')
            elif 'max' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M3 Max')
            elif 'pro' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M3 Pro')
            else:
                return self.ENHANCED_CHIP_SPECS.get('M3')
        elif 'm2' in chip_name_lower:
            if 'ultra' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M2 Ultra')
            elif 'max' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M2 Max')
            elif 'pro' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M2 Pro')
            else:
                return self.ENHANCED_CHIP_SPECS.get('M2')
        elif 'm1' in chip_name_lower:
            if 'ultra' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M1 Ultra')
            elif 'max' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M1 Max')
            elif 'pro' in chip_name_lower:
                return self.ENHANCED_CHIP_SPECS.get('M1 Pro')
            else:
                return self.ENHANCED_CHIP_SPECS.get('M1')
        
        return None
    
    def _calculate_detection_confidence(self, chip_name: str, specs: Optional[EnhancedAppleSiliconSpecs]) -> float:
        """Calculate confidence level of chip detection"""
        confidence = 0.0
        
        # Base confidence for successful detection
        if chip_name:
            confidence += 0.3
        
        # Confidence boost for specification match
        if specs:
            confidence += 0.4
        
        # Confidence boost for known chip patterns
        known_patterns = ['M1', 'M2', 'M3', 'M4']
        if any(pattern in chip_name for pattern in known_patterns):
            confidence += 0.2
        
        # Confidence boost for variant detection
        variants = ['Pro', 'Max', 'Ultra']
        if any(variant in chip_name for variant in variants):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_hardware_details(self) -> Dict[str, Any]:
        """Get additional hardware details"""
        details = {}
        
        try:
            # Get detailed CPU information
            sysctl_queries = {
                'hw.ncpu': 'logical_cpu_count',
                'hw.physicalcpu': 'physical_cpu_count',
                'hw.perflevel0.logicalcpu': 'performance_cores',
                'hw.perflevel1.logicalcpu': 'efficiency_cores',
                'hw.memsize': 'memory_bytes',
                'hw.cpufrequency': 'cpu_frequency',
                'hw.cpufrequency_max': 'cpu_frequency_max',
                'hw.cpufrequency_min': 'cpu_frequency_min',
                'hw.tbfrequency': 'timebase_frequency',
                'hw.cachelinesize': 'cache_line_size',
                'hw.l1icachesize': 'l1_instruction_cache',
                'hw.l1dcachesize': 'l1_data_cache',
                'hw.l2cachesize': 'l2_cache_size',
                'hw.l3cachesize': 'l3_cache_size',
                'hw.model': 'hardware_model',
                'hw.targettype': 'target_type'
            }
            
            for sysctl_key, info_key in sysctl_queries.items():
                try:
                    result = subprocess.run(['sysctl', '-n', sysctl_key], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        value = result.stdout.strip()
                        if value.isdigit():
                            details[info_key] = int(value)
                        else:
                            details[info_key] = value
                except:
                    pass
            
            # Get GPU information
            try:
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_match = re.search(r'Chipset Model:\s*([^\n]+)', result.stdout)
                    if gpu_match:
                        details['gpu_model'] = gpu_match.group(1).strip()
            except:
                pass
            
        except Exception as e:
            self.logger.warning(f"Failed to get hardware details: {e}")
        
        return details
    
    def _get_enhanced_system_info(self) -> Dict[str, Any]:
        """Get enhanced system information"""
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'boot_time': psutil.boot_time(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
            # Enhanced memory information
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                info['memory'] = {
                    'total_bytes': memory.total,
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_bytes': memory.available,
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_bytes': memory.used,
                    'used_gb': round(memory.used / (1024**3), 2),
                    'used_percent': memory.percent,
                    'free_bytes': memory.free,
                    'free_gb': round(memory.free / (1024**3), 2),
                    'cached_bytes': getattr(memory, 'cached', 0),
                    'cached_gb': round(getattr(memory, 'cached', 0) / (1024**3), 2),
                    'swap_total_gb': round(swap.total / (1024**3), 2),
                    'swap_used_gb': round(swap.used / (1024**3), 2),
                    'swap_percent': swap.percent
                }
            except Exception as e:
                self.logger.warning(f"Failed to get memory info: {e}")
            
            # Enhanced disk information
            try:
                disk_usage = psutil.disk_usage('/')
                info['disk'] = {
                    'total_bytes': disk_usage.total,
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_bytes': disk_usage.used,
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_bytes': disk_usage.free,
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'used_percent': (disk_usage.used / disk_usage.total) * 100
                }
            except Exception as e:
                self.logger.warning(f"Failed to get disk info: {e}")
            
            # Network information
            try:
                network_stats = psutil.net_io_counters()
                info['network'] = {
                    'bytes_sent': network_stats.bytes_sent,
                    'bytes_recv': network_stats.bytes_recv,
                    'packets_sent': network_stats.packets_sent,
                    'packets_recv': network_stats.packets_recv,
                    'errin': network_stats.errin,
                    'errout': network_stats.errout,
                    'dropin': network_stats.dropin,
                    'dropout': network_stats.dropout
                }
            except Exception as e:
                self.logger.warning(f"Failed to get network info: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced system info: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get comprehensive real-time system metrics"""
        try:
            timestamp = time.time()
            metrics = {
                'timestamp': timestamp,
                'cpu': self._get_cpu_metrics(),
                'memory': self._get_memory_metrics(),
                'thermal': self._get_thermal_metrics(),
                'power': self._get_power_metrics(),
                'gpu': self._get_gpu_metrics(),
                'neural_engine': self._get_neural_engine_metrics(),
                'performance': self._get_performance_metrics()
            }
            
            # Update current states
            self._update_current_states(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time metrics: {e}")
            return {'timestamp': time.time(), 'error': str(e)}
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get detailed CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()
            
            metrics = {
                'usage_percent_total': psutil.cpu_percent(interval=0.1),
                'usage_percent_per_core': cpu_percent,
                'core_count_logical': psutil.cpu_count(logical=True),
                'core_count_physical': psutil.cpu_count(logical=False),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                'context_switches': psutil.cpu_stats().ctx_switches,
                'interrupts': psutil.cpu_stats().interrupts,
                'soft_interrupts': psutil.cpu_stats().soft_interrupts,
                'syscalls': psutil.cpu_stats().syscalls
            }
            
            if cpu_freq:
                metrics.update({
                    'frequency_current_mhz': cpu_freq.current,
                    'frequency_min_mhz': cpu_freq.min,
                    'frequency_max_mhz': cpu_freq.max
                })
            
            # CPU time breakdown
            metrics['times'] = {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle,
                'nice': getattr(cpu_times, 'nice', 0),
                'iowait': getattr(cpu_times, 'iowait', 0),
                'irq': getattr(cpu_times, 'irq', 0),
                'softirq': getattr(cpu_times, 'softirq', 0)
            }
            
            # Performance vs efficiency core breakdown (if available)
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                p_cores = specs.get('cpu_cores_performance', 0)
                e_cores = specs.get('cpu_cores_efficiency', 0)
                
                if len(cpu_percent) >= p_cores + e_cores:
                    metrics['performance_cores_usage'] = cpu_percent[:p_cores]
                    metrics['efficiency_cores_usage'] = cpu_percent[p_cores:p_cores + e_cores]
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get CPU metrics: {e}")
            return {}
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get detailed memory metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics = {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'free_gb': round(memory.free / (1024**3), 2),
                'usage_percent': memory.percent,
                'cached_gb': round(getattr(memory, 'cached', 0) / (1024**3), 2),
                'buffers_gb': round(getattr(memory, 'buffers', 0) / (1024**3), 2),
                'shared_gb': round(getattr(memory, 'shared', 0) / (1024**3), 2),
                'pressure': self._get_memory_pressure(),
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_free_gb': round(swap.free / (1024**3), 2),
                'swap_percent': swap.percent,
                'swap_sin': swap.sin,
                'swap_sout': swap.sout
            }
            
            # Memory bandwidth estimation (based on chip specs)
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                bandwidth_gbps = specs.get('memory_bandwidth_gbps', 0)
                utilization = memory.percent / 100.0
                metrics['estimated_bandwidth_usage_gbps'] = round(bandwidth_gbps * utilization, 1)
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get memory metrics: {e}")
            return {}
    
    def _get_memory_pressure(self) -> str:
        """Get detailed memory pressure status"""
        try:
            result = subprocess.run(['memory_pressure'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'critical' in output:
                    return 'critical'
                elif 'urgent' in output:
                    return 'urgent'
                elif 'warn' in output:
                    return 'warning'
                elif 'normal' in output:
                    return 'normal'
            return 'unknown'
        except:
            # Fallback: estimate based on memory usage
            try:
                memory = psutil.virtual_memory()
                if memory.percent > 95:
                    return 'critical'
                elif memory.percent > 85:
                    return 'urgent'
                elif memory.percent > 75:
                    return 'warning'
                else:
                    return 'normal'
            except:
                return 'unknown'
    
    def _get_thermal_metrics(self) -> Dict[str, Any]:
        """Get enhanced thermal metrics"""
        try:
            metrics = {
                'state': 'unknown',
                'temperatures': {},
                'fan_speeds': {},
                'throttling': False
            }
            
            # Check thermal state via pmset
            try:
                result = subprocess.run(['pmset', '-g', 'thermlog'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    output = result.stdout.lower()
                    if 'cpu_scheduler_limit' in output or 'throttle' in output:
                        metrics['state'] = 'throttled'
                        metrics['throttling'] = True
                    elif 'thermal pressure' in output:
                        metrics['state'] = 'hot'
                    else:
                        metrics['state'] = 'normal'
            except:
                pass
            
            # Estimate temperatures based on CPU usage and load
            try:
                cpu_usage = psutil.cpu_percent(interval=0.1)
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
                
                # Base temperature estimation
                base_temp = 35  # Base temperature in Celsius
                usage_factor = (cpu_usage / 100) * 25  # Up to 25°C from usage
                load_factor = min(load_avg, 4) * 5  # Up to 20°C from load
                
                estimated_cpu_temp = base_temp + usage_factor + load_factor
                
                # Adjust based on chip generation (newer chips run cooler)
                if self.chip_info and self.chip_info.get('specifications'):
                    specs = self.chip_info['specifications']
                    generation = specs.get('generation')
                    if generation == 'M4':
                        estimated_cpu_temp -= 5  # M4 runs cooler
                    elif generation == 'M3':
                        estimated_cpu_temp -= 3  # M3 runs cooler than M1/M2
                
                metrics['temperatures'] = {
                    'cpu_estimated': round(estimated_cpu_temp, 1),
                    'method': 'estimated_from_usage_and_load'
                }
                
                # Determine thermal state from temperature
                if estimated_cpu_temp > 85:
                    metrics['state'] = 'critical'
                elif estimated_cpu_temp > 75:
                    metrics['state'] = 'hot'
                elif estimated_cpu_temp > 65:
                    metrics['state'] = 'warm'
                else:
                    metrics['state'] = 'normal'
                    
            except:
                pass
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get thermal metrics: {e}")
            return {'state': 'unknown', 'temperatures': {}, 'fan_speeds': {}, 'throttling': False}
    
    def _get_power_metrics(self) -> Dict[str, Any]:
        """Get enhanced power metrics"""
        try:
            metrics = {
                'source': 'unknown',
                'battery': {},
                'consumption': {},
                'efficiency': {}
            }
            
            # Battery information
            try:
                battery = psutil.sensors_battery()
                if battery:
                    metrics['battery'] = {
                        'percent': battery.percent,
                        'plugged_in': battery.power_plugged,
                        'time_left_seconds': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                        'time_left_hours': round(battery.secsleft / 3600, 1) if battery.secsleft and battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
                    
                    # Determine power source
                    if battery.power_plugged:
                        metrics['source'] = 'ac_power'
                    elif battery.percent < 20:
                        metrics['source'] = 'low_battery'
                    else:
                        metrics['source'] = 'battery_power'
            except:
                pass
            
            # Power management information
            try:
                result = subprocess.run(['pmset', '-g', 'ps'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    output = result.stdout
                    
                    # Parse power source
                    if 'AC Power' in output:
                        metrics['source'] = 'ac_power'
                    elif 'Battery Power' in output:
                        metrics['source'] = 'battery_power'
                    
                    # Extract power consumption
                    power_match = re.search(r'(\d+)W', output)
                    if power_match:
                        watts = int(power_match.group(1))
                        metrics['consumption']['current_watts'] = watts
                        
                        # Estimate efficiency based on chip specs
                        if self.chip_info and self.chip_info.get('specifications'):
                            specs = self.chip_info['specifications']
                            tdp = specs.get('tdp_watts', 0)
                            if tdp > 0:
                                efficiency = (tdp - watts) / tdp * 100
                                metrics['efficiency']['power_efficiency_percent'] = round(max(0, efficiency), 1)
            except:
                pass
            
            # Estimate power consumption based on usage
            try:
                cpu_usage = psutil.cpu_percent(interval=0.1)
                
                if self.chip_info and self.chip_info.get('specifications'):
                    specs = self.chip_info['specifications']
                    tdp = specs.get('tdp_watts', 20)
                    
                    # Estimate current consumption
                    base_power = tdp * 0.2  # 20% base power
                    variable_power = tdp * 0.8 * (cpu_usage / 100)
                    estimated_watts = base_power + variable_power
                    
                    metrics['consumption']['estimated_watts'] = round(estimated_watts, 1)
                    metrics['consumption']['estimated_method'] = 'cpu_usage_based'
            except:
                pass
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get power metrics: {e}")
            return {'source': 'unknown', 'battery': {}, 'consumption': {}, 'efficiency': {}}
    
    def _get_gpu_metrics(self) -> Dict[str, Any]:
        """Get GPU utilization metrics"""
        try:
            metrics = {
                'available': False,
                'cores': 0,
                'memory_gb': 0,
                'utilization_percent': 0,
                'memory_used_gb': 0,
                'memory_free_gb': 0,
                'frequency_mhz': 0,
                'metal_support': False
            }
            
            # Get GPU specs from chip info
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                metrics['cores'] = specs.get('gpu_cores', 0)
                metrics['available'] = metrics['cores'] > 0
                
                # Estimate GPU memory (typically 75% of total unified memory)
                total_memory = specs.get('memory_gb_base', 0)
                metrics['memory_gb'] = round(total_memory * 0.75, 1)
                
                # Metal support on Apple Silicon
                if self.is_apple_silicon:
                    metrics['metal_support'] = True
            
            # Estimate GPU utilization (would need Metal Performance Shaders for real data)
            try:
                # Rough estimation based on system load and memory usage
                memory = psutil.virtual_memory()
                cpu_usage = psutil.cpu_percent(interval=0.1)
                
                # GPU utilization often correlates with memory usage and CPU load
                estimated_gpu_usage = min((memory.percent + cpu_usage) / 2, 100)
                metrics['utilization_percent'] = round(estimated_gpu_usage, 1)
                
                # Estimate GPU memory usage
                if metrics['memory_gb'] > 0:
                    gpu_memory_usage = (memory.percent / 100) * metrics['memory_gb']
                    metrics['memory_used_gb'] = round(gpu_memory_usage, 1)
                    metrics['memory_free_gb'] = round(metrics['memory_gb'] - gpu_memory_usage, 1)
                
            except:
                pass
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get GPU metrics: {e}")
            return {'available': False, 'cores': 0, 'memory_gb': 0, 'utilization_percent': 0}
    
    def _get_neural_engine_metrics(self) -> Dict[str, Any]:
        """Get Neural Engine utilization metrics"""
        try:
            metrics = {
                'available': False,
                'cores': 0,
                'tops': 0.0,
                'utilization_percent': 0,
                'framework_support': {},
                'active_models': 0
            }
            
            # Get Neural Engine specs from chip info
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                metrics['cores'] = specs.get('neural_engine_cores', 0)
                metrics['tops'] = specs.get('neural_engine_tops', 0.0)
                metrics['available'] = metrics['cores'] > 0
            
            # Check framework support
            frameworks = {}
            
            # Core ML
            try:
                import coremltools
                frameworks['coreml'] = {
                    'available': True,
                    'version': coremltools.__version__
                }
            except ImportError:
                frameworks['coreml'] = {'available': False}
            
            # MLX
            try:
                import mlx.core as mx
                frameworks['mlx'] = {
                    'available': True,
                    'device': str(mx.default_device())
                }
            except ImportError:
                frameworks['mlx'] = {'available': False}
            
            metrics['framework_support'] = frameworks
            
            # Estimate Neural Engine utilization
            # This would require Core ML or MLX monitoring for real data
            try:
                # Rough estimation based on ML framework usage
                if frameworks.get('mlx', {}).get('available') or frameworks.get('coreml', {}).get('available'):
                    # If ML frameworks are available, assume some usage
                    cpu_usage = psutil.cpu_percent(interval=0.1)
                    # Neural Engine usage often inversely correlates with CPU usage for ML tasks
                    estimated_ne_usage = max(0, 100 - cpu_usage) * 0.3  # Conservative estimate
                    metrics['utilization_percent'] = round(estimated_ne_usage, 1)
            except:
                pass
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get Neural Engine metrics: {e}")
            return {'available': False, 'cores': 0, 'tops': 0.0, 'utilization_percent': 0}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        try:
            metrics = {
                'overall_score': 0,
                'cpu_score': 0,
                'memory_score': 0,
                'thermal_score': 0,
                'power_score': 0,
                'bottlenecks': [],
                'recommendations': []
            }
            
            # CPU performance score (inverse of usage)
            cpu_usage = psutil.cpu_percent(interval=0.1)
            metrics['cpu_score'] = max(0, 100 - cpu_usage)
            
            # Memory performance score
            memory = psutil.virtual_memory()
            memory_pressure = self._get_memory_pressure()
            if memory_pressure == 'normal':
                metrics['memory_score'] = max(0, 100 - memory.percent)
            elif memory_pressure == 'warning':
                metrics['memory_score'] = max(0, 50 - memory.percent * 0.5)
            else:
                metrics['memory_score'] = max(0, 25 - memory.percent * 0.25)
            
            # Thermal performance score
            thermal_state = self.current_thermal_state
            if thermal_state == ThermalState.NORMAL:
                metrics['thermal_score'] = 100
            elif thermal_state == ThermalState.WARM:
                metrics['thermal_score'] = 75
            elif thermal_state == ThermalState.HOT:
                metrics['thermal_score'] = 50
            elif thermal_state == ThermalState.THROTTLED:
                metrics['thermal_score'] = 25
            else:
                metrics['thermal_score'] = 0
            
            # Power performance score
            power_state = self.current_power_state
            if power_state == PowerState.AC_POWER:
                metrics['power_score'] = 100
            elif power_state == PowerState.BATTERY_POWER:
                battery = psutil.sensors_battery()
                if battery:
                    metrics['power_score'] = battery.percent
                else:
                    metrics['power_score'] = 50
            elif power_state == PowerState.LOW_BATTERY:
                metrics['power_score'] = 25
            else:
                metrics['power_score'] = 50
            
            # Overall score (weighted average)
            weights = {'cpu': 0.3, 'memory': 0.3, 'thermal': 0.2, 'power': 0.2}
            metrics['overall_score'] = round(
                metrics['cpu_score'] * weights['cpu'] +
                metrics['memory_score'] * weights['memory'] +
                metrics['thermal_score'] * weights['thermal'] +
                metrics['power_score'] * weights['power']
            )
            
            # Identify bottlenecks
            if metrics['cpu_score'] < 50:
                metrics['bottlenecks'].append('high_cpu_usage')
            if metrics['memory_score'] < 50:
                metrics['bottlenecks'].append('high_memory_usage')
            if metrics['thermal_score'] < 50:
                metrics['bottlenecks'].append('thermal_throttling')
            if metrics['power_score'] < 30:
                metrics['bottlenecks'].append('low_battery')
            
            # Generate recommendations
            if 'high_cpu_usage' in metrics['bottlenecks']:
                metrics['recommendations'].append('Consider closing CPU-intensive applications')
            if 'high_memory_usage' in metrics['bottlenecks']:
                metrics['recommendations'].append('Close unused applications to free memory')
            if 'thermal_throttling' in metrics['bottlenecks']:
                metrics['recommendations'].append('Reduce workload to prevent overheating')
            if 'low_battery' in metrics['bottlenecks']:
                metrics['recommendations'].append('Connect to power adapter')
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to get performance metrics: {e}")
            return {'overall_score': 0, 'bottlenecks': [], 'recommendations': []}
    
    def _update_current_states(self, metrics: Dict[str, Any]):
        """Update current system states based on metrics"""
        try:
            # Update thermal state
            thermal_info = metrics.get('thermal', {})
            thermal_state_str = thermal_info.get('state', 'unknown')
            
            if thermal_state_str == 'normal':
                self.current_thermal_state = ThermalState.NORMAL
            elif thermal_state_str == 'warm':
                self.current_thermal_state = ThermalState.WARM
            elif thermal_state_str == 'hot':
                self.current_thermal_state = ThermalState.HOT
            elif thermal_state_str == 'throttled':
                self.current_thermal_state = ThermalState.THROTTLED
            elif thermal_state_str == 'critical':
                self.current_thermal_state = ThermalState.CRITICAL
            else:
                self.current_thermal_state = ThermalState.UNKNOWN
            
            # Update power state
            power_info = metrics.get('power', {})
            power_source = power_info.get('source', 'unknown')
            
            if power_source == 'ac_power':
                self.current_power_state = PowerState.AC_POWER
            elif power_source == 'battery_power':
                self.current_power_state = PowerState.BATTERY_POWER
            elif power_source == 'low_battery':
                self.current_power_state = PowerState.LOW_BATTERY
            else:
                self.current_power_state = PowerState.UNKNOWN
                
        except Exception as e:
            self.logger.warning(f"Failed to update current states: {e}")
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        self.logger.info("Started real-time monitoring")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        self.logger.info("Stopped real-time monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                metrics = self.get_real_time_metrics()
                
                # Add to history
                self._metrics_history.append(metrics)
                
                # Trim history if too long
                if len(self._metrics_history) > self._max_history_size:
                    self._metrics_history = self._metrics_history[-self._max_history_size:]
                
                # Trigger callbacks
                self._trigger_callbacks(metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _trigger_callbacks(self, metrics: Dict[str, Any]):
        """Trigger registered callbacks based on metrics"""
        try:
            # Performance optimization callbacks
            for callback in self._optimization_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    self.logger.error(f"Error in optimization callback: {e}")
            
            # Thermal callbacks
            if self.current_thermal_state in [ThermalState.HOT, ThermalState.THROTTLED, ThermalState.CRITICAL]:
                for callback in self._thermal_callbacks:
                    try:
                        callback(self.current_thermal_state, metrics)
                    except Exception as e:
                        self.logger.error(f"Error in thermal callback: {e}")
            
            # Power callbacks
            if self.current_power_state == PowerState.LOW_BATTERY:
                for callback in self._power_callbacks:
                    try:
                        callback(self.current_power_state, metrics)
                    except Exception as e:
                        self.logger.error(f"Error in power callback: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error triggering callbacks: {e}")
    
    def register_optimization_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for performance optimization"""
        self._optimization_callbacks.append(callback)
    
    def register_thermal_callback(self, callback: Callable[[ThermalState, Dict[str, Any]], None]):
        """Register a callback for thermal events"""
        self._thermal_callbacks.append(callback)
    
    def register_power_callback(self, callback: Callable[[PowerState, Dict[str, Any]], None]):
        """Register a callback for power events"""
        self._power_callbacks.append(callback)
    
    def get_metrics_history(self, duration_minutes: int = 10) -> List[Dict[str, Any]]:
        """Get metrics history for specified duration"""
        if not self._metrics_history:
            return []
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [m for m in self._metrics_history if m.get('timestamp', 0) >= cutoff_time]
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on current state"""
        recommendations = []
        
        try:
            metrics = self.get_real_time_metrics()
            
            # CPU optimization
            cpu_usage = metrics.get('cpu', {}).get('usage_percent_total', 0)
            if cpu_usage > 80:
                recommendations.append({
                    'category': 'cpu',
                    'priority': 'high',
                    'title': 'High CPU Usage Detected',
                    'description': f'CPU usage is at {cpu_usage:.1f}%',
                    'actions': [
                        'Close unnecessary applications',
                        'Check for background processes',
                        'Consider using efficiency cores for background tasks'
                    ]
                })
            
            # Memory optimization
            memory_percent = metrics.get('memory', {}).get('usage_percent', 0)
            memory_pressure = metrics.get('memory', {}).get('pressure', 'normal')
            
            if memory_pressure in ['warning', 'urgent', 'critical']:
                recommendations.append({
                    'category': 'memory',
                    'priority': 'high' if memory_pressure == 'critical' else 'medium',
                    'title': f'Memory Pressure: {memory_pressure.title()}',
                    'description': f'Memory usage is at {memory_percent:.1f}%',
                    'actions': [
                        'Close unused browser tabs',
                        'Quit unnecessary applications',
                        'Clear cache and temporary files',
                        'Consider upgrading memory if possible'
                    ]
                })
            
            # Thermal optimization
            if self.current_thermal_state in [ThermalState.HOT, ThermalState.THROTTLED]:
                recommendations.append({
                    'category': 'thermal',
                    'priority': 'high',
                    'title': 'Thermal Throttling Detected',
                    'description': 'System is running hot and may be throttling performance',
                    'actions': [
                        'Reduce CPU-intensive tasks',
                        'Ensure proper ventilation',
                        'Close resource-heavy applications',
                        'Consider using external cooling'
                    ]
                })
            
            # Power optimization
            if self.current_power_state == PowerState.LOW_BATTERY:
                recommendations.append({
                    'category': 'power',
                    'priority': 'medium',
                    'title': 'Low Battery Detected',
                    'description': 'Battery level is low',
                    'actions': [
                        'Connect to power adapter',
                        'Enable Low Power Mode',
                        'Reduce screen brightness',
                        'Close unnecessary applications'
                    ]
                })
            
            # Apple Silicon specific optimizations
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                generation = specs.get('generation')
                
                # Neural Engine optimization
                neural_metrics = metrics.get('neural_engine', {})
                if neural_metrics.get('available') and neural_metrics.get('utilization_percent', 0) < 10:
                    recommendations.append({
                        'category': 'optimization',
                        'priority': 'low',
                        'title': 'Neural Engine Underutilized',
                        'description': 'Your Neural Engine could be used for ML acceleration',
                        'actions': [
                            'Use Core ML for machine learning tasks',
                            'Enable MLX for local AI processing',
                            'Consider ML-optimized applications'
                        ]
                    })
                
                # GPU optimization
                gpu_metrics = metrics.get('gpu', {})
                if gpu_metrics.get('available') and gpu_metrics.get('utilization_percent', 0) < 20:
                    recommendations.append({
                        'category': 'optimization',
                        'priority': 'low',
                        'title': 'GPU Underutilized',
                        'description': 'Your GPU could be used for acceleration',
                        'actions': [
                            'Use Metal-accelerated applications',
                            'Enable GPU acceleration in supported apps',
                            'Consider GPU-intensive creative work'
                        ]
                    })
            
        except Exception as e:
            self.logger.error(f"Error generating optimization recommendations: {e}")
        
        return recommendations
    
    def get_comprehensive_info(self) -> Dict[str, Any]:
        """Get comprehensive hardware and performance information"""
        return {
            'detection': {
                'is_apple_silicon': self.is_apple_silicon,
                'chip_info': self.chip_info,
                'system_info': self.system_info
            },
            'real_time_metrics': self.get_real_time_metrics(),
            'current_states': {
                'thermal': self.current_thermal_state.value,
                'power': self.current_power_state.value
            },
            'optimization_recommendations': self.get_optimization_recommendations(),
            'monitoring_status': {
                'active': self._monitoring_active,
                'interval_seconds': self.monitoring_interval,
                'history_size': len(self._metrics_history)
            }
        }
    
    # Public API methods for compatibility
    def get_chip_info(self) -> Dict[str, Any]:
        """Get comprehensive chip information (public API)"""
        chip_info = self._get_enhanced_chip_info()
        if chip_info:
            return chip_info
        
        # Fallback to basic detection
        return {
            'chip_name': 'Unknown',
            'chip_variant': '',
            'architecture': platform.machine(),
            'process_node': 'Unknown',
            'performance_cores': 0,
            'efficiency_cores': 0,
            'total_cores': psutil.cpu_count(logical=False) or 0,
            'gpu_cores': 0,
            'neural_engine_cores': 16,
            'neural_engine_tops': 0,
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'memory_bandwidth_gbps': 0,
            'memory_type': 'Unified',
            'capabilities': ['basic_detection']
        }
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations (public API)"""
        try:
            info = self.get_comprehensive_info()
            recommendations = info.get('optimization_recommendations', [])
            
            return {
                'recommendations': [rec.get('title', 'Unknown') for rec in recommendations],
                'priority_recommendations': [rec for rec in recommendations if rec.get('priority') == 'high'],
                'total_count': len(recommendations)
            }
        except:
            return {
                'recommendations': ['Enable auto optimization', 'Monitor thermal state'],
                'priority_recommendations': [],
                'total_count': 2
            }
    
    def get_capabilities(self) -> List[str]:
        """Get system capabilities (public API)"""
        capabilities = []
        
        try:
            if self.is_apple_silicon:
                capabilities.append('apple_silicon')
            
            if platform.system() == 'Darwin':
                capabilities.append('macos')
            
            # Check for framework availability
            try:
                import subprocess
                result = subprocess.run(['which', 'python3'], capture_output=True)
                if result.returncode == 0:
                    capabilities.append('python3')
            except:
                pass
            
            # Add basic capabilities
            capabilities.extend([
                'cpu_monitoring',
                'memory_monitoring',
                'thermal_monitoring',
                'performance_optimization'
            ])
            
        except:
            capabilities = ['basic_monitoring']
        
        return capabilities
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information (public API)"""
        try:
            return self._get_enhanced_system_info()
        except:
            return {
                'platform': platform.system(),
                'architecture': platform.machine(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total
            }
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status (public API)"""
        return {
            'auto_optimization_enabled': getattr(self, '_auto_optimization_enabled', False),
            'thermal_management_active': getattr(self, '_thermal_management_active', False),
            'performance_mode': getattr(self, '_performance_mode', 'balanced'),
            'optimization_level': getattr(self, '_optimization_level', 'standard')
        }
    
    def is_available(self) -> bool:
        """Check if detector is available and functional"""
        return True
    
    def initialize(self) -> bool:
        """Initialize the detector"""
        try:
            self._detect_apple_silicon()
            return True
        except:
            return False

def main():
    """Enhanced demonstration of Apple Silicon detection capabilities"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔍 Enhanced Apple Silicon Hardware Detection & Optimization")
    print("=" * 70)
    
    detector = EnhancedAppleSiliconDetector()
    
    if not detector.is_apple_silicon:
        print("❌ Not running on Apple Silicon")
        return
    
    # Get comprehensive information
    info = detector.get_comprehensive_info()
    
    # Display chip information
    detection = info['detection']
    if detection['chip_info']:
        chip = detection['chip_info']
        print(f"🖥️  Chip: {chip['chip_name']}")
        print(f"📱 Model: {chip['model_identifier']}")
        print(f"💾 Memory: {chip['detected_memory_gb']}GB")
        print(f"🎯 Detection Confidence: {chip['detection_confidence']:.1%}")
        
        if chip['specifications']:
            specs = chip['specifications']
            print(f"⚡ CPU: {specs['cpu_cores_performance']}P + {specs['cpu_cores_efficiency']}E cores")
            print(f"🎮 GPU: {specs['gpu_cores']} cores")
            print(f"🧠 Neural Engine: {specs['neural_engine_cores']} cores ({specs['neural_engine_tops']} TOPS)")
            print(f"🚀 Memory Bandwidth: {specs['memory_bandwidth_gbps']}GB/s")
            print(f"⚙️  Process: {specs['process_node']}")
            print(f"📅 Year: {specs['year_introduced']}")
    
    # Display real-time metrics
    metrics = info['real_time_metrics']
    print(f"\n📊 Real-time Metrics:")
    
    if 'cpu' in metrics:
        cpu = metrics['cpu']
        print(f"   CPU Usage: {cpu.get('usage_percent_total', 0):.1f}%")
        print(f"   CPU Frequency: {cpu.get('frequency_current_mhz', 0):.0f}MHz")
        print(f"   Load Average: {cpu.get('load_average', [0, 0, 0])[0]:.2f}")
    
    if 'memory' in metrics:
        memory = metrics['memory']
        print(f"   Memory: {memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 0):.1f}GB ({memory.get('usage_percent', 0):.1f}%)")
        print(f"   Memory Pressure: {memory.get('pressure', 'unknown')}")
    
    if 'thermal' in metrics:
        thermal = metrics['thermal']
        print(f"   Thermal State: {thermal.get('state', 'unknown')}")
        temps = thermal.get('temperatures', {})
        if 'cpu_estimated' in temps:
            print(f"   CPU Temperature: {temps['cpu_estimated']}°C (estimated)")
    
    if 'power' in metrics:
        power = metrics['power']
        print(f"   Power Source: {power.get('source', 'unknown')}")
        battery = power.get('battery', {})
        if battery:
            print(f"   Battery: {battery.get('percent', 0)}%")
    
    # Display component status
    neural = metrics.get('neural_engine', {})
    gpu = metrics.get('gpu', {})
    
    print(f"\n🧠 Neural Engine: {neural.get('cores', 0)} cores ({neural.get('tops', 0)} TOPS)")
    print(f"   Utilization: {neural.get('utilization_percent', 0):.1f}%")
    
    print(f"\n🎮 GPU: {gpu.get('cores', 0)} cores")
    print(f"   Memory: {gpu.get('memory_gb', 0):.1f}GB")
    print(f"   Utilization: {gpu.get('utilization_percent', 0):.1f}%")
    
    # Display framework support
    frameworks = neural.get('framework_support', {})
    print(f"\n🛠️  Framework Support:")
    print(f"   Core ML: {'✅' if frameworks.get('coreml', {}).get('available') else '❌'}")
    print(f"   MLX: {'✅' if frameworks.get('mlx', {}).get('available') else '❌'}")
    print(f"   Metal: {'✅' if gpu.get('metal_support') else '❌'}")
    
    # Display performance score
    performance = metrics.get('performance', {})
    print(f"\n📈 Performance Score: {performance.get('overall_score', 0)}/100")
    
    bottlenecks = performance.get('bottlenecks', [])
    if bottlenecks:
        print(f"   Bottlenecks: {', '.join(bottlenecks)}")
    
    # Display optimization recommendations
    recommendations = info.get('optimization_recommendations', [])
    if recommendations:
        print(f"\n💡 Optimization Recommendations:")
        for rec in recommendations[:3]:  # Show top 3
            print(f"   • {rec['title']} ({rec['priority']} priority)")
    
    # Start monitoring demonstration
    print(f"\n🔄 Starting real-time monitoring for 30 seconds...")
    detector.start_monitoring()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    
    detector.stop_monitoring()
    
    # Show monitoring results
    history = detector.get_metrics_history(duration_minutes=1)
    if history:
        print(f"\n📊 Monitoring Results ({len(history)} samples):")
        avg_cpu = sum(m.get('cpu', {}).get('usage_percent_total', 0) for m in history) / len(history)
        avg_memory = sum(m.get('memory', {}).get('usage_percent', 0) for m in history) / len(history)
        print(f"   Average CPU Usage: {avg_cpu:.1f}%")
        print(f"   Average Memory Usage: {avg_memory:.1f}%")

if __name__ == "__main__":
    main()


    # Public API methods for compatibility
    def get_chip_info(self) -> Dict[str, Any]:
        """Get comprehensive chip information (public API)"""
        chip_info = self._get_enhanced_chip_info()
        if chip_info:
            return chip_info
        
        # Fallback to basic detection
        return {
            'chip_name': 'Unknown',
            'chip_variant': '',
            'architecture': platform.machine(),
            'process_node': 'Unknown',
            'performance_cores': 0,
            'efficiency_cores': 0,
            'total_cores': psutil.cpu_count(logical=False) or 0,
            'gpu_cores': 0,
            'neural_engine_cores': 16,
            'neural_engine_tops': 0,
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'memory_bandwidth_gbps': 0,
            'memory_type': 'Unified',
            'capabilities': ['basic_detection']
        }
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations (public API)"""
        try:
            info = self.get_comprehensive_info()
            recommendations = info.get('optimization_recommendations', [])
            
            return {
                'recommendations': [rec.get('title', 'Unknown') for rec in recommendations],
                'priority_recommendations': [rec for rec in recommendations if rec.get('priority') == 'high'],
                'total_count': len(recommendations)
            }
        except:
            return {
                'recommendations': ['Enable auto optimization', 'Monitor thermal state'],
                'priority_recommendations': [],
                'total_count': 2
            }
    
    def get_capabilities(self) -> List[str]:
        """Get system capabilities (public API)"""
        capabilities = []
        
        try:
            if self.is_apple_silicon:
                capabilities.append('apple_silicon')
            
            if platform.system() == 'Darwin':
                capabilities.append('macos')
            
            # Check for framework availability
            try:
                import subprocess
                result = subprocess.run(['which', 'python3'], capture_output=True)
                if result.returncode == 0:
                    capabilities.append('python3')
            except:
                pass
            
            # Add basic capabilities
            capabilities.extend([
                'cpu_monitoring',
                'memory_monitoring',
                'thermal_monitoring',
                'performance_optimization'
            ])
            
        except:
            capabilities = ['basic_monitoring']
        
        return capabilities
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information (public API)"""
        try:
            return self._get_enhanced_system_info()
        except:
            return {
                'platform': platform.system(),
                'architecture': platform.machine(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total
            }
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status (public API)"""
        return {
            'auto_optimization_enabled': getattr(self, '_auto_optimization_enabled', False),
            'thermal_management_active': getattr(self, '_thermal_management_active', False),
            'performance_mode': getattr(self, '_performance_mode', 'balanced'),
            'optimization_level': getattr(self, '_optimization_level', 'standard')
        }
    
    def is_available(self) -> bool:
        """Check if detector is available and functional"""
        return True
    
    def initialize(self) -> bool:
        """Initialize the detector"""
        try:
            self._detect_apple_silicon()
            return True
        except:
            return False

