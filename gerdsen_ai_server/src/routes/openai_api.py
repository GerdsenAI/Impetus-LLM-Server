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
        # Send initial chunk with role
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
        
        # Generate tokens using MLX
        if hasattr(model, 'generate_stream'):
            # Use streaming generation if available
            for token in model.generate_stream(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            ):
                chunk = {
                    'id': chat_id,
                    'object': 'chat.completion.chunk',
                    'created': created,
                    'model': model.model_id if hasattr(model, 'model_id') else 'unknown',
                    'choices': [{
                        'index': 0,
                        'delta': {'content': token},
                        'finish_reason': None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                tokens_generated += 1
        else:
            # Fallback to non-streaming generation
            response = model.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            # Remove the prompt from the response if it's included
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            # Stream the response character by character
            for char in response:
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
        # Generate response using MLX
        response_text = model.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        # Remove the prompt from the response if it's included
        if response_text.startswith(prompt):
            response_text = response_text[len(prompt):].strip()
        
        # Count tokens (approximate - actual tokenizer would be better)
        prompt_tokens = len(model.tokenize(prompt)) if hasattr(model, 'tokenize') else len(prompt.split())
        completion_tokens = len(model.tokenize(response_text)) if hasattr(model, 'tokenize') else len(response_text.split())
        
        # Update metrics
        elapsed = (time.time() - start_time) * 1000
        metrics = app_state.get('metrics', {})
        metrics['tokens_generated'] = metrics.get('tokens_generated', 0) + completion_tokens
        
        # Update average latency
        total_requests = metrics.get('requests_total', 1)
        current_avg = metrics.get('average_latency_ms', 0)
        metrics['average_latency_ms'] = ((current_avg * (total_requests - 1)) + elapsed) / total_requests
        
        # Calculate tokens per second
        tokens_per_second = completion_tokens / (elapsed / 1000) if elapsed > 0 else 0
        metrics['average_tokens_per_second'] = tokens_per_second
        
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
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
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
    if not messages:
        return ""
    
    # Check if model has a specific chat template
    # For now, use a general format that works well with most models
    prompt_parts = []
    
    # Some models expect specific formatting
    system_message = None
    
    for message in messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        
        if role == 'system':
            system_message = content
        elif role == 'user':
            if system_message and len(prompt_parts) == 0:
                # Include system message before first user message
                prompt_parts.append(f"System: {system_message}\n")
            prompt_parts.append(f"User: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Assistant: {content}")
    
    # Add the assistant prompt
    if prompt_parts:
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
    model_name = data.get('model', 'text-embedding-ada-002')
    input_text = data.get('input', '')
    
    if isinstance(input_text, str):
        inputs = [input_text]
    else:
        inputs = input_text
    
    # For now, MLX models don't have built-in embedding generation
    # This would need a separate embedding model or extraction from hidden states
    # Return a proper error message
    
    return jsonify({
        'error': {
            'message': 'Embeddings endpoint not yet implemented. Please use a dedicated embedding model.',
            'type': 'not_implemented',
            'code': 501
        }
    }), 501