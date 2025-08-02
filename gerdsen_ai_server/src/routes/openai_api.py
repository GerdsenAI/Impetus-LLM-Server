"""
OpenAI-compatible API endpoints for VS Code integration
"""

from flask import Blueprint, jsonify, request, Response, current_app, stream_with_context
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Generator
from loguru import logger
from ..config.settings import settings

bp = Blueprint('openai_api', __name__)


def verify_api_key():
    """Verify API key if configured"""
    if not settings.server.api_key:
        return True
    
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return token == settings.server.api_key
    
    return False


@bp.before_request
def check_auth():
    """Check authentication before each request"""
    if not verify_api_key():
        return jsonify({'error': 'Invalid API key'}), 401


@bp.route('/models', methods=['GET'])
def list_models():
    """List available models in OpenAI format"""
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})
    
    models = []
    
    # Add loaded models
    for model_id in loaded_models:
        models.append({
            'id': model_id,
            'object': 'model',
            'created': int(time.time()),
            'owned_by': 'impetus',
            'permission': [],
            'root': model_id,
            'parent': None
        })
    
    # Add default model if no models loaded
    if not models:
        models.append({
            'id': settings.model.default_model,
            'object': 'model',
            'created': int(time.time()),
            'owned_by': 'impetus',
            'permission': [],
            'root': settings.model.default_model,
            'parent': None
        })
    
    return jsonify({
        'object': 'list',
        'data': models
    })


@bp.route('/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    data = request.get_json()
    
    # Extract parameters
    model = data.get('model', settings.model.default_model)
    messages = data.get('messages', [])
    temperature = data.get('temperature', settings.inference.temperature)
    max_tokens = data.get('max_tokens', settings.inference.max_tokens)
    stream = data.get('stream', settings.inference.stream_by_default)
    top_p = data.get('top_p', settings.inference.top_p)
    
    # Validate messages
    if not messages:
        return jsonify({'error': 'Messages are required'}), 400
    
    # Get model from app state
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})
    
    # Check if model is loaded
    if model not in loaded_models:
        # Try to load the model
        try:
            from ..model_loaders.mlx_loader import MLXModelLoader
            loader = MLXModelLoader()
            loaded_model = loader.load_model(model)
            loaded_models[model] = loaded_model
            logger.info(f"Auto-loaded model: {model}")
        except Exception as e:
            logger.error(f"Failed to auto-load model {model}: {e}")
            return jsonify({
                'error': 'Model not found',
                'message': f'Model {model} is not loaded. Please load it first.'
            }), 404
    
    # Update metrics
    metrics = app_state.get('metrics', {})
    metrics['requests_total'] = metrics.get('requests_total', 0) + 1
    
    # Generate response
    if stream:
        return Response(
            stream_with_context(
                generate_chat_stream(
                    loaded_models[model],
                    messages,
                    temperature,
                    max_tokens,
                    top_p,
                    app_state
                )
            ),
            mimetype='text/event-stream'
        )
    else:
        # Non-streaming response
        response = generate_chat_completion(
            loaded_models[model],
            messages,
            temperature,
            max_tokens,
            top_p,
            app_state
        )
        return jsonify(response)


def generate_chat_stream(model, messages: List[Dict], temperature: float, 
                        max_tokens: int, top_p: float, app_state: Dict) -> Generator:
    """Generate streaming chat completion response"""
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    
    # Convert messages to prompt
    prompt = convert_messages_to_prompt(messages)
    
    # Start timing
    start_time = time.time()
    tokens_generated = 0
    
    try:
        # Generate tokens
        # TODO: Use actual model inference here
        # For now, mock response
        mock_response = "I'm a helpful AI assistant running on Apple Silicon. How can I help you today?"
        
        # Send initial chunk
        chunk = {
            'id': chat_id,
            'object': 'chat.completion.chunk',
            'created': created,
            'model': model.model_id if hasattr(model, 'model_id') else 'unknown',
            'choices': [{
                'index': 0,
                'delta': {'role': 'assistant', 'content': ''},
                'finish_reason': None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        
        # Stream tokens
        for i, char in enumerate(mock_response):
            chunk = {
                'id': chat_id,
                'object': 'chat.completion.chunk',
                'created': created,
                'model': model.model_id if hasattr(model, 'model_id') else 'unknown',
                'choices': [{
                    'index': 0,
                    'delta': {'content': char},
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            tokens_generated += 1
            time.sleep(0.01)  # Simulate generation delay
        
        # Send final chunk
        chunk = {
            'id': chat_id,
            'object': 'chat.completion.chunk',
            'created': created,
            'model': model.model_id if hasattr(model, 'model_id') else 'unknown',
            'choices': [{
                'index': 0,
                'delta': {},
                'finish_reason': 'stop'
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
        # Update metrics
        elapsed = (time.time() - start_time) * 1000
        metrics = app_state.get('metrics', {})
        metrics['tokens_generated'] = metrics.get('tokens_generated', 0) + tokens_generated
        
        # Update average latency
        total_requests = metrics.get('requests_total', 1)
        current_avg = metrics.get('average_latency_ms', 0)
        metrics['average_latency_ms'] = ((current_avg * (total_requests - 1)) + elapsed) / total_requests
        
    except Exception as e:
        logger.error(f"Error in chat stream generation: {e}")
        error_chunk = {
            'id': chat_id,
            'object': 'chat.completion.chunk',
            'created': created,
            'choices': [{
                'index': 0,
                'delta': {},
                'finish_reason': 'error'
            }],
            'error': str(e)
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"


def generate_chat_completion(model, messages: List[Dict], temperature: float,
                           max_tokens: int, top_p: float, app_state: Dict) -> Dict:
    """Generate non-streaming chat completion response"""
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    
    # Convert messages to prompt
    prompt = convert_messages_to_prompt(messages)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Generate response
        # TODO: Use actual model inference here
        # For now, mock response
        response_text = "I'm a helpful AI assistant running on Apple Silicon. How can I help you today?"
        tokens_generated = len(response_text.split())
        
        # Update metrics
        elapsed = (time.time() - start_time) * 1000
        metrics = app_state.get('metrics', {})
        metrics['tokens_generated'] = metrics.get('tokens_generated', 0) + tokens_generated
        
        # Update average latency
        total_requests = metrics.get('requests_total', 1)
        current_avg = metrics.get('average_latency_ms', 0)
        metrics['average_latency_ms'] = ((current_avg * (total_requests - 1)) + elapsed) / total_requests
        
        return {
            'id': chat_id,
            'object': 'chat.completion',
            'created': created,
            'model': model.model_id if hasattr(model, 'model_id') else 'unknown',
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': response_text
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(prompt.split()),
                'completion_tokens': tokens_generated,
                'total_tokens': len(prompt.split()) + tokens_generated
            }
        }
        
    except Exception as e:
        logger.error(f"Error in chat completion generation: {e}")
        return {
            'error': {
                'message': str(e),
                'type': 'internal_error',
                'code': 500
            }
        }, 500


def convert_messages_to_prompt(messages: List[Dict]) -> str:
    """Convert OpenAI message format to a single prompt string"""
    prompt_parts = []
    
    for message in messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        
        if role == 'system':
            prompt_parts.append(f"System: {content}")
        elif role == 'user':
            prompt_parts.append(f"User: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Assistant: {content}")
    
    prompt_parts.append("Assistant:")
    return "\n\n".join(prompt_parts)


@bp.route('/completions', methods=['POST'])
def completions():
    """OpenAI-compatible completions endpoint"""
    data = request.get_json()
    
    # Extract parameters
    model = data.get('model', settings.model.default_model)
    prompt = data.get('prompt', '')
    temperature = data.get('temperature', settings.inference.temperature)
    max_tokens = data.get('max_tokens', settings.inference.max_tokens)
    
    # Convert to chat format and use chat completions
    messages = [{'role': 'user', 'content': prompt}]
    
    # Reuse chat completions logic
    request.json['messages'] = messages
    return chat_completions()


@bp.route('/embeddings', methods=['POST'])
def embeddings():
    """OpenAI-compatible embeddings endpoint"""
    data = request.get_json()
    
    # Extract parameters
    model = data.get('model', 'text-embedding-ada-002')
    input_text = data.get('input', '')
    
    if isinstance(input_text, str):
        inputs = [input_text]
    else:
        inputs = input_text
    
    # TODO: Implement actual embeddings generation
    # For now, return mock embeddings
    
    embeddings_data = []
    for i, text in enumerate(inputs):
        # Generate mock embedding (1536 dimensions like ada-002)
        import random
        embedding = [random.random() for _ in range(1536)]
        
        embeddings_data.append({
            'object': 'embedding',
            'embedding': embedding,
            'index': i
        })
    
    return jsonify({
        'object': 'list',
        'data': embeddings_data,
        'model': model,
        'usage': {
            'prompt_tokens': sum(len(text.split()) for text in inputs),
            'total_tokens': sum(len(text.split()) for text in inputs)
        }
    })