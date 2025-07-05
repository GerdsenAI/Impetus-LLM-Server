#!/usr/bin/env python3
"""
VS Code/Cline Integration Test
Tests OpenAI-compatible API endpoints that VS Code extensions expect
"""

import requests
import json
import time
import sys
from pathlib import Path

class VSCodeIntegrationTester:
    """Test VS Code AI extension compatibility"""
    
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url
        self.api_key = "sk-dev-gerdsen-ai-local-development-key"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    def test_server_health(self):
        """Test if server is running and healthy"""
        print("🔍 Testing server health...")
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Server healthy: {health_data['server']}")
                print(f"   ML Status: {'Ready' if health_data['ml_components_loaded'] else 'Loading'}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Server not reachable: {e}")
            return False
    
    def test_models_endpoint(self):
        """Test /v1/models endpoint (required by Cline)"""
        print("\n🔍 Testing /v1/models endpoint...")
        try:
            response = requests.get(
                f"{self.server_url}/v1/models",
                headers=self.headers,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Models endpoint working")
                print(f"   Object: {data.get('object', 'unknown')}")
                print(f"   Models: {len(data.get('data', []))}")
                
                if data.get('data'):
                    print("   Available models:")
                    for model in data['data'][:3]:  # Show first 3
                        print(f"     - {model.get('id', 'unknown')}")
                
                return data
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
            return None
    
    def test_chat_completions(self):
        """Test /v1/chat/completions endpoint (main Cline endpoint)"""
        print("\n🔍 Testing /v1/chat/completions endpoint...")
        
        # Test data that Cline typically sends
        test_data = {
            "model": "gpt-4",  # Cline often defaults to this
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful coding assistant."
                },
                {
                    "role": "user", 
                    "content": "Write a simple Python function that adds two numbers."
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                headers=self.headers,
                json=test_data,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Chat completions working")
                
                # Check response structure
                if 'choices' in data and data['choices']:
                    choice = data['choices'][0]
                    if 'message' in choice:
                        content = choice['message'].get('content', '')
                        print(f"   Response length: {len(content)} chars")
                        print(f"   Preview: {content[:100]}...")
                        
                        # Check if it looks like a reasonable response
                        if 'def' in content.lower() or 'function' in content.lower():
                            print("✅ Response appears to contain code")
                        else:
                            print("⚠️  Response doesn't appear to contain code")
                    else:
                        print("⚠️  Response missing message content")
                else:
                    print("⚠️  Response missing choices")
                
                return True
                
            elif response.status_code == 503:
                data = response.json()
                print("⏳ Chat completions not ready (ML components loading)")
                print(f"   Message: {data.get('error', {}).get('message', 'Unknown')}")
                return False
                
            else:
                print(f"❌ Chat completions failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Chat completions error: {e}")
            return False
    
    def test_streaming_chat(self):
        """Test streaming chat completions (used by Cline for real-time responses)"""
        print("\n🔍 Testing streaming chat completions...")
        
        test_data = {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5"}
            ],
            "max_tokens": 50,
            "temperature": 0.7,
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                headers=self.headers,
                json=test_data,
                timeout=30,
                stream=True
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Streaming initiated")
                
                # Try to read first few chunks
                chunk_count = 0
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            chunk_count += 1
                            if chunk_count <= 3:  # Show first 3 chunks
                                print(f"   Chunk {chunk_count}: {decoded_line[:50]}...")
                            if chunk_count >= 5:  # Stop after 5 chunks
                                break
                
                if chunk_count > 0:
                    print(f"✅ Streaming working ({chunk_count} chunks received)")
                    return True
                else:
                    print("⚠️  No streaming chunks received")
                    return False
                    
            elif response.status_code == 501:
                print("⚠️  Streaming not implemented yet")
                return False
                
            else:
                print(f"❌ Streaming failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            return False
    
    def test_completions_endpoint(self):
        """Test /v1/completions endpoint (legacy but still used)"""
        print("\n🔍 Testing /v1/completions endpoint...")
        
        test_data = {
            "model": "gpt-4",
            "prompt": "def add_numbers(a, b):",
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/completions",
                headers=self.headers,
                json=test_data,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Completions endpoint working")
                
                if 'choices' in data and data['choices']:
                    text = data['choices'][0].get('text', '')
                    print(f"   Completion: {text[:50]}...")
                    return True
                else:
                    print("⚠️  Response missing choices")
                    return False
                    
            else:
                print(f"❌ Completions failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Completions error: {e}")
            return False
    
    def test_cline_specific_requests(self):
        """Test requests that Cline specifically makes"""
        print("\n🔍 Testing Cline-specific scenarios...")
        
        # Test 1: Code explanation request
        print("   Testing code explanation...")
        explanation_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Claude, a helpful AI assistant created by Anthropic."
                },
                {
                    "role": "user",
                    "content": "Explain this Python code:\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                headers=self.headers,
                json=explanation_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("   ✅ Code explanation request successful")
            else:
                print(f"   ❌ Code explanation failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Code explanation error: {e}")
        
        # Test 2: File modification request (common Cline use case)
        print("   Testing file modification request...")
        modification_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "I need to add error handling to this function. Please modify it:\n\ndef divide(a, b):\n    return a / b"
                }
            ],
            "max_tokens": 150,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                headers=self.headers,
                json=modification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("   ✅ File modification request successful")
            else:
                print(f"   ❌ File modification failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ File modification error: {e}")
    
    def generate_cline_config(self):
        """Generate Cline configuration for user"""
        print("\n📋 Generating Cline Configuration...")
        
        config = {
            "cline.apiProvider": "openai",
            "cline.openaiApiKey": self.api_key,
            "cline.openaiBaseUrl": self.server_url,
            "cline.openaiModel": "gpt-4"
        }
        
        print("✅ Add this to your VS Code settings.json:")
        print(json.dumps(config, indent=2))
        
        print("\nOr in VS Code settings UI:")
        print(f"   - API Provider: OpenAI")
        print(f"   - API Key: {self.api_key}")
        print(f"   - Base URL: {self.server_url}")
        print(f"   - Model: gpt-4")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 VS Code/Cline Integration Tests")
        print("=" * 50)
        
        results = {}
        
        # Test 1: Server Health
        results['health'] = self.test_server_health()
        
        # Test 2: Models Endpoint
        results['models'] = self.test_models_endpoint() is not None
        
        # Test 3: Chat Completions
        results['chat'] = self.test_chat_completions()
        
        # Test 4: Streaming (optional)
        results['streaming'] = self.test_streaming_chat()
        
        # Test 5: Text Completions
        results['completions'] = self.test_completions_endpoint()
        
        # Test 6: Cline-specific scenarios
        self.test_cline_specific_requests()
        
        # Generate config
        self.generate_cline_config()
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Test Summary")
        print("=" * 50)
        
        for test, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {test.title()}: {'PASS' if passed else 'FAIL'}")
        
        passed_count = sum(results.values())
        total_count = len(results)
        
        print(f"\nOverall: {passed_count}/{total_count} tests passed")
        
        if results['health'] and results['models'] and results['chat']:
            print("\n🎉 READY FOR CLINE INTEGRATION!")
            print("   Core functionality working - you can use Cline with this server")
        elif results['health'] and results['models']:
            print("\n⏳ PARTIALLY READY")
            print("   Server is healthy but ML components may still be loading")
        else:
            print("\n❌ NOT READY")
            print("   Server issues detected - check server logs")
        
        return results

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test VS Code/Cline integration')
    parser.add_argument('--server', default='http://localhost:8080', 
                       help='Server URL (default: http://localhost:8080)')
    parser.add_argument('--wait', type=int, default=0,
                       help='Seconds to wait before testing (default: 0)')
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏰ Waiting {args.wait} seconds for server to initialize...")
        time.sleep(args.wait)
    
    tester = VSCodeIntegrationTester(args.server)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['health'] and results['models']:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()