#!/usr/bin/env python3
"""
Production GerdsenAI MLX Manager Server
Complete Flask server implementation with real functionality
"""

import os
import sys
import logging
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import our production components
from src.production_gerdsen_ai import (
    ProductionGerdsenAI, 
    ProductionConfig, 
    RealTimeMetricsCollector
)
from src.enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
from src.integrated_mlx_manager import IntegratedMLXManager
from src.enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
from src.routes.terminal import terminal_bp
from src.routes.hardware import hardware_bp
from src.routes.service_management import service_mgmt_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gerdsen_ai_server.log')
    ]
)

logger = logging.getLogger(__name__)

class ProductionFlaskServer:
    """Production Flask server with integrated components"""
    
    def __init__(self, config: ProductionConfig = None):
        self.config = config or ProductionConfig()
        
        # Initialize core components
        self.apple_detector = EnhancedAppleSiliconDetector()
        self.frameworks = EnhancedAppleFrameworksIntegration()
        self.mlx_manager = IntegratedMLXManager(
            apple_detector=self.apple_detector,
            frameworks=self.frameworks
        )
        self.metrics_collector = RealTimeMetricsCollector(self.apple_detector)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        static_folder=os.path.join(os.path.dirname(__file__), '..', '..', 'ui'),
                        static_url_path='')
        
        self.app.config['SECRET_KEY'] = 'gerdsen_ai_production_secret_2025'
        
        # Enable CORS for all routes
        CORS(self.app, origins="*")
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Setup routes and handlers
        self._setup_routes()
        self._setup_websocket_handlers()
        
        # Background tasks
        self.metrics_thread = None
        self.running = False
        
        logger.info("Production Flask server initialized")
    
    def _setup_routes(self):
        """Setup all Flask routes with real implementations"""
        
        # Register blueprints
        self.app.register_blueprint(terminal_bp, url_prefix='/api/terminal')
        self.app.register_blueprint(hardware_bp, url_prefix='/api/hardware')
        self.app.register_blueprint(service_mgmt_bp, url_prefix='/api/service')
        
        @self.app.route('/')
        def index():
            """Serve the main UI"""
            return send_from_directory(self.app.static_folder, 'enhanced_index.html')
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '1.0.0',
                'components': {
                    'apple_detector': self.apple_detector.is_available(),
                    'mlx_manager': self.mlx_manager.is_initialized(),
                    'frameworks': self.frameworks.is_initialized()
                }
            })
        
        @self.app.route('/api/hardware/detect')
        def detect_hardware():
            """Real Apple Silicon hardware detection"""
            try:
                chip_info = self.apple_detector.get_chip_info()
                optimization_info = self.apple_detector.get_optimization_recommendations()
                
                return jsonify({
                    'success': True,
                    'chip_name': chip_info.get('chip_name', 'Unknown'),
                    'chip_variant': chip_info.get('chip_variant', ''),
                    'cpu_cores': {
                        'performance': chip_info.get('performance_cores', 0),
                        'efficiency': chip_info.get('efficiency_cores', 0),
                        'total': chip_info.get('total_cores', 0)
                    },
                    'gpu_cores': chip_info.get('gpu_cores', 0),
                    'neural_engine': {
                        'cores': chip_info.get('neural_engine_cores', 16),
                        'tops': chip_info.get('neural_engine_tops', 0)
                    },
                    'memory': {
                        'total': chip_info.get('memory_gb', 0),
                        'bandwidth': chip_info.get('memory_bandwidth_gbps', 0),
                        'type': chip_info.get('memory_type', 'Unified')
                    },
                    'process_node': chip_info.get('process_node', 'Unknown'),
                    'architecture': chip_info.get('architecture', 'Unknown'),
                    'frameworks': {
                        'coreml': {
                            'available': self.frameworks.is_coreml_available(),
                            'version': self.frameworks.get_coreml_version()
                        },
                        'mlx': {
                            'available': self.frameworks.is_mlx_available(),
                            'version': self.frameworks.get_mlx_version()
                        },
                        'metal': {
                            'available': self.frameworks.is_metal_available(),
                            'version': self.frameworks.get_metal_version()
                        }
                    },
                    'optimization': optimization_info,
                    'capabilities': chip_info.get('capabilities', [])
                })
            except Exception as e:
                logger.error(f"Hardware detection error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/hardware/metrics')
        def get_hardware_metrics():
            """Real-time hardware metrics"""
            try:
                cpu_metrics = self.metrics_collector.get_cpu_metrics()
                memory_metrics = self.metrics_collector.get_memory_metrics()
                thermal_metrics = self.metrics_collector.get_thermal_metrics()
                gpu_metrics = self.metrics_collector.get_gpu_metrics()
                network_metrics = self.metrics_collector.get_network_metrics()
                
                return jsonify({
                    'success': True,
                    'timestamp': time.time(),
                    'cpu': {
                        'usage_percent': cpu_metrics.get('usage_percent', 0),
                        'cores_usage': cpu_metrics.get('per_core_usage', []),
                        'frequency_mhz': cpu_metrics.get('frequency_mhz', 0),
                        'performance_cores': cpu_metrics.get('performance_cores', 0),
                        'efficiency_cores': cpu_metrics.get('efficiency_cores', 0)
                    },
                    'memory': {
                        'used_gb': memory_metrics.get('used_gb', 0),
                        'total_gb': memory_metrics.get('total_gb', 0),
                        'available_gb': memory_metrics.get('available_gb', 0),
                        'percent_used': memory_metrics.get('percent_used', 0),
                        'cached_gb': memory_metrics.get('cached_gb', 0),
                        'pressure': memory_metrics.get('memory_pressure', 'normal')
                    },
                    'thermal': {
                        'temperature_c': thermal_metrics.get('cpu_temperature_c', 0),
                        'thermal_state': thermal_metrics.get('thermal_state', 'normal')
                    },
                    'gpu': {
                        'cores': gpu_metrics.get('gpu_cores', 0),
                        'utilization_percent': gpu_metrics.get('gpu_utilization_percent', 0),
                        'memory_used_mb': gpu_metrics.get('gpu_memory_used_mb', 0),
                        'memory_total_mb': gpu_metrics.get('gpu_memory_total_mb', 0)
                    },
                    'network': {
                        'bytes_sent': network_metrics.get('bytes_sent', 0),
                        'bytes_recv': network_metrics.get('bytes_recv', 0),
                        'active_connections': network_metrics.get('active_connections', 0)
                    },
                    'models': {
                        'loaded_count': len(self.mlx_manager.get_loaded_models()),
                        'total_memory_mb': self.mlx_manager.get_total_model_memory()
                    }
                })
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/hardware/info')
        def get_hardware_info():
            """Detailed hardware information"""
            try:
                chip_info = self.apple_detector.get_chip_info()
                system_info = self.apple_detector.get_system_info()
                
                return jsonify({
                    'success': True,
                    'system': system_info,
                    'chip': chip_info,
                    'capabilities': self.apple_detector.get_capabilities(),
                    'optimization_status': self.apple_detector.get_optimization_status()
                })
            except Exception as e:
                logger.error(f"Hardware info error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/models')
        def get_models():
            """Get all loaded models"""
            try:
                models = self.mlx_manager.get_loaded_models()
                model_list = []
                
                for model_id, model_info in models.items():
                    model_list.append({
                        'id': model_id,
                        'name': model_info.get('name', model_id),
                        'description': model_info.get('description', ''),
                        'status': model_info.get('status', 'unknown'),
                        'parameters': model_info.get('parameters', 'Unknown'),
                        'quantization': model_info.get('quantization', 'FP16'),
                        'size_gb': model_info.get('size_gb', 0),
                        'optimization_level': model_info.get('optimization_level', 'none'),
                        'memory_usage_mb': model_info.get('memory_usage_mb', 0),
                        'load_time': model_info.get('load_time', 0),
                        'inference_speed': model_info.get('inference_speed', 0)
                    })
                
                return jsonify({
                    'success': True,
                    'models': model_list,
                    'total_count': len(model_list),
                    'total_memory_mb': sum(m.get('memory_usage_mb', 0) for m in model_list)
                })
            except Exception as e:
                logger.error(f"Models list error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/models/upload', methods=['POST'])
        def upload_model():
            """Upload and load a new model"""
            try:
                if 'model' not in request.files:
                    return jsonify({'success': False, 'error': 'No model file provided'}), 400
                
                file = request.files['model']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'}), 400
                
                # Validate file type
                allowed_extensions = {'.mlx', '.gguf', '.safetensors', '.bin', '.mlpackage'}
                file_ext = Path(file.filename).suffix.lower()
                
                if file_ext not in allowed_extensions:
                    return jsonify({
                        'success': False, 
                        'error': f'Unsupported file type: {file_ext}. Supported: {", ".join(allowed_extensions)}'
                    }), 400
                
                # Load the model
                result = self.mlx_manager.load_model_from_file(file)
                
                return jsonify({
                    'success': True,
                    'model_id': result.get('model_id'),
                    'model_info': result.get('model_info', {}),
                    'message': 'Model uploaded and loaded successfully'
                })
            except Exception as e:
                logger.error(f"Model upload error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/models/<model_id>/unload', methods=['POST'])
        def unload_model(model_id):
            """Unload a specific model"""
            try:
                result = self.mlx_manager.unload_model(model_id)
                
                return jsonify({
                    'success': True,
                    'model_id': model_id,
                    'message': 'Model unloaded successfully'
                })
            except Exception as e:
                logger.error(f"Model unload error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/models/clear-cache', methods=['POST'])
        def clear_model_cache():
            """Clear model cache"""
            try:
                freed_memory = self.mlx_manager.clear_cache()
                
                return jsonify({
                    'success': True,
                    'freed_memory_mb': freed_memory,
                    'message': f'Cache cleared, freed {freed_memory:.1f} MB'
                })
            except Exception as e:
                logger.error(f"Cache clear error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/optimization/auto', methods=['POST'])
        def toggle_auto_optimization():
            """Toggle auto optimization"""
            try:
                data = request.get_json()
                enabled = data.get('enabled', False)
                
                self.mlx_manager.set_auto_optimization(enabled)
                
                return jsonify({
                    'success': True,
                    'auto_optimization': enabled,
                    'message': f'Auto optimization {"enabled" if enabled else "disabled"}'
                })
            except Exception as e:
                logger.error(f"Auto optimization toggle error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/optimization/settings', methods=['POST'])
        def update_optimization_settings():
            """Update optimization settings"""
            try:
                data = request.get_json()
                
                # Update individual settings
                for setting, value in data.items():
                    self.mlx_manager.update_optimization_setting(setting, value)
                
                return jsonify({
                    'success': True,
                    'updated_settings': data,
                    'message': 'Optimization settings updated'
                })
            except Exception as e:
                logger.error(f"Optimization settings error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/optimization/optimize-all', methods=['POST'])
        def optimize_all_models():
            """Optimize all loaded models"""
            try:
                results = self.mlx_manager.optimize_all_models()
                
                return jsonify({
                    'success': True,
                    'optimization_results': results,
                    'message': 'All models optimized for Apple Silicon'
                })
            except Exception as e:
                logger.error(f"Model optimization error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/performance/metrics')
        def get_performance_metrics():
            """Get performance analytics"""
            try:
                performance_data = self.mlx_manager.get_performance_metrics()
                
                return jsonify({
                    'success': True,
                    'overall_score': performance_data.get('overall_score', 0),
                    'cpu_efficiency': performance_data.get('cpu_efficiency', 0),
                    'memory_efficiency': performance_data.get('memory_efficiency', 0),
                    'thermal_efficiency': performance_data.get('thermal_efficiency', 0),
                    'gpu_efficiency': performance_data.get('gpu_efficiency', 0),
                    'neural_engine_efficiency': performance_data.get('neural_engine_efficiency', 0),
                    'recommendations': performance_data.get('recommendations', []),
                    'bottlenecks': performance_data.get('bottlenecks', []),
                    'optimization_opportunities': performance_data.get('optimization_opportunities', [])
                })
            except Exception as e:
                logger.error(f"Performance metrics error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/benchmark/run', methods=['POST'])
        def run_benchmark():
            """Run system benchmark"""
            try:
                benchmark_results = self.mlx_manager.run_benchmark()
                
                return jsonify({
                    'success': True,
                    'benchmark_results': benchmark_results,
                    'score': benchmark_results.get('overall_score', 0),
                    'message': 'Benchmark completed successfully'
                })
            except Exception as e:
                logger.error(f"Benchmark error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/settings/export')
        def export_settings():
            """Export application settings"""
            try:
                settings = self.mlx_manager.export_settings()
                
                return jsonify({
                    'success': True,
                    'settings': settings,
                    'export_timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Settings export error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # OpenAI Compatible API endpoints
        @self.app.route('/v1/models')
        def openai_list_models():
            """OpenAI compatible models endpoint"""
            try:
                models = self.mlx_manager.get_loaded_models()
                openai_models = []
                
                for model_id, model_info in models.items():
                    openai_models.append({
                        'id': model_id,
                        'object': 'model',
                        'created': int(time.time()),
                        'owned_by': 'gerdsen-ai',
                        'permission': [],
                        'root': model_id,
                        'parent': None
                    })
                
                return jsonify({
                    'object': 'list',
                    'data': openai_models
                })
            except Exception as e:
                logger.error(f"OpenAI models list error: {e}")
                return jsonify({'error': {'message': str(e), 'type': 'server_error'}}), 500
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def openai_chat_completions():
            """OpenAI compatible chat completions endpoint"""
            try:
                data = request.get_json()
                model_id = data.get('model', 'default')
                messages = data.get('messages', [])
                stream = data.get('stream', False)
                max_tokens = data.get('max_tokens', 1000)
                temperature = data.get('temperature', 0.7)
                
                # Generate response using MLX manager
                response = self.mlx_manager.generate_chat_completion(
                    model_id=model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=stream
                )
                
                if stream:
                    # Return streaming response (would need to implement SSE)
                    return jsonify({'error': {'message': 'Streaming not yet implemented', 'type': 'not_implemented'}}), 501
                else:
                    # Return complete response
                    return jsonify({
                        'id': f'chatcmpl-{int(time.time())}',
                        'object': 'chat.completion',
                        'created': int(time.time()),
                        'model': model_id,
                        'choices': [{
                            'index': 0,
                            'message': {
                                'role': 'assistant',
                                'content': response.get('content', '')
                            },
                            'finish_reason': 'stop'
                        }],
                        'usage': {
                            'prompt_tokens': response.get('prompt_tokens', 0),
                            'completion_tokens': response.get('completion_tokens', 0),
                            'total_tokens': response.get('total_tokens', 0)
                        }
                    })
            except Exception as e:
                logger.error(f"Chat completions error: {e}")
                return jsonify({'error': {'message': str(e), 'type': 'server_error'}}), 500
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to WebSocket')
            emit('status', {'connected': True, 'timestamp': time.time()})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from WebSocket')
        
        @self.socketio.on('request_metrics')
        def handle_metrics_request():
            """Send current metrics to client"""
            try:
                metrics = self._get_current_metrics()
                emit('metrics_update', metrics)
            except Exception as e:
                logger.error(f"WebSocket metrics error: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('request_hardware_info')
        def handle_hardware_request():
            """Send hardware info to client"""
            try:
                chip_info = self.apple_detector.get_chip_info()
                emit('hardware_update', {
                    'type': 'hardware_update',
                    'data': chip_info
                })
            except Exception as e:
                logger.error(f"WebSocket hardware error: {e}")
                emit('error', {'message': str(e)})
    
    def _get_current_metrics(self) -> dict:
        """Get current system metrics for WebSocket"""
        try:
            cpu_metrics = self.metrics_collector.get_cpu_metrics()
            memory_metrics = self.metrics_collector.get_memory_metrics()
            thermal_metrics = self.metrics_collector.get_thermal_metrics()
            
            return {
                'type': 'metrics_update',
                'data': {
                    'cpu_usage': cpu_metrics.get('usage_percent', 0),
                    'cpu_cores': cpu_metrics.get('per_core_usage', []),
                    'memory_used': memory_metrics.get('used_gb', 0),
                    'memory_total': memory_metrics.get('total_gb', 0),
                    'memory_percent': memory_metrics.get('percent_used', 0),
                    'temperature': thermal_metrics.get('cpu_temperature_c', 0),
                    'thermal_state': thermal_metrics.get('thermal_state', 'normal'),
                    'loaded_models': len(self.mlx_manager.get_loaded_models()),
                    'timestamp': time.time()
                }
            }
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {'type': 'error', 'message': str(e)}
    
    def start_metrics_broadcasting(self):
        """Start broadcasting metrics via WebSocket"""
        def broadcast_metrics():
            while self.running:
                try:
                    metrics = self._get_current_metrics()
                    self.socketio.emit('metrics_update', metrics)
                    time.sleep(2)  # Broadcast every 2 seconds
                except Exception as e:
                    logger.error(f"Metrics broadcasting error: {e}")
                    time.sleep(5)
        
        if not self.metrics_thread or not self.metrics_thread.is_alive():
            self.metrics_thread = threading.Thread(target=broadcast_metrics, daemon=True)
            self.metrics_thread.start()
            logger.info("Started metrics broadcasting thread")
    
    def initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing system components...")
        
        try:
            # Initialize Apple Silicon detector
            self.apple_detector.initialize()
            
            # Initialize frameworks
            self.frameworks.initialize()
            
            # Initialize MLX manager
            chip_info = self.apple_detector.get_chip_info()
            self.mlx_manager.initialize(chip_info)
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return False
    
    def start_server(self, host='0.0.0.0', port=None, debug=False):
        """Start the production Flask server"""
        if port is None:
            port = self.config.server_port
        
        self.running = True
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components, server not started")
            return False
        
        # Start metrics broadcasting
        self.start_metrics_broadcasting()
        
        logger.info(f"Starting production server on {host}:{port}")
        
        try:
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            logger.error(f"Server startup error: {e}")
            return False
        
        return True
    
    def stop_server(self):
        """Stop the production server"""
        self.running = False
        
        if self.metrics_thread and self.metrics_thread.is_alive():
            self.metrics_thread.join(timeout=2)
        
        # Cleanup components
        if hasattr(self, 'mlx_manager'):
            self.mlx_manager.cleanup()
        
        logger.info("Production server stopped")

def main():
    """Main entry point for production server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GerdsenAI MLX Manager - Production Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    # Service-related arguments
    parser.add_argument('--service', action='store_true', 
                       help='Run as macOS service')
    parser.add_argument('--install-service', action='store_true',
                       help='Install as macOS service for auto-start')
    parser.add_argument('--uninstall-service', action='store_true',
                       help='Uninstall macOS service')
    parser.add_argument('--service-status', action='store_true',
                       help='Check service status')
    parser.add_argument('--app-bundle', action='store_true',
                       help='Run from app bundle')
    parser.add_argument('--minimize-to-tray', action='store_true',
                       help='Enable system tray integration')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Handle service management commands
    if args.install_service or args.uninstall_service or args.service_status:
        try:
            # Import service manager
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from src.macos_service_integration import MacOSServiceManager
            
            service_manager = MacOSServiceManager(port=args.port)
            
            if args.install_service:
                if service_manager.install_service():
                    print("✅ Service installed successfully")
                    print(f"   The service will start automatically on login")
                    print(f"   Application URL: http://localhost:{args.port}")
                else:
                    print("❌ Failed to install service")
                return
            
            elif args.uninstall_service:
                if service_manager.uninstall_service():
                    print("✅ Service uninstalled successfully")
                else:
                    print("❌ Failed to uninstall service")
                return
            
            elif args.service_status:
                status = service_manager.get_service_status()
                print("GerdsenAI Service Status:")
                print("=" * 30)
                for key, value in status.items():
                    print(f"{key:20}: {value}")
                return
                
        except ImportError as e:
            logger.error(f"Service integration not available: {e}")
            return
        except Exception as e:
            logger.error(f"Service management error: {e}")
            return
    
    # Create and configure server
    config = ProductionConfig()
    config.server_port = args.port
    
    server = ProductionFlaskServer(config)
    
    # Set up service integration if running as service
    if args.service or args.app_bundle:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from src.macos_service_integration import MacOSServiceManager, SystemTrayIntegration
            
            service_manager = MacOSServiceManager(port=args.port)
            tray_integration = SystemTrayIntegration(service_manager)
            
            # Configure for service mode
            if args.minimize_to_tray:
                tray_integration.minimize_to_tray()
            
            logger.info("Running in service mode")
            
        except ImportError:
            logger.warning("Service integration not available, running in standard mode")
        except Exception as e:
            logger.warning(f"Service integration error: {e}")
    
    try:
        # Start server
        logger.info(f"Starting GerdsenAI server on {args.host}:{args.port}")
        
        if args.service:
            # Run in service mode (no debug, quiet)
            server.start_server(host=args.host, port=args.port, debug=False)
        else:
            # Run in interactive mode
            server.start_server(host=args.host, port=args.port, debug=args.debug)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        server.stop_server()
    except Exception as e:
        logger.error(f"Server error: {e}")
        server.stop_server()

if __name__ == "__main__":
    main()

