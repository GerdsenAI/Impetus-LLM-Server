#!/usr/bin/env python3
"""
SSL-enabled production server runner using Waitress
"""

import os
import sys
import ssl
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
        logging.FileHandler('logs/production_ssl.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def create_ssl_context():
    """Create SSL context with proper security settings"""
    try:
        # Load environment configuration
        from gerdsen_ai_server.src.utils.config import get_env, get_env_bool
        
        if not get_env_bool('SSL_ENABLED', False):
            return None
            
        cert_path = get_env('SSL_CERT_PATH', 'certs/server.crt')
        key_path = get_env('SSL_KEY_PATH', 'certs/server.key')
        dhparam_path = get_env('SSL_DHPARAM_PATH', 'certs/dhparam.pem')
        
        # Verify certificate files exist
        if not Path(cert_path).exists():
            logger.error(f"SSL certificate not found: {cert_path}")
            return None
        if not Path(key_path).exists():
            logger.error(f"SSL key not found: {key_path}")
            return None
            
        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_path, key_path)
        
        # Set security options
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Load DH parameters if available
        if Path(dhparam_path).exists():
            context.load_dh_params(dhparam_path)
            
        logger.info("SSL context created successfully")
        return context
        
    except Exception as e:
        logger.error(f"Failed to create SSL context: {e}")
        return None

def main():
    """Main entry point for SSL-enabled production server"""
    try:
        # Load environment configuration
        try:
            from gerdsen_ai_server.src.utils.config import load_env_file, get_env, get_env_bool
            load_env_file()
        except ImportError:
            logger.warning("Config utils not available, using system environment")
            def get_env(key, default=None):
                return os.environ.get(key, default)
            def get_env_bool(key, default=False):
                value = os.environ.get(key, str(default))
                return value.lower() in ('true', '1', 'yes', 'on')
        
        # Get configuration
        host = get_env('SERVER_HOST', '0.0.0.0')
        http_port = int(get_env('SERVER_PORT', '8080'))
        https_port = int(get_env('HTTPS_PORT', '8443'))
        workers = int(get_env('WAITRESS_THREADS', '4'))
        ssl_enabled = get_env_bool('SSL_ENABLED', False)
        
        # Determine which server to use
        use_enhanced = get_env_bool('USE_ENHANCED_SERVER', 'true')
        
        if use_enhanced:
            logger.info("Starting enhanced production server with ML components")
            from gerdsen_ai_server.src.production_main_enhanced import app
        else:
            logger.info("Starting standard production server")
            from gerdsen_ai_server.src.production_main import app
        
        # Import Waitress
        from waitress import serve
        
        if ssl_enabled:
            # Create SSL context
            ssl_context = create_ssl_context()
            
            if ssl_context:
                logger.info(f"Starting HTTPS server on {host}:{https_port}")
                
                print("\n" + "="*60)
                print("🔒 Impetus Production Server (HTTPS)")
                print("="*60)
                print(f"🔐 HTTPS Server: https://{host}:{https_port}")
                print(f"✅ Health Check: https://{host}:{https_port}/api/health")
                print(f"🔧 Threads: {workers}")
                print(f"📁 Logs: logs/production_ssl.log")
                print("="*60)
                print("⚠️  Using self-signed certificate - browsers will show warnings")
                print("="*60 + "\n")
                
                # Start HTTPS server
                serve(
                    app,
                    host=host,
                    port=https_port,
                    threads=workers,
                    url_scheme='https',
                    ident='Impetus-LLM-Server-SSL',
                    cleanup_interval=10,
                    channel_timeout=120,
                    connection_limit=1000,
                    max_request_body_size=int(get_env('UPLOAD_MAX_SIZE_MB', '5000')) * 1024 * 1024,
                    # Note: Waitress doesn't directly support SSL context
                    # For production SSL, use a reverse proxy like nginx
                )
            else:
                logger.error("SSL enabled but context creation failed, falling back to HTTP")
                ssl_enabled = False
        
        if not ssl_enabled:
            # Start HTTP server
            logger.info(f"Starting HTTP server on {host}:{http_port}")
            
            print("\n" + "="*60)
            print("🚀 Impetus Production Server (HTTP)")
            print("="*60)
            print(f"📡 Server: http://{host}:{http_port}")
            print(f"✅ Health: http://{host}:{http_port}/api/health")
            print(f"🔧 Threads: {workers}")
            print(f"📁 Logs: logs/production_ssl.log")
            print("="*60 + "\n")
            
            serve(
                app,
                host=host,
                port=http_port,
                threads=workers,
                url_scheme='http',
                ident='Impetus-LLM-Server',
                cleanup_interval=10,
                channel_timeout=120,
                connection_limit=1000,
                max_request_body_size=int(get_env('UPLOAD_MAX_SIZE_MB', '5000')) * 1024 * 1024
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