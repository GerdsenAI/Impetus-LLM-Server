# API Reference

GerdsenAI MLX Manager Enhanced provides a comprehensive REST API with OpenAI compatibility for seamless integration with VS Code extensions and other AI tools.

## Base URL

```
http://localhost:8080
```

## Authentication

All API endpoints support optional API key authentication via the `Authorization` header:

```http
Authorization: Bearer gerdsen-ai-local-key
```

Default API key: `gerdsen-ai-local-key` (configurable in settings)

## OpenAI-Compatible Endpoints

These endpoints provide full compatibility with OpenAI's API specification, enabling integration with VS Code extensions like Cline, Continue, and others.

### List Models

Get a list of available models.

```http
GET /v1/models
```

#### Response
```json
{
  "object": "list",
  "data": [
    {
      "id": "gerdsen-ai-optimized",
      "object": "model",
      "created": 1703980800,
      "owned_by": "gerdsen-ai",
      "permission": [],
      "root": "gerdsen-ai-optimized",
      "parent": null
    }
  ]
}
```

### Chat Completions

Generate chat completions with support for streaming.

```http
POST /v1/chat/completions
```

#### Request Body
```json
{
  "model": "gerdsen-ai-optimized",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user", 
      "content": "Write a Python function to calculate fibonacci numbers."
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.7,
  "stream": false
}
```

#### Response (Non-streaming)
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1703980800,
  "model": "gerdsen-ai-optimized",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Here's a Python function to calculate Fibonacci numbers:\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  }
}
```

#### Response (Streaming)
When `stream: true`, responses are sent as Server-Sent Events:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1703980800,"model":"gerdsen-ai-optimized","choices":[{"index":0,"delta":{"role":"assistant","content":"Here's"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1703980800,"model":"gerdsen-ai-optimized","choices":[{"index":0,"delta":{"content":" a"},"finish_reason":null}]}

data: [DONE]
```

### Text Completions

Generate text completions (legacy format).

```http
POST /v1/completions
```

#### Request Body
```json
{
  "model": "gerdsen-ai-optimized",
  "prompt": "Write a Python function to",
  "max_tokens": 100,
  "temperature": 0.7,
  "stream": false
}
```

#### Response
```json
{
  "id": "cmpl-123",
  "object": "text_completion",
  "created": 1703980800,
  "model": "gerdsen-ai-optimized",
  "choices": [
    {
      "text": " calculate the factorial of a number:\n\n```python\ndef factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    return n * factorial(n - 1)\n```",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 45,
    "total_tokens": 50
  }
}
```

### Embeddings

Generate embeddings for text input.

```http
POST /v1/embeddings
```

#### Request Body
```json
{
  "model": "gerdsen-ai-embeddings",
  "input": "The quick brown fox jumps over the lazy dog",
  "encoding_format": "float"
}
```

#### Response
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, 0.3, ...],
      "index": 0
    }
  ],
  "model": "gerdsen-ai-embeddings",
  "usage": {
    "prompt_tokens": 9,
    "total_tokens": 9
  }
}
```

## Hardware Monitoring Endpoints

These endpoints provide detailed information about Apple Silicon hardware and real-time performance metrics.

### Hardware Information

Get comprehensive hardware information.

```http
GET /api/hardware/info
```

#### Response
```json
{
  "chip_name": "M4 Pro",
  "chip_variant": "Pro",
  "architecture": "arm64",
  "process_node": "3nm",
  "performance_cores": 10,
  "efficiency_cores": 4,
  "total_cores": 14,
  "gpu_cores": 20,
  "neural_engine_cores": 16,
  "neural_engine_tops": 38.0,
  "memory_gb": 24,
  "memory_bandwidth_gbps": 273,
  "memory_type": "Unified",
  "capabilities": [
    "apple_silicon",
    "macos",
    "cpu_monitoring",
    "memory_monitoring",
    "thermal_monitoring",
    "performance_optimization"
  ]
}
```

### Real-time Metrics

Get current system performance metrics.

```http
GET /api/hardware/metrics
```

#### Response
```json
{
  "timestamp": 1703980800.123,
  "cpu": {
    "usage_percent_total": 25.5,
    "usage_percent_per_core": [30, 25, 20, 15, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    "performance_cores_usage": [30, 25, 20, 15, 10, 5, 0, 0, 0, 0],
    "efficiency_cores_usage": [0, 0, 0, 0],
    "frequency_current_mhz": 3200,
    "load_average": [1.5, 1.2, 1.0],
    "temperature_celsius": 45.2
  },
  "memory": {
    "total_gb": 24.0,
    "used_gb": 12.5,
    "available_gb": 11.5,
    "usage_percent": 52.1,
    "pressure": "normal",
    "swap_used_gb": 0.0
  },
  "gpu": {
    "cores": 20,
    "utilization_percent": 15.3,
    "memory_gb": 18.0,
    "memory_used_gb": 2.1,
    "metal_support": true
  },
  "neural_engine": {
    "cores": 16,
    "tops": 38.0,
    "utilization_percent": 5.2,
    "framework_support": {
      "coreml": {"available": true},
      "mlx": {"available": true}
    }
  },
  "thermal": {
    "state": "normal",
    "cpu_temperature": 45.2,
    "throttling": false
  },
  "power": {
    "source": "ac_power",
    "battery_percent": 85,
    "estimated_watts": 15.2
  }
}
```

### Optimization Recommendations

Get performance optimization recommendations.

```http
GET /api/hardware/optimization
```

#### Response
```json
{
  "recommendations": [
    {
      "category": "performance",
      "priority": "medium",
      "title": "Enable Neural Engine Acceleration",
      "description": "Your Neural Engine is underutilized",
      "actions": [
        "Use Core ML for machine learning tasks",
        "Enable MLX for local AI processing"
      ]
    }
  ],
  "current_optimization": {
    "auto_optimize": true,
    "thermal_management": true,
    "performance_mode": "balanced"
  },
  "performance_score": 85
}
```

## Model Management Endpoints

These endpoints handle model loading, optimization, and management.

### List Models

Get information about loaded models.

```http
GET /api/models/list
```

#### Response
```json
{
  "models": [
    {
      "id": "gerdsen-ai-optimized",
      "name": "GerdsenAI Optimized Model",
      "format": "mlx",
      "size_mb": 1024,
      "optimization_level": "high",
      "compute_device": "neural_engine",
      "loaded": true,
      "performance_score": 92
    }
  ],
  "total_models": 1,
  "memory_usage_mb": 1024
}
```

### Upload Model

Upload and optimize a new model.

```http
POST /api/models/upload
Content-Type: multipart/form-data
```

#### Request Body
```
model_file: [binary file data]
optimization_level: "balanced"
compute_device: "auto"
```

#### Response
```json
{
  "model_id": "custom-model-123",
  "status": "uploaded",
  "optimization_applied": true,
  "performance_improvement": 25.5,
  "size_reduction": 40.2
}
```

### Optimize Model

Optimize an existing model for Apple Silicon.

```http
POST /api/models/optimize
```

#### Request Body
```json
{
  "model_id": "custom-model-123",
  "optimization_strategy": "neural_engine",
  "quantization": "int8",
  "target_device": "m4_pro"
}
```

#### Response
```json
{
  "model_id": "custom-model-123",
  "optimization_applied": true,
  "performance_improvement": 35.2,
  "memory_reduction": 50.1,
  "optimizations": [
    "quantization_int8",
    "neural_engine_acceleration",
    "memory_layout_optimization"
  ]
}
```

## WebSocket Endpoints

Real-time data streaming via WebSocket connections.

### Real-time Metrics Stream

Connect to receive real-time system metrics.

```
ws://localhost:8080/ws/metrics
```

#### Message Format
```json
{
  "type": "metrics_update",
  "timestamp": 1703980800.123,
  "data": {
    "cpu_usage": 25.5,
    "memory_usage": 52.1,
    "gpu_usage": 15.3,
    "neural_engine_usage": 5.2,
    "thermal_state": "normal",
    "power_source": "ac_power"
  }
}
```

### Model Status Stream

Monitor model loading and optimization progress.

```
ws://localhost:8080/ws/models
```

#### Message Format
```json
{
  "type": "model_status",
  "model_id": "custom-model-123",
  "status": "optimizing",
  "progress": 65.5,
  "eta_seconds": 45
}
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages.

### Error Response Format
```json
{
  "error": {
    "type": "invalid_request",
    "message": "The model 'invalid-model' does not exist",
    "code": "model_not_found",
    "details": {
      "available_models": ["gerdsen-ai-optimized"]
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | `invalid_request` | Malformed request or invalid parameters |
| 401 | `authentication_error` | Invalid or missing API key |
| 404 | `not_found` | Resource not found |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |
| 503 | `service_unavailable` | Service temporarily unavailable |

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Default limit**: 60 requests per minute per API key
- **Burst limit**: 10 requests per second
- **Model operations**: 5 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1703980860
```

## VS Code Extension Configuration

### Cline Configuration
```json
{
  "cline.apiProvider": "openai",
  "cline.openai.baseUrl": "http://localhost:8080",
  "cline.openai.apiKey": "gerdsen-ai-local-key",
  "cline.openai.model": "gerdsen-ai-optimized",
  "cline.maxTokens": 4000,
  "cline.temperature": 0.7
}
```

### Continue Configuration
```json
{
  "models": [
    {
      "title": "GerdsenAI Local",
      "provider": "openai",
      "model": "gerdsen-ai-optimized",
      "apiBase": "http://localhost:8080",
      "apiKey": "gerdsen-ai-local-key"
    }
  ]
}
```

### CodeGPT Configuration
```json
{
  "codegpt.apiUrl": "http://localhost:8080",
  "codegpt.apiKey": "gerdsen-ai-local-key",
  "codegpt.model": "gerdsen-ai-optimized"
}
```

## SDK Examples

### Python SDK
```python
import requests

class GerdsenAIClient:
    def __init__(self, base_url="http://localhost:8080", api_key="gerdsen-ai-local-key"):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def chat_completion(self, messages, model="gerdsen-ai-optimized", **kwargs):
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json={
                "model": model,
                "messages": messages,
                **kwargs
            }
        )
        return response.json()
    
    def get_hardware_info(self):
        response = requests.get(
            f"{self.base_url}/api/hardware/info",
            headers=self.headers
        )
        return response.json()

# Usage
client = GerdsenAIClient()
response = client.chat_completion([
    {"role": "user", "content": "Hello, how are you?"}
])
print(response["choices"][0]["message"]["content"])
```

### JavaScript SDK
```javascript
class GerdsenAIClient {
    constructor(baseUrl = 'http://localhost:8080', apiKey = 'gerdsen-ai-local-key') {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async chatCompletion(messages, model = 'gerdsen-ai-optimized', options = {}) {
        const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                model,
                messages,
                ...options
            })
        });
        return response.json();
    }
    
    async getHardwareInfo() {
        const response = await fetch(`${this.baseUrl}/api/hardware/info`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const client = new GerdsenAIClient();
const response = await client.chatCompletion([
    { role: 'user', content: 'Hello, how are you?' }
]);
console.log(response.choices[0].message.content);
```

### cURL Examples

#### Chat Completion
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer gerdsen-ai-local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gerdsen-ai-optimized",
    "messages": [
      {"role": "user", "content": "Write a hello world program in Python"}
    ],
    "max_tokens": 100
  }'
```

#### Hardware Metrics
```bash
curl -X GET http://localhost:8080/api/hardware/metrics \
  -H "Authorization: Bearer gerdsen-ai-local-key"
```

#### Model Upload
```bash
curl -X POST http://localhost:8080/api/models/upload \
  -H "Authorization: Bearer gerdsen-ai-local-key" \
  -F "model_file=@my_model.mlx" \
  -F "optimization_level=balanced"
```

## Performance Optimization

### Best Practices

1. **Use Streaming**: Enable streaming for long responses to improve perceived performance
2. **Batch Requests**: Group multiple requests when possible
3. **Cache Results**: Implement client-side caching for repeated requests
4. **Monitor Metrics**: Use the metrics endpoints to monitor system performance
5. **Optimize Models**: Use the model optimization endpoints for better performance

### Performance Tuning

#### Request Parameters
- `max_tokens`: Limit response length for faster generation
- `temperature`: Lower values (0.1-0.3) for faster, more deterministic responses
- `stream`: Enable for immediate response start

#### System Configuration
- Enable auto-optimization in configuration
- Use appropriate performance mode (balanced/performance/efficiency)
- Monitor thermal state and adjust workload accordingly

---

**API Reference Complete! 🚀**

This comprehensive API enables seamless integration with VS Code extensions and provides full control over Apple Silicon optimization features.

