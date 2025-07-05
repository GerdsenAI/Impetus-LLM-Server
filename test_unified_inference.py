#!/usr/bin/env python3
"""
Test script for the unified inference interface
IMPETUS (Intelligent Model Platform Enabling Taskbar Unified Server)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gerdsen_ai_server.src.inference import get_unified_inference_engine, GenerationConfig
import logging

def test_unified_inference():
    """Test the unified inference engine with dummy models"""
    
    logging.basicConfig(level=logging.INFO)
    print("🚀 Testing IMPETUS Unified Inference Engine")
    print("=" * 50)
    
    # Get the unified inference engine
    engine = get_unified_inference_engine()
    
    # Test supported formats
    print(f"Supported formats: {engine.get_supported_formats()}")
    
    # Test model loading for different formats
    test_models = [
        ("test-gguf", "/path/to/test.gguf", {"name": "test-gguf"}, "gguf"),
        ("test-safetensors", "/path/to/test.safetensors", {"name": "test-safetensors"}, "safetensors"),
        ("test-mlx", "/path/to/test.mlx", {"name": "test-mlx"}, "mlx"),
        ("test-coreml", "/path/to/test.mlmodel", {"name": "test-coreml"}, "coreml"),
        ("test-pytorch", "/path/to/test.pt", {"name": "test-pytorch"}, "pytorch"),
        ("test-onnx", "/path/to/test.onnx", {"name": "test-onnx"}, "onnx"),
    ]
    
    loaded_models = []
    
    for model_id, path, info, format_type in test_models:
        print(f"\n📁 Testing {format_type.upper()} model:")
        
        # Load model
        success = engine.load_model_for_inference(model_id, path, info, format_type)
        if success:
            print(f"✅ Loaded {model_id}")
            loaded_models.append(model_id)
            
            # Test generation
            try:
                result = engine.generate(model_id, "Hello, how are you?")
                print(f"🤖 Generated: {result.text[:100]}...")
                print(f"📊 Speed: {result.tokens_per_second:.2f} tokens/sec")
            except Exception as e:
                print(f"❌ Generation failed: {e}")
            
            # Test chat completion
            try:
                messages = [{"role": "user", "content": "What is AI?"}]
                response = engine.create_chat_completion(model_id, messages)
                print(f"💬 Chat response: {response['choices'][0]['message']['content'][:100]}...")
            except Exception as e:
                print(f"❌ Chat completion failed: {e}")
        else:
            print(f"❌ Failed to load {model_id}")
    
    # Test unified statistics
    print(f"\n📈 Unified Inference Statistics:")
    print(f"Loaded models: {engine.get_loaded_models()}")
    print(f"Format statistics: {engine.get_format_statistics()}")
    
    # Test streaming for one model
    if loaded_models:
        test_model = loaded_models[0]
        print(f"\n🌊 Testing streaming with {test_model}:")
        try:
            for i, token in enumerate(engine.generate_stream(test_model, "Tell me about AI")):
                print(token, end='', flush=True)
                if i > 10:  # Limit output
                    break
            print("\n✅ Streaming test completed")
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
    
    # Test unloading
    print(f"\n🗑️ Testing model unloading:")
    for model_id in loaded_models:
        success = engine.unload_model(model_id)
        print(f"{'✅' if success else '❌'} Unloaded {model_id}")
    
    print(f"\nFinal loaded models: {engine.get_all_loaded_models()}")
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_unified_inference()