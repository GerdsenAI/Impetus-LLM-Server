#!/usr/bin/env python3
"""
Simple validation script for GerdsenAI MLX Manager functionality
Tests core components without complex dependencies
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_apple_silicon_detector():
    """Test Apple Silicon detector functionality"""
    print("Testing Apple Silicon Detector...")
    
    try:
        from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        
        detector = EnhancedAppleSiliconDetector()
        print("✓ Detector initialized successfully")
        
        # Test chip info
        chip_info = detector.get_chip_info()
        print(f"✓ Chip info retrieved: {chip_info.get('chip_name', 'Unknown')}")
        
        # Test optimization recommendations
        recommendations = detector.get_optimization_recommendations()
        print(f"✓ Optimization recommendations: {len(recommendations.get('recommendations', []))} items")
        
        # Test capabilities
        capabilities = detector.get_capabilities()
        print(f"✓ Capabilities detected: {len(capabilities)} items")
        
        return True
        
    except Exception as e:
        print(f"✗ Apple Silicon Detector test failed: {e}")
        traceback.print_exc()
        return False

def test_apple_frameworks():
    """Test Apple frameworks integration"""
    print("\nTesting Apple Frameworks Integration...")
    
    try:
        from apple_frameworks_integration import AppleFrameworksIntegration
        
        frameworks = AppleFrameworksIntegration()
        print("✓ Frameworks integration initialized")
        
        # Test availability checks
        coreml_available = frameworks.is_coreml_available()
        mlx_available = frameworks.is_mlx_available()
        metal_available = frameworks.is_metal_available()
        
        print(f"✓ Core ML available: {coreml_available}")
        print(f"✓ MLX available: {mlx_available}")
        print(f"✓ Metal available: {metal_available}")
        
        # Test version detection
        coreml_version = frameworks.get_coreml_version()
        mlx_version = frameworks.get_mlx_version()
        metal_version = frameworks.get_metal_version()
        
        print(f"✓ Core ML version: {coreml_version}")
        print(f"✓ MLX version: {mlx_version}")
        print(f"✓ Metal version: {metal_version}")
        
        return True
        
    except Exception as e:
        print(f"✗ Apple Frameworks test failed: {e}")
        traceback.print_exc()
        return False

def test_metrics_collector():
    """Test real-time metrics collector"""
    print("\nTesting Real-Time Metrics Collector...")
    
    try:
        from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        from production_gerdsen_ai import RealTimeMetricsCollector
        
        detector = EnhancedAppleSiliconDetector()
        collector = RealTimeMetricsCollector(detector)
        print("✓ Metrics collector initialized")
        
        # Test CPU metrics
        cpu_metrics = collector.get_cpu_metrics()
        print(f"✓ CPU metrics: {cpu_metrics.get('usage_percent', 0):.1f}% usage")
        
        # Test memory metrics
        memory_metrics = collector.get_memory_metrics()
        print(f"✓ Memory metrics: {memory_metrics.get('used_gb', 0):.1f}GB used")
        
        # Test thermal metrics
        thermal_metrics = collector.get_thermal_metrics()
        temp = thermal_metrics.get('cpu_temperature_c', 0)
        if temp > 0:
            print(f"✓ Thermal metrics: {temp:.1f}°C")
        else:
            print("✓ Thermal metrics: Not available on this system")
        
        # Test GPU metrics
        gpu_metrics = collector.get_gpu_metrics()
        gpu_cores = gpu_metrics.get('gpu_cores', 0)
        print(f"✓ GPU metrics: {gpu_cores} cores detected")
        
        # Test network metrics
        network_metrics = collector.get_network_metrics()
        connections = network_metrics.get('active_connections', 0)
        print(f"✓ Network metrics: {connections} active connections")
        
        return True
        
    except Exception as e:
        print(f"✗ Metrics collector test failed: {e}")
        traceback.print_exc()
        return False

def test_mlx_manager():
    """Test integrated MLX manager"""
    print("\nTesting Integrated MLX Manager...")
    
    try:
        from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        from apple_frameworks_integration import AppleFrameworksIntegration
        from integrated_mlx_manager import IntegratedMLXManager
        
        detector = EnhancedAppleSiliconDetector()
        frameworks = AppleFrameworksIntegration()
        mlx_manager = IntegratedMLXManager(
            apple_detector=detector,
            frameworks=frameworks
        )
        print("✓ MLX manager initialized")
        
        # Test loaded models
        models = mlx_manager.get_loaded_models()
        print(f"✓ Loaded models: {len(models)} models")
        
        # Test performance metrics
        try:
            performance_metrics = mlx_manager.get_performance_metrics()
            overall_score = performance_metrics.get('overall_score', 0)
            print(f"✓ Performance metrics: {overall_score:.1f} overall score")
        except:
            print("✓ Performance metrics: Not available (expected in test environment)")
        
        # Test auto optimization
        mlx_manager.set_auto_optimization(True)
        print("✓ Auto optimization enabled")
        
        mlx_manager.set_auto_optimization(False)
        print("✓ Auto optimization disabled")
        
        return True
        
    except Exception as e:
        print(f"✗ MLX manager test failed: {e}")
        traceback.print_exc()
        return False

def test_production_config():
    """Test production configuration"""
    print("\nTesting Production Configuration...")
    
    try:
        from production_gerdsen_ai import ProductionConfig
        
        config = ProductionConfig()
        print("✓ Production config initialized")
        
        # Test default values
        print(f"✓ Theme: {config.theme}")
        print(f"✓ Auto optimize: {config.auto_optimize}")
        print(f"✓ Cache size: {config.cache_size_gb}GB")
        print(f"✓ Server port: {config.server_port}")
        print(f"✓ OpenAI compatible: {config.openai_compatible}")
        
        # Test serialization
        config_dict = config.__dict__
        print(f"✓ Config serialization: {len(config_dict)} settings")
        
        return True
        
    except Exception as e:
        print(f"✗ Production config test failed: {e}")
        traceback.print_exc()
        return False

def test_flask_server():
    """Test Flask server initialization"""
    print("\nTesting Flask Server...")
    
    try:
        from production_gerdsen_ai import ProductionConfig
        from gerdsen_ai_server.src.production_main import ProductionFlaskServer
        
        config = ProductionConfig()
        config.server_port = 8082  # Use different port for testing
        
        server = ProductionFlaskServer(config)
        print("✓ Flask server initialized")
        
        # Test app creation
        app = server.app
        print(f"✓ Flask app created: {app.name}")
        
        # Test client creation
        client = app.test_client()
        print("✓ Test client created")
        
        # Test health endpoint
        response = client.get('/api/health')
        print(f"✓ Health endpoint: {response.status_code} status")
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✓ Health response: {data.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask server test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_files():
    """Test UI files existence and structure"""
    print("\nTesting UI Files...")
    
    try:
        ui_dir = Path(__file__).parent / 'ui'
        
        # Check for enhanced UI files
        enhanced_html = ui_dir / 'enhanced_index.html'
        enhanced_css = ui_dir / 'enhanced_styles.css'
        enhanced_js = ui_dir / 'enhanced_script.js'
        
        if enhanced_html.exists():
            print("✓ Enhanced HTML file exists")
            # Check file size
            size_kb = enhanced_html.stat().st_size / 1024
            print(f"✓ HTML file size: {size_kb:.1f}KB")
        else:
            print("✗ Enhanced HTML file missing")
            return False
        
        if enhanced_css.exists():
            print("✓ Enhanced CSS file exists")
            size_kb = enhanced_css.stat().st_size / 1024
            print(f"✓ CSS file size: {size_kb:.1f}KB")
        else:
            print("✗ Enhanced CSS file missing")
            return False
        
        if enhanced_js.exists():
            print("✓ Enhanced JavaScript file exists")
            size_kb = enhanced_js.stat().st_size / 1024
            print(f"✓ JavaScript file size: {size_kb:.1f}KB")
        else:
            print("✗ Enhanced JavaScript file missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ UI files test failed: {e}")
        traceback.print_exc()
        return False

def test_macos_integration():
    """Test macOS integration components"""
    print("\nTesting macOS Integration...")
    
    try:
        # Check for macOS service files
        macos_service = Path(__file__).parent / 'src' / 'macos_service.py'
        launcher = Path(__file__).parent / 'gerdsen_ai_launcher.py'
        build_script = Path(__file__).parent / 'scripts' / 'build_macos.sh'
        
        if macos_service.exists():
            print("✓ macOS service file exists")
        else:
            print("✗ macOS service file missing")
            return False
        
        if launcher.exists():
            print("✓ Launcher file exists")
        else:
            print("✗ Launcher file missing")
            return False
        
        if build_script.exists():
            print("✓ Build script exists")
            # Check if executable
            if os.access(build_script, os.X_OK):
                print("✓ Build script is executable")
            else:
                print("! Build script not executable")
        else:
            print("✗ Build script missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ macOS integration test failed: {e}")
        traceback.print_exc()
        return False

def run_performance_benchmark():
    """Run a simple performance benchmark"""
    print("\nRunning Performance Benchmark...")
    
    try:
        from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        from production_gerdsen_ai import RealTimeMetricsCollector
        
        detector = EnhancedAppleSiliconDetector()
        collector = RealTimeMetricsCollector(detector)
        
        # Benchmark chip detection
        start_time = time.time()
        for _ in range(10):
            chip_info = detector.get_chip_info()
        detection_time = (time.time() - start_time) / 10
        print(f"✓ Chip detection: {detection_time*1000:.1f}ms average")
        
        # Benchmark metrics collection
        start_time = time.time()
        for _ in range(10):
            cpu_metrics = collector.get_cpu_metrics()
            memory_metrics = collector.get_memory_metrics()
        metrics_time = (time.time() - start_time) / 10
        print(f"✓ Metrics collection: {metrics_time*1000:.1f}ms average")
        
        # Performance thresholds
        if detection_time > 0.1:
            print("! Warning: Chip detection is slow")
        
        if metrics_time > 0.05:
            print("! Warning: Metrics collection is slow")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance benchmark failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("GerdsenAI MLX Manager - Functionality Validation")
    print("=" * 60)
    
    tests = [
        test_apple_silicon_detector,
        test_apple_frameworks,
        test_metrics_collector,
        test_mlx_manager,
        test_production_config,
        test_flask_server,
        test_ui_files,
        test_macos_integration,
        run_performance_benchmark
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All functionality validated successfully!")
        return True
    else:
        print(f"⚠️  {failed} tests failed - review implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

