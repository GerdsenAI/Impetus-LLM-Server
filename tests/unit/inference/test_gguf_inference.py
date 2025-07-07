"""
Test GGUF Inference Engine
"""

import pytest
import time
from unittest.mock import Mock, patch

from gerdsen_ai_server.src.inference import (
    GGUFInferenceEngine,
    GenerationConfig,
    get_inference_engine
)


class TestGGUFInferenceEngine:
    """Test suite for GGUF inference engine"""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh inference engine"""
        return GGUFInferenceEngine()
    
    @pytest.fixture
    def test_model_info(self):
        """Test model information"""
        return {
            'name': 'test-model',
            'architecture': 'llama',
            'context_length': 2048,
            'embedding_length': 4096,
            'n_layers': 32,
            'quantization': 'Q4_K_M'
        }
    
    def test_load_model(self, engine, test_model_info):
        """Test loading a model for inference"""
        success = engine.load_model_for_inference(
            'test-model',
            '/fake/path/model.gguf',
            test_model_info
        )
        
        assert success is True
        assert 'test-model' in engine.loaded_models
        assert engine.loaded_models['test-model']['info'] == test_model_info
    
    def test_generate_basic(self, engine, test_model_info):
        """Test basic text generation"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        result = engine.generate(
            'test-model',
            'Hello, world!',
            GenerationConfig(max_tokens=50)
        )
        
        assert result.text is not None
        assert len(result.text) > 0
        assert result.tokens_generated > 0
        assert result.time_taken > 0
        assert result.tokens_per_second > 0
        assert result.finish_reason == 'stop'
    
    def test_generate_with_config(self, engine, test_model_info):
        """Test generation with custom config"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        config = GenerationConfig(
            max_tokens=100,
            temperature=0.5,
            top_p=0.95,
            repetition_penalty=1.2
        )
        
        result = engine.generate('test-model', 'Test prompt', config)
        
        assert result.text is not None
        assert result.tokens_generated > 0
    
    def test_generate_stream(self, engine, test_model_info):
        """Test streaming generation"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        tokens = []
        for token in engine.generate_stream('test-model', 'Stream test'):
            tokens.append(token)
        
        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)
    
    def test_chat_completion(self, engine, test_model_info):
        """Test OpenAI-compatible chat completion"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"}
        ]
        
        response = engine.create_chat_completion('test-model', messages)
        
        assert response['object'] == 'chat.completion'
        assert 'choices' in response
        assert len(response['choices']) == 1
        assert response['choices'][0]['message']['role'] == 'assistant'
        assert 'content' in response['choices'][0]['message']
        assert 'usage' in response
        assert 'prompt_tokens' in response['usage']
        assert 'completion_tokens' in response['usage']
    
    def test_chat_completion_stream(self, engine, test_model_info):
        """Test streaming chat completion"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        messages = [{"role": "user", "content": "Stream test"}]
        
        chunks = list(engine.create_chat_completion(
            'test-model', 
            messages,
            stream=True
        ))
        
        assert len(chunks) > 2  # At least start, content, and end chunks
        assert chunks[0]['choices'][0]['delta'].get('role') == 'assistant'
        assert chunks[-1]['choices'][0]['finish_reason'] == 'stop'
        
        # Check content chunks
        content_chunks = [c for c in chunks[1:-1]]
        assert all('content' in c['choices'][0]['delta'] for c in content_chunks)
    
    def test_messages_to_prompt(self, engine):
        """Test message formatting"""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = engine._messages_to_prompt(messages)
        
        assert "System: Be helpful" in prompt
        assert "User: Hi" in prompt
        assert "Assistant: Hello!" in prompt
        assert "User: How are you?" in prompt
        assert prompt.endswith("Assistant:")
    
    def test_unload_model(self, engine, test_model_info):
        """Test unloading a model"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        assert 'test-model' in engine.loaded_models
        
        success = engine.unload_model('test-model')
        assert success is True
        assert 'test-model' not in engine.loaded_models
    
    def test_unload_nonexistent_model(self, engine):
        """Test unloading a model that doesn't exist"""
        success = engine.unload_model('nonexistent')
        assert success is False
    
    def test_get_loaded_models(self, engine, test_model_info):
        """Test getting list of loaded models"""
        assert engine.get_loaded_models() == []
        
        engine.load_model_for_inference('model1', '/fake/path1', test_model_info)
        engine.load_model_for_inference('model2', '/fake/path2', test_model_info)
        
        loaded = engine.get_loaded_models()
        assert len(loaded) == 2
        assert 'model1' in loaded
        assert 'model2' in loaded
    
    def test_get_model_info(self, engine, test_model_info):
        """Test getting model information"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        info = engine.get_model_info('test-model')
        assert info == test_model_info
        
        assert engine.get_model_info('nonexistent') is None
    
    def test_generate_without_loaded_model(self, engine):
        """Test generation with unloaded model raises error"""
        with pytest.raises(ValueError, match="Model .* not loaded"):
            engine.generate('nonexistent', 'test')
    
    def test_singleton_instance(self):
        """Test singleton pattern for inference engine"""
        engine1 = get_inference_engine()
        engine2 = get_inference_engine()
        
        assert engine1 is engine2
    
    def test_dummy_responses(self, engine, test_model_info):
        """Test different dummy response patterns"""
        engine.load_model_for_inference('test-model', '/fake/path', test_model_info)
        
        # Test hello response
        result = engine.generate('test-model', 'Hello there!')
        assert 'Hello!' in result.text
        assert 'GGUF model' in result.text
        
        # Test code response
        result = engine.generate('test-model', 'Write some code')
        assert 'def' in result.text
        assert 'python' in result.text.lower()
        
        # Test explain response
        result = engine.generate('test-model', 'Explain this')
        assert 'explain' in result.text.lower()
        assert 'locally' in result.text