#!/usr/bin/env python3
"""
Test script to verify GGUF dependencies are installed correctly
"""

import sys
import os

print("🔍 Testing GGUF Dependencies")
print("=" * 50)

# Test numpy
try:
    import numpy as np
    print("✅ numpy installed - version:", np.__version__)
except ImportError as e:
    print("❌ numpy NOT installed:", e)
    print("   Run: pip install numpy==1.26.4")

# Test llama-cpp-python
try:
    from llama_cpp import Llama
    print("✅ llama-cpp-python installed")
    
    # Check if Metal support is available
    test_model = None
    try:
        # Try to create a minimal test instance (will fail without model, but shows Metal support)
        test_model = Llama(model_path="dummy.gguf", n_ctx=128, verbose=False)
    except Exception as e:
        error_str = str(e).lower()
        if "metal" in error_str:
            print("✅ Metal GPU acceleration available")
        elif "file" in error_str or "not found" in error_str:
            print("✅ llama-cpp-python working (model file not found as expected)")
        else:
            print("⚠️ llama-cpp-python status unclear:", e)
            
except ImportError as e:
    print("❌ llama-cpp-python NOT installed:", e)
    print("   Run: pip install llama-cpp-python>=0.2.0")

# Test our imports
print("\n🔍 Testing IMPETUS Imports")
print("-" * 50)

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gerdsen_ai_server', 'src'))

try:
    from inference.gguf_inference import GGUFInferenceEngine, get_inference_engine
    print("✅ GGUF inference engine imports successfully")
    
    # Check which backend is being used
    from inference.gguf_inference import INFERENCE_BACKEND
    print(f"✅ Inference backend: {INFERENCE_BACKEND}")
    
except Exception as e:
    print("❌ Failed to import GGUF inference engine:", e)

# Check for models
print("\n🔍 Checking for GGUF Models")
print("-" * 50)

models_dir = os.path.expanduser("~/Models/GGUF/chat/")
if os.path.exists(models_dir):
    print(f"✅ Models directory exists: {models_dir}")
    
    # List GGUF files
    gguf_files = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]
    if gguf_files:
        print(f"✅ Found {len(gguf_files)} GGUF models:")
        for model in gguf_files:
            size_mb = os.path.getsize(os.path.join(models_dir, model)) / (1024 * 1024)
            print(f"   - {model} ({size_mb:.1f} MB)")
    else:
        print("⚠️ No GGUF models found in directory")
else:
    print(f"❌ Models directory not found: {models_dir}")

print("\n✅ Dependency check complete!")