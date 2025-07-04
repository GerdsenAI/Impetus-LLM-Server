#!/usr/bin/env python3
"""
Simple test server to verify basic functionality
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the main UI"""
    return send_from_directory('ui', 'apple_hig_index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'GerdsenAI server is running',
        'version': '1.0.0'
    })

@app.route('/api/system/info')
def system_info():
    """System information endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'platform': 'test',
            'cpu_count': 4,
            'memory_gb': 8,
            'apple_silicon': False
        }
    })

@app.route('/api/openai/models')
def openai_models():
    """OpenAI models endpoint"""
    return jsonify({
        'success': True,
        'data': [
            {
                'id': 'gpt-4',
                'name': 'GPT-4',
                'description': 'Most capable GPT-4 model'
            },
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'description': 'Fast and efficient model'
            }
        ]
    })

@app.route('/api/terminal/execute', methods=['POST'])
def terminal_execute():
    """Terminal execution endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'output': 'Command executed successfully (test mode)',
            'exit_code': 0
        }
    })

@app.route('/api/service/status')
def service_status():
    """Service status endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'running': True,
            'port': 8080,
            'service_available': True
        }
    })

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('ui', filename)

if __name__ == '__main__':
    print("Starting GerdsenAI Test Server...")
    print("Server will be available at: http://localhost:8081")
    app.run(host='0.0.0.0', port=8081, debug=False)

