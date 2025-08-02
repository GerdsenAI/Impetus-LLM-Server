# Impetus LLM Server API Documentation

This document provides comprehensive API documentation for Impetus LLM Server, including endpoint details, request/response schemas, and usage examples.

## API Overview

Impetus LLM Server provides a RESTful API with OpenAI-compatible endpoints for seamless integration with existing AI tools and applications.

### Base URL
- **Development**: `http://localhost:8080`
- **Production**: `https://your-domain.com`

### Authentication
All API endpoints require Bearer token authentication:

```http
Authorization: Bearer your-api-key
```

### Interactive Documentation
- **Swagger UI**: Available at `/docs` or `/api/docs`
- **OpenAPI Spec**: Available at `/api/docs/openapi.json`

## OpenAI-Compatible Endpoints

### List Models
Get available models that can be used with chat completions.

```http
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
      "object": "model",
      "created": 1699553600,
      "owned_by": "impetus",
      "permission": [],
      "root": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
      "parent": null
    }
  ]
}
```

### Chat Completions
Create a chat completion with streaming support.

```http
POST /v1/chat/completions
```

**Request Body:**
```json
{
  "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "messages": [
    {
      "role": "user", 
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false,
  "top_p": 1.0,
  "conversation_id": "chat-12345",
  "use_cache": true
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699553600,
  "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 16,
    "total_tokens": 26
  },
  "conversation_id": "chat-12345",
  "performance_metrics": {
    "inference_time_ms": 1250,
    "tokens_per_second": 12.8
  }
}
```

### Text Completions
Create a text completion (legacy endpoint).

```http
POST /v1/completions
```

**Request Body:**
```json
{
  "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "prompt": "The future of artificial intelligence is",
  "max_tokens": 100,
  "temperature": 0.7,
  "top_p": 1.0,
  "n": 1,
  "stream": false
}
```

## Model Management Endpoints

### Discover Models
Browse available models for download with performance estimates.

```http
GET /api/models/discover
```

**Query Parameters:**
- `category` (optional): Filter by model category
- `size_limit_gb` (optional): Maximum model size in GB

**Response:**
```json
{
  "models": [
    {
      "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
      "name": "Mistral 7B Instruct (4-bit)",
      "description": "Fast and efficient instruction-following model",
      "size_gb": 4.1,
      "parameters": "7B",
      "architecture": "Mistral",
      "quantization": "4-bit",
      "performance_estimate": {
        "tokens_per_second_m1": 35.2,
        "tokens_per_second_m2": 52.8,
        "tokens_per_second_m3": 75.4
      },
      "recommended_memory_gb": 8.0,
      "tags": ["instruct", "fast", "efficient"],
      "is_downloaded": false
    }
  ],
  "total_models": 1,
  "categories": ["instruct", "base", "code"],
  "hardware_compatibility": {
    "mlx_support": true,
    "metal_support": true
  }
}
```

### Download Model
Download a model from HuggingFace with optional auto-loading.

```http
POST /api/models/download
```

**Request Body:**
```json
{
  "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "auto_load": true,
  "force_download": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Model download started",
  "data": {
    "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "download_id": "download-abc123",
    "estimated_size_gb": 4.1
  }
}
```

### List Loaded Models
Get currently loaded models with their status and metrics.

```http
GET /api/models/list
```

**Response:**
```json
{
  "models": [
    {
      "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
      "status": "loaded",
      "size_mb": 4198.4,
      "memory_usage_mb": 4250.1,
      "load_time_seconds": 3.2,
      "last_used": "2025-01-01T12:30:00Z",
      "format": "MLX",
      "architecture": "Mistral",
      "parameters": "7B",
      "quantization": "4-bit"
    }
  ],
  "total_memory_usage_mb": 4250.1,
  "available_memory_mb": 12288.0
}
```

### Load Model
Load a model into memory for inference.

```http
POST /api/models/load
```

**Request Body:**
```json
{
  "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "force_reload": false
}
```

### Unload Model
Unload a model from memory to free resources.

```http
POST /api/models/unload
```

**Request Body:**
```json
{
  "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "force": false
}
```

### Benchmark Model
Run performance benchmarks on a loaded model.

```http
POST /api/models/benchmark/{model_id}
```

**Request Body:**
```json
{
  "num_samples": 10,
  "max_tokens": 100,
  "temperature": 0.7,
  "include_memory_test": true,
  "include_warmup": true
}
```

**Response:**
```json
{
  "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
  "timestamp": "2025-01-01T12:30:00Z",
  "tokens_per_second": 45.2,
  "first_token_latency_ms": 180.5,
  "total_tokens": 1000,
  "total_time_seconds": 22.1,
  "memory_usage_mb": 4250.1,
  "gpu_utilization_percent": 87.3,
  "samples": [
    {
      "tokens": 100,
      "time_seconds": 2.21,
      "tokens_per_second": 45.2
    }
  ]
}
```

## Hardware Monitoring Endpoints

### Hardware Information
Get detailed information about the system hardware.

```http
GET /api/hardware/info
```

**Response:**
```json
{
  "chip_type": "M3 Pro",
  "chip_variant": "Pro",
  "cpu": {
    "brand": "Apple M3 Pro",
    "architecture": "arm64",
    "performance_cores": 8,
    "efficiency_cores": 4,
    "total_cores": 12,
    "base_frequency_ghz": 3.2,
    "max_frequency_ghz": 4.0
  },
  "memory": {
    "total_gb": 18.0,
    "available_gb": 12.5,
    "used_gb": 5.5,
    "usage_percent": 30.6
  },
  "gpu": {
    "name": "Apple M3 Pro",
    "vendor": "Apple",
    "memory_gb": 18.0,
    "compute_units": 14,
    "metal_support": true,
    "unified_memory": true
  },
  "thermal": {
    "cpu_temperature_c": 45.2,
    "thermal_state": "nominal",
    "throttling": false
  },
  "os_version": "macOS 14.2",
  "mlx_version": "0.16.1",
  "python_version": "3.11.7"
}
```

### Real-time Metrics
Get current system performance metrics.

```http
GET /api/hardware/metrics
```

**Response:**
```json
{
  "timestamp": "2025-01-01T12:30:00Z",
  "cpu": {
    "usage_percent": 45.2,
    "performance_core_usage": [50.1, 48.3, 52.7, 46.9],
    "efficiency_core_usage": [20.1, 18.5, 22.3, 19.8],
    "frequency_ghz": [3.8, 3.7, 3.9, 3.6],
    "load_average": [2.1, 1.8, 1.5]
  },
  "memory": {
    "total_gb": 18.0,
    "available_gb": 12.5,
    "used_gb": 5.5,
    "usage_percent": 30.6
  },
  "thermal": {
    "cpu_temperature_c": 45.2,
    "thermal_state": "nominal",
    "throttling": false
  },
  "metal": {
    "gpu_utilization_percent": 75.3,
    "memory_used_mb": 2048.0,
    "memory_total_mb": 18432.0,
    "memory_usage_percent": 11.1,
    "compute_units_active": 12
  },
  "process": {
    "pid": 12345,
    "cpu_percent": 25.3,
    "memory_mb": 1024.5,
    "memory_percent": 5.7,
    "threads": 8,
    "file_descriptors": 45,
    "uptime_seconds": 3600.5
  }
}
```

### Performance Mode
Set system performance mode for optimal inference.

```http
POST /api/hardware/performance-mode
```

**Request Body:**
```json
{
  "mode": "performance"
}
```

**Options:**
- `efficiency`: Lower power consumption, moderate performance
- `balanced`: Balance between power and performance (default)
- `performance`: Maximum performance, higher power consumption

## Health Check Endpoints

### Basic Health Check
Simple health check for monitoring systems.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600.5
}
```

### Readiness Probe
Kubernetes-compatible readiness probe.

```http
GET /api/health/ready
```

**Response:**
```json
{
  "ready": true,
  "timestamp": "2025-01-01T12:30:00Z",
  "checks": {
    "memory_available": true,
    "models_loaded": true,
    "mlx_available": true
  },
  "message": "Ready"
}
```

### Liveness Probe
Kubernetes-compatible liveness probe.

```http
GET /api/health/live
```

**Response:**
```json
{
  "alive": true,
  "timestamp": "2025-01-01T12:30:00Z",
  "uptime_seconds": 3600.5,
  "last_heartbeat": "2025-01-01T12:30:00Z"
}
```

### Detailed Status
Comprehensive health status with component breakdown.

```http
GET /api/health/status
```

### Prometheus Metrics
Prometheus-compatible metrics for monitoring.

```http
GET /api/health/metrics
```

**Response Format:** Prometheus text format
```
# HELP impetus_requests_total Total number of requests
# TYPE impetus_requests_total counter
impetus_requests_total 1234

# HELP impetus_tokens_generated_total Total tokens generated
# TYPE impetus_tokens_generated_total counter
impetus_tokens_generated_total 56789

# HELP impetus_cpu_usage_percent CPU usage percentage
# TYPE impetus_cpu_usage_percent gauge
impetus_cpu_usage_percent 45.2
```

## Error Handling

All endpoints return consistent error responses with appropriate HTTP status codes.

### Error Response Format
```json
{
  "error": "Error description",
  "type": "error_type",
  "details": ["Additional error details"],
  "timestamp": "2025-01-01T12:30:00Z"
}
```

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable (unhealthy)

## Rate Limiting

Production deployments include rate limiting:
- **Default**: 100 requests per minute per IP
- **Burst**: Up to 10 requests per second
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## WebSocket Events

Real-time updates via WebSocket connection at `/socket.io/`:

### Events
- `model_status` - Model loading/unloading updates
- `hardware_metrics` - Real-time hardware metrics
- `download_progress` - Model download progress
- `inference_stats` - Inference performance statistics

### Example Client (JavaScript)
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8080');

socket.on('hardware_metrics', (data) => {
  console.log('Hardware metrics:', data);
});

socket.on('model_status', (data) => {
  console.log('Model status update:', data);
});
```

## SDK Integration

### Python Client
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your-api-key"
)

response = client.chat.completions.create(
    model="mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

### cURL Examples
```bash
# List models
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8080/v1/models

# Chat completion
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
       "messages": [{"role": "user", "content": "Hello!"}],
       "temperature": 0.7,
       "max_tokens": 100
     }' \
     http://localhost:8080/v1/chat/completions

# Download model
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
       "auto_load": true
     }' \
     http://localhost:8080/api/models/download
```

## Performance Optimization

### Tips for Best Performance
1. **Model Selection**: Choose quantized models (4-bit) for faster inference
2. **Batch Size**: Use appropriate batch sizes based on your hardware
3. **KV Cache**: Enable conversation caching for multi-turn chats
4. **Warmup**: Use model warmup to eliminate cold start latency
5. **Memory Management**: Monitor memory usage and unload unused models

### Hardware Recommendations
- **M1/M2**: 8GB+ RAM, use 4-bit models
- **M3/M4**: 16GB+ RAM, can handle larger models
- **Pro/Max/Ultra**: Best performance with multiple concurrent requests