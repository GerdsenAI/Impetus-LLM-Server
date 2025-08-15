#!/usr/bin/env python3
"""
Impetus LLM Server - Main Server File
Fixed version with threading mode to resolve Python 3.13 + eventlet compatibility
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import time
import threading
import subprocess
import psutil
from datetime import datetime

# Fix for Python 3.13: Use standard Flask instead of eventlet
app = Flask(__name__)
CORS(app)

# Try to import SocketIO but fall back gracefully if not available
try:
    from flask_socketio import SocketIO
    # Use threading mode instead of eventlet for Python 3.13 compatibility
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    SOCKETIO_AVAILABLE = True
    print("📡 SocketIO initialized with threading mode")
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("⚠️  SocketIO not available, running Flask only mode")

# Global server state
server_state = {
    "status": "running",
    "start_time": datetime.now(),
    "loaded_model": None,
    "performance_mode": "balanced",
    "models_directory": "/Volumes/M2 Raid0/AI Models"
}

@app.route('/')
def index():
    return jsonify({
        "name": "Impetus LLM Server",
        "version": "1.0.2", 
        "status": "running",
        "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
        "socketio_available": SOCKETIO_AVAILABLE
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime.total_seconds(),
        "server_info": {
            "status": server_state["status"],
            "uptime": str(uptime),
            "loaded_model": server_state["loaded_model"],
            "performance_mode": server_state["performance_mode"]
        }
    })

@app.route('/api/status')
def status():
    """Detailed status endpoint"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    uptime = datetime.now() - server_state["start_time"]
    
    return jsonify({
        "status": "healthy",
        "server": {
            "status": server_state["status"],
            "start_time": server_state["start_time"].isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "uptime_string": str(uptime)
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent
        },
        "model": {
            "loaded": server_state["loaded_model"],
            "performance_mode": server_state["performance_mode"]
        },
        "features": {
            "socketio": SOCKETIO_AVAILABLE,
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
        }
    })

@app.route('/api/models/list')
def list_models():
    """List available models"""
    models = [
        {
            "id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "name": "Mistral 7B (4-bit)",
            "size": "3.8 GB",
            "status": "available",
            "loaded": server_state["loaded_model"] == "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
        },
        {
            "id": "mlx-community/Llama-3.2-3B-Instruct-4bit", 
            "name": "Llama 3.2 3B (4-bit)",
            "size": "1.8 GB", 
            "status": "available",
            "loaded": server_state["loaded_model"] == "mlx-community/Llama-3.2-3B-Instruct-4bit"
        },
        {
            "id": "mlx-community/Phi-3.5-mini-instruct-4bit",
            "name": "Phi 3.5 Mini (4-bit)",
            "size": "2.2 GB",
            "status": "available",
            "loaded": server_state["loaded_model"] == "mlx-community/Phi-3.5-mini-instruct-4bit"
        },
        {
            "id": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
            "name": "Qwen 2.5 Coder 7B (4-bit)", 
            "size": "4.0 GB",
            "status": "available",
            "loaded": server_state["loaded_model"] == "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
        }
    ]
    return jsonify({"models": models, "models_directory": server_state["models_directory"]})

@app.route('/api/models/load', methods=['POST'])
def load_model():
    """Load a model (simulated for testing)"""
    data = request.get_json()
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    
    # Simulate model loading delay
    time.sleep(1)
    server_state["loaded_model"] = model_id
    
    return jsonify({
        "status": "success",
        "message": f"Model {model_id} loaded successfully",
        "model_id": model_id,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/models/unload', methods=['POST'])
def unload_model():
    """Unload current model"""
    previous_model = server_state["loaded_model"]
    server_state["loaded_model"] = None
    return jsonify({
        "status": "success",
        "message": f"Model {previous_model} unloaded successfully" if previous_model else "No model was loaded",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/hardware/info')
def hardware_info():
    """Get hardware information"""
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    
    return jsonify({
        "cpu": {
            "count": cpu_count,
            "percent": psutil.cpu_percent(interval=0.1)
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent
        },
        "system": {
            "platform": os.uname().machine,
            "is_apple_silicon": "arm64" in os.uname().machine
        }
    })

@app.route('/api/hardware/performance-mode', methods=['POST'])
def set_performance_mode():
    """Set performance mode"""
    data = request.get_json()
    mode = data.get('mode', 'balanced')
    
    valid_modes = ['efficiency', 'balanced', 'performance']
    if mode not in valid_modes:
        return jsonify({"error": f"Invalid performance mode. Must be one of: {valid_modes}"}), 400
    
    server_state["performance_mode"] = mode
    
    return jsonify({
        "status": "success",
        "performance_mode": mode,
        "timestamp": datetime.now().isoformat()
    })

# OpenAI-compatible endpoints
@app.route('/v1/models')
def openai_models():
    """OpenAI-compatible models endpoint"""
    models = [
        {
            "id": model["id"],
            "object": "model",
            "created": int(time.time()),
            "owned_by": "mlx-community"
        }
        for model in [
            {"id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit"},
            {"id": "mlx-community/Llama-3.2-3B-Instruct-4bit"},
            {"id": "mlx-community/Phi-3.5-mini-instruct-4bit"},
            {"id": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"}
        ]
    ]
    return jsonify({"object": "list", "data": models})

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    data = request.get_json()
    
    if not server_state["loaded_model"]:
        return jsonify({"error": {"message": "No model loaded. Please load a model first.", "type": "invalid_request_error"}}), 400
    
    # Simulate response (in real implementation, this would call MLX)
    messages = data.get('messages', [])
    last_message = messages[-1] if messages else {"content": "Hello"}
    
    response = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": server_state["loaded_model"],
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant", 
                "content": f"Hello! I'm responding to: '{last_message.get('content', '')}'. This is a simulated response from {server_state['loaded_model']}. The server is working correctly with Python 3.13 and threading mode!"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(str(messages)) // 4,  # Rough estimate
            "completion_tokens": 25,
            "total_tokens": (len(str(messages)) // 4) + 25
        }
    }
    
    return jsonify(response)

@app.route('/docs')
@app.route('/api/docs')  
def api_docs():
    """API documentation"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Impetus LLM Server API</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .endpoint {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .method {{ color: #007bff; font-weight: bold; margin-right: 10px; }}
            .status {{ background: #d4edda; padding: 10px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 Impetus LLM Server API</h1>
            <p>High-performance local LLM server optimized for Apple Silicon</p>
            
            <div class="status">
                <strong>✅ Status:</strong> Server running with Python 3.13 + threading mode<br>
                <strong>📡 SocketIO:</strong> {'Available' if SOCKETIO_AVAILABLE else 'Not Available'}<br>
                <strong>⏰ Uptime:</strong> {datetime.now() - server_state['start_time']}<br>
                <strong>🤖 Loaded Model:</strong> {server_state['loaded_model'] or 'None'}
            </div>
            
            <h2>Health & Status</h2>
            <div class="endpoint">
                <span class="method">GET</span> /api/health - Basic health check
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/status - Detailed server status with system metrics
            </div>
            
            <h2>Model Management</h2>
            <div class="endpoint">
                <span class="method">GET</span> /api/models/list - List available models
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/models/load - Load a model: {{'model_id': 'model_name'}}
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/models/unload - Unload current model
            </div>
            
            <h2>Hardware</h2>
            <div class="endpoint">
                <span class="method">GET</span> /api/hardware/info - Hardware information
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/hardware/performance-mode - Set performance mode
            </div>
            
            <h2>OpenAI Compatible</h2>
            <div class="endpoint">
                <span class="method">GET</span> /v1/models - List models (OpenAI format)
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /v1/chat/completions - Chat completions (requires loaded model)
            </div>
            
            <h2>Test Commands</h2>
            <pre>
# Health check
curl http://localhost:8080/api/health

# Load a model
curl -X POST http://localhost:8080/api/models/load \
  -H "Content-Type: application/json" \
  -d '{{'model_id': 'mlx-community/Phi-3.5-mini-instruct-4bit'}}'

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{{'model': 'mlx-community/Phi-3.5-mini-instruct-4bit', 'messages': [{{'role': 'user', 'content': 'Hello!'}}]}}'
            </pre>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 Starting Impetus LLM Server...")
    print(f"📡 Server will be available at: http://localhost:8080")
    print(f"📚 API Documentation: http://localhost:8080/docs")
    print(f"🐍 Python Version: {psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}")
    print(f"🧵 Using threading mode (Python 3.13 compatible)")
    print(f"📡 SocketIO Available: {SOCKETIO_AVAILABLE}")
    
    try:
        # Use Flask's built-in server with threading
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        raise
