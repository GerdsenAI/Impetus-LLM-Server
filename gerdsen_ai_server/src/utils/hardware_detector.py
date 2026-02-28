"""
Apple Silicon Hardware Detection and Optimization
Detects M1/M2/M3/M4 chips and their capabilities
"""

import platform
import subprocess

import psutil
from loguru import logger


def run_command(cmd: list) -> str | None:
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Command {' '.join(cmd)} failed: {e}")
        return None


def detect_apple_silicon() -> dict[str, any]:
    """Detect Apple Silicon chip type and capabilities"""
    chip_info = {
        'chip_type': 'Unknown',
        'cpu_name': 'Unknown',
        'performance_cores': 0,
        'efficiency_cores': 0,
        'gpu_cores': 0,
        'neural_engine_cores': 0,
        'architecture': platform.machine(),
        'max_memory_bandwidth_gbps': 0
    }

    # Check if we're on macOS
    if platform.system() != 'Darwin':
        return chip_info

    # Get CPU brand string
    cpu_brand = run_command(['sysctl', '-n', 'machdep.cpu.brand_string'])
    if cpu_brand:
        chip_info['cpu_name'] = cpu_brand

        # Determine chip type from brand string
        if 'M5' in cpu_brand:
            chip_info['chip_type'] = 'M5'
            if 'Ultra' in cpu_brand:
                chip_info['chip_type'] = 'M5 Ultra'
                chip_info['performance_cores'] = 24
                chip_info['efficiency_cores'] = 8
                chip_info['gpu_cores'] = 80
                chip_info['max_memory_bandwidth_gbps'] = 1200
            elif 'Max' in cpu_brand:
                chip_info['chip_type'] = 'M5 Max'
                chip_info['performance_cores'] = 14
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 48
                chip_info['max_memory_bandwidth_gbps'] = 600
            elif 'Pro' in cpu_brand:
                chip_info['chip_type'] = 'M5 Pro'
                chip_info['performance_cores'] = 12
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 24
                chip_info['max_memory_bandwidth_gbps'] = 300
            else:
                # Base M5
                chip_info['performance_cores'] = 6
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 12
                chip_info['max_memory_bandwidth_gbps'] = 150
        elif 'M4' in cpu_brand:
            chip_info['chip_type'] = 'M4'
            if 'Pro' in cpu_brand:
                chip_info['chip_type'] = 'M4 Pro'
                chip_info['performance_cores'] = 10
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 20
                chip_info['max_memory_bandwidth_gbps'] = 273
            elif 'Max' in cpu_brand:
                chip_info['chip_type'] = 'M4 Max'
                chip_info['performance_cores'] = 12
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 40
                chip_info['max_memory_bandwidth_gbps'] = 546
            else:
                # Base M4
                chip_info['performance_cores'] = 4
                chip_info['efficiency_cores'] = 6
                chip_info['gpu_cores'] = 10
                chip_info['max_memory_bandwidth_gbps'] = 120
        elif 'M3' in cpu_brand:
            chip_info['chip_type'] = 'M3'
            if 'Ultra' in cpu_brand:
                chip_info['chip_type'] = 'M3 Ultra'
                chip_info['performance_cores'] = 24
                chip_info['efficiency_cores'] = 8
                chip_info['gpu_cores'] = 76
                chip_info['max_memory_bandwidth_gbps'] = 800
            elif 'Max' in cpu_brand:
                chip_info['chip_type'] = 'M3 Max'
                chip_info['performance_cores'] = 12
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 40
                chip_info['max_memory_bandwidth_gbps'] = 400
            elif 'Pro' in cpu_brand:
                chip_info['chip_type'] = 'M3 Pro'
                chip_info['performance_cores'] = 6
                chip_info['efficiency_cores'] = 6
                chip_info['gpu_cores'] = 18
                chip_info['max_memory_bandwidth_gbps'] = 150
            else:
                # Base M3
                chip_info['performance_cores'] = 4
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 10
                chip_info['max_memory_bandwidth_gbps'] = 100
        elif 'M2' in cpu_brand:
            chip_info['chip_type'] = 'M2'
            if 'Ultra' in cpu_brand:
                chip_info['chip_type'] = 'M2 Ultra'
                chip_info['performance_cores'] = 16
                chip_info['efficiency_cores'] = 8
                chip_info['gpu_cores'] = 76
                chip_info['max_memory_bandwidth_gbps'] = 800
            elif 'Max' in cpu_brand:
                chip_info['chip_type'] = 'M2 Max'
                chip_info['performance_cores'] = 8
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 38
                chip_info['max_memory_bandwidth_gbps'] = 400
            elif 'Pro' in cpu_brand:
                chip_info['chip_type'] = 'M2 Pro'
                chip_info['performance_cores'] = 6
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 19
                chip_info['max_memory_bandwidth_gbps'] = 200
            else:
                # Base M2
                chip_info['performance_cores'] = 4
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 10
                chip_info['max_memory_bandwidth_gbps'] = 100
        elif 'M1' in cpu_brand:
            chip_info['chip_type'] = 'M1'
            if 'Ultra' in cpu_brand:
                chip_info['chip_type'] = 'M1 Ultra'
                chip_info['performance_cores'] = 16
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 64
                chip_info['max_memory_bandwidth_gbps'] = 800
            elif 'Max' in cpu_brand:
                chip_info['chip_type'] = 'M1 Max'
                chip_info['performance_cores'] = 8
                chip_info['efficiency_cores'] = 2
                chip_info['gpu_cores'] = 32
                chip_info['max_memory_bandwidth_gbps'] = 400
            elif 'Pro' in cpu_brand:
                chip_info['chip_type'] = 'M1 Pro'
                chip_info['performance_cores'] = 8
                chip_info['efficiency_cores'] = 2
                chip_info['gpu_cores'] = 16
                chip_info['max_memory_bandwidth_gbps'] = 200
            else:
                # Base M1
                chip_info['performance_cores'] = 4
                chip_info['efficiency_cores'] = 4
                chip_info['gpu_cores'] = 8
                chip_info['max_memory_bandwidth_gbps'] = 68.25

    # All Apple Silicon chips have 16-core Neural Engine
    if chip_info['chip_type'] != 'Unknown':
        chip_info['neural_engine_cores'] = 16

    # Get actual core counts from system
    perf_cores = run_command(['sysctl', '-n', 'hw.perflevel0.physicalcpu'])
    eff_cores = run_command(['sysctl', '-n', 'hw.perflevel1.physicalcpu'])

    if perf_cores:
        chip_info['performance_cores'] = int(perf_cores)
    if eff_cores:
        chip_info['efficiency_cores'] = int(eff_cores)

    return chip_info


def detect_ane_availability() -> dict[str, any]:
    """Detect Apple Neural Engine availability and version"""
    ane_info = {
        'available': False,
        'version': 0,
        'compute_units': 'cpu_only',
    }

    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        return ane_info

    # Check if Core ML framework is importable
    try:
        import coremltools  # noqa: F401
        ane_info['coremltools_available'] = True
    except ImportError:
        ane_info['coremltools_available'] = False

    # Check ANE hardware via sysctl
    ane_version = run_command(['sysctl', '-n', 'hw.optional.ane.version'])
    if ane_version:
        try:
            ane_info['version'] = int(ane_version)
            ane_info['available'] = True
            ane_info['compute_units'] = 'cpu_and_ne'
        except ValueError:
            pass

    # All Apple Silicon has ANE even if sysctl key is missing
    chip_brand = run_command(['sysctl', '-n', 'machdep.cpu.brand_string'])
    if chip_brand and any(f'M{n}' in chip_brand for n in range(1, 10)):
        ane_info['available'] = True
        if ane_info['compute_units'] == 'cpu_only':
            ane_info['compute_units'] = 'cpu_and_ne'

    return ane_info


def get_memory_info() -> dict[str, float]:
    """Get system memory information"""
    memory = psutil.virtual_memory()
    return {
        'total_memory_gb': memory.total / (1024 ** 3),
        'available_memory_gb': memory.available / (1024 ** 3),
        'used_memory_gb': memory.used / (1024 ** 3),
        'memory_percent': memory.percent
    }


def get_thermal_state() -> dict[str, any]:
    """Get thermal state information (macOS specific)"""
    thermal_info = {
        'thermal_state': 'nominal',
        'thermal_pressure': 0,
        'fan_speed_rpm': 0
    }

    if platform.system() != 'Darwin':
        return thermal_info

    # Get thermal state using powermetrics (requires sudo)
    # For now, we'll use a simplified approach
    thermal_state = run_command(['sysctl', '-n', 'machdep.xcpm.cpu_thermal_level'])
    if thermal_state:
        level = int(thermal_state)
        if level == 0:
            thermal_info['thermal_state'] = 'nominal'
        elif level <= 50:
            thermal_info['thermal_state'] = 'fair'
        elif level <= 80:
            thermal_info['thermal_state'] = 'serious'
        else:
            thermal_info['thermal_state'] = 'critical'
        thermal_info['thermal_pressure'] = level

    return thermal_info


def detect_hardware() -> dict[str, any]:
    """Complete hardware detection combining all information"""
    hardware_info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(logical=True),
        'cpu_count_physical': psutil.cpu_count(logical=False)
    }

    # Add Apple Silicon specific info
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        silicon_info = detect_apple_silicon()
        hardware_info.update(silicon_info)

        # Add ANE detection
        ane_info = detect_ane_availability()
        hardware_info['ane_available'] = ane_info['available']
        hardware_info['ane_version'] = ane_info['version']
        hardware_info['ane_compute_units'] = ane_info['compute_units']
        hardware_info['memory_bandwidth_gbps'] = silicon_info.get('max_memory_bandwidth_gbps', 0)

    # Add memory info
    memory_info = get_memory_info()
    hardware_info.update(memory_info)

    # Add thermal info
    thermal_info = get_thermal_state()
    hardware_info.update(thermal_info)

    # Calculate optimization recommendations
    hardware_info['recommended_batch_size'] = 1
    hardware_info['recommended_context_length'] = 2048

    if hardware_info.get('chip_type', '').startswith('M'):
        # Optimize based on memory bandwidth
        bandwidth = hardware_info.get('max_memory_bandwidth_gbps', 100)
        if bandwidth >= 400:  # Max/Ultra chips
            hardware_info['recommended_batch_size'] = 4
            hardware_info['recommended_context_length'] = 8192
        elif bandwidth >= 200:  # Pro chips
            hardware_info['recommended_batch_size'] = 2
            hardware_info['recommended_context_length'] = 4096

    return hardware_info


if __name__ == "__main__":
    # Test hardware detection
    import json
    info = detect_hardware()
    print(json.dumps(info, indent=2))
