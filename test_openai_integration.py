"""
Test OpenAI API Integration with GGUF Models
"""

import requests
import json
import sys


def test_models_endpoint(base_url):
    """Test the /v1/models endpoint"""
    print("Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{base_url}/v1/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Models endpoint working")
            print(f"  Found {len(data.get('data', []))} models")
            for model in data.get('data', []):
                print(f"    - {model['id']}: {model['name']}")
            return True
        else:
            print(f"✗ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing models endpoint: {e}")
        return False


def test_chat_completion(base_url, model_id="test-model"):
    """Test the /v1/chat/completions endpoint"""
    print(f"\nTesting /v1/chat/completions with model {model_id}...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Can you tell me about GGUF models?"}
    ]
    
    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Chat completion working")
            print(f"  Response: {data['choices'][0]['message']['content'][:100]}...")
            print(f"  Tokens used: {data['usage']['total_tokens']}")
            return True
        else:
            print(f"✗ Chat completion failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error with chat completion: {e}")
        return False


def test_text_completion(base_url, model_id="test-model"):
    """Test the /v1/completions endpoint"""
    print(f"\nTesting /v1/completions with model {model_id}...")
    
    payload = {
        "model": model_id,
        "prompt": "The purpose of GGUF models is",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Text completion working")
            print(f"  Response: {data['choices'][0]['text'][:100]}...")
            print(f"  Tokens used: {data['usage']['total_tokens']}")
            return True
        else:
            print(f"✗ Text completion failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error with text completion: {e}")
        return False


def test_streaming(base_url, model_id="test-model"):
    """Test streaming chat completion"""
    print(f"\nTesting streaming with model {model_id}...")
    
    messages = [
        {"role": "user", "content": "Count from 1 to 5 slowly"}
    ]
    
    payload = {
        "model": model_id,
        "messages": messages,
        "stream": True,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if response.status_code == 200:
            print("✓ Streaming working")
            print("  Chunks received: ", end="", flush=True)
            
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    print(".", end="", flush=True)
            
            print(f"\n  Total chunks: {chunk_count}")
            return True
        else:
            print(f"✗ Streaming failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error with streaming: {e}")
        return False


def main():
    """Run all tests"""
    base_url = "http://localhost:8080"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing OpenAI API endpoints at {base_url}")
    print("=" * 50)
    
    # Run tests
    models_ok = test_models_endpoint(base_url)
    
    if models_ok:
        # Try to use a real model if available
        response = requests.get(f"{base_url}/v1/models")
        models = response.json().get('data', [])
        model_id = models[0]['id'] if models else 'test-model'
        
        chat_ok = test_chat_completion(base_url, model_id)
        text_ok = test_text_completion(base_url, model_id)
        stream_ok = test_streaming(base_url, model_id)
        
        print("\n" + "=" * 50)
        print("Summary:")
        print(f"  Models endpoint: {'✓' if models_ok else '✗'}")
        print(f"  Chat completion: {'✓' if chat_ok else '✗'}")
        print(f"  Text completion: {'✓' if text_ok else '✗'}")
        print(f"  Streaming: {'✓' if stream_ok else '✗'}")
        
        all_ok = models_ok and chat_ok and text_ok
        print(f"\nOverall: {'✓ All tests passed!' if all_ok else '✗ Some tests failed'}")
        
        if all_ok:
            print("\n🎉 The server is ready for VS Code/Cline integration!")
            print(f"   Set your VS Code API base URL to: {base_url}")
    else:
        print("\n✗ Cannot proceed without working models endpoint")


if __name__ == "__main__":
    main()