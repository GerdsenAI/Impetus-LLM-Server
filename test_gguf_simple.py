#!/usr/bin/env python3
"""
Simple test for GGUF inference with actual model
"""

import os
import sys

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gerdsen_ai_server', 'src'))

try:
    # Check dependencies first
    import numpy as np
    from llama_cpp import Llama
    print("✅ Dependencies OK")
    
    # Import our inference engine
    from inference.gguf_inference import get_inference_engine, GenerationConfig
    
    # Get the engine
    engine = get_inference_engine()
    print(f"✅ Using inference backend: {engine.loaded_models}")
    
    # Look for any available GGUF model
    models_dir = os.path.expanduser("~/Models/GGUF/chat/")
    gguf_files = [f for f in os.listdir(models_dir) if f.endswith('.gguf')] if os.path.exists(models_dir) else []
    
    if not gguf_files:
        print("❌ No GGUF models found!")
        sys.exit(1)
        
    # Use the first available model
    model_path = os.path.join(models_dir, gguf_files[0])
    print(f"✅ Using model: {gguf_files[0]}")
    
    # Load model
    model_info = {
        'name': gguf_files[0],
        'architecture': 'llama',
        'context_length': 2048,
        'quantization': 'Q4_K_M'
    }
    
    success = engine.load_model_for_inference('test-model', model_path, model_info)
    if not success:
        print("❌ Failed to load model")
        sys.exit(1)
        
    print("✅ Model loaded!")
    
    # Test simple generation
    config = GenerationConfig(max_tokens=20, temperature=0.7)
    result = engine.generate('test-model', "Hello! How are you?", config)
    
    print(f"\n📝 Response: {result.text}")
    print(f"⚡ Speed: {result.tokens_per_second:.1f} tokens/sec")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install numpy llama-cpp-python")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()