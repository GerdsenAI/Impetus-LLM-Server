/**
 * Test script for Python bundling
 * Tests the bundled Python environment before building the final Electron app
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class BundleTester {
    constructor() {
        this.electronRoot = path.join(__dirname, '..');
        this.bundlePath = path.join(this.electronRoot, 'resources', 'python-bundle');
        this.platform = process.platform;
        
        console.log('🧪 Python Bundle Tester initialized');
        console.log(`Bundle path: ${this.bundlePath}`);
    }
    
    async test() {
        try {
            console.log('🔍 Testing Python bundle...');
            
            // Check if bundle exists
            if (!fs.existsSync(this.bundlePath)) {
                throw new Error(`Bundle not found at ${this.bundlePath}. Run 'npm run bundle-python' first.`);
            }
            
            // Test bundle structure
            await this.testBundleStructure();
            
            // Test Python executable
            await this.testPythonExecutable();
            
            // Test dependencies
            await this.testDependencies();
            
            // Test server startup
            await this.testServerStartup();
            
            console.log('✅ Python bundle test completed successfully!');
            
        } catch (error) {
            console.error('❌ Bundle test failed:', error);
            throw error;
        }
    }
    
    async testBundleStructure() {
        console.log('📁 Testing bundle structure...');
        
        const requiredPaths = [
            'venv',
            'src',
            'src/production_main.py',
            'requirements_production.txt',
            'bundle-info.json'
        ];
        
        if (this.platform === 'win32') {
            requiredPaths.push('venv/Scripts/python.exe');
            requiredPaths.push('start-server.bat');
        } else {
            requiredPaths.push('venv/bin/python');
            requiredPaths.push('start-server.sh');
        }
        
        for (const relativePath of requiredPaths) {
            const fullPath = path.join(this.bundlePath, relativePath);
            if (!fs.existsSync(fullPath)) {
                throw new Error(`Required path missing: ${relativePath}`);
            }
        }
        
        console.log('✅ Bundle structure is valid');
    }
    
    async testPythonExecutable() {
        console.log('🐍 Testing Python executable...');
        
        const pythonPath = this.platform === 'win32'
            ? path.join(this.bundlePath, 'venv', 'Scripts', 'python.exe')
            : path.join(this.bundlePath, 'venv', 'bin', 'python');
        
        const result = await this.runCommand(pythonPath, ['--version']);
        console.log(`Python version: ${result.stdout.trim()}`);
        
        console.log('✅ Python executable works');
    }
    
    async testDependencies() {
        console.log('📦 Testing dependencies...');
        
        const pythonPath = this.platform === 'win32'
            ? path.join(this.bundlePath, 'venv', 'Scripts', 'python.exe')
            : path.join(this.bundlePath, 'venv', 'bin', 'python');
        
        const testScript = `
import sys
print(f"Python: {sys.version}")

# Test key dependencies
try:
    import flask
    print(f"Flask: {flask.__version__}")
except ImportError as e:
    print(f"Flask import failed: {e}")

try:
    import mlx
    print(f"MLX: imported successfully")
except ImportError as e:
    print(f"MLX import failed: {e}")

try:
    import torch
    print(f"PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"PyTorch import failed: {e}")

try:
    import safetensors
    print(f"SafeTensors: {safetensors.__version__}")
except ImportError as e:
    print(f"SafeTensors import failed: {e}")

try:
    import onnxruntime
    print(f"ONNX Runtime: {onnxruntime.__version__}")
except ImportError as e:
    print(f"ONNX Runtime import failed: {e}")

print("Dependencies check completed")
`;
        
        const result = await this.runCommand(pythonPath, ['-c', testScript]);
        console.log('Dependencies output:');
        console.log(result.stdout);
        
        console.log('✅ Dependencies test completed');
    }
    
    async testServerStartup() {
        console.log('🚀 Testing server startup...');
        
        const pythonPath = this.platform === 'win32'
            ? path.join(this.bundlePath, 'venv', 'Scripts', 'python.exe')
            : path.join(this.bundlePath, 'venv', 'bin', 'python');
        
        const serverPath = path.join(this.bundlePath, 'src', 'production_main_simple.py');
        
        // Start server in test mode
        const child = spawn(pythonPath, [serverPath], {
            cwd: path.join(this.bundlePath, 'src'),
            env: {
                ...process.env,
                PYTHONPATH: path.join(this.bundlePath, 'src'),
                IMPETUS_TEST_MODE: 'true'  // Signal test mode to server
            }
        });
        
        let serverOutput = '';
        let serverStarted = false;
        
        child.stdout.on('data', (data) => {
            serverOutput += data.toString();
            if (data.toString().includes('Running on')) {
                serverStarted = true;
            }
        });
        
        child.stderr.on('data', (data) => {
            serverOutput += data.toString();
        });
        
        // Wait for server to start or timeout
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                child.kill('SIGTERM');
                reject(new Error('Server startup timeout'));
            }, 30000); // 30 second timeout
            
            const checkInterval = setInterval(() => {
                if (serverStarted) {
                    clearTimeout(timeout);
                    clearInterval(checkInterval);
                    child.kill('SIGTERM');
                    resolve();
                }
            }, 1000);
        });
        
        console.log('Server output:');
        console.log(serverOutput);
        console.log('✅ Server startup test completed');
    }
    
    async runCommand(command, args, options = {}) {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: options.cwd || process.cwd(),
                env: options.env || process.env
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            child.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Command failed with code ${code}: ${stderr}`));
                } else {
                    resolve({ stdout, stderr, code });
                }
            });
            
            child.on('error', (error) => {
                reject(error);
            });
        });
    }
}

// Main execution
if (require.main === module) {
    const tester = new BundleTester();
    
    tester.test().catch(error => {
        console.error('❌ Bundle test failed:', error);
        process.exit(1);
    });
}

module.exports = BundleTester;
