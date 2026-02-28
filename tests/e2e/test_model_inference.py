#!/usr/bin/env python3
"""Model Inference Testing Suite"""

import requests
import time
import json
import asyncio
import aiohttp
from datetime import datetime

class ModelInferenceTester:
    def __init__(self):
        self.base_url = 'http://localhost:8080'
        self.test_models = [
            'mlx-community/Mistral-7B-Instruct-v0.3-4bit',
            'mlx-community/Phi-3-mini-4k-instruct-4bit'
        ]
        self.test_prompts = [
            'Hello! How are you?',
            'Explain quantum computing in one sentence.',
            'Write a haiku about programming.',
            'What is 2+2?',
            'Tell me a joke.'
        ]
    
    def log(self, message):
        print(f'[{datetime.now().strftime("%H:%M:%S")}] {message}')
    
    def test_model_availability(self):
        """Test which models are available"""
        self.log('Testing model availability...')
        try:
            response = requests.get(f'{self.base_url}/v1/models')
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['id'] for model in models_data.get('data', [])]
                self.log(f'Available models: {available_models}')
                return available_models
            else:
                self.log(f'Failed to get models: {response.status_code}')
                return []
        except Exception as e:
            self.log(f'Model availability test failed: {e}')
            return []
    
    def test_inference_quality(self, model_id):
        """Test inference quality with various prompts"""
        self.log(f'Testing inference quality for {model_id}...')
        results = {}
        
        for i, prompt in enumerate(self.test_prompts):
            self.log(f'  Prompt {i+1}: {prompt[:30]}...')
            
            payload = {
                'model': model_id,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 50,
                'temperature': 0.7,
                'stream': False
            }
            
            start_time = time.time()
            try:
                response = requests.post(f'{self.base_url}/v1/chat/completions', 
                                       json=payload, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    tokens_used = response_data.get('usage', {}).get('total_tokens', 0)
                    inference_time = time.time() - start_time
                    
                    results[f'prompt_{i+1}'] = {
                        'prompt': prompt,
                        'response': content[:100] + '...' if len(content) > 100 else content,
                        'tokens': tokens_used,
                        'time_seconds': inference_time,
                        'tokens_per_second': tokens_used / inference_time if inference_time > 0 else 0,
                        'success': True
                    }
                    
                    self.log(f'    Response: {content[:50]}...')
                    self.log(f'    Tokens: {tokens_used}, Time: {inference_time:.2f}s, Speed: {tokens_used/inference_time:.1f} t/s')
                else:
                    results[f'prompt_{i+1}'] = {
                        'prompt': prompt,
                        'error': f'HTTP {response.status_code}',
                        'success': False
                    }
                    self.log(f'    Error: HTTP {response.status_code}')
                    
            except Exception as e:
                results[f'prompt_{i+1}'] = {
                    'prompt': prompt,
                    'error': str(e),
                    'success': False
                }
                self.log(f'    Exception: {e}')
            
            time.sleep(1)  # Brief pause between requests
        
        return results
    
    def test_streaming_performance(self, model_id):
        """Test streaming inference performance"""
        self.log(f'Testing streaming performance for {model_id}...')
        
        payload = {
            'model': model_id,
            'messages': [{'role': 'user', 'content': 'Count from 1 to 10 with explanations'}],
            'max_tokens': 100,
            'temperature': 0.7,
            'stream': True
        }
        
        try:
            start_time = time.time()
            first_token_time = None
            chunk_count = 0
            total_content = ''
            
            response = requests.post(f'{self.base_url}/v1/chat/completions', 
                                   json=payload, stream=True, timeout=30)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line and line.startswith(b'data: '):
                        try:
                            data_str = line.decode('utf-8')[6:]  # Remove 'data: '
                            if data_str.strip() == '[DONE]':
                                break
                                
                            chunk_data = json.loads(data_str)
                            content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            
                            if content and first_token_time is None:
                                first_token_time = time.time() - start_time
                            
                            if content:
                                total_content += content
                                chunk_count += 1
                                
                        except json.JSONDecodeError:
                            continue
                
                total_time = time.time() - start_time
                
                return {
                    'success': True,
                    'total_time': total_time,
                    'first_token_latency': first_token_time,
                    'chunk_count': chunk_count,
                    'content_length': len(total_content),
                    'chunks_per_second': chunk_count / total_time if total_time > 0 else 0,
                    'content_preview': total_content[:100] + '...' if len(total_content) > 100 else total_content
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def test_concurrent_requests(self, model_id, concurrent_count=3):
        """Test concurrent request handling"""
        self.log(f'Testing {concurrent_count} concurrent requests for {model_id}...')
        
        async def single_request(session, request_id):
            payload = {
                'model': model_id,
                'messages': [{'role': 'user', 'content': f'Request {request_id}: What is AI?'}],
                'max_tokens': 30,
                'stream': False
            }
            
            start_time = time.time()
            try:
                async with session.post(f'{self.base_url}/v1/chat/completions', 
                                      json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        return {
                            'request_id': request_id,
                            'success': True,
                            'time': time.time() - start_time,
                            'content_length': len(content)
                        }
                    else:
                        return {
                            'request_id': request_id,
                            'success': False,
                            'error': f'HTTP {response.status}'
                        }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e)
                }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                tasks = [single_request(session, i+1) for i in range(concurrent_count)]
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                
                successful_requests = [r for r in results if r.get('success')]
                
                return {
                    'total_time': total_time,
                    'successful_requests': len(successful_requests),
                    'failed_requests': len(results) - len(successful_requests),
                    'average_response_time': sum(r.get('time', 0) for r in successful_requests) / len(successful_requests) if successful_requests else 0,
                    'requests_per_second': len(successful_requests) / total_time if total_time > 0 else 0,
                    'results': results
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_model_tests(self):
        """Run comprehensive model testing"""
        self.log('🧠 Starting Model Inference Testing Suite')
        self.log('=' * 50)
        
        # Test model availability
        available_models = self.test_model_availability()
        if not available_models:
            self.log('❌ No models available - cannot run inference tests')
            return
        
        test_results = {}
        
        for model_id in available_models:
            if any(test_model in model_id for test_model in self.test_models):
                self.log(f'
🔍 Testing model: {model_id}')
                
                model_results = {}
                
                # Test inference quality
                model_results['inference_quality'] = self.test_inference_quality(model_id)
                
                # Test streaming
                model_results['streaming_performance'] = self.test_streaming_performance(model_id)
                
                # Test concurrent requests
                try:
                    model_results['concurrent_requests'] = asyncio.run(
                        self.test_concurrent_requests(model_id, 3)
                    )
                except Exception as e:
                    model_results['concurrent_requests'] = {'error': str(e)}
                
                test_results[model_id] = model_results
        
        # Generate summary
        self.generate_model_summary(test_results)
        
        return test_results
    
    def generate_model_summary(self, test_results):
        """Generate model testing summary"""
        self.log('
📊 MODEL TESTING SUMMARY')
        self.log('=' * 50)
        
        for model_id, results in test_results.items():
            self.log(f'
Model: {model_id}')
            
            # Inference quality summary
            if 'inference_quality' in results:
                quality_results = results['inference_quality']
                successful_prompts = sum(1 for r in quality_results.values() if r.get('success'))
                total_prompts = len(quality_results)
                avg_speed = sum(r.get('tokens_per_second', 0) for r in quality_results.values() if r.get('success')) / successful_prompts if successful_prompts > 0 else 0
                
                self.log(f'  Inference Quality: {successful_prompts}/{total_prompts} prompts successful')
                self.log(f'  Average Speed: {avg_speed:.1f} tokens/sec')
            
            # Streaming performance
            if 'streaming_performance' in results:
                streaming = results['streaming_performance']
                if streaming.get('success'):
                    self.log(f'  Streaming: ✅ {streaming.get("chunk_count", 0)} chunks, {streaming.get("first_token_latency", 0):.2f}s first token')
                else:
                    self.log(f'  Streaming: ❌ {streaming.get("error", "Unknown error")}')
            
            # Concurrent requests
            if 'concurrent_requests' in results:
                concurrent = results['concurrent_requests']
                if 'successful_requests' in concurrent:
                    self.log(f'  Concurrent: {concurrent["successful_requests"]}/{concurrent["successful_requests"] + concurrent["failed_requests"]} requests successful')
                    self.log(f'  Throughput: {concurrent.get("requests_per_second", 0):.2f} req/sec')

if __name__ == '__main__':
    tester = ModelInferenceTester()
    tester.run_model_tests()

