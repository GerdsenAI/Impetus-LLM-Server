# Impetus LLM Server - Troubleshooting Guide

This guide helps you resolve common issues with Impetus LLM Server.

## Quick Diagnostics

Run the validation command first:
```bash
impetus validate
```

This will check your system compatibility and highlight any issues.

## Common Issues

### 🚫 Installation Issues

#### "Python 3.11+ is required"
**Symptom**: Install script fails with Python version error

**Solution**:
```bash
# macOS with Homebrew
brew install python@3.11
brew link python@3.11

# Verify
python3 --version
```

#### "This installer requires Apple Silicon"
**Symptom**: Install fails on Intel Mac

**Solution**: Impetus requires M1/M2/M3/M4 Macs. Intel Macs are not supported due to MLX dependency.

#### "Git is required"
**Symptom**: Install script can't clone repository

**Solution**:
```bash
xcode-select --install
```

### 🔌 Connection Issues

#### "Server is not running on port 8080"
**Symptom**: Can't connect to API or dashboard

**Solutions**:
1. Check if server is running:
   ```bash
   impetus server --check
   ```

2. Check if port is in use:
   ```bash
   lsof -i :8080
   ```

3. Start server manually:
   ```bash
   impetus-server
   ```

4. Use different port:
   ```bash
   IMPETUS_PORT=8081 impetus-server
   ```

#### "WebSocket connection failed"
**Symptom**: Dashboard shows disconnected status

**Solutions**:
1. Check CORS settings in `.env`:
   ```
   IMPETUS_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

2. Restart both server and frontend

3. Check browser console for errors

### 💾 Model Loading Issues

#### "MLX not available"
**Symptom**: Models won't load, MLX import error

**Solutions**:
```bash
# Reinstall MLX
pip uninstall mlx mlx-lm
pip install --no-cache-dir mlx mlx-lm

# Verify
python3 -c "import mlx; print(mlx.__version__)"
```

#### "Insufficient memory"
**Symptom**: Model fails to load with memory error

**Solutions**:
1. Try smaller model:
   - Use 4-bit quantized versions
   - Try Phi-3 Mini (1.4GB) instead of Mistral 7B

2. Free up memory:
   - Close other applications
   - Unload unused models
   - Restart Mac to clear memory

3. Adjust memory limit in `.env`:
   ```
   IMPETUS_MAX_MEMORY_PERCENT=85
   ```

#### "Model not found"
**Symptom**: Can't find downloaded model

**Solutions**:
1. Check model location:
   ```bash
   ls ~/.impetus/models/
   ```

2. Re-download from dashboard

3. Check disk space:
   ```bash
   df -h
   ```

### 🔥 Performance Issues

#### "Thermal throttling detected"
**Symptom**: Slow inference, high temperatures

**Solutions**:
1. Switch to efficiency mode:
   ```
   IMPETUS_PERFORMANCE_MODE=efficiency
   ```

2. Improve cooling:
   - Elevate laptop for airflow
   - Use in cooler environment
   - Clean dust from vents

3. Reduce load:
   - Lower max tokens
   - Use smaller models
   - Add delays between requests

#### "First token takes too long"
**Symptom**: Long delay before response starts

**Solutions**:
1. Use model warmup:
   ```bash
   curl -X POST http://localhost:8080/api/models/warmup/your-model-id
   ```

2. Keep models loaded between sessions

3. Use SSD storage for models

#### "Low tokens per second"
**Symptom**: Inference slower than expected

**Solutions**:
1. Check performance mode:
   ```
   IMPETUS_PERFORMANCE_MODE=performance
   ```

2. Close other GPU-intensive apps

3. Use quantized models (4-bit vs 8-bit)

4. Check benchmark results:
   ```bash
   curl -X POST http://localhost:8080/api/models/benchmark/your-model-id
   ```

### 🐛 Error Messages

#### "Failed to load model: [error details]"
Check the error suggestions in the API response. Common fixes:
- Corrupted files: Re-download model
- Permission denied: Check file permissions
- Invalid format: Ensure MLX-compatible model

#### "Port already in use"
Another process is using the port. Solutions:
1. Find and kill process:
   ```bash
   lsof -i :8080
   kill -9 <PID>
   ```

2. Use different port:
   ```bash
   IMPETUS_PORT=8081 impetus-server
   ```

#### "API key required"
Set API key in `.env`:
```
IMPETUS_API_KEY=your-secret-key
```

### 📱 Dashboard Issues

#### Blank dashboard
1. Check if backend is running
2. Verify frontend URL: http://localhost:5173
3. Check browser console for errors
4. Try different browser

#### Models not showing
1. Refresh page
2. Check API endpoint: http://localhost:8080/api/models/list
3. Verify backend connection

## Advanced Debugging

### Enable debug logging
```bash
IMPETUS_LOG_LEVEL=DEBUG impetus-server
```

### Check system resources
```bash
# CPU usage
top

# Memory usage
vm_stat

# GPU usage (requires additional tools)
sudo powermetrics --samplers gpu_power
```

### Test MLX directly
```python
import mlx.core as mx

# Test basic operations
a = mx.array([1, 2, 3])
print(a * 2)

# Test GPU
print(mx.metal.is_available())
```

### Reset everything
```bash
# Stop server
pkill -f "impetus-server"

# Clear cache
rm -rf ~/.impetus/cache/*

# Reinstall
cd ~/impetus-llm-server
git pull
pip install -e . --upgrade
```

## Getting Help

If these solutions don't work:

1. **Check logs**:
   ```bash
   tail -f ~/.impetus/logs/impetus.log
   ```

2. **Run validation**:
   ```bash
   impetus validate
   ```

3. **Report issue**:
   - Include error messages
   - Include system info from validation
   - Include steps to reproduce
   - File at: https://github.com/GerdsenAI/Impetus-LLM-Server/issues

## FAQ

**Q: Can I run multiple models simultaneously?**
A: Yes, up to the limit set in IMPETUS_MAX_LOADED_MODELS (default 3)

**Q: Why is my M1 slower than expected?**
A: M1 base has fewer GPU cores. Expect 40-60 tokens/sec for 7B models.

**Q: Can I use this on Intel Mac?**
A: No, MLX requires Apple Silicon (M1/M2/M3/M4)

**Q: How much memory do I need?**
A: 8GB minimum, 16GB recommended. Each 7B model uses ~4-7GB.

**Q: Can I change the model directory?**
A: Yes, set IMPETUS_MODELS_DIR in .env

**Q: Is GPU required?**
A: MLX uses the integrated GPU on Apple Silicon automatically.

---

Still having issues? Join our community: https://github.com/GerdsenAI/Impetus-LLM-Server/discussions