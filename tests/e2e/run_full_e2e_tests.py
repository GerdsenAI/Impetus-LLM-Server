#!/usr/bin/env python3
"""Comprehensive End-to-End Testing Suite for Impetus LLM Server"""

import asyncio
import json
import os
import subprocess
import time
import requests
import psutil
from datetime import datetime
from pathlib import Path

class ImpetusE2ETester:
    def __init__(self):
        self.repo_path = Path('/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server')
        self.test_results = {}
        self.server_process = None
        self.menubar_process = None
        self.base_url = 'http://localhost:8080'
        self.dashboard_url = 'http://localhost:5173'
        
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f'[{timestamp}] {level}: {message}')
        
    def take_screenshot(self, name):
        """Take screenshot using macOS screencapture"""
        screenshot_path = self.repo_path / 'tests' / 'screenshots' / f'{name}.png'
        try:
            subprocess.run(['screencapture', '-x', str(screenshot_path)], check=True)
            self.log(f'Screenshot saved: {screenshot_path}')
            return True
        except Exception as e:
            self.log(f'Screenshot failed: {e}', 'ERROR')
            return False
    
    def start_server(self):
        """Start the Impetus server"""
        self.log('Starting Impetus server...')
        try:
            os.chdir(self.repo_path)
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.repo_path)
            
            self.server_process = subprocess.Popen([
                str(self.repo_path / '.venv' / 'bin' / 'python'),
                'gerdsen_ai_server/src/main.py'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):
                try:
                    response = requests.get(f'{self.base_url}/api/health', timeout=2)
                    if response.status_code == 200:
                        self.log('Server started successfully')
                        return True
                except:
                    time.sleep(1)
            
            self.log('Server failed to start within 30 seconds', 'ERROR')
            return False
        except Exception as e:
            self.log(f'Failed to start server: {e}', 'ERROR')
            return False
    
    def start_menubar(self):
        """Start the menu bar application"""
        self.log('Starting menu bar application...')
        try:
            os.chdir(self.repo_path)
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.repo_path)
            env['IMPETUS_TEST_MODE'] = '1'  # Disable interactive prompts
            
            self.menubar_process = subprocess.Popen([
                str(self.repo_path / '.venv' / 'bin' / 'python'),
                'run_menubar.py'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(5)  # Give menu bar time to initialize
            self.log('Menu bar application started')
            return True
        except Exception as e:
            self.log(f'Failed to start menu bar: {e}', 'ERROR')
            return False
    
    def test_phase_1_server_core(self):
        """Phase 1: Server Core Testing"""
        self.log('=== PHASE 1: Server Core Testing ===')
        results = {}
        
        # Test 1: Server startup
        self.log('Test 1.1: Server startup')
        results['server_startup'] = self.start_server()
        
        if not results['server_startup']:
            return results
            
        # Test 2: Health endpoint
        self.log('Test 1.2: Health endpoint')
        try:
            response = requests.get(f'{self.base_url}/api/health')
            results['health_endpoint'] = response.status_code == 200
            if results['health_endpoint']:
                health_data = response.json()
                self.log(f'Health status: {health_data.get("status")}')
        except Exception as e:
            self.log(f'Health endpoint failed: {e}', 'ERROR')
            results['health_endpoint'] = False
            
        # Test 3: Authentication (should work without API key by default)
        self.log('Test 1.3: Authentication')
        try:
            response = requests.get(f'{self.base_url}/v1/models')
            results['auth_working'] = response.status_code == 200
        except Exception as e:
            self.log(f'Authentication test failed: {e}', 'ERROR')
            results['auth_working'] = False
        
        return results
    
    def test_phase_2_model_testing(self):
        """Phase 2: Model Testing"""
        self.log('=== PHASE 2: Model Testing ===')
        results = {}
        
        # Test model endpoint
        self.log('Test 2.1: Models endpoint')
        try:
            response = requests.get(f'{self.base_url}/v1/models')
            if response.status_code == 200:
                models_data = response.json()
                results['models_endpoint'] = True
                results['available_models'] = len(models_data.get('data', []))
                self.log(f'Available models: {results["available_models"]}')
            else:
                results['models_endpoint'] = False
        except Exception as e:
            self.log(f'Models endpoint failed: {e}', 'ERROR')
            results['models_endpoint'] = False
        
        # Test chat completion
        self.log('Test 2.2: Chat completion')
        try:
            payload = {
                'model': 'mlx-community/Mistral-7B-Instruct-v0.3-4bit',
                'messages': [{'role': 'user', 'content': 'Say hello in exactly 5 words'}],
                'max_tokens': 20,
                'stream': False
            }
            response = requests.post(f'{self.base_url}/v1/chat/completions', json=payload, timeout=30)
            if response.status_code == 200:
                chat_data = response.json()
                results['chat_completion'] = True
                results['response_content'] = chat_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                self.log(f'Chat response: {results["response_content"][:50]}...')
            else:
                results['chat_completion'] = False
        except Exception as e:
            self.log(f'Chat completion failed: {e}', 'ERROR')
            results['chat_completion'] = False
        
        # Test streaming
        self.log('Test 2.3: Streaming completion')
        try:
            payload = {
                'model': 'mlx-community/Mistral-7B-Instruct-v0.3-4bit',
                'messages': [{'role': 'user', 'content': 'Count: 1, 2, 3'}],
                'max_tokens': 15,
                'stream': True
            }
            response = requests.post(f'{self.base_url}/v1/chat/completions', 
                                   json=payload, stream=True, timeout=30)
            
            if response.status_code == 200:
                stream_chunks = 0
                for line in response.iter_lines():
                    if line and line.startswith(b'data: '):
                        stream_chunks += 1
                        if stream_chunks >= 3:  # Got some chunks
                            break
                results['streaming_completion'] = stream_chunks >= 3
                self.log(f'Received {stream_chunks} stream chunks')
            else:
                results['streaming_completion'] = False
        except Exception as e:
            self.log(f'Streaming test failed: {e}', 'ERROR')
            results['streaming_completion'] = False
        
        return results
    
    def test_phase_3_visual_gui(self):
        """Phase 3: Visual & GUI Testing"""
        self.log('=== PHASE 3: Visual & GUI Testing ===')
        results = {}
        
        # Start menu bar app
        self.log('Test 3.1: Menu bar application')
        results['menubar_startup'] = self.start_menubar()
        
        if results['menubar_startup']:
            time.sleep(3)
            results['menubar_screenshot'] = self.take_screenshot('menubar_running')
        
        # Test dashboard (if available)
        self.log('Test 3.2: Dashboard availability')
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            results['dashboard_available'] = response.status_code == 200
            if results['dashboard_available']:
                self.log('Dashboard is running')
                results['dashboard_screenshot'] = self.take_screenshot('dashboard_main')
        except Exception as e:
            self.log(f'Dashboard not available: {e}')
            results['dashboard_available'] = False
        
        return results
    
    def test_phase_4_api_endpoints(self):
        """Phase 4: API Endpoint Testing"""
        self.log('=== PHASE 4: API Endpoint Testing ===')
        results = {}
        
        endpoints_to_test = [
            ('/api/health', 'health'),
            ('/api/status', 'status'),
            ('/api/metrics', 'metrics'),
            ('/v1/models', 'v1_models')
        ]
        
        for endpoint, name in endpoints_to_test:
            self.log(f'Test 4.{len(results)+1}: {endpoint}')
            try:
                response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
                results[name] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_size': len(response.content)
                }
                self.log(f'{endpoint}: {response.status_code} ({len(response.content)} bytes)')
            except Exception as e:
                self.log(f'{endpoint} failed: {e}', 'ERROR')
                results[name] = {'success': False, 'error': str(e)}
        
        return results
    
    def test_phase_5_performance(self):
        """Phase 5: Performance Testing"""
        self.log('=== PHASE 5: Performance Testing ===')
        results = {}
        
        # Memory usage
        self.log('Test 5.1: Memory usage')
        if self.server_process:
            try:
                process = psutil.Process(self.server_process.pid)
                memory_info = process.memory_info()
                results['memory_usage_mb'] = memory_info.rss / 1024 / 1024
                results['cpu_percent'] = process.cpu_percent()
                self.log(f'Memory: {results["memory_usage_mb"]:.1f}MB, CPU: {results["cpu_percent"]:.1f}%')
            except Exception as e:
                self.log(f'Performance monitoring failed: {e}', 'ERROR')
                results['performance_monitoring'] = False
        
        # Simple latency test
        self.log('Test 5.2: Response latency')
        latencies = []
        for i in range(3):
            start_time = time.time()
            try:
                response = requests.get(f'{self.base_url}/api/health', timeout=5)
                if response.status_code == 200:
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
            except:
                pass
        
        if latencies:
            results['avg_latency_ms'] = sum(latencies) / len(latencies)
            results['max_latency_ms'] = max(latencies)
            self.log(f'Avg latency: {results["avg_latency_ms"]:.1f}ms')
        
        return results
    
    def cleanup(self):
        """Clean up test processes"""
        self.log('Cleaning up test processes...')
        
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
        
        if self.menubar_process:
            self.menubar_process.terminate()
            try:
                self.menubar_process.wait(timeout=5)
            except:
                self.menubar_process.kill()
    
    def run_all_tests(self):
        """Run the complete test suite"""
        self.log('🚀 Starting Comprehensive E2E Testing Suite')
        self.log('=' * 60)
        
        start_time = time.time()
        
        try:
            # Run all test phases
            self.test_results['phase_1'] = self.test_phase_1_server_core()
            
            if self.test_results['phase_1'].get('server_startup'):
                self.test_results['phase_2'] = self.test_phase_2_model_testing()
                self.test_results['phase_3'] = self.test_phase_3_visual_gui()
                self.test_results['phase_4'] = self.test_phase_4_api_endpoints()
                self.test_results['phase_5'] = self.test_phase_5_performance()
            else:
                self.log('Server failed to start - skipping remaining tests', 'ERROR')
        
        finally:
            self.cleanup()
        
        # Generate test report
        total_time = time.time() - start_time
        self.generate_report(total_time)
    
    def generate_report(self, total_time):
        """Generate comprehensive test report"""
        self.log('=' * 60)
        self.log('📊 TEST RESULTS SUMMARY')
        self.log('=' * 60)
        
        # Count passed/failed tests
        total_tests = 0
        passed_tests = 0
        
        for phase_name, phase_results in self.test_results.items():
            self.log(f'
{phase_name.upper().replace("_", " ")}:')
            for test_name, result in phase_results.items():
                total_tests += 1
                if isinstance(result, bool):
                    status = '✅ PASS' if result else '❌ FAIL'
                    if result:
                        passed_tests += 1
                elif isinstance(result, dict) and 'success' in result:
                    status = '✅ PASS' if result['success'] else '❌ FAIL'
                    if result['success']:
                        passed_tests += 1
                else:
                    status = '📊 INFO'
                
                self.log(f'  {test_name}: {status}')
                if isinstance(result, dict) and not isinstance(result, bool):
                    for key, value in result.items():
                        if key != 'success':
                            self.log(f'    {key}: {value}')
        
        # Overall summary
        self.log(f'
📈 OVERALL RESULTS:')
        self.log(f'  Total Tests: {total_tests}')
        self.log(f'  Passed: {passed_tests}')
        self.log(f'  Failed: {total_tests - passed_tests}')
        self.log(f'  Success Rate: {(passed_tests/total_tests*100):.1f}%')
        self.log(f'  Total Time: {total_time:.1f}s')
        
        # Save results to file
        results_file = self.repo_path / 'tests' / 'logs' / f'e2e_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_time': total_time,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': passed_tests/total_tests*100,
                'results': self.test_results
            }, f, indent=2)
        
        self.log(f'
📁 Results saved to: {results_file}')
        
        if passed_tests == total_tests:
            self.log('
🎉 ALL TESTS PASSED! Server is fully functional.')
        elif passed_tests / total_tests >= 0.8:
            self.log('
⚠️  Most tests passed. Minor issues detected.')
        else:
            self.log('
🚨 Multiple test failures. Server needs attention.')

if __name__ == '__main__':
    tester = ImpetusE2ETester()
    tester.run_all_tests()

