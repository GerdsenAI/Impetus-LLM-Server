#!/usr/bin/env python3
"""
Dummy Model Loader for Testing Purposes
"""

import time

def load_dummy_model(model_path: str):
    """Simulates loading a model with detailed metadata."""
    print(f"Simulating loading model from: {model_path}")
    time.sleep(1)  # Simulate time taken to load
    # Determine model format based on path or extension
    model_format = "mlx" if "mlx" in model_path.lower() or model_path.endswith('.mlx') else "coreml"
    # Simulate model size and parameters
    model_size_bytes = 1024 * 1024 * 1024 if model_format == "mlx" else 512 * 1024 * 1024  # 1GB for MLX, 512MB for CoreML
    model_parameters = 7000000000 if model_format == "mlx" else 3000000000  # 7B for MLX, 3B for CoreML
    return {
        "status": "loaded",
        "model_path": model_path,
        "format": model_format,
        "size_bytes": model_size_bytes,
        "parameters": model_parameters,
        "capabilities": ["chat", "completion"] if model_format == "mlx" else ["chat"],
        "requirements": {"memory_gb": 8 if model_format == "mlx" else 4, "compute": "gpu" if model_format == "mlx" else "neural_engine"},
        "optimization_hints": {"device": "gpu" if model_format == "mlx" else "neural_engine", "quantization": "int8"}
    }

def dummy_predict(input_data: dict) -> dict:
    """Simulates a model prediction."""
    if 'messages' in input_data:
        last_message = input_data['messages'][-1]['content']
        response_content = f"This is a dummy response to: '{last_message}'"
        return {
            'content': response_content,
            'prompt_tokens': len(last_message.split()),
            'completion_tokens': len(response_content.split()),
            'total_tokens': len(last_message.split()) + len(response_content.split())
        }
    elif 'prompt' in input_data:
        prompt = input_data['prompt']
        response_text = f"This is a dummy completion for the prompt: '{prompt}'"
        return {
            'text': response_text,
            'prompt_tokens': len(prompt.split()),
            'completion_tokens': len(response_text.split()),
            'total_tokens': len(prompt.split()) + len(response_text.split())
        }
    elif 'task' in input_data and input_data['task'] == 'embeddings':
        text_to_embed = input_data['input']
        return {
            'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
            'prompt_tokens': len(text_to_embed.split()),
            'total_tokens': len(text_to_embed.split())
        }
    return {"error": "Invalid input for dummy prediction"}
