# Production Deployment Guide

This guide covers deploying Impetus LLM Server in production environments with high availability, security, and performance.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Native Deployment](#native-deployment)
- [Load Balancing](#load-balancing)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Security Hardening](#security-hardening)
- [Performance Tuning](#performance-tuning)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **CPU**: 8+ cores (Apple Silicon recommended for optimal performance)
- **Memory**: 16GB+ RAM (32GB+ for large models)
- **Storage**: 100GB+ SSD for models and cache
- **Network**: 1Gbps+ connection for model downloads

### Software Dependencies
- Docker 20.10+ and Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- nginx 1.20+ (for reverse proxy)
- Python 3.11+ (for native deployment)

### Security Requirements
- Valid SSL certificates
- Firewall configuration
- Secure API key management
- Network segmentation

## Deployment Options

### 1. Docker Compose (Recommended for Small-Medium Scale)
- Easy setup and management
- Built-in service orchestration
- Automatic restarts and health checks
- Suitable for single-server deployments

### 2. Kubernetes (Enterprise/Large Scale)
- High availability and scalability
- Advanced networking and security
- Rolling updates and rollbacks
- Multi-node deployments

### 3. Native Installation (Maximum Performance)
- Direct hardware access
- Optimal Apple Silicon performance
- Custom system optimization
- Manual configuration required

## Docker Deployment

### Quick Start
```bash
# Clone repository
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f impetus-server
```

### Environment Configuration
Create `.env` file:
```bash
# API Configuration
IMPETUS_API_KEY=your-secure-api-key-here
IMPETUS_ENVIRONMENT=production
IMPETUS_LOG_LEVEL=info

# Performance Settings
IMPETUS_MAX_LOADED_MODELS=2
IMPETUS_PERFORMANCE_MODE=performance
IMPETUS_MAX_WORKER_MEMORY_MB=8192

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password
```

### Service Configuration

#### Core Services
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  impetus-server:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 16G
          cpus: '8.0'
    environment:
      - IMPETUS_WORKERS=4
```

#### SSL Certificate Setup
```bash
# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=CA/L=SF/O=YourOrg/CN=your-domain.com"

# Or copy your certificates
cp /path/to/your/cert.pem ssl/
cp /path/to/your/key.pem ssl/
```

### Production Docker Configuration

#### Multi-Stage Build Optimization
```dockerfile
# Dockerfile.production
FROM node:18-alpine AS frontend-builder
# ... frontend build steps

FROM python:3.11-slim AS production
# ... optimized production build

# Security hardening
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -r -s /bin/false impetus

USER impetus
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/health/live || exit 1
```

## Kubernetes Deployment

### Namespace Setup
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: impetus-system
  labels:
    name: impetus-system
```

### ConfigMap and Secrets
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: impetus-config
  namespace: impetus-system
data:
  IMPETUS_ENVIRONMENT: "production"
  IMPETUS_LOG_LEVEL: "info"
  IMPETUS_MAX_LOADED_MODELS: "2"
  IMPETUS_PERFORMANCE_MODE: "performance"

---
apiVersion: v1
kind: Secret
metadata:
  name: impetus-secrets
  namespace: impetus-system
type: Opaque
stringData:
  IMPETUS_API_KEY: "your-secure-api-key"
  GRAFANA_PASSWORD: "secure-grafana-password"
```

### Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: impetus-server
  namespace: impetus-system
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: impetus-server
  template:
    metadata:
      labels:
        app: impetus-server
    spec:
      containers:
      - name: impetus-server
        image: gerdsenai/impetus-llm-server:latest
        ports:
        - containerPort: 8080
          name: http
        
        envFrom:
        - configMapRef:
            name: impetus-config
        - secretRef:
            name: impetus-secrets
        
        resources:
          requests:
            memory: "8Gi"
            cpu: "2000m"
          limits:
            memory: "16Gi"
            cpu: "8000m"
        
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        startupProbe:
          httpGet:
            path: /api/health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
        
        volumeMounts:
        - name: models-storage
          mountPath: /models
        - name: logs-storage
          mountPath: /logs
      
      volumes:
      - name: models-storage
        persistentVolumeClaim:
          claimName: impetus-models-pvc
      - name: logs-storage
        persistentVolumeClaim:
          claimName: impetus-logs-pvc
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - impetus-server
              topologyKey: kubernetes.io/hostname
```

### Service and Ingress
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: impetus-service
  namespace: impetus-system
spec:
  selector:
    app: impetus-server
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: impetus-ingress
  namespace: impetus-system
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - api.your-domain.com
    secretName: impetus-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: impetus-service
            port:
              number: 8080
```

## Native Deployment

### System Preparation
```bash
# Install system dependencies (macOS)
brew install python@3.11 nginx redis

# Install system dependencies (Ubuntu)
sudo apt update
sudo apt install python3.11 python3.11-venv nginx redis-server

# Create dedicated user
sudo useradd -m -s /bin/bash impetus
sudo usermod -aG sudo impetus
```

### Application Installation
```bash
# Switch to impetus user
sudo su - impetus

# Clone repository
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install production dependencies
cd gerdsen_ai_server
pip install -r requirements_production.txt

# Create configuration
cp .env.example .env
# Edit .env with production values

# Test installation
python src/main.py --validate
```

### Service Configuration (systemd)
```bash
# Copy service file
sudo cp service/impetus.service /etc/systemd/system/

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable impetus
sudo systemctl start impetus

# Check status
sudo systemctl status impetus
```

### Nginx Configuration
```bash
# Copy nginx configuration
sudo cp nginx/conf.d/impetus.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/impetus.conf /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

## Load Balancing

### HAProxy Configuration
```bash
# /etc/haproxy/haproxy.cfg
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend impetus_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/impetus.pem
    redirect scheme https if !{ ssl_fc }
    default_backend impetus_backend

backend impetus_backend
    balance roundrobin
    option httpchk GET /api/health/ready
    server impetus1 10.0.1.10:8080 check
    server impetus2 10.0.1.11:8080 check
    server impetus3 10.0.1.12:8080 check
```

### Health Check Configuration
```bash
# Health check script
#!/bin/bash
curl -f -m 5 http://localhost:8080/api/health/ready || exit 1
```

## SSL/TLS Configuration

### Certificate Generation (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d api.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### SSL Security Headers
```nginx
# In nginx configuration
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

## Monitoring & Logging

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'impetus'
    static_configs:
      - targets: ['impetus-server:8080']
    metrics_path: /api/health/metrics
    scrape_interval: 30s
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Impetus LLM Server",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(impetus_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "impetus_average_latency_ms"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation (ELK Stack)
```yaml
# logstash.conf
input {
  file {
    path => "/var/log/impetus/*.log"
    type => "impetus"
  }
}

filter {
  if [type] == "impetus" {
    json {
      source => "message"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "impetus-logs-%{+YYYY.MM.dd}"
  }
}
```

## Security Hardening

### API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Store in environment
export IMPETUS_API_KEY="your-generated-key"

# Use secrets management
kubectl create secret generic impetus-api-key \
  --from-literal=key="your-generated-key"
```

### Network Security
```bash
# Firewall rules (ufw)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8080/tcp  # Block direct access
sudo ufw enable
```

### Container Security
```dockerfile
# Use distroless or minimal base images
FROM gcr.io/distroless/python3

# Run as non-root user
USER 1000:1000

# Read-only root filesystem
--read-only --tmpfs /tmp
```

## Performance Tuning

### System Optimization
```bash
# Increase file descriptors
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# TCP optimization
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf
sysctl -p
```

### Application Tuning
```bash
# Environment variables
export IMPETUS_WORKERS=4
export IMPETUS_MAX_WORKER_MEMORY_MB=8192
export IMPETUS_PERFORMANCE_MODE=performance
```

### Database Optimization (if using)
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
```

## Backup & Recovery

### Model Backup Strategy
```bash
#!/bin/bash
# backup-models.sh

BACKUP_DIR="/backup/models"
MODELS_DIR="/models"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup models
rsync -av "$MODELS_DIR/" "$BACKUP_DIR/$DATE/"

# Compress backup
tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "models_*.tar.gz" -mtime +7 -delete
```

### Configuration Backup
```bash
#!/bin/bash
# backup-config.sh

kubectl get configmap impetus-config -o yaml > backup/configmap.yaml
kubectl get secret impetus-secrets -o yaml > backup/secrets.yaml
kubectl get deployment impetus-server -o yaml > backup/deployment.yaml
```

### Recovery Procedures
```bash
# Restore from backup
tar -xzf models_20250101_120000.tar.gz
rsync -av models_20250101_120000/ /models/

# Restart services
kubectl rollout restart deployment/impetus-server
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
kubectl top pods -n impetus-system

# Scale down replicas
kubectl scale deployment impetus-server --replicas=1

# Check for memory leaks
kubectl exec -it pod-name -- ps aux
```

#### 2. Model Loading Failures
```bash
# Check disk space
df -h /models

# Check model integrity
python -c "import mlx.core as mx; print('MLX working')"

# Clear cache
rm -rf /models/.cache/*
```

#### 3. SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in cert.pem -text -noout | grep "Not After"

# Renew certificate
certbot renew --dry-run
```

#### 4. Performance Issues
```bash
# Check system metrics
top
iostat 1
nvidia-smi  # If using GPU

# Check application logs
kubectl logs -f deployment/impetus-server

# Profile application
python -m cProfile src/main.py
```

### Debug Commands
```bash
# Health checks
curl -f http://localhost:8080/api/health/ready
curl -f http://localhost:8080/api/health/live

# Check metrics
curl http://localhost:8080/api/health/metrics

# Test API
curl -X POST \
  -H "Authorization: Bearer $IMPETUS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}' \
  http://localhost:8080/v1/chat/completions
```

### Monitoring Alerts
```yaml
# Prometheus alerts
groups:
- name: impetus
  rules:
  - alert: ImpetusDown
    expr: up{job="impetus"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Impetus server is down"
  
  - alert: HighMemoryUsage
    expr: impetus_memory_usage_percent > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## Best Practices

1. **Scaling**: Start with single instance, scale horizontally as needed
2. **Monitoring**: Implement comprehensive monitoring from day one
3. **Security**: Use secrets management, enable TLS, restrict network access
4. **Backup**: Regular automated backups of models and configuration
5. **Updates**: Use rolling updates with health checks
6. **Testing**: Test deployments in staging environment first
7. **Documentation**: Keep deployment documentation up to date
8. **Capacity Planning**: Monitor resource usage and plan for growth

## Support

For deployment issues:
1. Check troubleshooting section
2. Review logs and metrics
3. Consult [GitHub Issues](https://github.com/GerdsenAI/Impetus-LLM-Server/issues)
4. Join community discussions