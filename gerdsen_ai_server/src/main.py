#!/usr/bin/env python3
"""
Impetus LLM Server - Main Server File
Threading-compatible app factory for Python 3.13 and production WSGI.
"""

from datetime import datetime
import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS


# Exposed globals filled by create_app()
app = None
socketio = None
SOCKETIO_AVAILABLE = False


def create_app():
    """Application factory that registers blueprints and initializes app state.

    Returns:
        tuple[Flask, Any]: (app, socketio_instance or None)
    """
    from importlib import import_module

    # Make sure the repository root is on sys.path when running as a script
    try:
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
    except Exception:
        pass

    flask_app = Flask(__name__)
    CORS(flask_app)

    # Initialize SocketIO in threading mode for Python 3.13 compatibility
    sio = None
    global SOCKETIO_AVAILABLE
    try:
        from flask_socketio import SocketIO
        sio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="threading")
        SOCKETIO_AVAILABLE = True
        print("📡 SocketIO initialized with threading mode")
    except Exception:
        SOCKETIO_AVAILABLE = False
        print("⚠️  SocketIO not available, running Flask-only mode")

    # App state shared across blueprints
    flask_app.config["app_state"] = {
        "start_time": datetime.now(),
        "status": "running",
        "loaded_models": {},
        "metrics": {},
        "socketio": sio,
    }

    # Lightweight index and docs
    @flask_app.route("/")
    def index():
        start_time = flask_app.config["app_state"]["start_time"]
        uptime = (datetime.now() - start_time).total_seconds()
        return jsonify({
            "name": "Impetus LLM Server",
            "version": "1.0.2",
            "status": "running",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "socketio_available": SOCKETIO_AVAILABLE,
            "uptime_seconds": uptime,
        })

    @flask_app.route("/docs")
    @flask_app.route("/api/docs")
    def api_docs():
        return (
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Impetus LLM Server API</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .method { color: #007bff; font-weight: bold; margin-right: 10px; }
                    .status { background: #d4edda; padding: 10px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🧠 Impetus LLM Server API</h1>
                    <p>High-performance local LLM server optimized for Apple Silicon</p>
                    <div class="status">
                        See <code>/api/health</code>, <code>/api/status</code>, <code>/api/metrics</code>, and OpenAI-compatible <code>/v1/*</code>
                    </div>
                </div>
            </body>
            </html>
            """
        )

    # Register blueprints if available
    def _maybe_register(module_path: str, attr: str, prefix: str):
        try:
            mod = import_module(module_path)
            bp = getattr(mod, attr)
            flask_app.register_blueprint(bp, url_prefix=prefix)
            print(f"✅ Registered {module_path} at {prefix}")
        except Exception as e:
            print(f"ℹ️ Skipped registering {module_path}: {e}")

    # Use absolute import paths to work both as script and package
    _maybe_register("gerdsen_ai_server.src.routes.health", "bp", "/api")
    _maybe_register("gerdsen_ai_server.src.routes.models", "bp", "/api/models")
    _maybe_register("gerdsen_ai_server.src.routes.hardware", "bp", "/api/hardware")
    _maybe_register("gerdsen_ai_server.src.routes.openai_api", "bp", "/v1")

    return flask_app, sio


# Initialize globals for importers (e.g., gunicorn wsgi:application)
app, socketio = create_app()


if __name__ == "__main__":
    print("🚀 Starting Impetus LLM Server...")
    print("📡 Server will be available at: http://localhost:8080")
    print("📚 API Documentation: http://localhost:8080/docs")
    print(f"🐍 Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"🧵 Using threading mode (Python 3.13 compatible)")
    print(f"📡 SocketIO Available: {SOCKETIO_AVAILABLE}")

    try:
        # Use Flask's built-in server with threading for local runs
        app.run(host="0.0.0.0", port=8080, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        raise
