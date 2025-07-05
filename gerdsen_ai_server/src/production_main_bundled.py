#!/usr/bin/env python3
"""
Production GerdsenAI MLX Manager Server - Bundled Version
Complete Flask server implementation for bundled Electron app
"""

import os
import sys
import logging
import threading
import time
from pathlib import Path

from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import our production components - use relative imports for bundled version
from production_gerdsen_ai import (
    ProductionGerdsenAI, 
    ProductionConfig, 
    RealTimeMetricsCollector
)
from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
from integrated_mlx_manager import IntegratedMLXManager
from enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
from routes.terminal import terminal_bp
from routes.hardware import hardware_bp
from routes.service_management import service_mgmt_bp
from routes.mcp_routes import mcp_bp

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
        """Initialize production server with configuration"""
        self.config = config or ProductionConfig()
        self.app = Flask(__name__)
        
        # Configure Flask app
        self.app.config['SECRET_KEY'] = self.config.secret_key
        self.app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
        
        # Initialize CORS with production settings
        CORS(self.app, 
             origins=self.config.cors_origins,
             supports_credentials=True,
             expose_headers=['Content-Type', 'Authorization'])
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins=self.config.cors_origins,
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Initialize components
        self._initialize_components()
        
        # Register routes and error handlers
        self._register_routes()
        self._register_error_handlers()
        
        # Setup real-time metrics
        self._setup_metrics()
        
        logger.info("Production Flask server initialized successfully")
    
    def _initialize_components(self):
        """Initialize all server components"""
        try:
            # Initialize Apple Silicon detector
            self.silicon_detector = EnhancedAppleSiliconDetector()
            
            # Initialize Apple frameworks integration
            self.apple_frameworks = EnhancedAppleFrameworksIntegration()
            
            # Initialize MLX manager with production config
            mlx_config = self.config.get_mlx_config()
            self.mlx_manager = IntegratedMLXManager(config=mlx_config)
            
            # Initialize production AI system
            self.gerdsen_ai = ProductionGerdsenAI(
                mlx_manager=self.mlx_manager,
                config=self.config
            )
            
            # Share components with app context
            self.app.silicon_detector = self.silicon_detector
            self.app.apple_frameworks = self.apple_frameworks
            self.app.mlx_manager = self.mlx_manager
            self.app.gerdsen_ai = self.gerdsen_ai
            
            logger.info("All server components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _register_routes(self):
        """Register all API routes"""
        # Register blueprint routes
        self.app.register_blueprint(terminal_bp, url_prefix='/api/terminal')
        self.app.register_blueprint(hardware_bp, url_prefix='/api/hardware')
        self.app.register_blueprint(service_mgmt_bp, url_prefix='/api/services')
        self.app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
        
        # Core API routes
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'version': self.config.version,
                'components': {
                    'silicon_detector': 'active',
                    'apple_frameworks': 'active',
                    'mlx_manager': 'active',
                    'gerdsen_ai': 'active'
                },
                'timestamp': time.time()
            })
        
        @self.app.route('/api/system/info', methods=['GET'])
        def system_info():
            """Get system information"""
            silicon_info = self.silicon_detector.get_processor_info()
            return jsonify({
                'silicon': silicon_info,
                'frameworks': self.apple_frameworks.get_framework_info(),
                'mlx': self.mlx_manager.get_status(),
                'config': self.config.get_public_config()
            })
        
        # OpenAI-compatible API endpoints
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            """List available models (OpenAI-compatible)"""
            models = self.mlx_manager.get_available_models()
            return jsonify({
                "object": "list",
                "data": models
            })
        
        @self.app.route('/v1/models/<model_id>', methods=['GET'])
        def get_model(model_id):
            """Get specific model information"""
            model_info = self.mlx_manager.get_model_info(model_id)
            if model_info:
                return jsonify(model_info)
            return jsonify({"error": "Model not found"}), 404
        
        @self.app.route('/v1/models/<model_id>/switch', methods=['POST'])
        def switch_model(model_id):
            """Switch to a different model"""
            try:
                success = self.mlx_manager.switch_model(model_id)
                if success:
                    return jsonify({
                        "status": "success",
                        "model": model_id,
                        "message": f"Switched to model {model_id}"
                    })
                return jsonify({"error": "Failed to switch model"}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def chat_completions():
            """Create chat completion (OpenAI-compatible)"""
            try:
                data = request.json
                model = data.get('model', 'default')
                messages = data.get('messages', [])
                
                # Pass to GerdsenAI for processing
                response = self.gerdsen_ai.create_chat_completion(
                    model=model,
                    messages=messages,
                    **data
                )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "internal_error",
                        "code": 500
                    }
                }), 500
        
        @self.app.route('/v1/completions', methods=['POST'])
        def completions():
            """Create text completion (OpenAI-compatible)"""
            try:
                data = request.json
                model = data.get('model', 'default')
                prompt = data.get('prompt', '')
                
                response = self.gerdsen_ai.create_completion(
                    model=model,
                    prompt=prompt,
                    **data
                )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Completion error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "internal_error",
                        "code": 500
                    }
                }), 500
        
        @self.app.route('/v1/embeddings', methods=['POST'])
        def embeddings():
            """Create embeddings (OpenAI-compatible)"""
            try:
                data = request.json
                model = data.get('model', 'default')
                input_text = data.get('input', '')
                
                response = self.gerdsen_ai.create_embeddings(
                    model=model,
                    input=input_text,
                    **data
                )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Embeddings error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "internal_error",
                        "code": 500
                    }
                }), 500
        
        # Model management endpoints
        @self.app.route('/api/models/scan', methods=['GET'])
        def scan_user_models():
            """Scan user's model directories"""
            format_type = request.args.get('format')
            capability = request.args.get('capability')
            
            models = self.mlx_manager.scan_user_models(format_type, capability)
            return jsonify({
                "models": models,
                "count": len(models),
                "directory": str(Path.home() / "Models")
            })
        
        @self.app.route('/api/models/load', methods=['POST'])
        def load_model():
            """Load a model from file path"""
            try:
                data = request.json
                model_path = data.get('path')
                model_id = data.get('id')
                
                if not model_path:
                    return jsonify({"error": "Model path required"}), 400
                
                success = self.mlx_manager.load_model_from_path(
                    model_path,
                    model_id
                )
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Model loaded from {model_path}"
                    })
                return jsonify({"error": "Failed to load model"}), 500
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Serve static files in development
        if self.config.debug:
            @self.app.route('/')
            def index():
                return send_from_directory('static', 'index.html')
            
            @self.app.route('/<path:path>')
            def static_files(path):
                return send_from_directory('static', path)
        
        logger.info("All routes registered successfully")
    
    def _register_error_handlers(self):
        """Register error handlers"""
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Not found',
                'message': 'The requested resource was not found'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            logger.error(f"Unhandled exception: {e}")
            return jsonify({
                'error': 'Server error',
                'message': str(e)
            }), 500
    
    def _setup_metrics(self):
        """Setup real-time metrics collection"""
        self.metrics_collector = RealTimeMetricsCollector(
            self.silicon_detector,
            self.mlx_manager
        )
        
        # Start metrics broadcasting
        def broadcast_metrics():
            while True:
                metrics = self.metrics_collector.get_current_metrics()
                self.socketio.emit('metrics_update', metrics)
                time.sleep(self.config.metrics_interval)
        
        self.metrics_thread = threading.Thread(
            target=broadcast_metrics,
            daemon=True
        )
        self.metrics_thread.start()
        
        logger.info("Real-time metrics collection started")
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the production server"""
        logger.info(f"Starting production server on {host}:{port}")
        
        # Print startup information
        print("\n" + "="*60)
        print(f"🚀 GerdsenAI Production Server v{self.config.version}")
        print("="*60)
        print(f"🖥️  System: {self.silicon_detector.get_processor_info()['model']}")
        print(f"🎯 Cores: {self.silicon_detector.get_processor_info()['cores']['total']}")
        print(f"🔧 MLX: {self.mlx_manager.get_status()['mlx_available']}")
        print(f"📡 Server: http://{host}:{port}")
        print("="*60 + "\n")
        
        # Run with SocketIO
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            log_output=True
        )


def main():
    """Main entry point for production server"""
    # Load configuration
    config = ProductionConfig()
    
    # Create and run server
    server = ProductionFlaskServer(config)
    
    # Get host and port from environment or use defaults
    host = os.environ.get('GERDSEN_HOST', '0.0.0.0')
    port = int(os.environ.get('GERDSEN_PORT', 8080))
    debug = os.environ.get('GERDSEN_DEBUG', 'False').lower() == 'true'
    
    try:
        server.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == '__main__':
    main()