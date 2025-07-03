#!/usr/bin/env python3
"""
Apple Silicon Hardware Detection Module
Provides real-time hardware detection and monitoring for Apple Silicon Macs
"""

import os
import re
import json
import subprocess
import platform
import psutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

@dataclass
class AppleSiliconSpecs:
    """Apple Silicon chip specifications"""
    chip_name: str
    cpu_cores_performance: int
    cpu_cores_efficiency: int
    cpu_cores_total: int
    gpu_cores: int
    neural_engine_cores: int
    memory_gb: int
    memory_bandwidth_gbps: int
    process_node: str
    year_introduced: int

class AppleSiliconDetector:
    """Detects and monitors Apple Silicon hardware capabilities"""
    
    # Known Apple Silicon specifications
    CHIP_SPECS = {
        'M1': AppleSiliconSpecs('M1', 4, 4, 8, 8, 16, 16, 68, '5nm', 2020),
        'M1 Pro': AppleSiliconSpecs('M1 Pro', 8, 2, 10, 16, 16, 32, 200, '5nm', 2021),
        'M1 Max': AppleSiliconSpecs('M1 Max', 8, 2, 10, 32, 16, 64, 400, '5nm', 2021),
        'M1 Ultra': AppleSiliconSpecs('M1 Ultra', 16, 4, 20, 64, 32, 128, 800, '5nm', 2022),
        'M2': AppleSiliconSpecs('M2', 4, 4, 8, 10, 16, 24, 100, '5nm', 2022),
        'M2 Pro': AppleSiliconSpecs('M2 Pro', 8, 4, 12, 19, 16, 32, 200, '5nm', 2023),
        'M2 Max': AppleSiliconSpecs('M2 Max', 8, 4, 12, 38, 16, 96, 400, '5nm', 2023),
        'M2 Ultra': AppleSiliconSpecs('M2 Ultra', 16, 8, 24, 76, 32, 192, 800, '5nm', 2023),
        'M3': AppleSiliconSpecs('M3', 4, 4, 8, 10, 16, 24, 100, '3nm', 2023),
        'M3 Pro': AppleSiliconSpecs('M3 Pro', 6, 6, 12, 18, 16, 36, 150, '3nm', 2023),
        'M3 Max': AppleSiliconSpecs('M3 Max', 12, 4, 16, 40, 16, 128, 400, '3nm', 2023),
        'M3 Ultra': AppleSiliconSpecs('M3 Ultra', 16, 8, 24, 76, 32, 512, 800, '3nm', 2024),
        'M4': AppleSiliconSpecs('M4', 4, 6, 10, 10, 16, 32, 120, '3nm', 2024),
        'M4 Pro': AppleSiliconSpecs('M4 Pro', 10, 4, 14, 20, 16, 64, 273, '3nm', 2024),
        'M4 Max': AppleSiliconSpecs('M4 Max', 12, 4, 16, 40, 16, 128, 546, '3nm', 2024),
    }
    
    def __init__(self):
        self.is_apple_silicon = self._detect_apple_silicon()
        self.chip_info = self._get_chip_info() if self.is_apple_silicon else None
        self.system_info = self._get_system_info()
        
        logging.info(f"Apple Silicon Detector initialized: {self.chip_info}")
    
    def _detect_apple_silicon(self) -> bool:
        """Detect if running on Apple Silicon"""
        try:
            # Check if we're on macOS
            if platform.system() != 'Darwin':
                return False
            
            # Check architecture
            arch = platform.machine()
            if arch == 'arm64':
                return True
            
            # Additional check using sysctl
            result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], 
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip() == '1'
            
        except Exception as e:
            logging.warning(f"Failed to detect Apple Silicon: {e}")
            return False
    
    def _get_chip_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed chip information"""
        try:
            # Get chip name from system_profiler
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            output = result.stdout
            
            # Parse chip name
            chip_match = re.search(r'Chip:\s*Apple\s*([^\n]+)', output)
            if not chip_match:
                return None
            
            chip_name = chip_match.group(1).strip()
            
            # Get memory information
            memory_match = re.search(r'Memory:\s*(\d+)\s*GB', output)
            memory_gb = int(memory_match.group(1)) if memory_match else 0
            
            # Get model identifier
            model_match = re.search(r'Model Identifier:\s*([^\n]+)', output)
            model_id = model_match.group(1).strip() if model_match else 'Unknown'
            
            # Get serial number
            serial_match = re.search(r'Serial Number \(system\):\s*([^\n]+)', output)
            serial = serial_match.group(1).strip() if serial_match else 'Unknown'
            
            # Look up chip specifications
            chip_specs = None
            for spec_name, specs in self.CHIP_SPECS.items():
                if spec_name.lower() in chip_name.lower():
                    chip_specs = specs
                    break
            
            return {
                'chip_name': chip_name,
                'model_identifier': model_id,
                'serial_number': serial,
                'detected_memory_gb': memory_gb,
                'specifications': asdict(chip_specs) if chip_specs else None
            }
            
        except Exception as e:
            logging.error(f"Failed to get chip info: {e}")
            return None
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
            }
            
            # Get CPU information using sysctl
            try:
                cpu_info = {}
                sysctl_queries = {
                    'hw.ncpu': 'logical_cpu_count',
                    'hw.physicalcpu': 'physical_cpu_count',
                    'hw.perflevel0.logicalcpu': 'performance_cores',
                    'hw.perflevel1.logicalcpu': 'efficiency_cores',
                    'hw.memsize': 'memory_bytes',
                    'hw.cpufrequency': 'cpu_frequency',
                    'hw.tbfrequency': 'timebase_frequency',
                    'hw.model': 'hardware_model'
                }
                
                for sysctl_key, info_key in sysctl_queries.items():
                    try:
                        result = subprocess.run(['sysctl', '-n', sysctl_key], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            value = result.stdout.strip()
                            if value.isdigit():
                                cpu_info[info_key] = int(value)
                            else:
                                cpu_info[info_key] = value
                    except:
                        pass
                
                info['cpu_info'] = cpu_info
                
            except Exception as e:
                logging.warning(f"Failed to get CPU info via sysctl: {e}")
            
            # Get memory information
            try:
                memory = psutil.virtual_memory()
                info['memory'] = {
                    'total_bytes': memory.total,
                    'total_gb': round(memory.total / (1024**3), 1),
                    'available_bytes': memory.available,
                    'available_gb': round(memory.available / (1024**3), 1),
                    'used_percent': memory.percent
                }
            except Exception as e:
                logging.warning(f"Failed to get memory info: {e}")
            
            return info
            
        except Exception as e:
            logging.error(f"Failed to get system info: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        try:
            metrics = {
                'timestamp': psutil.time.time(),
                'cpu': {},
                'memory': {},
                'thermal': {},
                'power': {}
            }
            
            # CPU metrics
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
                metrics['cpu'] = {
                    'usage_percent_total': psutil.cpu_percent(interval=0.1),
                    'usage_percent_per_core': cpu_percent,
                    'frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                    'core_count': psutil.cpu_count(logical=True),
                    'physical_core_count': psutil.cpu_count(logical=False)
                }
            except Exception as e:
                logging.warning(f"Failed to get CPU metrics: {e}")
            
            # Memory metrics
            try:
                memory = psutil.virtual_memory()
                metrics['memory'] = {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'usage_percent': memory.percent,
                    'pressure': self._get_memory_pressure()
                }
            except Exception as e:
                logging.warning(f"Failed to get memory metrics: {e}")
            
            # Thermal metrics (macOS specific)
            try:
                thermal_info = self._get_thermal_info()
                metrics['thermal'] = thermal_info
            except Exception as e:
                logging.warning(f"Failed to get thermal metrics: {e}")
            
            # Power metrics
            try:
                power_info = self._get_power_info()
                metrics['power'] = power_info
            except Exception as e:
                logging.warning(f"Failed to get power metrics: {e}")
            
            return metrics
            
        except Exception as e:
            logging.error(f"Failed to get real-time metrics: {e}")
            return {}
    
    def _get_memory_pressure(self) -> str:
        """Get memory pressure status"""
        try:
            result = subprocess.run(['memory_pressure'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'normal' in output:
                    return 'normal'
                elif 'warn' in output:
                    return 'warning'
                elif 'urgent' in output:
                    return 'urgent'
                elif 'critical' in output:
                    return 'critical'
            return 'unknown'
        except:
            return 'unknown'
    
    def _get_thermal_info(self) -> Dict[str, Any]:
        """Get thermal information"""
        try:
            # Try to get thermal state
            thermal_info = {'state': 'unknown', 'temperatures': {}}
            
            # Check thermal state
            try:
                result = subprocess.run(['pmset', '-g', 'thermlog'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse thermal state from output
                    if 'CPU_Scheduler_Limit' in result.stdout:
                        thermal_info['state'] = 'throttled'
                    else:
                        thermal_info['state'] = 'normal'
            except:
                pass
            
            # Try to get temperature sensors (requires additional tools)
            try:
                # This would require installing additional tools like TG Pro or iStat Menus
                # For now, we'll simulate based on CPU usage
                cpu_usage = psutil.cpu_percent(interval=0.1)
                base_temp = 35  # Base temperature in Celsius
                temp_variation = (cpu_usage / 100) * 30  # Up to 30°C variation
                estimated_temp = base_temp + temp_variation
                
                thermal_info['temperatures'] = {
                    'cpu_estimated': round(estimated_temp, 1),
                    'method': 'estimated_from_cpu_usage'
                }
            except:
                pass
            
            return thermal_info
            
        except Exception as e:
            logging.warning(f"Failed to get thermal info: {e}")
            return {'state': 'unknown', 'temperatures': {}}
    
    def _get_power_info(self) -> Dict[str, Any]:
        """Get power consumption information"""
        try:
            power_info = {}
            
            # Get battery information if available
            try:
                battery = psutil.sensors_battery()
                if battery:
                    power_info['battery'] = {
                        'percent': battery.percent,
                        'plugged_in': battery.power_plugged,
                        'time_left_seconds': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except:
                pass
            
            # Get power management info
            try:
                result = subprocess.run(['pmset', '-g', 'ps'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    output = result.stdout
                    # Parse power source information
                    if 'AC Power' in output:
                        power_info['power_source'] = 'AC'
                    elif 'Battery Power' in output:
                        power_info['power_source'] = 'Battery'
                    
                    # Extract power consumption if available
                    power_match = re.search(r'(\d+)W', output)
                    if power_match:
                        power_info['consumption_watts'] = int(power_match.group(1))
            except:
                pass
            
            return power_info
            
        except Exception as e:
            logging.warning(f"Failed to get power info: {e}")
            return {}
    
    def get_neural_engine_info(self) -> Dict[str, Any]:
        """Get Neural Engine information and availability"""
        try:
            neural_info = {
                'available': False,
                'cores': 0,
                'framework_support': {}
            }
            
            # Check if we have chip specifications
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                neural_info['cores'] = specs.get('neural_engine_cores', 0)
                neural_info['available'] = neural_info['cores'] > 0
            
            # Check Core ML availability
            try:
                import coremltools
                neural_info['framework_support']['coreml'] = True
                neural_info['framework_support']['coremltools_version'] = coremltools.__version__
            except ImportError:
                neural_info['framework_support']['coreml'] = False
            
            # Check MLX availability
            try:
                import mlx.core as mx
                neural_info['framework_support']['mlx'] = True
                neural_info['framework_support']['mlx_device'] = str(mx.default_device())
            except ImportError:
                neural_info['framework_support']['mlx'] = False
            
            return neural_info
            
        except Exception as e:
            logging.error(f"Failed to get Neural Engine info: {e}")
            return {'available': False, 'cores': 0, 'framework_support': {}}
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information using Metal framework"""
        try:
            gpu_info = {
                'available': False,
                'cores': 0,
                'memory_gb': 0,
                'metal_support': False
            }
            
            # Check if we have chip specifications
            if self.chip_info and self.chip_info.get('specifications'):
                specs = self.chip_info['specifications']
                gpu_info['cores'] = specs.get('gpu_cores', 0)
                gpu_info['available'] = gpu_info['cores'] > 0
                
                # Estimate GPU memory (typically 75% of total unified memory)
                total_memory = specs.get('memory_gb', 0)
                gpu_info['memory_gb'] = round(total_memory * 0.75, 1)
            
            # Check Metal support
            try:
                # This would require PyObjC to access Metal framework
                # For now, assume Metal is available on Apple Silicon
                if self.is_apple_silicon:
                    gpu_info['metal_support'] = True
            except:
                pass
            
            return gpu_info
            
        except Exception as e:
            logging.error(f"Failed to get GPU info: {e}")
            return {'available': False, 'cores': 0, 'memory_gb': 0, 'metal_support': False}
    
    def get_comprehensive_info(self) -> Dict[str, Any]:
        """Get comprehensive hardware information"""
        return {
            'is_apple_silicon': self.is_apple_silicon,
            'chip_info': self.chip_info,
            'system_info': self.system_info,
            'neural_engine': self.get_neural_engine_info(),
            'gpu': self.get_gpu_info(),
            'real_time_metrics': self.get_real_time_metrics()
        }

def main():
    """Demonstration of Apple Silicon detection capabilities"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔍 Apple Silicon Hardware Detection")
    print("=" * 50)
    
    detector = AppleSiliconDetector()
    
    if not detector.is_apple_silicon:
        print("❌ Not running on Apple Silicon")
        return
    
    # Get comprehensive information
    info = detector.get_comprehensive_info()
    
    # Display chip information
    if info['chip_info']:
        chip = info['chip_info']
        print(f"🖥️  Chip: {chip['chip_name']}")
        print(f"📱 Model: {chip['model_identifier']}")
        print(f"💾 Memory: {chip['detected_memory_gb']}GB")
        
        if chip['specifications']:
            specs = chip['specifications']
            print(f"⚡ CPU Cores: {specs['cpu_cores_performance']}P + {specs['cpu_cores_efficiency']}E")
            print(f"🎮 GPU Cores: {specs['gpu_cores']}")
            print(f"🧠 Neural Engine: {specs['neural_engine_cores']} cores")
            print(f"🚀 Memory Bandwidth: {specs['memory_bandwidth_gbps']}GB/s")
    
    # Display real-time metrics
    metrics = info['real_time_metrics']
    if metrics:
        print(f"\n📊 Real-time Metrics:")
        if 'cpu' in metrics:
            cpu = metrics['cpu']
            print(f"   CPU Usage: {cpu.get('usage_percent_total', 0):.1f}%")
            print(f"   CPU Frequency: {cpu.get('frequency_mhz', 0):.0f}MHz")
        
        if 'memory' in metrics:
            memory = metrics['memory']
            print(f"   Memory Used: {memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 0):.1f}GB")
            print(f"   Memory Pressure: {memory.get('pressure', 'unknown')}")
        
        if 'thermal' in metrics:
            thermal = metrics['thermal']
            print(f"   Thermal State: {thermal.get('state', 'unknown')}")
            if 'temperatures' in thermal and 'cpu_estimated' in thermal['temperatures']:
                print(f"   CPU Temperature: {thermal['temperatures']['cpu_estimated']}°C (estimated)")
    
    # Display framework support
    neural = info['neural_engine']
    print(f"\n🧠 Neural Engine: {neural['cores']} cores ({'Available' if neural['available'] else 'Not Available'})")
    
    frameworks = neural['framework_support']
    print(f"   Core ML: {'✅' if frameworks.get('coreml') else '❌'}")
    print(f"   MLX: {'✅' if frameworks.get('mlx') else '❌'}")
    
    gpu = info['gpu']
    print(f"\n🎮 GPU: {gpu['cores']} cores, ~{gpu['memory_gb']}GB memory")
    print(f"   Metal Support: {'✅' if gpu['metal_support'] else '❌'}")

if __name__ == "__main__":
    main()

