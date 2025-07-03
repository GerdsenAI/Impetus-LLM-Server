# VS Code Integration Guide

This guide explains how to integrate GerdsenAI MLX Manager with VS Code extensions like Cline, CodeGPT, and other AI coding assistants.

## Overview

GerdsenAI MLX Manager provides OpenAI-compatible API endpoints that allow VS Code extensions to use local Apple Silicon hardware for AI assistance instead of cloud services.

## Benefits

- **Privacy**: All processing happens locally on your Mac
- **Performance**: Optimized for Apple Silicon (M1/M2/M3/M4)
- **Cost**: No API usage fees
- **Offline**: Works without internet connection
- **Customization**: Full control over models and responses

## Quick Setup

### 1. Start GerdsenAI MLX Manager

```bash
# Start the service
python gerdsen_ai_launcher.py --mode service

# Or start server only
python gerdsen_ai_launcher.py --mode server-only --port 5000
```

The server will be available at: `http://localhost:5000`

### 2. Get API Key

For development, you can use the default API key:
```
sk-dev-gerdsen-ai-local-development-key
```

Or create a custom key:
```bash
curl -X POST http://localhost:5000/v1/auth/keys \
  -H "Authorization: Bearer gerdsen-ai-master-key-2025" \
  -H "Content-Type: application/json" \
  -d '{"key": "sk-your-custom-key-here"}'
```

### 3. Test the API

```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Authorization: Bearer sk-dev-gerdsen-ai-local-development-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gerdsen-mlx-default",
    "messages": [
      {"role": "user", "content": "Hello, can you help me with Python code?"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

## VS Code Extension Configuration

### Cline (Claude Dev)

1. Install the Cline extension from VS Code marketplace
2. Open VS Code settings (Cmd+,)
3. Search for "Cline"
4. Configure the following settings:

```json
{
  "cline.apiProvider": "openai",
  "cline.openaiApiKey": "sk-dev-gerdsen-ai-local-development-key",
  "cline.openaiBaseUrl": "http://localhost:5000",
  "cline.openaiModel": "gerdsen-mlx-default"
}
```

### CodeGPT

1. Install CodeGPT extension
2. Open Command Palette (Cmd+Shift+P)
3. Run "CodeGPT: Set API Key"
4. Enter: `sk-dev-gerdsen-ai-local-development-key`
5. Configure base URL in settings:

```json
{
  "codegpt.apiKey": "sk-dev-gerdsen-ai-local-development-key",
  "codegpt.apiUrl": "http://localhost:5000",
  "codegpt.model": "gerdsen-mlx-default"
}
```

### Continue.dev

1. Install Continue extension
2. Open `~/.continue/config.json`
3. Add configuration:

```json
{
  "models": [
    {
      "title": "GerdsenAI MLX",
      "provider": "openai",
      "model": "gerdsen-mlx-default",
      "apiKey": "sk-dev-gerdsen-ai-local-development-key",
      "apiBase": "http://localhost:5000"
    }
  ]
}
```

### GitHub Copilot Chat (Custom)

For extensions that support custom OpenAI endpoints:

```json
{
  "github.copilot.advanced": {
    "debug.overrideEngine": "gerdsen-mlx-default",
    "debug.overrideProxyUrl": "http://localhost:5000"
  }
}
```

## Available Models

GerdsenAI MLX Manager provides several model endpoints:

- `gerdsen-mlx-default` - General purpose model
- `gerdsen-mlx-code` - Optimized for code generation
- `gerdsen-mlx-chat` - Optimized for conversational AI

## API Endpoints

### Chat Completions
```
POST /v1/chat/completions
```

### Legacy Completions
```
POST /v1/completions
```

### Models List
```
GET /v1/models
```

### Embeddings
```
POST /v1/embeddings
```

### Authentication
```
POST /v1/auth/validate
GET /v1/auth/keys (admin only)
POST /v1/auth/keys (admin only)
```

## Example Requests

### Chat Completion
```javascript
const response = await fetch('http://localhost:5000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-dev-gerdsen-ai-local-development-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gerdsen-mlx-default',
    messages: [
      { role: 'system', content: 'You are a helpful coding assistant.' },
      { role: 'user', content: 'Write a Python function to calculate fibonacci numbers.' }
    ],
    max_tokens: 500,
    temperature: 0.7,
    stream: false
  })
});
```

### Streaming Chat
```javascript
const response = await fetch('http://localhost:5000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-dev-gerdsen-ai-local-development-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gerdsen-mlx-default',
    messages: [
      { role: 'user', content: 'Explain how Apple Silicon optimizes ML workloads.' }
    ],
    stream: true
  })
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = new TextDecoder().decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') return;
      
      try {
        const parsed = JSON.parse(data);
        const content = parsed.choices[0]?.delta?.content;
        if (content) {
          process.stdout.write(content);
        }
      } catch (e) {
        // Skip invalid JSON
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure GerdsenAI MLX Manager is running
   - Check the port (default: 5000)
   - Verify firewall settings

2. **Authentication Failed**
   - Check API key format
   - Ensure key is properly configured
   - Try the default development key

3. **Model Not Found**
   - Use one of the available models
   - Check model name spelling
   - Verify server logs

4. **Slow Responses**
   - Check Apple Silicon optimization
   - Monitor system resources
   - Consider adjusting max_tokens

### Debug Mode

Enable debug logging:
```bash
python gerdsen_ai_launcher.py --mode server-only --log-level DEBUG
```

### Health Check

Test server health:
```bash
curl http://localhost:5000/api/health
```

## Performance Optimization

### Apple Silicon Optimization

GerdsenAI automatically detects and optimizes for your Apple Silicon chip:

- **M1**: 8-core CPU, 8-core GPU, 16-core Neural Engine
- **M2**: 8-core CPU, 10-core GPU, 16-core Neural Engine
- **M3**: 8-core CPU, 10-core GPU, 16-core Neural Engine
- **M4**: 10-core CPU, 10-core GPU, 16-core Neural Engine

### Memory Management

The system automatically manages memory allocation:
- Neural Engine: Primary ML acceleration
- GPU: Secondary compute for large models
- CPU: Fallback and coordination

### Temperature Monitoring

Monitor system temperature to prevent throttling:
```bash
curl http://localhost:5000/api/hardware/real-time-metrics
```

## Security Considerations

### Local Network Only

By default, the server only accepts connections from localhost. To allow network access:

```bash
# WARNING: Only use on trusted networks
python gerdsen_ai_launcher.py --mode server-only --host 0.0.0.0
```

### API Key Management

- Use unique API keys for different applications
- Rotate keys regularly
- Never commit keys to version control
- Use environment variables for production

### Rate Limiting

The server includes built-in rate limiting:
- Default: 100 requests per hour
- Premium: 1000 requests per hour (configurable)

## Advanced Configuration

### Custom Models

To add custom MLX models:

1. Place model files in the models directory
2. Update the model registry
3. Restart the server

### Environment Variables

```bash
export OPENAI_API_KEYS="sk-key1,sk-key2,sk-key3"
export OPENAI_MASTER_KEY="your-master-key"
export GERDSEN_AI_PORT=5000
export GERDSEN_AI_LOG_LEVEL=INFO
```

### Production Deployment

For production use:

1. Use proper API key management
2. Enable HTTPS with reverse proxy
3. Configure proper logging
4. Set up monitoring and alerts
5. Use systemd or launchd for service management

## Support

For issues and questions:

1. Check the server logs
2. Review this documentation
3. Test with curl commands
4. Check VS Code extension documentation
5. Report issues with detailed logs

## Examples Repository

Find more examples and configurations at:
- `/docs/examples/vscode/`
- `/docs/examples/api/`
- `/docs/examples/integrations/`

