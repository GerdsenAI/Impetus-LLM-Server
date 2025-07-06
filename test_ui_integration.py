#!/usr/bin/env python3
"""Test Model Management UI integration with backend"""

import time
import subprocess
import requests
import json

def test_backend_api():
    """Test backend API endpoints"""
    print("Testing Backend API...")
    
    # Test model scan
    try:
        response = requests.get("http://localhost:8080/api/models/scan")
        data = response.json()
        print(f"✅ Model scan successful - Found {data['total_models']} models")
        print(f"   - GGUF models: {data['directory_info']['format_directories']['gguf']['model_count']}")
    except Exception as e:
        print(f"❌ Model scan failed: {e}")
    
    # Test performance metrics
    try:
        response = requests.get("http://localhost:8080/api/performance/metrics")
        data = response.json()
        print(f"✅ Performance metrics available")
        print(f"   - CPU: {data['cpu']['usage']:.1f}%")
        print(f"   - Memory: {data['memory']['percent']:.1f}%")
    except Exception as e:
        print(f"❌ Performance metrics failed: {e}")
    
    # Test model list
    try:
        response = requests.get("http://localhost:8080/v1/models")
        data = response.json()
        print(f"✅ Model list endpoint working - {len(data['data'])} models loaded")
    except Exception as e:
        print(f"❌ Model list failed: {e}")

def test_frontend_access():
    """Test frontend accessibility"""
    print("\nTesting Frontend Access...")
    
    try:
        response = requests.get("http://localhost:5173")
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:5173")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")

def main():
    print("=== Model Management UI Integration Test ===\n")
    
    # Check if servers are running
    print("Checking server status...")
    
    # Test backend
    backend_running = False
    try:
        requests.get("http://localhost:8080", timeout=2)
        backend_running = True
        print("✅ Backend server is running on port 8080")
    except:
        print("❌ Backend server is not running")
        print("   Run: source venv/bin/activate && python gerdsen_ai_server/src/production_main.py")
    
    # Test frontend
    frontend_running = False
    try:
        requests.get("http://localhost:5173", timeout=2)
        frontend_running = True
        print("✅ Frontend server is running on port 5173")
    except:
        print("❌ Frontend server is not running")
        print("   Run: cd gerdsen-ai-frontend && pnpm dev")
    
    if backend_running:
        test_backend_api()
    
    if frontend_running:
        test_frontend_access()
    
    if backend_running and frontend_running:
        print("\n✅ Both servers are running! You can access the UI at:")
        print("   http://localhost:5173")
        print("\nThe Model Management UI provides:")
        print("   - Model Library view with all detected models")
        print("   - Drag & drop upload for new models")
        print("   - HuggingFace model search and download")
        print("   - Real-time performance monitoring")
        print("   - WebSocket updates for model status")
    else:
        print("\n⚠️  Please start both servers to test the full integration")

if __name__ == "__main__":
    main()