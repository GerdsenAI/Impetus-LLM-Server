#!/usr/bin/env python3
"""
Test script for enhanced OpenAI API endpoints with model switching
IMPETUS (Intelligent Model Platform Enabling Taskbar Unified Server)
"""

import requests
import json
import time


def test_openai_api_endpoints():
    """Test the enhanced OpenAI API endpoints"""
    
    base_url = "http://localhost:8080"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-dummy-api-key-for-development"
    }
    
    print("🚀 Testing IMPETUS Enhanced OpenAI API Endpoints")
    print("=" * 60)
    
    # Test 1: List models
    print("\n📋 Test 1: List Models (/v1/models)")
    try:
        response = requests.get(f"{base_url}/v1/models", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('data', []))} models")
            print(f"Supported formats: {data.get('supported_formats', [])}")
            print(f"Format statistics: {data.get('format_statistics', {})}")
            
            # Store first model for testing
            models = data.get('data', [])
            if models:
                test_model = models[0]['id']
                print(f"📌 Will use model '{test_model}' for testing")
                return test_model
            else:
                print("❌ No models available for testing")
                return None
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on localhost:8080?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_chat_completions(model_id):
    """Test chat completions endpoint"""
    
    base_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n💬 Test 2: Chat Completions (/v1/chat/completions)")
    
    # Test data
    chat_data = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What is IMPETUS?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{base_url}/v1/chat/completions", 
                               headers=headers, 
                               json=chat_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received from {data.get('model')} ({data.get('model_format')})")
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"💬 Response: {content[:200]}...")
            print(f"📊 Tokens: {data.get('usage', {})}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_text_completions(model_id):
    """Test text completions endpoint"""
    
    base_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n📝 Test 3: Text Completions (/v1/completions)")
    
    # Test data
    completion_data = {
        "model": model_id,
        "prompt": "IMPETUS is an intelligent platform that",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{base_url}/v1/completions", 
                               headers=headers, 
                               json=completion_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received from {data.get('model')} ({data.get('model_format')})")
            text = data.get('choices', [{}])[0].get('text', '')
            print(f"📝 Completion: {completion_data['prompt']}{text}")
            print(f"📊 Tokens: {data.get('usage', {})}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_model_switching(model_id):
    """Test model switching endpoint"""
    
    base_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n🔄 Test 4: Model Switching (/v1/models/{model_id}/switch)")
    
    try:
        response = requests.post(f"{base_url}/v1/models/{model_id}/switch", 
                               headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully switched to {data.get('model')}")
            print(f"Format: {data.get('format')}")
            print(f"Capabilities: {data.get('capabilities', [])}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_model_info(model_id):
    """Test model info endpoint"""
    
    base_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n📊 Test 5: Model Info (/v1/models/{model_id}/info)")
    
    try:
        response = requests.get(f"{base_url}/v1/models/{model_id}/info", 
                              headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model info retrieved")
            print(f"ID: {data.get('id')}")
            print(f"Format: {data.get('format')}")
            print(f"Capabilities: {data.get('capabilities', [])}")
            print(f"Loaded in engine: {data.get('loaded_in_engine')}")
            print(f"Inference engine: {data.get('inference_engine')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_nonexistent_model():
    """Test error handling with nonexistent model"""
    
    base_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n❌ Test 6: Error Handling (nonexistent model)")
    
    chat_data = {
        "model": "nonexistent-model",
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(f"{base_url}/v1/chat/completions", 
                               headers=headers, 
                               json=chat_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            print(f"✅ Proper error handling: {data.get('error', {}).get('message', '')}")
        else:
            print(f"⚠️ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests"""
    
    # Test 1: List models and get a test model
    test_model = test_openai_api_endpoints()
    
    if test_model:
        # Test 2-5: Test with the available model
        test_chat_completions(test_model)
        test_text_completions(test_model)
        test_model_switching(test_model)
        test_model_info(test_model)
        
    # Test 6: Error handling
    test_nonexistent_model()
    
    print("\n🎉 OpenAI API endpoint testing completed!")
    print("\nTo manually test with curl:")
    print("curl -X GET http://localhost:8080/v1/models")
    print('curl -X POST http://localhost:8080/v1/chat/completions \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"model":"test-gguf","messages":[{"role":"user","content":"Hello"}]}\'')


if __name__ == "__main__":
    main()