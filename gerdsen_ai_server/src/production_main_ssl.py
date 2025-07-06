#!/usr/bin/env python3
"""
SSL-enabled production server with Flask's built-in SSL support
For production, use this behind a reverse proxy like nginx
"""

import os
import sys
import ssl
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the enhanced production server
from production_main_enhanced import EnhancedProductionServer, logger

# Additional imports for SSL
from utils.config import load_env_file, get_env, get_env_bool

class SSLProductionServer(EnhancedProductionServer):
    """SSL-enabled version of the enhanced production server"""
    
    def create_ssl_context(self):
        """Create and configure SSL context"""
        try:
            cert_path = get_env('SSL_CERT_PATH', 'certs/server.crt')
            key_path = get_env('SSL_KEY_PATH', 'certs/server.key')
            
            # Check if certificate files exist
            cert_path = Path(cert_path)
            key_path = Path(key_path)
            
            if not cert_path.exists():
                logger.error(f"SSL certificate not found: {cert_path}")
                return None
            
            if not key_path.exists():
                logger.error(f"SSL key not found: {key_path}")
                return None
            
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(cert_path), str(key_path))
            
            # Set security options
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            logger.info("SSL context created successfully")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    def run_https(self, host='0.0.0.0', port=8443):
        """Run the server with HTTPS"""
        ssl_context = self.create_ssl_context()
        
        if not ssl_context:
            logger.error("Failed to create SSL context, falling back to HTTP")
            return self.run(host, 8080)
        
        logger.info(f"Starting SSL-enabled production server on https://{host}:{port}")
        
        print("\n" + "="*60)
        print("🔒 Impetus SSL Production Server")
        print("="*60)
        print(f"🔐 HTTPS Server: https://{host}:{port}")
        print(f"✅ Health Check: https://{host}:{port}/api/health")
        print(f"🔧 ML Status: {'Ready' if self.ml_components_loaded else 'Loading...'}")
        print("="*60)
        print("⚠️  Using self-signed certificate - browsers will show warnings")
        print("💡 For production, use a reverse proxy with proper certificates")
        print("="*60 + "\n")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            ssl_context=ssl_context
        )
    
    def run_dual(self, http_host='0.0.0.0', http_port=8080, https_host='0.0.0.0', https_port=8443):
        """Run both HTTP and HTTPS servers (requires threading)"""
        import threading
        
        # Start HTTP server in a thread
        http_thread = threading.Thread(
            target=self.run,
            args=(http_host, http_port),
            daemon=True
        )
        http_thread.start()
        
        # Run HTTPS server in main thread
        self.run_https(https_host, https_port)


def main():
    """Main entry point for SSL server"""
    # Load environment variables
    load_env_file()
    
    server = SSLProductionServer()
    
    # Get configuration
    ssl_enabled = get_env_bool('SSL_ENABLED', False)
    http_port = int(get_env('SERVER_PORT', '8080'))
    https_port = int(get_env('HTTPS_PORT', '8443'))
    host = get_env('SERVER_HOST', '0.0.0.0')
    
    try:
        if ssl_enabled:
            # Check if we should run both HTTP and HTTPS
            dual_mode = get_env_bool('SSL_DUAL_MODE', False)
            
            if dual_mode:
                logger.info("Starting in dual mode (HTTP + HTTPS)")
                server.run_dual(
                    http_host=host,
                    http_port=http_port,
                    https_host=host,
                    https_port=https_port
                )
            else:
                # HTTPS only
                server.run_https(host, https_port)
        else:
            # HTTP only
            server.run(host, http_port)
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


# Create app instance for WSGI servers that support SSL
server = SSLProductionServer()
app = server.app

if __name__ == '__main__':
    main()