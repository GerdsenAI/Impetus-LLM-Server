#!/usr/bin/env python3
"""
Simplified Production Server for Bundled Electron App
Minimal Flask server that starts without complex imports
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class SimplifiedProductionServer:
    """Simplified production server for bundled deployment"""
    
    def __init__(self):
        """Initialize the simplified server"""
        self.app = Flask(__name__)
        
        # Configure Flask app
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
        
        # Initialize CORS
        CORS(self.app, origins=['http://localhost:*', 'http://127.0.0.1:*'])
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Simplified production server initialized")
    
    def _setup_routes(self):
        """Setup basic API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'server': 'impetus-production',
                'timestamp': time.time()
            })
        
        @self.app.route('/api/system/info', methods=['GET'])
        def system_info():
            """Get basic system information"""
            return jsonify({
                'platform': sys.platform,
                'python_version': sys.version,
                'server_status': 'running'
            })
        
        # OpenAI-compatible endpoints (minimal implementation)
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            """List available models"""
            return jsonify({
                "object": "list",
                "data": []  # No models loaded in simplified version
            })
        
        @self.app.route('/v1/models/<model_id>', methods=['GET'])
        def get_model(model_id):
            """Get model information"""
            return jsonify({"error": "Model not found"}), 404
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def chat_completions():
            """Chat completions endpoint"""
            return jsonify({
                "error": {
                    "message": "No models loaded. Please load a model first.",
                    "type": "no_models_loaded",
                    "code": 503
                }
            }), 503
        
        @self.app.route('/v1/completions', methods=['POST'])
        def completions():
            """Text completions endpoint"""
            return jsonify({
                "error": {
                    "message": "No models loaded. Please load a model first.",
                    "type": "no_models_loaded", 
                    "code": 503
                }
            }), 503
        
        @self.app.route('/api/models/scan', methods=['GET'])
        def scan_models():
            """Scan for models in user directory"""
            models_dir = Path.home() / "Models"
            return jsonify({
                "models": [],
                "count": 0,
                "directory": str(models_dir)
            })
        
        logger.info("Routes configured successfully")
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the server"""
        logger.info(f"Starting simplified production server on {host}:{port}")
        
        print("\n" + "="*60)
        print("🚀 Impetus Production Server (Simplified)")
        print("="*60)
        print(f"📡 Server: http://{host}:{port}")
        print(f"✅ Health: http://{host}:{port}/api/health")
        print("="*60 + "\n")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        )


def main():
    """Main entry point"""
    server = SimplifiedProductionServer()
    
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


if __name__ == '__main__':
    main()