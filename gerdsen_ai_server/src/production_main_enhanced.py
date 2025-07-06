#!/usr/bin/env python3
"""
Enhanced Production Server for Bundled Electron App
Bridges simplified server reliability with full ML functionality
"""

import os
import sys
import logging
import json
import time
import threading
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add path for utils
sys.path.insert(0, os.path.dirname(__file__))
try:
    from utils.config import load_env_file, get_cors_origins, get_api_config, get_env
    # Load environment variables
    load_env_file()
except ImportError:
    # Fallback if utils not available
    def get_cors_origins():
        env_origins = os.environ.get('ALLOWED_ORIGINS', '')
        default_origins = [
            'http://localhost:8080',
            'http://127.0.0.1:8080',
            'http://localhost:5173',
            'http://localhost:3000',
            'http://127.0.0.1:3000'
        ]
        origins = [o.strip() for o in env_origins.split(',') if o.strip()] if env_origins else default_origins
        # Always include frontend dev server for local development
        if 'http://localhost:5173' not in origins:
            origins.append('http://localhost:5173')
        return origins
    def get_api_config():
        return {'secret_key': os.environ.get('SECRET_KEY', 'dev-secret-key')}
    def get_env(key, default=None):
        return os.environ.get(key, default)

# Configure logging
try:
    from utils.logging_config import setup_structured_logging
    setup_structured_logging()
    logger = logging.getLogger(__name__)
except ImportError:
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

class EnhancedProductionServer:
    """Enhanced production server that progressively loads ML functionality"""
    
    def __init__(self):
        """Initialize the enhanced server with progressive ML loading"""
        self.app = Flask(__name__)
        
        # Configure Flask app with environment-based settings
        api_config = get_api_config()
        self.app.config['SECRET_KEY'] = api_config.get('secret_key', get_env('SECRET_KEY', 'dev-secret-key'))
        
        # Initialize CORS with environment-based origins
        cors_origins = get_cors_origins()
        logger.info(f"Configuring CORS with origins: {cors_origins}")
        # DEVELOPMENT: Allow all origins and headers for CORS (no credentials)
        CORS(self.app, origins="*", allow_headers="*", send_wildcard=True)
        
        # Progressive ML initialization flags
        self.ml_components_loaded = False
        self.ml_manager = None
        self.apple_detector = None
        self.frameworks = None
        self.ml_lock = threading.Lock()  # Lock for thread-safe ML access
        
        # Setup routes
        self._setup_routes()
        
        # Initialize secure upload handler
        try:
            from api.upload_handler import init_upload_routes
            init_upload_routes(self.app)
        except ImportError:
            logger.warning("Upload handler not available")
        
        # Initialize ML components in background
        self._init_ml_components_async()
        
        logger.info("Enhanced production server initialized")
    
    def _init_ml_components_async(self):
        """Initialize ML components asynchronously to avoid blocking startup"""
        def load_ml_components():
            try:
                logger.info("Starting ML components initialization...")
                
                # Try to import ML components with graceful fallback
                try:
                    from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
                    from enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
                    from integrated_mlx_manager import IntegratedMLXManager
                    
                    # Initialize components with thread safety
                    with self.ml_lock:
                        self.apple_detector = EnhancedAppleSiliconDetector()
                        self.frameworks = EnhancedAppleFrameworksIntegration()
                        self.ml_manager = IntegratedMLXManager()
                        
                        self.ml_components_loaded = True
                    logger.info("✅ ML components loaded successfully")
                    
                except ImportError as e:
                    logger.warning(f"ML components not available: {e}")
                    self.ml_components_loaded = False
                except Exception as e:
                    logger.error(f"Failed to load ML components: {e}")
                    self.ml_components_loaded = False
                    
            except Exception as e:
                logger.error(f"ML initialization error: {e}")
                self.ml_components_loaded = False
        
        # Start ML loading in background thread
        ml_thread = threading.Thread(target=load_ml_components, daemon=True)
        ml_thread.start()
    
    def _setup_routes(self):
        """Setup API routes with progressive enhancement"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint with ML status"""
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'server': 'impetus-enhanced-production',
                'timestamp': time.time(),
                'ml_components_loaded': self.ml_components_loaded,
                'components': {
                    'apple_detector': self.apple_detector is not None,
                    'frameworks': self.frameworks is not None,
                    'ml_manager': self.ml_manager is not None
                }
            })
        
        @self.app.route('/api/system/info', methods=['GET'])
        def system_info():
            """Get system information with optional ML details"""
            base_info = {
                'platform': sys.platform,
                'python_version': sys.version,
                'server_status': 'running',
                'ml_status': 'loading' if not self.ml_components_loaded else 'ready'
            }
            
            # Add ML info if available
            if self.ml_components_loaded and self.apple_detector:
                try:
                    chip_info = self.apple_detector.get_processor_info()
                    base_info['hardware'] = chip_info
                except Exception as e:
                    logger.warning(f"Could not get hardware info: {e}")
            
            return jsonify(base_info)
        
        # OpenAI-compatible endpoints with progressive enhancement
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            """List available models with progressive loading"""
            if not self.ml_components_loaded or not self.ml_manager:
                return jsonify({
                    "object": "list",
                    "data": [],
                    "status": "ml_components_loading",
                    "message": "ML components still initializing. Please wait..."
                })
            
            try:
                # Get models from ML manager
                models = self.ml_manager.get_available_models()
                return jsonify({
                    "object": "list",
                    "data": models,
                    "status": "ready"
                })
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return jsonify({
                    "object": "list", 
                    "data": [],
                    "error": str(e)
                })
        
        @self.app.route('/v1/models/<model_id>', methods=['GET'])
        def get_model(model_id):
            """Get model information"""
            if not self.ml_components_loaded or not self.ml_manager:
                return jsonify({
                    "error": "ML components not ready",
                    "status": "loading"
                }), 503
            
            try:
                model_info = self.ml_manager.get_model_info(model_id)
                if model_info:
                    return jsonify(model_info)
                return jsonify({"error": "Model not found"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def chat_completions():
            """Chat completions endpoint with progressive enhancement"""
            if not self.ml_components_loaded or not self.ml_manager:
                return jsonify({
                    "error": {
                        "message": "ML components are still loading. Please wait and try again.",
                        "type": "ml_components_loading",
                        "code": 503
                    }
                }), 503
            
            try:
                data = request.json
                model = data.get('model', 'default')
                messages = data.get('messages', [])
                
                # Use ML manager for actual inference
                response = self.ml_manager.create_chat_completion(
                    model=model,
                    messages=messages,
                    max_tokens=data.get('max_tokens', 1000),
                    temperature=data.get('temperature', 0.7),
                    stream=data.get('stream', False)
                )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "inference_error",
                        "code": 500
                    }
                }), 500
        
        @self.app.route('/v1/completions', methods=['POST'])
        def completions():
            """Text completions endpoint with progressive enhancement"""
            if not self.ml_components_loaded or not self.ml_manager:
                return jsonify({
                    "error": {
                        "message": "ML components are still loading. Please wait and try again.",
                        "type": "ml_components_loading",
                        "code": 503
                    }
                }), 503
            
            try:
                data = request.json
                model = data.get('model', 'default')
                prompt = data.get('prompt', '')
                
                response = self.ml_manager.generate_text(
                    model=model,
                    prompt=prompt,
                    max_tokens=data.get('max_tokens', 1000),
                    temperature=data.get('temperature', 0.7)
                )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Completion error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "inference_error",
                        "code": 500
                    }
                }), 500
        
        @self.app.route('/api/models/scan', methods=['GET'])
        def scan_models():
            """Scan for models in user directory with ML integration"""
            models_dir = Path.home() / "Models"
            
            # Basic directory scanning always available
            basic_result = {
                "models": [],
                "count": 0,
                "directory": str(models_dir),
                "status": "ml_components_loading" if not self.ml_components_loaded else "ready"
            }
            
            # Enhanced scanning if ML components are loaded
            with self.ml_lock:
                if self.ml_components_loaded and self.ml_manager:
                    try:
                        models = self.ml_manager.scan_user_models()
                        basic_result.update({
                            "models": models,
                            "count": len(models),
                            "status": "ready"
                        })
                    except Exception as e:
                        logger.error(f"Model scanning error: {e}")
                        basic_result["error"] = str(e)
            
            return jsonify(basic_result)
        
        @self.app.route('/api/models/load', methods=['POST'])
        def load_model():
            """Load a model from file path"""
            with self.ml_lock:
                if not self.ml_components_loaded or not self.ml_manager:
                    return jsonify({
                        "error": "ML components not ready",
                        "status": "loading"
                    }), 503
            
            try:
                data = request.json
                model_path = data.get('path')
                model_id = data.get('id')
                
                if not model_path:
                    return jsonify({"error": "Model path required"}), 400
                
                # Thread-safe model loading
                with self.ml_lock:
                    success = self.ml_manager.load_model_from_path(
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
        
        @self.app.route('/api/models/directory', methods=['GET'])
        def get_models_directory():
            """Get models directory info and create if needed"""
            models_dir = Path.home() / "Models"
            
            # Ensure directory exists
            try:
                models_dir.mkdir(exist_ok=True)
                
                # Create subdirectories for different formats
                for format_dir in ['GGUF/chat', 'SafeTensors/chat', 'MLX/chat', 
                                 'CoreML/chat', 'PyTorch/chat', 'ONNX/chat']:
                    (models_dir / format_dir).mkdir(parents=True, exist_ok=True)
                
                return jsonify({
                    'success': True,
                    'directory': str(models_dir),
                    'exists': models_dir.exists(),
                    'created_subdirs': True
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'directory': str(models_dir),
                    'error': str(e)
                }), 500
        
        # Model management endpoints
        @self.app.route('/v1/models/<model_id>/switch', methods=['POST'])
        def switch_model(model_id):
            """Switch to a different model"""
            with self.ml_lock:
                if not self.ml_components_loaded or not self.ml_manager:
                    return jsonify({
                        "error": "ML components not ready",
                        "status": "loading"
                    }), 503
            
            try:
                # Thread-safe model switching
                with self.ml_lock:
                    success = self.ml_manager.switch_model(model_id)
                if success:
                    return jsonify({
                        "status": "success",
                        "model": model_id,
                        "message": f"Switched to model {model_id}"
                    })
                return jsonify({"error": "Failed to switch model"}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        # Hardware detection endpoints
        @self.app.route('/api/hardware/detect', methods=['GET'])
        def detect_hardware():
            """Hardware detection endpoint"""
            if not self.ml_components_loaded or not self.apple_detector:
                # Provide basic system info
                return jsonify({
                    'success': True,
                    'status': 'ml_components_loading',
                    'basic_info': {
                        'platform': sys.platform,
                        'cpu_count': os.cpu_count()
                    }
                })
            
            try:
                chip_info = self.apple_detector.get_processor_info()
                return jsonify({
                    'success': True,
                    'status': 'ready',
                    'hardware': chip_info
                })
            except Exception as e:
                logger.error(f"Hardware detection error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        logger.info("Routes configured successfully")
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the enhanced server"""
        logger.info(f"Starting enhanced production server on {host}:{port}")
        
        print("\n" + "="*60)
        print("🚀 Impetus Enhanced Production Server")
        print("="*60)
        print(f"📡 Server: http://{host}:{port}")
        print(f"✅ Health: http://{host}:{port}/api/health")
        print(f"🔧 ML Status: {'Ready' if self.ml_components_loaded else 'Loading...'}")
        print("="*60 + "\n")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        )


def main():
    """Main entry point"""
    server = EnhancedProductionServer()
    
    # Get configuration from environment
    host = os.environ.get('IMPETUS_HOST', '0.0.0.0')
    port = int(os.environ.get('IMPETUS_PORT', 8080))
    
    try:
        server.run(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


# Create app instance for WSGI servers
server = EnhancedProductionServer()
app = server.app

if __name__ == '__main__':
    main()
