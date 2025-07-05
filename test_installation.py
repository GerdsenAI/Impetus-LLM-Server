#!/usr/bin/env python3
"""
Test IMPETUS installation and model scanning
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

def test_directories():
    """Test if model directories exist"""
    print("🔍 Checking model directories...")
    
    models_dir = Path.home() / "Models"
    if not models_dir.exists():
        print("❌ Models directory not found!")
        return False
    
    print(f"✅ Models directory exists: {models_dir}")
    
    # Check subdirectories
    expected_dirs = ['GGUF', 'SafeTensors', 'MLX', 'CoreML', 'PyTorch', 'ONNX']
    for dir_name in expected_dirs:
        dir_path = models_dir / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ exists")
        else:
            print(f"  ✗ {dir_name}/ missing")
    
    return True

def test_server_connection():
    """Test if IMPETUS server is running"""
    print("\n🔍 Checking server connection...")
    
    try:
        req = urllib.request.Request("http://localhost:8080/api/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print("✅ Server is running at http://localhost:8080")
                return True
            else:
                print(f"❌ Server returned status: {response.status}")
                return False
    except urllib.error.URLError:
        print("❌ Server is not running. Please start IMPETUS from Applications.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_model_scanning():
    """Test model scanning API"""
    print("\n🔍 Testing model scanning API...")
    
    try:
        req = urllib.request.Request("http://localhost:8080/api/models/scan")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get('success'):
                    models = data.get('models', {})
                    total = data.get('total_models', 0)
                    
                    print(f"✅ Model scan successful!")
                    print(f"  Found {total} models")
                    
                    if total > 0:
                        print("\n  Models found:")
                        for model_name, model_list in models.items():
                            for model in model_list:
                                print(f"    - {model_name} ({model['format']}) in {model['capability']}/")
                    else:
                        print("\n  No models found. To add models:")
                        print("  1. Download models from https://huggingface.co/models")
                        print("  2. Place them in ~/Models/<format>/<capability>/")
                        print("  3. Run 'Scan for Models' from IMPETUS menu")
                    
                    return True
                else:
                    print(f"❌ Model scan failed: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Server returned status: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Error scanning models: {e}")
        return False

def test_openai_compatibility():
    """Test OpenAI API compatibility"""
    print("\n🔍 Testing OpenAI API compatibility...")
    
    try:
        req = urllib.request.Request("http://localhost:8080/v1/models")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                models = data.get('data', [])
                
                print(f"✅ OpenAI API endpoint working!")
                print(f"  Available models: {len(models)}")
                
                for model in models:
                    print(f"    - {model['id']} (created: {model.get('created', 'unknown')})")
                
                return True
            else:
                print(f"❌ Server returned status: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Error testing OpenAI API: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 IMPETUS Installation Test")
    print("============================\n")
    
    # Check if IMPETUS is installed
    app_path = Path("/Applications/IMPETUS.app")
    if app_path.exists():
        print("✅ IMPETUS.app is installed in Applications")
    else:
        print("❌ IMPETUS.app not found in Applications")
        print("  Run: ./impetus-electron/install-impetus.sh")
    
    # Run tests
    tests_passed = 0
    tests_total = 4
    
    if test_directories():
        tests_passed += 1
    
    if test_server_connection():
        tests_passed += 1
        
        # Only run API tests if server is running
        if test_model_scanning():
            tests_passed += 1
        
        if test_openai_compatibility():
            tests_passed += 1
    else:
        print("\n⚠️  Skipping API tests - server not running")
        print("Please start IMPETUS from Applications first")
        tests_total = 2  # Only directory and connection tests
    
    # Summary
    print(f"\n{'='*40}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✅ All tests passed! IMPETUS is ready to use.")
        print("\nNext steps:")
        print("1. Add models to ~/Models/GGUF/chat/")
        print("2. Click 'Scan for Models' in IMPETUS menu")
        print("3. Configure VS Code/Cline to use http://localhost:8080")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()