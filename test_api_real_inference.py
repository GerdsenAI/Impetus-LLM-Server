#!/usr/bin/env python3
"""
Test OpenAI API endpoints with real GGUF inference
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_models_endpoint():
    """Test /v1/models endpoint"""
    print("🔍 Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models endpoint working")
            print(f"   Found {len(data.get('data', []))} models")
            for model in data.get('data', []):
                print(f"   - {model['id']} ({model.get('format', 'unknown')})")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_chat_completion():
    """Test /v1/chat/completions with real inference"""
    print("\n🔍 Testing /v1/chat/completions with real inference...")
    
    # Get available models first
    try:
        models_response = requests.get(f"{BASE_URL}/v1/models")
        models = models_response.json().get('data', [])
        
        if not models:
            print("⚠️ No models loaded!")
            return False
            
        # Use the first available model
        model_id = models[0]['id']
        print(f"✅ Using model: {model_id}")
        
        # Test chat completion
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a simple Python hello world function."}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-dev-test"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got a real response (not dummy)
            content = data['choices'][0]['message']['content']
            
            print(f"✅ Chat completion successful!")
            print(f"⏱️ Response time: {elapsed:.2f}s")
            print(f"📝 Response preview: {content[:100]}...")
            
            # Check if it's a dummy response
            if "I received your prompt" in content:
                print("⚠️ WARNING: Using dummy responses, not real inference!")
                return False
            else:
                print("✅ Real inference detected!")
                return True
                
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_text_completion():
    """Test /v1/completions endpoint"""
    print("\n🔍 Testing /v1/completions endpoint...")
    
    try:
        models_response = requests.get(f"{BASE_URL}/v1/models")
        models = models_response.json().get('data', [])
        
        if not models:
            print("⚠️ No models loaded!")
            return False
            
        model_id = models[0]['id']
        
        payload = {
            "model": model_id,
            "prompt": "def hello_world():",
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/v1/completions", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['text']
            print(f"✅ Text completion successful!")
            print(f"📝 Generated: {text}")
            return True
        else:
            print(f"❌ Text completion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 Testing IMPETUS API with Real GGUF Inference")
    print("=" * 50)
    
    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/api/health")
        if health.status_code != 200:
            print("❌ Server not responding on http://localhost:8080")
            print("   Please start the server first: python gerdsen_ai_server/src/production_main.py")
            return
    except:
        print("❌ Cannot connect to server at http://localhost:8080")
        print("   Please start the server first: python gerdsen_ai_server/src/production_main.py")
        return
    
    print("✅ Server is running")
    
    # Run tests
    models_ok = test_models_endpoint()
    chat_ok = test_chat_completion() if models_ok else False
    text_ok = test_text_completion() if models_ok else False
    
    print("\n📊 Test Summary:")
    print(f"   Models endpoint: {'✅' if models_ok else '❌'}")
    print(f"   Chat completion: {'✅' if chat_ok else '❌'}")
    print(f"   Text completion: {'✅' if text_ok else '❌'}")
    
    if models_ok and chat_ok and text_ok:
        print("\n🎉 All tests passed! Real GGUF inference is working!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()