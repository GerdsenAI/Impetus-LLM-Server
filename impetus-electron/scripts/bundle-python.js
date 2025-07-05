/**
 * Python Environment Bundling Script for IMPETUS Electron App
 * Creates a portable Python environment that can be bundled with the Electron app
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const os = require('os');

class PythonBundler {
    constructor() {
        this.projectRoot = path.join(__dirname, '..', '..');
        this.electronRoot = path.join(__dirname, '..');
        this.pythonServerPath = path.join(this.projectRoot, 'gerdsen_ai_server');
        this.bundleOutputDir = path.join(this.electronRoot, 'resources', 'python-bundle');
        this.platform = os.platform();
        this.arch = os.arch();
        
        console.log('🐍 Python Bundler initialized');
        console.log(`Platform: ${this.platform}-${this.arch}`);
        console.log(`Project root: ${this.projectRoot}`);
        console.log(`Bundle output: ${this.bundleOutputDir}`);
    }
    
    async bundle() {
        try {
            console.log('🚀 Starting Python environment bundling...');
            
            // Create output directory
            await this.ensureDirectory(this.bundleOutputDir);
            
            // Step 1: Create portable Python environment
            await this.createPortablePython();
            
            // Step 2: Install dependencies
            await this.installDependencies();
            
            // Step 3: Copy source code
            await this.copySourceCode();
            
            // Step 4: Create wrapper scripts
            await this.createWrapperScripts();
            
            // Step 5: Create metadata
            await this.createMetadata();
            
            console.log('✅ Python environment bundling completed successfully!');
            console.log(`📦 Bundle created at: ${this.bundleOutputDir}`);
            
        } catch (error) {
            console.error('❌ Python bundling failed:', error);
            throw error;
        }
    }
    
    async createPortablePython() {
        console.log('📦 Creating portable Python environment...');
        
        const venvPath = path.join(this.bundleOutputDir, 'venv');
        
        // Remove existing bundle if it exists
        if (fs.existsSync(this.bundleOutputDir)) {
            console.log('🗑️  Removing existing bundle...');
            fs.rmSync(this.bundleOutputDir, { recursive: true, force: true });
        }
        
        await this.ensureDirectory(this.bundleOutputDir);
        
        // Create virtual environment
        await this.runCommand('python3', ['-m', 'venv', venvPath], {
            cwd: this.bundleOutputDir
        });
        
        console.log('✅ Portable Python environment created');
    }
    
    async installDependencies() {
        console.log('📋 Installing Python dependencies...');
        
        const venvPath = path.join(this.bundleOutputDir, 'venv');
        const pipPath = this.platform === 'win32' 
            ? path.join(venvPath, 'Scripts', 'pip.exe')
            : path.join(venvPath, 'bin', 'pip');
        
        const requirementsPath = path.join(this.pythonServerPath, 'requirements_production.txt');
        
        if (!fs.existsSync(requirementsPath)) {
            throw new Error(`Requirements file not found: ${requirementsPath}`);
        }
        
        // Upgrade pip first
        await this.runCommand(pipPath, ['install', '--upgrade', 'pip'], {
            cwd: this.bundleOutputDir
        });
        
        // Install requirements
        await this.runCommand(pipPath, ['install', '-r', requirementsPath], {
            cwd: this.bundleOutputDir
        });
        
        // Install additional packaging tools
        await this.runCommand(pipPath, ['install', 'pyinstaller'], {
            cwd: this.bundleOutputDir
        });
        
        console.log('✅ Dependencies installed');
    }
    
    async copySourceCode() {
        console.log('📁 Copying source code...');
        
        const srcPath = path.join(this.bundleOutputDir, 'src');
        await this.ensureDirectory(srcPath);
        
        // Copy the entire gerdsen_ai_server directory
        await this.copyDirectory(
            path.join(this.pythonServerPath, 'src'),
            srcPath
        );
        
        // Copy requirements file
        fs.copyFileSync(
            path.join(this.pythonServerPath, 'requirements_production.txt'),
            path.join(this.bundleOutputDir, 'requirements_production.txt')
        );
        
        console.log('✅ Source code copied');
    }
    
    async createWrapperScripts() {
        console.log('📝 Creating wrapper scripts...');
        
        const venvPath = path.join(this.bundleOutputDir, 'venv');
        const pythonPath = this.platform === 'win32'
            ? path.join(venvPath, 'Scripts', 'python.exe')
            : path.join(venvPath, 'bin', 'python');
        
        // Create launcher script for different platforms
        if (this.platform === 'win32') {
            await this.createWindowsLauncher(pythonPath);
        } else {
            await this.createUnixLauncher(pythonPath);
        }
        
        console.log('✅ Wrapper scripts created');
    }
    
    async createUnixLauncher(pythonPath) {
        const launcherScript = `#!/bin/bash
# IMPETUS Python Server Launcher
# This script launches the IMPETUS server with the bundled Python environment

# Get the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "\${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set up paths
PYTHON_PATH="\${SCRIPT_DIR}/venv/bin/python"
SERVER_PATH="\${SCRIPT_DIR}/src/production_main.py"

# Check if Python exists
if [ ! -f "\${PYTHON_PATH}" ]; then
    echo "❌ Python not found at \${PYTHON_PATH}"
    exit 1
fi

# Check if server exists
if [ ! -f "\${SERVER_PATH}" ]; then
    echo "❌ Server not found at \${SERVER_PATH}"
    exit 1
fi

# Change to the source directory
cd "\${SCRIPT_DIR}/src"

# Launch the server
echo "🚀 Starting IMPETUS server..."
exec "\${PYTHON_PATH}" "\${SERVER_PATH}" "$@"
`;
        
        const launcherPath = path.join(this.bundleOutputDir, 'start-server.sh');
        fs.writeFileSync(launcherPath, launcherScript);
        
        // Make executable
        fs.chmodSync(launcherPath, '755');
    }
    
    async createWindowsLauncher(pythonPath) {
        const launcherScript = `@echo off
REM IMPETUS Python Server Launcher
REM This script launches the IMPETUS server with the bundled Python environment

REM Get the directory containing this script
set SCRIPT_DIR=%~dp0

REM Set up paths
set PYTHON_PATH=%SCRIPT_DIR%venv\\Scripts\\python.exe
set SERVER_PATH=%SCRIPT_DIR%src\\production_main.py

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo ❌ Python not found at %PYTHON_PATH%
    exit /b 1
)

REM Check if server exists
if not exist "%SERVER_PATH%" (
    echo ❌ Server not found at %SERVER_PATH%
    exit /b 1
)

REM Change to the source directory
cd /d "%SCRIPT_DIR%src"

REM Launch the server
echo 🚀 Starting IMPETUS server...
"%PYTHON_PATH%" "%SERVER_PATH%" %*
`;
        
        const launcherPath = path.join(this.bundleOutputDir, 'start-server.bat');
        fs.writeFileSync(launcherPath, launcherScript);
    }
    
    async createMetadata() {
        console.log('📄 Creating metadata...');
        
        const metadata = {
            name: 'IMPETUS Python Bundle',
            version: '1.0.0',
            description: 'Portable Python environment for IMPETUS LLM Server',
            platform: this.platform,
            arch: this.arch,
            created: new Date().toISOString(),
            python_version: await this.getPythonVersion(),
            dependencies: await this.getDependencies()
        };
        
        fs.writeFileSync(
            path.join(this.bundleOutputDir, 'bundle-info.json'),
            JSON.stringify(metadata, null, 2)
        );
        
        // Create README for the bundle
        const readme = `# IMPETUS Python Bundle

This directory contains a portable Python environment for the IMPETUS LLM Server.

## Contents

- **venv/**: Virtual environment with all dependencies
- **src/**: IMPETUS server source code
- **start-server.sh** (Unix) / **start-server.bat** (Windows): Launch script
- **bundle-info.json**: Bundle metadata

## Usage

The Electron app will automatically use this bundled environment.
To manually run the server:

### Unix/macOS:
\`\`\`bash
./start-server.sh
\`\`\`

### Windows:
\`\`\`cmd
start-server.bat
\`\`\`

## Bundle Info

- Platform: ${this.platform}-${this.arch}
- Created: ${new Date().toISOString()}
- Python Version: ${await this.getPythonVersion()}

## Dependencies

See requirements_production.txt for the full list of dependencies.
`;
        
        fs.writeFileSync(
            path.join(this.bundleOutputDir, 'README.md'),
            readme
        );
        
        console.log('✅ Metadata created');
    }
    
    async getPythonVersion() {
        try {
            const result = await this.runCommand('python3', ['--version'], { capture: true });
            return result.stdout.trim();
        } catch (error) {
            return 'Unknown';
        }
    }
    
    async getDependencies() {
        try {
            const requirementsPath = path.join(this.pythonServerPath, 'requirements_production.txt');
            const requirements = fs.readFileSync(requirementsPath, 'utf-8');
            return requirements.split('\n').filter(line => line.trim() && !line.startsWith('#'));
        } catch (error) {
            return [];
        }
    }
    
    async runCommand(command, args, options = {}) {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, {
                stdio: options.capture ? ['pipe', 'pipe', 'pipe'] : 'inherit',
                cwd: options.cwd || process.cwd(),
                shell: true
            });
            
            let stdout = '';
            let stderr = '';
            
            if (options.capture) {
                child.stdout.on('data', (data) => {
                    stdout += data.toString();
                });
                
                child.stderr.on('data', (data) => {
                    stderr += data.toString();
                });
            }
            
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
    
    async ensureDirectory(dir) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }
    
    async copyDirectory(src, dest) {
        await this.ensureDirectory(dest);
        
        const entries = fs.readdirSync(src, { withFileTypes: true });
        
        for (const entry of entries) {
            const srcPath = path.join(src, entry.name);
            const destPath = path.join(dest, entry.name);
            
            if (entry.isDirectory()) {
                await this.copyDirectory(srcPath, destPath);
            } else {
                fs.copyFileSync(srcPath, destPath);
            }
        }
    }
}

// Main execution
if (require.main === module) {
    const bundler = new PythonBundler();
    
    bundler.bundle().catch(error => {
        console.error('❌ Bundling failed:', error);
        process.exit(1);
    });
}

module.exports = PythonBundler;