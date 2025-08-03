# Impetus LLM Server - Installation Suite

**v1.0.0** - Complete installation and deployment toolkit for Impetus LLM Server with multiple deployment options, enterprise features, and automated management.

## 📑 Table of Contents

- [Overview](#overview)
- [Installation Options](#installation-options)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Management Tools](#management-tools)
- [Troubleshooting](#troubleshooting)

## Overview

This installer suite provides multiple deployment options for Impetus LLM Server, from simple desktop installations to enterprise production deployments with full automation and monitoring.

### ✨ Features

- **Multiple Deployment Types**: Native, Docker, macOS GUI, Production
- **Zero-Downtime Updates**: Automatic updates with rollback capability
- **Enterprise Ready**: Service integration, monitoring, security hardening
- **Cross-Platform**: macOS and Linux support with platform-specific optimizations
- **Automated Management**: Complete lifecycle management from install to uninstall

## Installation Options

### 🖥️ Desktop Installation (Recommended for Development)

**Standard installer with GUI support and development tools**

```bash
# Quick one-line install
curl -sSL https://raw.githubusercontent.com/GerdsenAI/Impetus-LLM-Server/main/install.sh | bash

# Or clone and run
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
./install.sh
```

**Features:**
- Automatic Python environment setup
- Model browser with one-click downloads
- Web dashboard for monitoring
- Development-friendly configuration

### 🍎 macOS GUI Package (App Store Style)

**Native macOS package installer with GUI wizard**

```bash
# Build the .pkg installer
./installers/macos_gui_installer.sh

# Install the generated package
open Impetus-LLM-Server-1.0.0.pkg
```

**Features:**
- Native macOS installer experience
- Code-signed package (with Developer ID)
- Desktop shortcuts and Applications folder integration
- Automatic dependency installation
- Uninstaller included

### 🏭 Production Deployment (Enterprise)

**Full production deployment with enterprise features**

```bash
# Run as root for system-wide installation
sudo ./installers/production_installer.sh

# With custom options
sudo ./installers/production_installer.sh \
  --api-key "your-secure-key" \
  --workers 8 \
  --port 8080
```

**Features:**
- Gunicorn production server with worker management
- nginx reverse proxy with SSL/TLS
- systemd/launchd service integration
- Health monitoring and metrics
- Log rotation and management
- Security hardening
- Backup and recovery procedures

### 🐳 Docker Deployment (Containerized)

**Docker-based deployment with container orchestration**

```bash
# Install with Docker Compose
./installers/docker_installer.sh

# With custom configuration
./installers/docker_installer.sh \
  --api-key "your-key" \
  --port 8080 \
  --dir ~/my-impetus
```

**Features:**
- Multi-container architecture
- nginx reverse proxy
- Prometheus monitoring (optional)
- Grafana dashboards (optional)
- Volume persistence for models and config
- Auto-scaling and health checks

### ⚙️ Service Integration

**Add system service capabilities to existing installation**

```bash
# Configure as system service
sudo ./installers/service_installer.sh

# With custom options
sudo ./installers/service_installer.sh \
  --install-dir /opt/impetus \
  --user impetus \
  --no-auto-start
```

**Features:**
- systemd service configuration (Linux)
- launchd service configuration (macOS)
- Automatic startup on boot
- Service management commands
- Health monitoring integration

## Quick Start

### 1. Choose Your Installation Type

| Use Case | Recommended Installer | Command |
|----------|----------------------|---------|
| Development & Testing | Standard | `./install.sh` |
| macOS Desktop Users | GUI Package | `./installers/macos_gui_installer.sh` |
| Production Servers | Production | `sudo ./installers/production_installer.sh` |
| Container Deployment | Docker | `./installers/docker_installer.sh` |
| Existing Installation + Service | Service Integration | `sudo ./installers/service_installer.sh` |

### 2. Basic Configuration

All installers support common configuration options:

```bash
# Set custom API key
--api-key "your-secure-api-key"

# Set custom port
--port 8080

# Set installation directory
--dir /custom/path

# Skip auto-start
--no-auto-start
```

### 3. Post-Installation

After installation, access Impetus at:

- **API Documentation**: `http://localhost:8080/docs`
- **Health Status**: `http://localhost:8080/api/health/status`
- **OpenAI API**: `http://localhost:8080/v1/`
- **Dashboard**: `http://localhost:5173` (development)

## Production Deployment

### Architecture Overview

```
[Internet] → [nginx] → [Gunicorn] → [Impetus App]
                ↓
           [Monitoring]
```

### Production Features

#### ✅ Security
- nginx reverse proxy with security headers
- Rate limiting and DDoS protection
- SSL/TLS termination
- Input validation and sanitization
- Service isolation and restricted permissions

#### ✅ Reliability
- Gunicorn worker management
- Automatic restart on failure
- Health check endpoints
- Graceful shutdown handling
- Zero-downtime deployments

#### ✅ Monitoring
- Prometheus metrics endpoint
- Grafana dashboards (Docker deployment)
- Log aggregation and rotation
- Resource usage monitoring
- Alert integration ready

#### ✅ Scalability
- Multi-worker configuration
- Load balancing support
- Container orchestration
- Kubernetes manifests available
- Auto-scaling capabilities

### Production Deployment Steps

1. **System Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y  # Linux
   brew update && brew upgrade             # macOS
   
   # Install dependencies
   sudo apt install nginx python3.11 git  # Linux
   brew install nginx python@3.11 git     # macOS
   ```

2. **Deploy Impetus**
   ```bash
   # Clone repository
   git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
   cd Impetus-LLM-Server
   
   # Run production installer
   sudo ./installers/production_installer.sh
   ```

3. **Verify Deployment**
   ```bash
   # Check service status
   systemctl status impetus nginx
   
   # Test API
   curl http://localhost/api/health/status
   
   # View logs
   journalctl -u impetus -f
   ```

4. **SSL Configuration** (Optional)
   ```bash
   # Install SSL certificate
   sudo certbot --nginx -d your-domain.com
   
   # Test SSL
   curl https://your-domain.com/api/health/status
   ```

## Management Tools

### Update System

**Automatic updates with zero-downtime and rollback**

```bash
# Check for updates
./installers/updater.sh

# Force update
./installers/updater.sh --force

# Update to specific version
./installers/updater.sh --version v1.1.0

# Rollback to previous version
./installers/updater.sh --rollback
```

**Update Features:**
- Zero-downtime rolling updates
- Automatic dependency updates
- Configuration backup and restore
- Health testing before completion
- Automatic rollback on failure
- Docker image rebuilding

### Service Management

**System service commands (after service installation)**

```bash
# Service control
impetus-start     # Start service
impetus-stop      # Stop service
impetus-restart   # Restart service
impetus-status    # Show status and health
impetus-logs      # View logs (-f for follow)

# Direct systemd/launchd commands
systemctl start impetus        # Linux
launchctl load service.plist   # macOS
```

### Docker Management

**Container management (Docker deployment)**

```bash
# Service control
./start.sh        # Start all services
./stop.sh         # Stop all services
./status.sh       # Show status
./logs.sh -f      # Follow logs
./update.sh       # Update containers
./backup.sh       # Backup config and models

# Docker Compose commands
docker-compose ps                    # Show containers
docker-compose logs -f impetus-server # Follow logs
docker-compose restart impetus-server # Restart service
```

### Uninstaller

**Complete removal of Impetus and all components**

```bash
# Interactive uninstall
sudo ./installers/uninstaller.sh

# Silent uninstall with options
sudo ./installers/uninstaller.sh \
  --yes \
  --keep-models \
  --keep-config
```

**Uninstall Features:**
- Complete system cleanup
- Optional model and config preservation
- Service removal
- Docker container cleanup
- Desktop shortcut removal
- Log file cleanup

## Configuration

### Environment Variables

All installers support configuration through environment variables or `.env` files:

```bash
# Server Configuration
IMPETUS_HOST=0.0.0.0
IMPETUS_PORT=8080
IMPETUS_API_KEY=your-secure-key
IMPETUS_ENVIRONMENT=production

# Model Configuration
IMPETUS_DEFAULT_MODEL=mlx-community/Mistral-7B-Instruct-v0.3-4bit
IMPETUS_MODEL_DIR=/path/to/models
IMPETUS_CACHE_DIR=/path/to/cache

# Performance
IMPETUS_WORKERS=4
IMPETUS_PERFORMANCE_MODE=performance
IMPETUS_MAX_TOKENS=2048

# Logging
IMPETUS_LOG_LEVEL=INFO
IMPETUS_LOG_DIR=/var/log/impetus
```

### Configuration Files

| Installation Type | Config Location |
|------------------|-----------------|
| Standard | `~/impetus-llm-server/gerdsen_ai_server/.env` |
| Production | `/etc/impetus/.env` |
| Docker | `~/impetus-docker/config/.env` |
| macOS GUI | `/Applications/Impetus LLM Server/Contents/SharedSupport/.env` |

## Monitoring

### Health Endpoints

All deployments include comprehensive health monitoring:

```bash
# Basic health check
curl http://localhost:8080/api/health/live

# Detailed status
curl http://localhost:8080/api/health/status

# Prometheus metrics
curl http://localhost:8080/api/health/metrics

# JSON metrics
curl http://localhost:8080/api/health/metrics/json
```

### Metrics Available

- **Application**: Request count, response times, error rates
- **System**: CPU, memory, disk usage
- **Models**: Load status, inference performance
- **MLX**: GPU utilization, Metal performance
- **Service**: Uptime, health status, worker information

### Log Locations

| Installation Type | Log Location |
|------------------|--------------|
| Standard | `~/.impetus/logs/` |
| Production | `/var/log/impetus/` |
| Docker | Container logs + `./data/logs/` |
| macOS GUI | `/var/log/impetus.log` |

## Troubleshooting

### Common Issues

#### Installation Fails

```bash
# Check system requirements
./installers/production_installer.sh --help

# Verify Python version
python3 --version

# Check disk space
df -h

# Install missing dependencies
sudo apt install python3.11-venv git  # Linux
brew install python@3.11 git          # macOS
```

#### Service Won't Start

```bash
# Check service status
systemctl status impetus  # Linux
launchctl list | grep impetus  # macOS

# Check logs
journalctl -u impetus -f  # Linux
tail -f /var/log/impetus.log  # macOS

# Test manual start
cd /path/to/impetus/gerdsen_ai_server
source ../venv/bin/activate
python src/main.py
```

#### Docker Issues

```bash
# Check Docker status
docker info

# Rebuild containers
docker-compose build --no-cache

# Check container logs
docker-compose logs impetus-server

# Reset Docker deployment
docker-compose down -v
docker-compose up -d
```

#### Port Conflicts

```bash
# Check what's using the port
lsof -i :8080

# Use different port
./installers/production_installer.sh --port 8081

# Update existing installation
export IMPETUS_PORT=8081
systemctl restart impetus
```

#### Model Download Issues

```bash
# Check disk space
df -h

# Test network connectivity
curl -I https://huggingface.co

# Manual model download
cd /path/to/models
git lfs install
git clone https://huggingface.co/mlx-community/Mistral-7B-Instruct-v0.3-4bit
```

### Getting Help

1. **Check logs first**: Always start with service and application logs
2. **Health endpoints**: Use `/api/health/status` for detailed diagnostics
3. **Documentation**: Full documentation at `/docs` endpoint
4. **GitHub Issues**: Report bugs at [GitHub Issues](https://github.com/GerdsenAI/Impetus-LLM-Server/issues)

### Performance Tuning

#### Optimize for Your Hardware

```bash
# M1/M2 Macs (8-16GB RAM)
IMPETUS_WORKERS=2
IMPETUS_PERFORMANCE_MODE=balanced

# M3/M4 Macs (16GB+ RAM)
IMPETUS_WORKERS=4
IMPETUS_PERFORMANCE_MODE=performance

# Server deployment
IMPETUS_WORKERS=$(($(nproc) * 2))
IMPETUS_PERFORMANCE_MODE=performance
```

#### Resource Monitoring

```bash
# Monitor system resources
htop
iostat -x 1
nvidia-smi  # If using NVIDIA GPUs

# Monitor Impetus specifically
curl http://localhost:8080/api/health/metrics/json | jq .
docker stats  # For Docker deployment
```

## Support Matrix

### Operating Systems

| OS | Standard | GUI | Production | Docker | Service |
|----|----------|-----|------------|--------|---------|
| macOS 13+ (Apple Silicon) | ✅ | ✅ | ✅ | ✅ | ✅ |
| macOS 13+ (Intel) | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |
| Ubuntu 20.04+ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Debian 11+ | ✅ | ❌ | ✅ | ✅ | ✅ |
| CentOS 8+ | ✅ | ❌ | ✅ | ✅ | ✅ |

### Python Versions

- **Required**: Python 3.11+
- **Recommended**: Python 3.11 or 3.12
- **Virtual Environment**: Always used (automatically created)

### Hardware Requirements

#### Minimum
- **CPU**: Any Apple Silicon or x86_64
- **RAM**: 8GB (4GB available)
- **Storage**: 10GB free space
- **Network**: Internet connection for model downloads

#### Recommended
- **CPU**: Apple Silicon M2+ or modern x86_64
- **RAM**: 16GB+ (8GB+ available)
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet for faster model downloads

## Advanced Usage

### Custom Deployment

```bash
# Clone the installer suite only
git clone --depth 1 https://github.com/GerdsenAI/Impetus-LLM-Server.git installers-only
cd installers-only/installers

# Customize installer before running
vim production_installer.sh

# Run customized installer
./production_installer.sh
```

### Integration with CI/CD

```yaml
# Example GitHub Actions workflow
name: Deploy Impetus
on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          ssh user@server 'cd /opt/impetus && ./installers/updater.sh'
```

### Kubernetes Deployment

```bash
# Use the production installer to generate configs
sudo ./installers/production_installer.sh --help

# Then adapt for Kubernetes using the provided manifests
kubectl apply -f docs/kubernetes/
```

---

**🚀 Ready to deploy Impetus LLM Server?**

Choose your installation method above and get started with high-performance local LLM inference in minutes!

For more information, visit the [main documentation](../README.md) or the [production deployment guide](../docs/PRODUCTION_DEPLOYMENT.md).