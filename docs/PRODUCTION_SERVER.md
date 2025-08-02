# Production Server Configuration

This guide covers deploying Impetus LLM Server with Gunicorn for production use.

## Quick Start

### 1. Install Production Dependencies
```bash
cd gerdsen_ai_server
pip install -r requirements_production.txt
```

### 2. Start Production Server
```bash
# Using the startup script
./start_production.sh

# Or directly with Gunicorn
gunicorn --config gunicorn_config.py wsgi:application
```

## Configuration Options

### Environment Variables
- `IMPETUS_ENVIRONMENT=production` - Enable production mode
- `IMPETUS_HOST=0.0.0.0` - Bind address (default: 0.0.0.0)
- `IMPETUS_PORT=8080` - Port number (default: 8080)
- `IMPETUS_WORKERS=auto` - Number of workers (default: auto-detect)
- `IMPETUS_LOG_LEVEL=info` - Log level (default: info)
- `IMPETUS_MAX_WORKER_MEMORY_MB=4096` - Max memory per worker

### Gunicorn Configuration
The `gunicorn_config.py` file includes:
- **Workers**: Auto-configured based on CPU cores (max 4 for ML workloads)
- **Worker Class**: `eventlet` for WebSocket support
- **Timeout**: 300 seconds for long-running inference
- **Memory Monitoring**: Auto-restart workers exceeding memory limits
- **Graceful Shutdown**: 120 seconds graceful timeout

## Deployment Methods

### 1. Systemd (Linux)
```bash
# Copy service file
sudo cp service/impetus.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable impetus
sudo systemctl start impetus

# Check status
sudo systemctl status impetus
```

### 2. Launchd (macOS)
```bash
# Copy plist file
sudo cp service/com.gerdsenai.impetus.plist /Library/LaunchDaemons/

# Load service
sudo launchctl load /Library/LaunchDaemons/com.gerdsenai.impetus.plist

# Check status
sudo launchctl list | grep impetus
```

### 3. Docker
```bash
# Build image
docker build -t impetus-llm-server .

# Run container
docker run -d \
  --name impetus \
  -p 8080:8080 \
  -v ./models:/models \
  -e IMPETUS_ENVIRONMENT=production \
  impetus-llm-server
```

## Reverse Proxy Setup

### Nginx Configuration
```nginx
upstream impetus_backend {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Proxy settings
    location / {
        proxy_pass http://impetus_backend;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running inference
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://impetus_backend/api/health/status;
        access_log off;
    }
}
```

## Performance Tuning

### 1. Worker Configuration
```bash
# For high concurrency (API usage)
export IMPETUS_WORKERS=4

# For large models (limited memory)
export IMPETUS_WORKERS=2
export IMPETUS_MAX_WORKER_MEMORY_MB=8192
```

### 2. System Limits
```bash
# Increase file descriptors
ulimit -n 65536

# For persistent settings, add to /etc/security/limits.conf:
* soft nofile 65536
* hard nofile 65536
```

### 3. Memory Management
- Workers auto-restart when exceeding memory limits
- Configure `IMPETUS_MAX_WORKER_MEMORY_MB` based on your system
- Use `preload_app = True` in gunicorn_config.py for better memory sharing

## Monitoring

### Health Endpoints
- `/api/health/status` - Basic health check
- `/api/health/ready` - Readiness probe
- `/api/hardware/metrics` - System metrics

### Logs
- **Systemd**: `journalctl -u impetus -f`
- **Docker**: `docker logs -f impetus`
- **Manual**: Check stdout/stderr or configured log files

### Metrics
The server provides Prometheus-compatible metrics at `/metrics` endpoint (when enabled).

## Security Considerations

1. **API Key**: Always set `IMPETUS_API_KEY` in production
2. **CORS**: Configure `IMPETUS_CORS_ORIGINS` appropriately
3. **SSL/TLS**: Use reverse proxy for SSL termination
4. **Firewall**: Restrict direct access to Gunicorn port
5. **Updates**: Keep dependencies updated

## Troubleshooting

### Common Issues

1. **Worker Memory Errors**
   - Reduce worker count
   - Increase `IMPETUS_MAX_WORKER_MEMORY_MB`
   - Check model sizes

2. **WebSocket Connection Failed**
   - Ensure `eventlet` worker class is used
   - Check reverse proxy WebSocket configuration
   - Verify CORS settings

3. **Slow Performance**
   - Check worker count vs CPU cores
   - Monitor memory usage
   - Review model loading strategy

### Debug Mode
```bash
# Enable debug logging
export IMPETUS_LOG_LEVEL=debug
gunicorn --config gunicorn_config.py --log-level debug wsgi:application
```

## Best Practices

1. **Load Balancing**: Use multiple instances behind a load balancer
2. **Model Persistence**: Configure model cache directory
3. **Monitoring**: Set up alerts for memory/CPU usage
4. **Backups**: Regular backups of models and configuration
5. **Updates**: Test updates in staging before production