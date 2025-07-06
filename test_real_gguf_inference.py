#!/usr/bin/env python3
"""
Test script for real GGUF inference using llama-cpp-python
"""

import sys
import os
import logging

# Add the source path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gerdsen_ai_server', 'src'))

from inference.gguf_inference import get_inference_engine, GenerationConfig

def test_gguf_inference():
    """Test GGUF inference with a real model"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Real GGUF Inference")
    print("=" * 50)
    
    # Get the inference engine
    engine = get_inference_engine()
    
    # Model path
    model_path = "/Users/gerdsenai/Models/GGUF/chat/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    print(f"📁 Model file exists: {model_path}")
    
    # Model info
    model_info = {
        'name': 'tinyllama-1.1b-chat',
        'architecture': 'llama', 
        'context_length': 2048,
        'quantization': 'Q4_K_M'
    }
    
    # Load model
    print("⏳ Loading model...")
    success = engine.load_model_for_inference('tinyllama-test', model_path, model_info)
    
    if not success:
        print("❌ Failed to load model")
        return False
    
    print("✅ Model loaded successfully!")
    
    # Test generation
    print("\n🔮 Testing text generation...")
    
    config = GenerationConfig(
        max_tokens=50,
        temperature=0.7,
        stream=False
    )
    
    test_prompt = "Hello, how are you today?"
    
    try:
        result = engine.generate('tinyllama-test', test_prompt, config)
        
        print(f"\n📝 Generated Response:")
        print(f"   Input: {test_prompt}")
        print(f"   Output: {result.text}")
        print(f"   Tokens: {result.tokens_generated}")
        print(f"   Speed: {result.tokens_per_second:.2f} tokens/sec")
        print(f"   Time: {result.time_taken:.2f}s")
        
        # Test streaming
        print("\n🌊 Testing streaming generation...")
        stream_prompt = "Write a short Python function:"
        
        print(f"Input: {stream_prompt}")
        print("Output: ", end="", flush=True)
        
        for token in engine.generate_stream('tinyllama-test', stream_prompt, config):
            print(token, end="", flush=True)
        
        print("\n")
        
        # Test chat completion
        print("\n💬 Testing chat completion...")
        
        messages = [
            {"role": "system", "content": "You are a helpful programming assistant."},
            {"role": "user", "content": "Explain what Python is in one sentence."}
        ]
        
        chat_response = engine.create_chat_completion('tinyllama-test', messages, config)
        
        print(f"Chat Response: {chat_response['choices'][0]['message']['content']}")
        
        print("\n✅ All tests passed! Real GGUF inference is working!")
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gguf_inference()
    if success:
        print("\n🎉 Real GGUF inference validation complete!")
    else:
        print("\n💥 Real GGUF inference validation failed!")
        sys.exit(1)
