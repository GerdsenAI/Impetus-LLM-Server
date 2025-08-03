# Kubernetes Health Probes Configuration

This document describes the health check endpoints and how to configure Kubernetes probes for Impetus LLM Server.

## Available Health Endpoints

### 1. Liveness Probe: `/api/health/live`
- **Purpose**: Determines if the application is alive and should be restarted
- **Response**: Simple JSON with `alive: true/false`
- **Use**: Kubernetes liveness probe
- **Failure Action**: Pod restart

### 2. Readiness Probe: `/api/health/ready`
- **Purpose**: Determines if the application is ready to serve traffic
- **Response**: JSON with individual readiness checks
- **Use**: Kubernetes readiness probe
- **Failure Action**: Remove from service endpoints

### 3. Health Check: `/api/health`
- **Purpose**: General health status with heartbeat monitoring
- **Response**: Comprehensive health status
- **Use**: External monitoring systems
- **Failure Action**: Alert/notification

### 4. Detailed Status: `/api/health/status`
- **Purpose**: Detailed component health information
- **Response**: Full health breakdown with scores
- **Use**: Debugging and monitoring dashboards

## Kubernetes Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: impetus-llm-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: impetus-llm-server
  template:
    metadata:
      labels:
        app: impetus-llm-server
    spec:
      containers:
      - name: impetus-llm-server
        image: gerdsenai/impetus-llm-server:latest
        ports:
        - containerPort: 8080
          name: http
        
        # Resource limits for ML workloads
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "16Gi"
            cpu: "4000m"
        
        # Health probes
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1
        
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
          successThreshold: 1
        
        # Startup probe for slow-starting ML models
        startupProbe:
          httpGet:
            path: /api/health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30  # Allow up to 5 minutes for startup
          successThreshold: 1
        
        # Environment variables
        env:
        - name: IMPETUS_ENVIRONMENT
          value: "production"
        - name: IMPETUS_HOST
          value: "0.0.0.0"
        - name: IMPETUS_PORT
          value: "8080"
        - name: IMPETUS_LOG_LEVEL
          value: "info"
        
        # Volume mounts for models
        volumeMounts:
        - name: models-storage
          mountPath: /models
        
      volumes:
      - name: models-storage
        persistentVolumeClaim:
          claimName: impetus-models-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: impetus-llm-service
spec:
  selector:
    app: impetus-llm-server
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: impetus-models-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

## Probe Configuration Guidelines

### Liveness Probe Settings
- **initialDelaySeconds**: 30s (allow time for application startup)
- **periodSeconds**: 10s (check every 10 seconds)
- **timeoutSeconds**: 5s (timeout for each check)
- **failureThreshold**: 3 (restart after 3 consecutive failures)

### Readiness Probe Settings
- **initialDelaySeconds**: 15s (check readiness earlier than liveness)
- **periodSeconds**: 5s (frequent readiness checks)
- **timeoutSeconds**: 3s (shorter timeout for readiness)
- **failureThreshold**: 3 (remove from endpoints after 3 failures)

### Startup Probe Settings (Recommended)
- **initialDelaySeconds**: 10s
- **periodSeconds**: 10s
- **failureThreshold**: 30 (allow up to 5 minutes for model loading)

## Health Check Response Examples

### Liveness Response (Healthy)
```json
{
  "alive": true,
  "timestamp": "2025-01-01T12:00:00Z",
  "uptime_seconds": 3600.5,
  "last_heartbeat": "2025-01-01T12:00:00Z"
}
```

### Readiness Response (Ready)
```json
{
  "ready": true,
  "timestamp": "2025-01-01T12:00:00Z",
  "checks": {
    "memory_available": true,
    "models_loaded": true,
    "mlx_available": true
  },
  "message": "Ready"
}
```

### Readiness Response (Not Ready)
```json
{
  "ready": false,
  "timestamp": "2025-01-01T12:00:00Z",
  "checks": {
    "memory_available": true,
    "models_loaded": false,
    "mlx_available": true
  },
  "message": "Not ready"
}
```

## Monitoring Integration

### Prometheus Metrics
The `/api/health/metrics` endpoint provides Prometheus-compatible metrics:

```
# Health status metrics
impetus_health_status 1
impetus_consecutive_health_failures 0

# System metrics
impetus_cpu_usage_percent 45.2
impetus_memory_usage_percent 67.8
impetus_models_loaded 2

# Application metrics
impetus_requests_total 1234
impetus_tokens_generated_total 56789
impetus_average_latency_ms 250.5
```

### Grafana Dashboard
Create alerts based on these metrics:
- `impetus_health_status == 0` (unhealthy)
- `impetus_consecutive_health_failures > 2` (repeated failures)
- `impetus_cpu_usage_percent > 90` (high CPU)
- `impetus_memory_usage_percent > 95` (memory pressure)

## Troubleshooting

### Common Issues

1. **Readiness Probe Failing**
   - Check if models are loaded: `GET /api/models/list`
   - Verify MLX availability on macOS
   - Check memory usage

2. **Liveness Probe Failing**
   - Application may be deadlocked
   - Check logs for errors
   - Verify heartbeat thread is running

3. **Startup Probe Timeout**
   - Increase `failureThreshold` for large models
   - Check model download progress
   - Verify sufficient memory

### Debug Commands
```bash
# Check readiness
kubectl exec -it <pod-name> -- curl http://localhost:8080/api/health/ready

# Check liveness
kubectl exec -it <pod-name> -- curl http://localhost:8080/api/health/live

# Get detailed status
kubectl exec -it <pod-name> -- curl http://localhost:8080/api/health/status

# Check metrics
kubectl exec -it <pod-name> -- curl http://localhost:8080/api/health/metrics
```

## Best Practices

1. **Resource Limits**: Set appropriate CPU and memory limits for ML workloads
2. **Storage**: Use persistent volumes for model storage
3. **Startup Time**: Allow sufficient time for model loading in startup probes
4. **Monitoring**: Set up alerts based on health metrics
5. **Graceful Shutdown**: Configure `terminationGracePeriodSeconds` appropriately
6. **Node Selection**: Use node selectors for GPU/Apple Silicon nodes if needed