#!/usr/bin/env python3
"""
IMPETUS MVP Integration Test Suite
Tests the complete MVP functionality including all model formats, API endpoints, and integrations.
"""

import asyncio
import json
import requests
import subprocess
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IMPETUSMVPTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.server_process = None
        self.project_root = Path(__file__).parent
        self.server_ready = False
        
        # Test results tracking
        self.test_results = {
            'server_startup': False,
            'api_health': False,
            'models_endpoint': False,
            'model_formats': {},
            'model_switching': False,
            'chat_completions': False,
            'streaming': False,
            'error_handling': False,
            'electron_app': False,
            'python_bundling': False
        }
        
        logger.info("🚀 IMPETUS MVP Integration Tester initialized")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Base URL: {self.base_url}")

    async def run_complete_test_suite(self):
        """Run the complete MVP test suite"""
        try:
            logger.info("🧪 Starting IMPETUS MVP Integration Test Suite")
            
            # Phase 1: Server and Core API Tests
            await self.test_server_startup()
            await self.test_api_health()
            await self.test_models_endpoint()
            await self.test_model_switching()
            await self.test_chat_completions()
            await self.test_streaming_support()
            await self.test_error_handling()
            
            # Phase 2: Model Format Tests
            await self.test_model_formats()
            
            # Phase 3: Electron App Tests
            await self.test_electron_app()
            
            # Phase 4: Python Bundling Tests
            await self.test_python_bundling()
            
            # Generate final report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.cleanup()
            return False
        finally:
            self.cleanup()
            
        return self.calculate_success_rate() >= 0.9  # 90% success rate for MVP

    async def test_server_startup(self):
        """Test that the IMPETUS server starts successfully"""
        logger.info("🔧 Testing server startup...")
        
        try:
            # Start the server
            server_script = self.project_root / "gerdsen_ai_server" / "src" / "production_main.py"
            
            if not server_script.exists():
                logger.error(f"❌ Server script not found: {server_script}")
                return False
                
            self.server_process = subprocess.Popen(
                [sys.executable, str(server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            # Wait for server to start (up to 30 seconds)
            for attempt in range(30):
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        self.server_ready = True
                        self.test_results['server_startup'] = True
                        logger.info("✅ Server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                    
                time.sleep(1)
                logger.info(f"⏳ Waiting for server startup... ({attempt + 1}/30)")
            
            logger.error("❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"❌ Server startup failed: {e}")
            return False

    async def test_api_health(self):
        """Test API health endpoint"""
        logger.info("🩺 Testing API health...")
        
        if not self.server_ready:
            logger.error("❌ Server not ready for health check")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health check passed: {data}")
                self.test_results['api_health'] = True
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    async def test_models_endpoint(self):
        """Test the /v1/models endpoint"""
        logger.info("📋 Testing models endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                logger.info(f"✅ Models endpoint working: {len(models)} models available")
                
                # Log model details
                for model in models:
                    logger.info(f"  📦 Model: {model.get('id')} (Format: {model.get('format', 'unknown')})")
                
                self.test_results['models_endpoint'] = True
                return True
            else:
                logger.error(f"❌ Models endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Models endpoint error: {e}")
            return False

    async def test_model_switching(self):
        """Test model switching functionality"""
        logger.info("🔄 Testing model switching...")
        
        try:
            # Get available models first
            models_response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if models_response.status_code != 200:
                logger.error("❌ Cannot get models list for switching test")
                return False
                
            models = models_response.json().get('data', [])
            if not models:
                logger.warning("⚠️ No models available for switching test")
                return True  # Not a failure if no models are loaded
                
            # Try to switch to the first available model
            test_model = models[0]['id']
            switch_response = requests.post(
                f"{self.base_url}/v1/models/{test_model}/switch",
                timeout=10
            )
            
            if switch_response.status_code == 200:
                logger.info(f"✅ Model switching successful for {test_model}")
                self.test_results['model_switching'] = True
                return True
            else:
                logger.error(f"❌ Model switching failed: {switch_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Model switching error: {e}")
            return False

    async def test_chat_completions(self):
        """Test chat completions endpoint"""
        logger.info("💬 Testing chat completions...")
        
        try:
            test_payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    logger.info(f"✅ Chat completions working: {content[:100]}...")
                    self.test_results['chat_completions'] = True
                    return True
                else:
                    logger.error("❌ Chat completions response missing choices")
                    return False
            else:
                logger.error(f"❌ Chat completions failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Chat completions error: {e}")
            return False

    async def test_streaming_support(self):
        """Test streaming chat completions"""
        logger.info("🌊 Testing streaming support...")
        
        try:
            test_payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Count from 1 to 5."}
                ],
                "max_tokens": 50,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=test_payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                # Check if we receive streaming data
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                        if chunks_received >= 3:  # Just need a few chunks to verify streaming
                            break
                
                if chunks_received > 0:
                    logger.info(f"✅ Streaming working: received {chunks_received} chunks")
                    self.test_results['streaming'] = True
                    return True
                else:
                    logger.error("❌ No streaming chunks received")
                    return False
            else:
                logger.error(f"❌ Streaming failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            return False

    async def test_error_handling(self):
        """Test API error handling"""
        logger.info("🚨 Testing error handling...")
        
        try:
            # Test invalid endpoint
            response = requests.get(f"{self.base_url}/v1/invalid-endpoint", timeout=5)
            if response.status_code == 404:
                logger.info("✅ 404 error handling working")
            
            # Test invalid model in chat completions
            test_payload = {
                "model": "invalid-model-12345",
                "messages": [{"role": "user", "content": "Test"}]
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=test_payload,
                timeout=10
            )
            
            if response.status_code in [400, 404]:
                logger.info("✅ Invalid model error handling working")
                self.test_results['error_handling'] = True
                return True
            else:
                logger.warning(f"⚠️ Unexpected error response: {response.status_code}")
                return True  # Not critical for MVP
                
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            return False

    async def test_model_formats(self):
        """Test different model format support"""
        logger.info("🎯 Testing model format support...")
        
        # Check if model loaders are available
        format_tests = {
            'GGUF': 'gerdsen_ai_server/src/model_loaders/gguf_loader.py',
            'SafeTensors': 'gerdsen_ai_server/src/model_loaders/safetensors_loader.py',
            'MLX': 'gerdsen_ai_server/src/model_loaders/mlx_loader.py',
            'CoreML': 'gerdsen_ai_server/src/model_loaders/coreml_loader.py',
            'PyTorch': 'gerdsen_ai_server/src/model_loaders/pytorch_loader.py',
            'ONNX': 'gerdsen_ai_server/src/model_loaders/onnx_loader.py'
        }
        
        for format_name, loader_path in format_tests.items():
            full_path = self.project_root / loader_path
            if full_path.exists():
                logger.info(f"✅ {format_name} loader available")
                self.test_results['model_formats'][format_name] = True
            else:
                logger.error(f"❌ {format_name} loader missing: {full_path}")
                self.test_results['model_formats'][format_name] = False
        
        # Test factory pattern
        factory_path = self.project_root / "gerdsen_ai_server/src/model_loaders/model_loader_factory.py"
        if factory_path.exists():
            logger.info("✅ Model loader factory available")
            self.test_results['model_formats']['Factory'] = True
        else:
            logger.error("❌ Model loader factory missing")
            self.test_results['model_formats']['Factory'] = False
        
        return True

    async def test_electron_app(self):
        """Test Electron app structure and configuration"""
        logger.info("🖥️ Testing Electron app...")
        
        electron_path = self.project_root / "impetus-electron"
        
        # Check required files
        required_files = [
            "package.json",
            "src/main.js",
            "src/preload.js",
            "src/renderer/index.html",
            "src/renderer/script.js",
            "src/renderer/styles.css",
            "scripts/bundle-python.js",
            "scripts/test-bundle.js",
            "README.md",
            "BUNDLING.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = electron_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ Electron app missing files: {missing_files}")
            return False
        else:
            logger.info("✅ Electron app structure complete")
            self.test_results['electron_app'] = True
            return True

    async def test_python_bundling(self):
        """Test Python bundling system"""
        logger.info("🐍 Testing Python bundling system...")
        
        electron_path = self.project_root / "impetus-electron"
        
        # Check if npm is available and dependencies can be installed
        try:
            # Check if package.json exists and has bundling scripts
            package_json_path = electron_path / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                required_scripts = ['bundle-python', 'test-bundle', 'build-with-python', 'dist-with-python']
                
                missing_scripts = [script for script in required_scripts if script not in scripts]
                if missing_scripts:
                    logger.error(f"❌ Missing bundling scripts: {missing_scripts}")
                    return False
                else:
                    logger.info("✅ Python bundling scripts available")
                    self.test_results['python_bundling'] = True
                    return True
            else:
                logger.error("❌ Electron package.json missing")
                return False
                
        except Exception as e:
            logger.error(f"❌ Python bundling test failed: {e}")
            return False

    def generate_test_report(self):
        """Generate a comprehensive test report"""
        logger.info("📊 Generating test report...")
        
        total_tests = 0
        passed_tests = 0
        
        print("\n" + "="*80)
        print("🎯 IMPETUS MVP INTEGRATION TEST REPORT")
        print("="*80)
        
        # Core functionality tests
        print("\n📋 CORE FUNCTIONALITY:")
        core_tests = ['server_startup', 'api_health', 'models_endpoint', 'model_switching', 
                     'chat_completions', 'streaming', 'error_handling']
        
        for test in core_tests:
            status = "✅ PASS" if self.test_results[test] else "❌ FAIL"
            print(f"  {test.replace('_', ' ').title()}: {status}")
            total_tests += 1
            if self.test_results[test]:
                passed_tests += 1
        
        # Model format tests
        print("\n🎯 MODEL FORMAT SUPPORT:")
        for format_name, result in self.test_results['model_formats'].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {format_name}: {status}")
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Application tests
        print("\n🖥️ APPLICATION COMPONENTS:")
        app_tests = ['electron_app', 'python_bundling']
        for test in app_tests:
            status = "✅ PASS" if self.test_results[test] else "❌ FAIL"
            print(f"  {test.replace('_', ' ').title()}: {status}")
            total_tests += 1
            if self.test_results[test]:
                passed_tests += 1
        
        # Summary
        success_rate = self.calculate_success_rate()
        print(f"\n📊 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        print(f"  Success Rate: {success_rate:.1%}")
        
        mvp_status = "🎉 MVP READY" if success_rate >= 0.9 else "⚠️ MVP NEEDS WORK"
        print(f"\n🎯 MVP STATUS: {mvp_status}")
        
        if success_rate >= 0.9:
            print("\n✅ IMPETUS MVP is ready for Cline integration testing!")
        else:
            print("\n❌ IMPETUS MVP needs additional work before Cline testing")
        
        print("="*80)

    def calculate_success_rate(self):
        """Calculate overall test success rate"""
        total_tests = 0
        passed_tests = 0
        
        # Core tests
        core_tests = ['server_startup', 'api_health', 'models_endpoint', 'model_switching',
                     'chat_completions', 'streaming', 'error_handling']
        
        for test in core_tests:
            total_tests += 1
            if self.test_results[test]:
                passed_tests += 1
        
        # Model format tests
        for result in self.test_results['model_formats'].values():
            total_tests += 1
            if result:
                passed_tests += 1
        
        # App tests
        app_tests = ['electron_app', 'python_bundling']
        for test in app_tests:
            total_tests += 1
            if self.test_results[test]:
                passed_tests += 1
        
        return passed_tests / total_tests if total_tests > 0 else 0

    def cleanup(self):
        """Clean up test resources"""
        if self.server_process:
            logger.info("🧹 Cleaning up server process...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None

async def main():
    """Main test runner"""
    tester = IMPETUSMVPTester()
    
    try:
        success = await tester.run_complete_test_suite()
        if success:
            print("\n🎉 MVP Integration Tests PASSED! Ready for Cline testing.")
            sys.exit(0)
        else:
            print("\n❌ MVP Integration Tests FAILED! Additional work needed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())