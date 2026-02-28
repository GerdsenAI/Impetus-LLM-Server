#!/usr/bin/env python3
"""Test Results Summary Generator"""

import json
import os
from datetime import datetime
from pathlib import Path

class TestSummaryGenerator:
    def __init__(self):
        self.repo_path = Path('/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server')
        self.tests_dir = self.repo_path / 'tests'
        
    def collect_test_results(self):
        """Collect all test results from various test runs"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'manual_verification': self.run_manual_verification(),
            'test_files': self.collect_test_files(),
            'performance_metrics': self.collect_performance_data()
        }
        
        # Look for automated test results
        logs_dir = self.tests_dir / 'logs'
        if logs_dir.exists():
            for json_file in logs_dir.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        test_data = json.load(f)
                        results[f'automated_test_{json_file.stem}'] = test_data
                except Exception as e:
                    print(f'Could not load {json_file}: {e}')
        
        return results
    
    def run_manual_verification(self):
        """Run quick manual verification"""
        import requests
        import subprocess
        
        verification = {}
        
        # Server health check
        try:
            response = requests.get('http://localhost:8080/api/health', timeout=5)
            verification['server_health'] = {
                'status': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            verification['server_health'] = {'status': False, 'error': str(e)}
        
        # Models endpoint
        try:
            response = requests.get('http://localhost:8080/v1/models', timeout=5)
            verification['models_endpoint'] = {
                'status': response.status_code == 200,
                'model_count': len(response.json().get('data', [])) if response.status_code == 200 else 0
            }
        except Exception as e:
            verification['models_endpoint'] = {'status': False, 'error': str(e)}
        
        # Process check
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('
') 
                              if 'python' in line.lower() and ('main.py' in line or 'menubar' in line)]
            verification['running_processes'] = {
                'count': len(python_processes),
                'processes': python_processes
            }
        except Exception as e:
            verification['running_processes'] = {'error': str(e)}
        
        return verification
    
    def collect_test_files(self):
        """Collect information about generated test files"""
        files_info = {
            'screenshots': [],
            'logs': [],
            'other': []
        }
        
        # Screenshots
        screenshots_dir = self.tests_dir / 'screenshots'
        if screenshots_dir.exists():
            for screenshot in screenshots_dir.glob('*.png'):
                files_info['screenshots'].append({
                    'name': screenshot.name,
                    'size': screenshot.stat().st_size,
                    'created': datetime.fromtimestamp(screenshot.stat().st_ctime).isoformat()
                })
        
        # Logs
        logs_dir = self.tests_dir / 'logs'
        if logs_dir.exists():
            for log_file in logs_dir.glob('*'):
                files_info['logs'].append({
                    'name': log_file.name,
                    'size': log_file.stat().st_size,
                    'created': datetime.fromtimestamp(log_file.stat().st_ctime).isoformat()
                })
        
        return files_info
    
    def collect_performance_data(self):
        """Collect basic performance metrics"""
        import psutil
        import subprocess
        
        perf_data = {}
        
        # System resources
        perf_data['system'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        # Check for server process
        try:
            result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
            if result.returncode == 0:
                pid = int(result.stdout.strip().split()[0])
                process = psutil.Process(pid)
                perf_data['server_process'] = {
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'open_files': len(process.open_files())
                }
        except Exception as e:
            perf_data['server_process'] = {'error': str(e)}
        
        return perf_data
    
    def generate_html_report(self, results):
        """Generate an HTML report"""
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Impetus LLM Server Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background: #d4edda; border-color: #c3e6cb; }}
        .warning {{ background: #fff3cd; border-color: #ffeaa7; }}
        .error {{ background: #f8d7da; border-color: #f5c6cb; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        .screenshot {{ max-width: 200px; margin: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Impetus LLM Server - Test Results</h1>
        <p>Generated: {results['timestamp']}</p>
    </div>
    
    <div class="section success">
        <h2>✅ Manual Verification Results</h2>
        <div class="metric">
            <strong>Server Health:</strong> {'✅ PASS' if results['manual_verification']['server_health']['status'] else '❌ FAIL'}
        </div>
        <div class="metric">
            <strong>Models Endpoint:</strong> {'✅ PASS' if results['manual_verification']['models_endpoint']['status'] else '❌ FAIL'}
        </div>
        <div class="metric">
            <strong>Running Processes:</strong> {results['manual_verification']['running_processes'].get('count', 0)}
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Performance Metrics</h2>
        <div class="metric">
            <strong>CPU Usage:</strong> {results['performance_metrics']['system']['cpu_percent']:.1f}%
        </div>
        <div class="metric">
            <strong>Memory Usage:</strong> {results['performance_metrics']['system']['memory_percent']:.1f}%
        </div>
        {f'<div class="metric"><strong>Server Memory:</strong> {results["performance_metrics"]["server_process"]["memory_mb"]:.1f}MB</div>' 
         if 'server_process' in results['performance_metrics'] and 'memory_mb' in results['performance_metrics']['server_process'] else ''}
    </div>
    
    <div class="section">
        <h2>📁 Generated Test Files</h2>
        <p><strong>Screenshots:</strong> {len(results['test_files']['screenshots'])}</p>
        <p><strong>Log Files:</strong> {len(results['test_files']['logs'])}</p>
    </div>
    
    <div class="section">
        <h2>📸 Screenshots</h2>
        {' '.join([f'<img src="screenshots/{img["name"]}" alt="{img["name"]}" class="screenshot">' 
                  for img in results['test_files']['screenshots']])}
    </div>
    
    <div class="section">
        <h2>🔍 Detailed Results</h2>
        <pre>{json.dumps(results, indent=2)}</pre>
    </div>
</body>
</html>
'''
        return html_content
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print('🔍 Collecting test results...')
        results = self.collect_test_results()
        
        # Save JSON results
        json_report_path = self.tests_dir / f'test_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate HTML report
        html_content = self.generate_html_report(results)
        html_report_path = self.tests_dir / f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(html_report_path, 'w') as f:
            f.write(html_content)
        
        print(f'📊 Test summary saved to: {json_report_path}')
        print(f'🌐 HTML report saved to: {html_report_path}')
        
        # Print summary
        print('
=== TEST RESULTS SUMMARY ===')
        manual = results['manual_verification']
        print(f'Server Health: {\'✅ PASS\' if manual[\'server_health\'][\'status\'] else \'❌ FAIL\'}')
        print(f'Models Endpoint: {\'✅ PASS\' if manual[\'models_endpoint\'][\'status\'] else \'❌ FAIL\'}')
        print(f'Running Processes: {manual[\'running_processes\'].get(\'count\', 0)}')
        print(f'Screenshots Captured: {len(results[\'test_files\'][\'screenshots\'])}')
        print(f'System CPU: {results[\'performance_metrics\'][\'system\'][\'cpu_percent\']:.1f}%')
        print(f'System Memory: {results[\'performance_metrics\'][\'system\'][\'memory_percent\']:.1f}%')
        
        return results

if __name__ == '__main__':
    generator = TestSummaryGenerator()
    generator.generate_report()

