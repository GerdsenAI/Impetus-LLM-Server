#!/usr/bin/env python3
"""
Production server launcher for Impetus LLM Server
Starts the server using gunicorn with optimal configuration for Apple Silicon
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch production server with gunicorn"""
    
    # Set production environment
    os.environ['IMPETUS_ENVIRONMENT'] = 'production'
    
    # Get repository root
    repo_root = Path(__file__).parent
    config_path = repo_root / "gerdsen_ai_server" / "gunicorn_config.py"
    
    # Ensure we're in the right directory
    os.chdir(repo_root)
    
    # Configuration
    host = os.getenv('IMPETUS_HOST', '127.0.0.1')  # Secure local binding
    port = os.getenv('IMPETUS_PORT', '8080')
    workers = os.getenv('IMPETUS_WORKERS', '4')
    log_level = os.getenv('IMPETUS_LOG_LEVEL', 'info')
    
    print("🏭 Starting Impetus LLM Server in Production Mode")
    print("=================================================")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👷 Workers: {workers}")
    print(f"📝 Log Level: {log_level}")
    print(f"📁 Config: {config_path}")
    print("")
    
    # Gunicorn command
    cmd = [
        "gunicorn",
        "--config", str(config_path),
        "--bind", f"{host}:{port}",
        "--workers", workers,
        "--worker-class", "eventlet",
        "--worker-connections", "1000",
        "--timeout", "300",
        "--graceful-timeout", "120",
        "--log-level", log_level,
        "--access-logfile", "-",
        "--error-logfile", "-",
        "gerdsen_ai_server.src.main:app"
    ]
    
    try:
        print("🚀 Starting server...")
        print(f"💡 Access the server at: http://{host}:{port}")
        print(f"📚 API docs at: http://{host}:{port}/docs")
        print("")
        
        # Run gunicorn
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Gunicorn not found. Please install it:")
        print("   pip install gunicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()