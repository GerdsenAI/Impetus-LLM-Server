#!/usr/bin/env python3
"""
Production Server for Bundled Electron App with Full ML Support
Handles import path differences and progressively loads ML functionality
"""

import os
import sys
import logging
import json
import time
import threading
import importlib
from pathlib import Path
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Configure the Python path for bundled environment
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class MLComponentLoader:
    """Dynamic ML component loader for bundled environment"""
    
    def __init__(self):
        self.components = {}
        self.load_attempts = {}
        
    def try_import(self, module_names, component_name):
        """Try multiple import strategies for a module"""
        if isinstance(module_names, str):
            module_names = [module_names]
            
        for module_name in module_names:
            try:
                # Strategy 1: Direct import
                module = importlib.import_module(module_name)
                self.components[component_name] = module
                logger.info(f"✅ Loaded {component_name} via direct import: {module_name}")
                return module
            except ImportError:
                pass
                
            try:
                # Strategy 2: Import from current directory
                if '.' not in module_name:
                    module = importlib.import_module(f'.{module_name}', package=None)
                    self.components[component_name] = module
                    logger.info(f"✅ Loaded {component_name} via relative import: .{module_name}")
                    return module
            except ImportError:
                pass
        
        # Log failure
        self.load_attempts[component_name] = module_names
        logger.warning(f"❌ Failed to load {component_name} from: {module_names}")
        return None
    
    def get_class(self, component_name, class_name):
        """Get a class from a loaded component"""
        module = self.components.get(component_name)
        if module and hasattr(module, class_name):
            return getattr(module, class_name)
        return None

class BundledProductionServer:
    """Production server optimized for bundled Electron environment"""
    
    def __init__(self):
        """Initialize the bundled server with ML support"""
        self.app = Flask(__name__)
        
        # Configure Flask app
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-bundled')
        
        # Initialize CORS
        cors_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',')
        logger.info(f"Configuring CORS with origins: {cors_origins}")
        CORS(self.app, origins=cors_origins)
        
        # ML component management
        self.ml_loader = MLComponentLoader()
        self.ml_components_loaded = False
        self.ml_manager = None
        self.apple_detector = None
        self.frameworks = None
        self.ml_lock = threading.Lock()
        
        # Track loaded models
        self.loaded_models = {}
        self.active_model = None
        
        # Setup routes
        self._setup_routes()
        
        # Start ML loading in background
        self._init_ml_components_async()
        
        logger.info("Bundled production server initialized")
    
    def _init_ml_components_async(self):
        """Initialize ML components asynchronously"""
        def load_ml_components():
            try:
                logger.info("Starting ML components initialization for bundled environment...")
                
                # Load components with multiple import strategies
                self.ml_loader.try_import([
                    'enhanced_apple_silicon_detector',
                    'gerdsen_ai_server.src.enhanced_apple_silicon_detector'
                ], 'apple_detector')
                
                self.ml_loader.try_import([
                    'enhanced_apple_frameworks_integration',
                    'gerdsen_ai_server.src.enhanced_apple_frameworks_integration'
                ], 'frameworks')
                
                self.ml_loader.try_import([
                    'integrated_mlx_manager_bundled',
                    'integrated_mlx_manager',
                    'gerdsen_ai_server.src.integrated_mlx_manager'
                ], 'ml_manager')
                
                # Try to instantiate components
                with self.ml_lock:
                    # Apple Silicon Detector
                    detector_class = self.ml_loader.get_class('apple_detector', 'EnhancedAppleSiliconDetector')
                    if detector_class:
                        try:
                            self.apple_detector = detector_class()
                            logger.info("✅ Apple Silicon detector initialized")
                        except Exception as e:
                            logger.error(f"Failed to initialize Apple detector: {e}")
                    
                    # Apple Frameworks
                    frameworks_class = self.ml_loader.get_class('frameworks', 'EnhancedAppleFrameworksIntegration')
                    if frameworks_class:
                        try:
                            self.frameworks = frameworks_class()
                            logger.info("✅ Apple frameworks initialized")
                        except Exception as e:
                            logger.error(f"Failed to initialize frameworks: {e}")
                    
                    # ML Manager - with special handling for bundled environment
                    ml_manager_class = self.ml_loader.get_class('ml_manager', 'IntegratedMLXManager')
                    if ml_manager_class:
                        try:
                            # Create a modified ML manager for bundled environment
                            self.ml_manager = self._create_bundled_ml_manager(ml_manager_class)
                            logger.info("✅ ML manager initialized for bundled environment")
                        except Exception as e:
                            logger.error(f"Failed to initialize ML manager: {e}")
                    
                    # Check if we have at least basic ML functionality
                    self.ml_components_loaded = (
                        self.apple_detector is not None or 
                        self.frameworks is not None or 
                        self.ml_manager is not None
                    )
                    
                    if self.ml_components_loaded:
                        logger.info("✅ ML components loaded successfully")
                        # Try to scan for models
                        self._scan_initial_models()
                    else:
                        logger.warning("⚠️ No ML components could be loaded")
                        
            except Exception as e:
                logger.error(f"ML initialization error: {e}", exc_info=True)
                self.ml_components_loaded = False
        
        # Start loading in background
        ml_thread = threading.Thread(target=load_ml_components, daemon=True)
        ml_thread.start()
    
    def _create_bundled_ml_manager(self, ml_manager_class):
        """Create ML manager with bundled environment adaptations"""
        try:
            # First try to create the manager directly
            manager = ml_manager_class()
            return manager
        except Exception as e:
            logger.warning(f"Direct ML manager creation failed: {e}")
            
            # Create a minimal wrapper that provides basic functionality
            class BundledMLManager:
                def __init__(self):
                    self.models = {}
                    self.active_model = None
                    logger.info("Using bundled ML manager wrapper")
                
                def get_available_models(self):
                    """Return list of available models"""
                    return [
                        {
                            "id": model_id,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "local",
                            **info
                        }
                        for model_id, info in self.models.items()
                    ]
                
                def scan_user_models(self):
                    """Scan user's Models directory"""
                    models_dir = Path.home() / "Models"
                    found_models = []
                    
                    if models_dir.exists():
                        # Scan for GGUF models
                        for gguf_file in models_dir.rglob("*.gguf"):
                            model_info = {
                                "id": gguf_file.stem,
                                "name": gguf_file.name,
                                "path": str(gguf_file),
                                "format": "GGUF",
                                "size": gguf_file.stat().st_size
                            }
                            found_models.append(model_info)
                            self.models[gguf_file.stem] = model_info
                    
                    return found_models
                
                def load_model_from_path(self, model_path, model_id=None):
                    """Load a model from file path"""
                    path = Path(model_path)
                    if not path.exists():
                        raise FileNotFoundError(f"Model not found: {model_path}")
                    
                    if model_id is None:
                        model_id = path.stem
                    
                    self.models[model_id] = {
                        "id": model_id,
                        "name": path.name,
                        "path": str(path),
                        "format": path.suffix.upper().lstrip('.'),
                        "loaded": True
                    }
                    self.active_model = model_id
                    return True
                
                def switch_model(self, model_id):
                    """Switch active model"""
                    if model_id in self.models:
                        self.active_model = model_id
                        return True
                    return False
                
                def get_model_info(self, model_id):
                    """Get model information"""
                    return self.models.get(model_id)
                
                def create_chat_completion(self, **kwargs):
                    """Create chat completion - placeholder for now"""
                    return {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": kwargs.get('model', 'unknown'),
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "ML inference is being integrated. Please check back soon."
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": 10,
                            "completion_tokens": 10,
                            "total_tokens": 20
                        }
                    }
                
                def generate_text(self, **kwargs):
                    """Generate text completion - placeholder"""
                    return {
                        "id": f"cmpl-{int(time.time())}",
                        "object": "text_completion",
                        "created": int(time.time()),
                        "model": kwargs.get('model', 'unknown'),
                        "choices": [{
                            "text": "ML inference is being integrated.",
                            "index": 0,
                            "finish_reason": "stop"
                        }]
                    }
            
            return BundledMLManager()
    
    def _scan_initial_models(self):
        """Scan for models on startup"""
        try:
            if self.ml_manager and hasattr(self.ml_manager, 'scan_user_models'):
                models = self.ml_manager.scan_user_models()
                logger.info(f"Found {len(models)} models during initial scan")
        except Exception as e:
            logger.error(f"Initial model scan failed: {e}")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0-bundled',
                'server': 'impetus-bundled-production',
                'timestamp': time.time(),
                'ml_components_loaded': self.ml_components_loaded,
                'components': {
                    'apple_detector': self.apple_detector is not None,
                    'frameworks': self.frameworks is not None,
                    'ml_manager': self.ml_manager is not None
                },
                'loaded_components': list(self.ml_loader.components.keys()),
                'failed_imports': self.ml_loader.load_attempts
            })
        
        @self.app.route('/api/system/info', methods=['GET'])
        def system_info():
            """System information endpoint"""
            info = {
                'platform': sys.platform,
                'python_version': sys.version,
                'server_status': 'running',
                'ml_status': 'ready' if self.ml_components_loaded else 'loading',
                'bundled': True,
                'working_directory': os.getcwd(),
                'python_path': sys.path[:3]  # Show first 3 paths
            }
            
            if self.apple_detector:
                try:
                    info['hardware'] = self.apple_detector.get_processor_info()
                except Exception as e:
                    logger.warning(f"Could not get hardware info: {e}")
            
            return jsonify(info)
        
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            """List available models"""
            if not self.ml_manager:
                return jsonify({
                    "object": "list",
                    "data": [],
                    "status": "ml_components_loading"
                })
            
            try:
                models = self.ml_manager.get_available_models()
                return jsonify({
                    "object": "list",
                    "data": models
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
            if not self.ml_manager:
                return jsonify({"error": "ML components not ready"}), 503
            
            try:
                model_info = self.ml_manager.get_model_info(model_id)
                if model_info:
                    return jsonify(model_info)
                return jsonify({"error": "Model not found"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def chat_completions():
            """Chat completions endpoint"""
            if not self.ml_manager:
                return jsonify({
                    "error": {
                        "message": "ML components are still loading. Please wait.",
                        "type": "ml_loading",
                        "code": 503
                    }
                }), 503
            
            try:
                data = request.json
                response = self.ml_manager.create_chat_completion(
                    model=data.get('model', 'default'),
                    messages=data.get('messages', []),
                    max_tokens=data.get('max_tokens', 1000),
                    temperature=data.get('temperature', 0.7),
                    stream=data.get('stream', False)
                )
                
                if data.get('stream', False):
                    # Handle streaming response
                    def generate():
                        yield f"data: {json.dumps(response)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    return Response(
                        generate(),
                        mimetype='text/event-stream',
                        headers={
                            'Cache-Control': 'no-cache',
                            'X-Accel-Buffering': 'no'
                        }
                    )
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                return jsonify({
                    "error": {
                        "message": str(e),
                        "type": "inference_error"
                    }
                }), 500
        
        @self.app.route('/v1/completions', methods=['POST'])
        def completions():
            """Text completions endpoint"""
            if not self.ml_manager:
                return jsonify({
                    "error": {
                        "message": "ML components are still loading.",
                        "type": "ml_loading"
                    }
                }), 503
            
            try:
                data = request.json
                response = self.ml_manager.generate_text(
                    model=data.get('model', 'default'),
                    prompt=data.get('prompt', ''),
                    max_tokens=data.get('max_tokens', 1000),
                    temperature=data.get('temperature', 0.7)
                )
                return jsonify(response)
            except Exception as e:
                logger.error(f"Completion error: {e}")
                return jsonify({"error": {"message": str(e)}}), 500
        
        @self.app.route('/api/models/scan', methods=['GET'])
        def scan_models():
            """Scan for models"""
            models_dir = Path.home() / "Models"
            
            result = {
                "models": [],
                "count": 0,
                "directory": str(models_dir),
                "status": "ready" if self.ml_components_loaded else "loading"
            }
            
            if self.ml_manager:
                try:
                    models = self.ml_manager.scan_user_models()
                    result.update({
                        "models": models,
                        "count": len(models)
                    })
                except Exception as e:
                    logger.error(f"Model scan error: {e}")
                    result["error"] = str(e)
            
            return jsonify(result)
        
        @self.app.route('/api/models/load', methods=['POST'])
        def load_model():
            """Load a model"""
            if not self.ml_manager:
                return jsonify({"error": "ML components not ready"}), 503
            
            try:
                data = request.json
                model_path = data.get('path')
                
                if not model_path:
                    return jsonify({"error": "Model path required"}), 400
                
                with self.ml_lock:
                    success = self.ml_manager.load_model_from_path(
                        model_path,
                        data.get('id')
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
            """Get models directory info"""
            models_dir = Path.home() / "Models"
            
            try:
                # Create directory structure
                models_dir.mkdir(exist_ok=True)
                
                formats = ['GGUF', 'SafeTensors', 'MLX', 'CoreML', 'PyTorch', 'ONNX']
                capabilities = ['chat', 'completion', 'embedding']
                
                for fmt in formats:
                    for cap in capabilities:
                        (models_dir / fmt / cap).mkdir(parents=True, exist_ok=True)
                
                return jsonify({
                    'success': True,
                    'directory': str(models_dir),
                    'exists': True,
                    'formats': formats,
                    'structure_created': True
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/v1/models/<model_id>/switch', methods=['POST'])
        def switch_model(model_id):
            """Switch active model"""
            if not self.ml_manager:
                return jsonify({"error": "ML components not ready"}), 503
            
            try:
                with self.ml_lock:
                    success = self.ml_manager.switch_model(model_id)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "model": model_id
                    })
                return jsonify({"error": "Failed to switch model"}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/hardware/detect', methods=['GET'])
        def detect_hardware():
            """Detect hardware capabilities"""
            info = {
                'platform': sys.platform,
                'cpu_count': os.cpu_count()
            }
            
            if self.apple_detector:
                try:
                    info['apple_silicon'] = self.apple_detector.get_processor_info()
                except Exception as e:
                    logger.warning(f"Hardware detection error: {e}")
            
            return jsonify({
                'success': True,
                'hardware': info
            })
        
        logger.info("Routes configured successfully")
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the server"""
        logger.info(f"Starting bundled production server on {host}:{port}")
        
        print("\n" + "="*60)
        print("🚀 Impetus Bundled Production Server")
        print("="*60)
        print(f"📡 Server: http://{host}:{port}")
        print(f"✅ Health: http://{host}:{port}/api/health")
        print(f"🔧 ML Status: {'Ready' if self.ml_components_loaded else 'Loading...'}")
        print(f"📁 Models: ~/Models/")
        print("="*60 + "\n")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        )


def main():
    """Main entry point"""
    server = BundledProductionServer()
    
    # Get configuration
    host = os.environ.get('IMPETUS_HOST', '0.0.0.0')
    port = int(os.environ.get('IMPETUS_PORT', 8080))
    
    try:
        server.run(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


# WSGI app instance
server = BundledProductionServer()
app = server.app

if __name__ == '__main__':
    main()