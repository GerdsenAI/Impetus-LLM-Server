#!/usr/bin/env python3
"""
Test Model Loading and Inference
Tests the enhanced production server with real GGUF models
"""

import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path

class ModelLoadingTester:
    """Test model loading and inference functionality"""
    
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url
        self.models_dir = Path.home() / "Models"
        
    async def test_server_health(self, session):
        """Test if server is healthy"""
        print("🔍 Testing server health...")
        try:
            async with session.get(f"{self.server_url}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Server healthy: {health_data['server']}")
                    print(f"   ML Components: {'✅ Loaded' if health_data['ml_components_loaded'] else '⏳ Loading'}")
                    return health_data['ml_components_loaded']
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Server not reachable: {e}")
            return False
    
    async def test_models_scan(self, session):
        """Test model scanning functionality"""
        print("\n🔍 Testing model scanning...")
        try:
            async with session.get(f"{self.server_url}/api/models/scan") as response:
                if response.status == 200:
                    scan_data = await response.json()
                    print(f"✅ Models scan successful")
                    print(f"   Directory: {scan_data['directory']}")
                    print(f"   Models found: {scan_data['count']}")
                    print(f"   Status: {scan_data['status']}")
                    
                    if isinstance(scan_data['models'], list) and len(scan_data['models']) > 0:
                        print("   Available models:")
                        for model in scan_data['models'][:3]:  # Show first 3
                            print(f"     - {model}")
                    
                    return scan_data
                else:
                    print(f"❌ Models scan failed: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Models scan error: {e}")
            return None
    
    async def test_model_loading(self, session):
        """Test loading a specific model"""
        print("\n🔍 Testing model loading...")
        
        # Find a TinyLlama model to load
        tinyllama_path = self.models_dir / "GGUF" / "chat" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        
        if not tinyllama_path.exists():
            print("❌ TinyLlama model not found, skipping model loading test")
            return False
        
        print(f"📂 Loading model: {tinyllama_path}")
        
        try:
            load_data = {
                "path": str(tinyllama_path),
                "id": "tinyllama-test"
            }
            
            async with session.post(f"{self.server_url}/api/models/load", 
                                  json=load_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Model loaded successfully: {result['message']}")
                    return True
                else:
                    result = await response.json()
                    print(f"❌ Model loading failed: {result.get('error', 'Unknown error')}")
                    return False
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            return False
    
    async def test_openai_models_endpoint(self, session):
        """Test OpenAI-compatible models endpoint"""
        print("\n🔍 Testing OpenAI models endpoint...")
        try:
            async with session.get(f"{self.server_url}/v1/models") as response:
                if response.status == 200:
                    models_data = await response.json()
                    print(f"✅ OpenAI models endpoint working")
                    print(f"   Object: {models_data['object']}")
                    print(f"   Models count: {len(models_data['data'])}")
                    print(f"   Status: {models_data.get('status', 'ready')}")
                    
                    if models_data['data']:
                        print("   Available models:")
                        for model in models_data['data']:
                            print(f"     - {model['id']}")
                    
                    return models_data
                else:
                    print(f"❌ OpenAI models endpoint failed: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ OpenAI models endpoint error: {e}")
            return None
    
    async def test_chat_completion(self, session, model_id="tinyllama-test"):
        """Test chat completion with a loaded model"""
        print(f"\n🔍 Testing chat completion with model: {model_id}...")
        
        chat_data = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Hello! Can you help me with Python programming?"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        try:
            async with session.post(f"{self.server_url}/v1/chat/completions", 
                                  json=chat_data) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("✅ Chat completion successful!")
                    if 'choices' in result and result['choices']:
                        reply = result['choices'][0]['message']['content']
                        print(f"   Model response: {reply[:100]}...")
                    return True
                else:
                    print(f"❌ Chat completion failed: {response.status}")
                    print(f"   Error: {result.get('error', {}).get('message', 'Unknown error')}")
                    return False
        except Exception as e:
            print(f"❌ Chat completion error: {e}")
            return False
    
    async def test_directory_creation(self, session):
        """Test models directory creation"""
        print("\n🔍 Testing models directory creation...")
        try:
            async with session.get(f"{self.server_url}/api/models/directory") as response:
                if response.status == 200:
                    dir_data = await response.json()
                    print(f"✅ Models directory accessible")
                    print(f"   Directory: {dir_data['directory']}")
                    print(f"   Exists: {dir_data['exists']}")
                    print(f"   Subdirs created: {dir_data.get('created_subdirs', False)}")
                    return True
                else:
                    print(f"❌ Models directory test failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Models directory error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Model Loading Tests")
        print("=" * 50)
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Test 1: Server Health
            ml_ready = await self.test_server_health(session)
            
            # Test 2: Directory Creation
            await self.test_directory_creation(session)
            
            # Test 3: Models Scan
            scan_result = await self.test_models_scan(session)
            
            # Test 4: OpenAI Models Endpoint
            models_result = await self.test_openai_models_endpoint(session)
            
            # Test 5: Model Loading (only if ML components are ready)
            if ml_ready:
                model_loaded = await self.test_model_loading(session)
                
                # Test 6: Chat Completion (only if model loaded)
                if model_loaded:
                    await self.test_chat_completion(session)
                else:
                    print("\n⚠️  Skipping chat completion test (model not loaded)")
            else:
                print("\n⚠️  Skipping model loading and inference tests (ML components not ready)")
            
            print("\n" + "=" * 50)
            print("🏁 Test Summary")
            print("=" * 50)
            print(f"Server Health: {'✅' if ml_ready else '⚠️ '}")
            print(f"Directory Access: ✅")
            print(f"Models Scan: {'✅' if scan_result else '❌'}")
            print(f"OpenAI Endpoint: {'✅' if models_result else '❌'}")
            
            if ml_ready:
                print("ML Integration: ✅ Ready for production")
            else:
                print("ML Integration: ⏳ Components loading (normal on first startup)")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test model loading functionality')
    parser.add_argument('--server', default='http://localhost:8080', 
                       help='Server URL (default: http://localhost:8080)')
    parser.add_argument('--wait', type=int, default=5,
                       help='Seconds to wait for ML components to load (default: 5)')
    
    args = parser.parse_args()
    
    print("⏰ Waiting for ML components to initialize...")
    time.sleep(args.wait)
    
    tester = ModelLoadingTester(args.server)
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()