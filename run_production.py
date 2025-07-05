#!/usr/bin/env python3
"""
Production server runner using Waitress (cross-platform WSGI server)
"""

import os
import sys
import logging
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'gerdsen_ai_server' / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/production.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for production server"""
    try:
        # Load environment configuration
        try:
            from gerdsen_ai_server.src.utils.config import load_env_file
            load_env_file()
        except ImportError:
            logger.warning("Config utils not available, using system environment")
        
        # Get configuration
        host = os.environ.get('SERVER_HOST', '0.0.0.0')
        port = int(os.environ.get('SERVER_PORT', '8080'))
        workers = int(os.environ.get('WAITRESS_THREADS', '4'))
        
        # Determine which server to use
        use_enhanced = os.environ.get('USE_ENHANCED_SERVER', 'true').lower() == 'true'
        
        if use_enhanced:
            logger.info("Starting enhanced production server with ML components")
            from gerdsen_ai_server.src.production_main_enhanced import app
        else:
            logger.info("Starting standard production server")
            from gerdsen_ai_server.src.production_main import app
        
        # Configure Waitress
        logger.info(f"Starting Waitress server on {host}:{port} with {workers} threads")
        
        print("\n" + "="*60)
        print("🚀 Impetus Production Server (Waitress)")
        print("="*60)
        print(f"📡 Server: http://{host}:{port}")
        print(f"✅ Health: http://{host}:{port}/api/health")
        print(f"🔧 Threads: {workers}")
        print(f"📁 Logs: logs/production.log")
        print("="*60 + "\n")
        
        # Import and run Waitress
        from waitress import serve
        
        serve(
            app,
            host=host,
            port=port,
            threads=workers,
            url_scheme='https' if os.environ.get('SSL_CERT_PATH') else 'http',
            ident='Impetus-LLM-Server',
            cleanup_interval=10,
            channel_timeout=120,
            connection_limit=1000,
            max_request_body_size=int(os.environ.get('UPLOAD_MAX_SIZE_MB', '5000')) * 1024 * 1024
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install Waitress: pip install waitress")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Run the server
    main()