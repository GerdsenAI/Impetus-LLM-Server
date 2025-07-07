#!/usr/bin/env node
/**
 * Post-install script for IMPETUS
 * Sets up model directories for the user
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

console.log('🚀 IMPETUS Post-Install Setup');
console.log('=============================');

// Check if this is the first install
const userHome = os.homedir();
const modelsDir = path.join(userHome, 'Models');
const firstInstall = !fs.existsSync(modelsDir);

if (firstInstall) {
    console.log('\n📁 Setting up model directories...');
    
    try {
        // Run the Python setup script
        const setupScript = path.join(__dirname, '..', '..', 'scripts', 'setup_user_models.py');
        
        if (fs.existsSync(setupScript)) {
            execSync(`python3 "${setupScript}"`, { stdio: 'inherit' });
        } else {
            // Fallback: create directories with Node.js
            console.log('Creating model directories with Node.js...');
            
            const formatDirs = ['GGUF', 'SafeTensors', 'MLX', 'CoreML', 'PyTorch', 'ONNX', 'Universal'];
            const capabilities = ['chat', 'completion', 'embedding', 'vision', 'audio', 'multimodal'];
            const utilityDirs = ['Downloads', 'Cache', 'Converted', 'Custom'];
            
            // Create directories
            for (const format of formatDirs) {
                for (const capability of capabilities) {
                    const dirPath = path.join(modelsDir, format, capability);
                    fs.mkdirSync(dirPath, { recursive: true });
                }
            }
            
            for (const util of utilityDirs) {
                const dirPath = path.join(modelsDir, util);
                fs.mkdirSync(dirPath, { recursive: true });
            }
            
            console.log('✅ Model directories created successfully!');
        }
        
        console.log(`\n📂 Your models directory: ${modelsDir}`);
        console.log('\nNext steps:');
        console.log('1. Download models from https://huggingface.co/models');
        console.log('2. Place them in the appropriate folder');
        console.log('3. Launch IMPETUS from your Applications folder');
        
    } catch (error) {
        console.error('⚠️  Could not set up model directories automatically');
        console.error('Error:', error.message);
        console.log('\nYou can set them up manually by running:');
        console.log('python3 scripts/setup_user_models.py');
    }
} else {
    console.log(`\n✅ Model directories already exist at: ${modelsDir}`);
}

console.log('\n🎉 IMPETUS installation complete!');
console.log('Launch IMPETUS from your Applications folder to get started.');