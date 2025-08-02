#!/usr/bin/env python3
"""
Impetus LLM Server - Main Application Entry Point
High-performance LLM server optimized for Apple Silicon
"""

import sys
import signal
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logger import app_logger
from src.routes import health, hardware, models, openai_api, websocket
from src.utils.hardware_detector import detect_hardware
from src.utils.error_recovery import error_recovery_service


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.server.api_key or 'impetus-default-secret-key'

# Configure CORS
CORS(app, origins=settings.server.cors_origins)

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=settings.server.cors_origins,
    ping_interval=settings.server.websocket_ping_interval,
    ping_timeout=settings.server.websocket_ping_timeout,
    logger=settings.server.debug,
    engineio_logger=settings.server.debug,
    async_mode='eventlet'
)

# Global state
app_state = {
    'hardware_info': None,
    'loaded_models': {},
    'active_sessions': {},
    'metrics': {
        'requests_total': 0,
        'tokens_generated': 0,
        'average_latency_ms': 0
    }
}


def register_blueprints():
    """Register all API blueprints"""
    app.register_blueprint(health.bp, url_prefix='/api')
    app.register_blueprint(hardware.bp, url_prefix='/api/hardware')
    app.register_blueprint(models.bp, url_prefix='/api/models')
    app.register_blueprint(openai_api.bp, url_prefix='/v1')
    
    # Register WebSocket handlers
    websocket.register_handlers(socketio, app_state)
    
    logger.info("All blueprints registered successfully")


def initialize_hardware():
    """Detect and initialize hardware capabilities"""
    try:
        hardware_info = detect_hardware()
        app_state['hardware_info'] = hardware_info
        
        logger.info(f"Hardware detected: {hardware_info['chip_type']} "
                   f"with {hardware_info['total_memory_gb']:.1f}GB RAM")
        
        # Set performance mode based on hardware
        if hardware_info['performance_cores'] >= 8:
            logger.info("High-performance hardware detected, enabling performance mode")
            settings.hardware.performance_mode = "performance"
        
        # Start Metal GPU monitoring if on macOS
        import platform
        if platform.system() == 'Darwin':
            from src.utils.metal_monitor import metal_monitor
            metal_monitor.start_monitoring(interval_seconds=2.0)
            logger.info("Started Metal GPU monitoring")
            
    except Exception as e:
        logger.error(f"Failed to detect hardware: {e}")
        app_state['hardware_info'] = {
            'chip_type': 'Unknown',
            'total_memory_gb': 8.0,
            'available_memory_gb': 4.0,
            'performance_cores': 4,
            'efficiency_cores': 4
        }


def handle_shutdown(signum, frame):
    """Graceful shutdown handler"""
    logger.info("Received shutdown signal, cleaning up...")
    
    # Stop Metal monitoring
    import platform
    if platform.system() == 'Darwin':
        try:
            from src.utils.metal_monitor import metal_monitor
            metal_monitor.stop_monitoring()
            logger.info("Stopped Metal GPU monitoring")
        except Exception as e:
            logger.error(f"Error stopping Metal monitoring: {e}")
    
    # Shutdown warmup service
    try:
        from src.services.model_warmup import model_warmup_service
        model_warmup_service.shutdown()
        logger.info("Shutdown warmup service")
    except Exception as e:
        logger.error(f"Error shutting down warmup service: {e}")
    
    # Unload all models
    for model_id in list(app_state['loaded_models'].keys()):
        try:
            app_state['loaded_models'][model_id].unload()
            logger.info(f"Unloaded model: {model_id}")
        except Exception as e:
            logger.error(f"Error unloading model {model_id}: {e}")
    
    sys.exit(0)


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def create_app():
    """Application factory"""
    # Store app_state in Flask config
    app.config['app_state'] = app_state
    
    # Initialize error recovery service
    error_recovery_service.set_app_state(app_state)
    
    # Initialize hardware detection
    initialize_hardware()
    
    # Register blueprints
    register_blueprints()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    logger.info(f"Impetus LLM Server v{settings.version} initialized")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Server will run on {settings.server.host}:{settings.server.port}")
    
    return app, socketio


def main():
    """Main entry point"""
    app, socketio = create_app()
    
    try:
        if settings.environment == "production":
            # Production mode with eventlet
            logger.info("Starting production server with eventlet...")
            socketio.run(
                app,
                host=settings.server.host,
                port=settings.server.port,
                debug=False,
                use_reloader=False
            )
        else:
            # Development mode
            logger.info("Starting development server...")
            socketio.run(
                app,
                host=settings.server.host,
                port=settings.server.port,
                debug=settings.server.debug,
                use_reloader=True
            )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()