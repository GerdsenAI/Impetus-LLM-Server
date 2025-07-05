#!/usr/bin/env python3
"""
Setup model directories for IMPETUS users
Creates the standard model directory structure in the user's home folder
"""

import os
import sys
import shutil
from pathlib import Path

def setup_model_directories():
    """Create the model directory structure for the current user"""
    
    # Get user home directory
    user_home = Path.home()
    models_base = user_home / "Models"
    
    print(f"Setting up IMPETUS model directories for user: {os.environ.get('USER', 'unknown')}")
    print(f"Creating structure at: {models_base}")
    
    # Define directory structure
    format_dirs = ['GGUF', 'SafeTensors', 'MLX', 'CoreML', 'PyTorch', 'ONNX', 'Universal']
    capabilities = ['chat', 'completion', 'embedding', 'vision', 'audio', 'multimodal']
    utility_dirs = ['Downloads', 'Cache', 'Converted', 'Custom']
    
    # Create format directories with capabilities
    for format_dir in format_dirs:
        for capability in capabilities:
            dir_path = models_base / format_dir / capability
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {dir_path.relative_to(user_home)}")
    
    # Create utility directories
    for util_dir in utility_dirs:
        dir_path = models_base / util_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {dir_path.relative_to(user_home)}")
    
    # Create README
    readme_content = """# Model Storage Directory

This directory contains all AI models for use with IMPETUS and other applications.

## Quick Start

1. Place your models in the appropriate format/capability folder
2. IMPETUS will automatically detect them
3. Use the menu bar to switch between models

## Directory Structure

- **GGUF/** - Quantized models (most common, best performance)
- **SafeTensors/** - Hugging Face models
- **MLX/** - Apple Silicon optimized models
- **CoreML/** - iOS/macOS native models
- **PyTorch/** - PyTorch model files
- **ONNX/** - Cross-platform models
- **Universal/** - Models of unknown format

Each format directory contains:
- chat/ - Conversational models (e.g., Code Llama, Mistral)
- completion/ - Text completion models
- embedding/ - Text embedding models
- vision/ - Vision models
- audio/ - Audio models (e.g., Whisper)
- multimodal/ - Multi-modal models

## Utility Directories

- **Downloads/** - Temporary download location
- **Cache/** - Model cache (managed by IMPETUS)
- **Converted/** - Models converted between formats
- **Custom/** - Your fine-tuned models

## Recommended Models

For coding assistance:
1. Code Llama (GGUF format) - https://huggingface.co/TheBloke
2. Mistral 7B Instruct (GGUF) - Excellent for general tasks
3. Phi-3 Mini (MLX) - Small but capable

## Tips

- GGUF models offer the best performance on Apple Silicon
- Place models in the correct capability folder for better organization
- Use the IMPETUS menu bar to scan for new models
"""
    
    readme_path = models_base / "README.md"
    readme_path.write_text(readme_content)
    print(f"  ✓ Created: README.md")
    
    # Create .gitignore
    gitignore_content = """# Ignore model files (too large for git)
*.gguf
*.safetensors
*.mlx
*.npz
*.mlmodel
*.mlpackage
*.pt
*.pth
*.bin
*.onnx
*.h5
*.tflite
*.pb

# Ignore cache and temporary files
Cache/
Downloads/
*.tmp
*.temp
*.partial
*.download

# Keep directory structure
!*/
!README.md
!.gitignore
!*.md

# Ignore system files
.DS_Store
.AppleDouble
.LSOverride
"""
    
    gitignore_path = models_base / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    print(f"  ✓ Created: .gitignore")
    
    print("\n✅ Model directories setup complete!")
    print(f"\nYour models directory: {models_base}")
    print("\nNext steps:")
    print("1. Download models from https://huggingface.co/models")
    print("2. Place them in the appropriate format/capability folder")
    print("3. Launch IMPETUS and it will detect your models")
    
    return str(models_base)

def check_existing_models():
    """Check for models in legacy locations and offer to migrate"""
    
    user_home = Path.home()
    legacy_locations = [
        user_home / ".cache" / "huggingface",
        user_home / ".gerdsen_ai" / "model_cache",
        user_home / "Downloads"  # Check for model files in Downloads
    ]
    
    found_models = []
    
    for location in legacy_locations:
        if location.exists():
            # Look for model files
            for ext in ['.gguf', '.safetensors', '.mlx', '.bin', '.onnx']:
                for model_file in location.rglob(f'*{ext}'):
                    found_models.append(model_file)
    
    if found_models:
        print(f"\n📦 Found {len(found_models)} existing models in legacy locations:")
        for model in found_models[:5]:  # Show first 5
            print(f"  - {model.name}")
        if len(found_models) > 5:
            print(f"  ... and {len(found_models) - 5} more")
        
        response = input("\nWould you like help organizing these models? (y/n): ")
        if response.lower() == 'y':
            print("\nTo organize your models:")
            print("1. Open your new Models directory")
            print("2. Move models to the appropriate format/capability folders")
            print("3. IMPETUS will automatically detect them")

if __name__ == "__main__":
    try:
        models_dir = setup_model_directories()
        check_existing_models()
        
        # Open the directory if on macOS
        if sys.platform == "darwin":
            response = input("\nOpen Models directory in Finder? (y/n): ")
            if response.lower() == 'y':
                os.system(f'open "{models_dir}"')
                
    except Exception as e:
        print(f"\n❌ Error setting up model directories: {e}")
        sys.exit(1)