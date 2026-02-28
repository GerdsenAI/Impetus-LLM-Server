"""
OpenAI-compatible API endpoints for VS Code integration
"""

import json
import time
import uuid
from collections.abc import Generator

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from loguru import logger

from ..config.settings import settings
from ..schemas.openai_schemas import (
    ChatCompletionRequest,
    ChatMessage,
    EmbeddingRequest,
)
from ..utils.validation import validate_json

bp = Blueprint('openai_api', __name__)


def verify_api_key():
    """Verify API key if configured"""
    if not settings.server.api_key:
        # Generate a secure API key on first run
        import secrets
        default_key = f"impetus-{secrets.token_urlsafe(32)}"
        settings.server.api_key = default_key
        print(f"🔑 Generated API key: {default_key}")
        print("💡 Save this key for future API requests!")
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
@validate_json(ChatCompletionRequest)
def chat_completions(validated_data: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""

    # Extract validated parameters with sensible defaults
    model = validated_data.model
    messages = validated_data.messages
    temperature = validated_data.temperature or 0.7  # Default temperature
    max_tokens = validated_data.max_tokens or 150    # Reasonable default to prevent excessive generation
    stream = validated_data.stream
    top_p = validated_data.top_p or 1.0              # Default top_p

    # KV cache parameters
    use_cache = validated_data.use_cache
    conversation_id = validated_data.conversation_id or validated_data.user or f'chat-{uuid.uuid4().hex[:8]}'

    # RAG context injection
    rag_sources = None
    if validated_data.use_rag:
        from ..services.rag_pipeline import build_rag_context

        user_query = messages[-1].content if messages else ""
        context_str, rag_sources = build_rag_context(
            query=user_query,
            n_results=validated_data.rag_n_results or 5,
            collection_name=validated_data.rag_collection,
        )
        if context_str:
            from ..schemas.openai_schemas import ChatMessage

            messages = [ChatMessage(role="system", content=context_str), *messages]
    elif validated_data.context_documents:
        from ..schemas.openai_schemas import ChatMessage

        context_str = "\n\n".join(
            f"[{i + 1}] {doc}" for i, doc in enumerate(validated_data.context_documents)
        )
        messages = [ChatMessage(role="system", content=f"Use this context:\n\n{context_str}"), *messages]

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
        response = Response(
            stream_with_context(
                generate_chat_stream(
                    loaded_models[model],
                    messages,
                    temperature,
                    max_tokens,
                    top_p,
                    app_state,
                    use_cache,
                    conversation_id
                )
            ),
            mimetype='text/event-stream'
        )
        # Ensure proper SSE headers
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        return response
    else:
        # Non-streaming response
        response = generate_chat_completion(
            loaded_models[model],
            messages,
            temperature,
            max_tokens,
            top_p,
            app_state,
            use_cache,
            conversation_id
        )
        if rag_sources:
            response["rag_sources"] = rag_sources
        return jsonify(response)


def generate_chat_stream(model, messages, temperature: float,
                        max_tokens: int, top_p: float, app_state: dict,
                        use_cache: bool = True, conversation_id: str = 'default') -> Generator:
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
                top_p=top_p,
                use_cache=use_cache,
                conversation_id=conversation_id
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
                top_p=top_p,
                use_cache=use_cache,
                conversation_id=conversation_id
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


def generate_chat_completion(model, messages, temperature: float,
                           max_tokens: int, top_p: float, app_state: dict,
                           use_cache: bool = True, conversation_id: str = 'default') -> dict:
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
            top_p=top_p,
            use_cache=use_cache,
            conversation_id=conversation_id
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


def convert_messages_to_prompt(messages) -> str:
    """Convert OpenAI message format to a single prompt string"""
    if not messages:
        return ""

    # Check if model has a specific chat template
    # For now, use a general format that works well with most models
    prompt_parts = []

    # Some models expect specific formatting
    system_message = None

    for message in messages:
        # Handle both dict and ChatMessage objects
        if hasattr(message, 'role'):
            role = message.role
            content = message.content
        else:
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
    data = request.get_json() or {}

    validated = ChatCompletionRequest(
        model=data.get('model', settings.model.default_model),
        messages=[ChatMessage(role='user', content=data.get('prompt', ''))],
        temperature=data.get('temperature', settings.inference.temperature),
        max_tokens=data.get('max_tokens', settings.inference.max_tokens),
        stream=data.get('stream', False),
    )
    return chat_completions(validated)


@bp.route('/embeddings', methods=['POST'])
@validate_json(EmbeddingRequest)
def embeddings(validated_data: EmbeddingRequest):
    """OpenAI-compatible embeddings endpoint powered by hybrid ANE/GPU compute"""
    from ..model_loaders.compute_dispatcher import compute_dispatcher

    # Normalise input to list
    texts = validated_data.input if isinstance(validated_data.input, list) else [validated_data.input]
    model_name = validated_data.model

    try:
        vectors = compute_dispatcher.embed(texts, model_name)
    except Exception as e:
        error_msg = str(e)
        if "Unknown embedding model" in error_msg:
            return jsonify({
                'error': {'message': error_msg, 'type': 'invalid_request_error', 'code': 'model_not_found'}
            }), 404
        if "No embedding backend" in error_msg:
            return jsonify({
                'error': {'message': error_msg, 'type': 'server_error', 'code': 'no_backend'}
            }), 503
        logger.error(f"Embedding error: {e}")
        return jsonify({
            'error': {'message': f'Embedding inference failed: {error_msg}', 'type': 'server_error'}
        }), 500

    # Optional dimension truncation
    if validated_data.dimensions is not None:
        dim = validated_data.dimensions
        vectors = [v[:dim] for v in vectors]

    # Optional base64 encoding
    if validated_data.encoding_format == "base64":
        import base64
        import struct
        encoded_vectors = []
        for v in vectors:
            raw = struct.pack(f'{len(v)}f', *v)
            encoded_vectors.append(base64.b64encode(raw).decode('ascii'))
        data_list = [
            {'object': 'embedding', 'embedding': enc, 'index': i}
            for i, enc in enumerate(encoded_vectors)
        ]
    else:
        data_list = [
            {'object': 'embedding', 'embedding': v, 'index': i}
            for i, v in enumerate(vectors)
        ]

    # Approximate token count
    total_tokens = sum(len(t.split()) for t in texts)

    return jsonify({
        'object': 'list',
        'data': data_list,
        'model': model_name,
        'usage': {
            'prompt_tokens': total_tokens,
            'total_tokens': total_tokens,
        }
    })
