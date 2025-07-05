#!/usr/bin/env python3
"""
Download an example model for IMPETUS
Downloads a small, efficient model to get users started
"""

import os
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

def download_with_progress(url, destination):
    """Download a file with progress bar"""
    
    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        progress = int(50 * percent / 100)
        sys.stdout.write(f'\r[{"=" * progress}{" " * (50 - progress)}] {percent:.1f}%')
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, destination, reporthook=download_progress)
        print()  # New line after progress bar
        return True
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False

def main():
    """Download a recommended starter model"""
    
    print("🤖 IMPETUS Example Model Downloader")
    print("===================================")
    
    # Get user's models directory
    user_home = Path.home()
    models_dir = user_home / "Models"
    
    # Example models (small, efficient ones for getting started)
    example_models = [
        {
            "name": "Phi-3 Mini 4k Instruct (Q4)",
            "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
            "size": "2.2 GB",
            "format": "GGUF",
            "capability": "chat",
            "description": "Small but capable model, great for code and general tasks"
        },
        {
            "name": "TinyLlama 1.1B Chat (Q4)",
            "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "size": "668 MB",
            "format": "GGUF",
            "capability": "chat",
            "description": "Very small and fast, good for quick tasks"
        },
        {
            "name": "CodeGemma 2B Instruct (Q4)",
            "url": "https://huggingface.co/google/codegemma-2b-gguf/resolve/main/codegemma-2b-it-Q4_K_M.gguf",
            "size": "1.6 GB",
            "format": "GGUF",
            "capability": "chat",
            "description": "Specialized for code completion and assistance"
        }
    ]
    
    print("\nAvailable example models:")
    for i, model in enumerate(example_models, 1):
        print(f"\n{i}. {model['name']} ({model['size']})")
        print(f"   {model['description']}")
    
    # Get user choice
    while True:
        try:
            choice = input("\nSelect a model to download (1-3) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Exiting...")
                return
            
            choice = int(choice)
            if 1 <= choice <= len(example_models):
                break
            else:
                print("Please enter a number between 1 and 3")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
    
    # Selected model
    model = example_models[choice - 1]
    
    # Determine destination
    format_dir = models_dir / model["format"] / model["capability"]
    format_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract filename from URL
    filename = os.path.basename(urlparse(model["url"]).path)
    destination = format_dir / filename
    
    if destination.exists():
        print(f"\n⚠️  Model already exists at: {destination}")
        overwrite = input("Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Skipping download.")
            return
    
    print(f"\n📥 Downloading: {model['name']}")
    print(f"Size: {model['size']}")
    print(f"Destination: {destination}")
    print("\nThis may take a few minutes depending on your connection...")
    
    # Download the model
    if download_with_progress(model["url"], str(destination)):
        print(f"\n✅ Successfully downloaded: {filename}")
        print(f"📁 Location: {destination}")
        print("\nNext steps:")
        print("1. Launch IMPETUS from your Applications folder")
        print("2. The model will be automatically detected")
        print("3. Select it from the Models menu in the taskbar")
    else:
        print("\n❌ Download failed. Please try again or download manually from:")
        print(model["url"])
        
        # Clean up partial download
        if destination.exists():
            os.remove(destination)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Download cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)