#!/bin/bash
#
# Impetus LLM Server - Docker Installation Script
# 
# This script sets up Impetus LLM Server using Docker containers
# with production-ready configuration and monitoring
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/GerdsenAI/Impetus-LLM-Server.git"
INSTALL_DIR="$HOME/impetus-docker"
COMPOSE_PROJECT="impetus"
DEFAULT_MODEL="mlx-community/Mistral-7B-Instruct-v0.3-4bit"
API_KEY=""
EXPOSE_PORT="8080"
DASHBOARD_PORT="5173"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Impetus LLM Server - Docker Installer             ║"
    echo "║     Containerized Deployment with Docker Compose        ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

check_requirements() {
    print_section "Checking Docker Requirements"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is required but not installed${NC}"
        echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is required but not found${NC}"
        echo "Please install Docker Compose or update Docker Desktop"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        echo "Please start Docker Desktop"
        exit 1
    fi
    
    echo "✓ Docker $(docker --version | cut -d' ' -f3 | sed 's/,//') found"
    
    # Check Docker Compose command
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo "✓ Docker Compose (v2) found"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo "✓ Docker Compose (v1) found"
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    fi
    
    if [[ $MEMORY_GB -lt 8 ]]; then
        echo -e "${YELLOW}Warning: System has ${MEMORY_GB}GB RAM. 8GB+ recommended for Docker deployment${NC}"
    else
        echo "✓ Memory: ${MEMORY_GB}GB RAM"
    fi
    
    # Check disk space
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DISK_FREE_GB=$(df -H . | awk 'NR==2 {print int($4)}' | sed 's/G.*//')
    else
        DISK_FREE_GB=$(df -BG . | awk 'NR==2 {print int($4)}' | sed 's/G.*//')
    fi
    
    if [[ $DISK_FREE_GB -lt 15 ]]; then
        echo -e "${YELLOW}Warning: Only ${DISK_FREE_GB}GB free disk space. 15GB+ recommended for Docker images and models${NC}"
    else
        echo "✓ Disk space: ${DISK_FREE_GB}GB available"
    fi
    
    # Check for conflicting ports
    if lsof -i :$EXPOSE_PORT &> /dev/null; then
        echo -e "${YELLOW}Warning: Port $EXPOSE_PORT is already in use${NC}"
        read -p "Use different port? (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter port number: " EXPOSE_PORT
        fi
    fi
    
    echo -e "${GREEN}✓ All Docker requirements met${NC}"
}

setup_directory() {
    print_section "Setting Up Installation Directory"
    
    # Create installation directory
    if [ -d "$INSTALL_DIR" ]; then
        echo "Installation directory exists. Updating..."
        cd "$INSTALL_DIR"
        git pull || true
    else
        echo "Creating installation directory..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    # Create directories for Docker volumes
    mkdir -p data/models
    mkdir -p data/cache
    mkdir -p data/logs
    mkdir -p config
    
    echo "✓ Installation directory ready: $INSTALL_DIR"
}

generate_config() {
    print_section "Generating Configuration"
    
    # Generate API key if not provided
    if [[ -z "$API_KEY" ]]; then
        API_KEY=$(openssl rand -hex 32)
        echo "Generated API key: $API_KEY"
        echo -e "${YELLOW}⚠️  Please save this API key securely!${NC}"
    fi
    
    # Create environment file for Docker
    cat > config/.env << EOL
# Impetus LLM Server Docker Configuration
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT

# Server Configuration
IMPETUS_ENVIRONMENT=production
IMPETUS_HOST=0.0.0.0
IMPETUS_PORT=8080
IMPETUS_API_KEY=$API_KEY
IMPETUS_DEFAULT_MODEL=$DEFAULT_MODEL
IMPETUS_PERFORMANCE_MODE=balanced

# Paths (container paths)
IMPETUS_LOG_DIR=/app/logs
IMPETUS_MODEL_DIR=/app/models
IMPETUS_CACHE_DIR=/app/cache

# Docker specific
EXPOSE_PORT=$EXPOSE_PORT
DASHBOARD_PORT=$DASHBOARD_PORT

# Resource limits
MEMORY_LIMIT=8g
CPU_LIMIT=4

# Logging
IMPETUS_LOG_LEVEL=INFO
EOL
    
    echo "✓ Configuration generated"
}

create_docker_compose() {
    print_section "Creating Docker Compose Configuration"
    
    cat > docker-compose.override.yml << EOL
# Impetus LLM Server - Docker Compose Override
# This file customizes the production deployment

version: '3.8'

services:
  impetus-server:
    ports:
      - "$EXPOSE_PORT:8080"
    environment:
      - IMPETUS_API_KEY=$API_KEY
      - IMPETUS_DEFAULT_MODEL=$DEFAULT_MODEL
      - IMPETUS_PERFORMANCE_MODE=balanced
      - IMPETUS_LOG_LEVEL=INFO
    volumes:
      - ./data/models:/app/models
      - ./data/cache:/app/cache
      - ./data/logs:/app/logs
      - ./config/.env:/app/.env:ro
    deploy:
      resources:
        limits:
          memory: 8g
          cpus: '4'
        reservations:
          memory: 2g
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.impetus.rule=Host(\`localhost\`)"
      - "traefik.http.services.impetus.loadbalancer.server.port=8080"

  # Optional: Add reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/ssl:/etc/nginx/ssl:ro
    depends_on:
      - impetus-server
    restart: unless-stopped
    profiles:
      - proxy

  # Optional: Add monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
    restart: unless-stopped
    profiles:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
EOL
    
    echo "✓ Docker Compose override created"
}

create_nginx_config() {
    print_section "Creating Nginx Configuration"
    
    mkdir -p config/ssl
    
    cat > config/nginx.conf << EOL
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone \$binary_remote_addr zone=health:10m rate=60r/m;
    
    upstream impetus_backend {
        server impetus-server:8080;
        keepalive 32;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Health checks (no rate limiting)
        location /api/health/ {
            limit_req zone=health burst=10 nodelay;
            proxy_pass http://impetus_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://impetus_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_connect_timeout 10s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # OpenAI API endpoints
        location /v1/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://impetus_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_connect_timeout 10s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
        
        # Documentation
        location /docs {
            proxy_pass http://impetus_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        # Default location
        location / {
            return 301 /docs;
        }
    }
}
EOL
    
    echo "✓ Nginx configuration created"
}

create_monitoring_config() {
    print_section "Creating Monitoring Configuration"
    
    # Prometheus configuration
    cat > config/prometheus.yml << EOL
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'impetus'
    static_configs:
      - targets: ['impetus-server:8080']
    metrics_path: '/api/health/metrics'
    scrape_interval: 30s

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']
    scrape_interval: 30s
EOL
    
    # Grafana provisioning
    mkdir -p config/grafana/dashboards
    mkdir -p config/grafana/datasources
    
    cat > config/grafana/datasources/prometheus.yml << EOL
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOL
    
    echo "✓ Monitoring configuration created"
}

create_management_scripts() {
    print_section "Creating Management Scripts"
    
    # Start script
    cat > start.sh << EOL
#!/bin/bash
# Start Impetus LLM Server with Docker Compose

set -e

echo "Starting Impetus LLM Server..."

# Load environment
source config/.env

# Start core services
$COMPOSE_CMD up -d impetus-server

echo "Waiting for server to be ready..."
sleep 10

# Health check
if curl -f http://localhost:$EXPOSE_PORT/api/health/live > /dev/null 2>&1; then
    echo "✓ Impetus is running on http://localhost:$EXPOSE_PORT"
    echo "✓ API documentation: http://localhost:$EXPOSE_PORT/docs"
    echo "✓ Health status: http://localhost:$EXPOSE_PORT/api/health/status"
else
    echo "❌ Health check failed. Check logs with: $COMPOSE_CMD logs impetus-server"
    exit 1
fi
EOL
    
    # Stop script
    cat > stop.sh << EOL
#!/bin/bash
# Stop Impetus LLM Server

echo "Stopping Impetus LLM Server..."
$COMPOSE_CMD down
echo "✓ Impetus stopped"
EOL
    
    # Status script
    cat > status.sh << EOL
#!/bin/bash
# Check Impetus LLM Server status

echo "=== Impetus LLM Server Status ==="
echo
echo "Container status:"
$COMPOSE_CMD ps

echo
echo "Health check:"
if curl -f http://localhost:$EXPOSE_PORT/api/health/status 2>/dev/null | jq .; then
    echo "✓ Server is healthy"
else
    echo "❌ Server is not responding"
fi

echo
echo "Resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \$(docker ps --filter "name=$COMPOSE_PROJECT" --format "{{.Names}}")
EOL
    
    # Logs script
    cat > logs.sh << EOL
#!/bin/bash
# View Impetus LLM Server logs

if [[ "\$1" == "-f" ]]; then
    $COMPOSE_CMD logs -f impetus-server
else
    $COMPOSE_CMD logs --tail=100 impetus-server
fi
EOL
    
    # Update script
    cat > update.sh << EOL
#!/bin/bash
# Update Impetus LLM Server

set -e

echo "Updating Impetus LLM Server..."

# Pull latest code
git pull

# Rebuild and restart
$COMPOSE_CMD build --pull impetus-server
$COMPOSE_CMD up -d impetus-server

echo "✓ Update complete"
EOL
    
    # Backup script
    cat > backup.sh << EOL
#!/bin/bash
# Backup Impetus configuration and models

BACKUP_DIR="backups/\$(date +%Y%m%d_%H%M%S)"
mkdir -p "\$BACKUP_DIR"

echo "Creating backup in \$BACKUP_DIR..."

# Backup configuration
cp -r config "\$BACKUP_DIR/"

# Backup models (if they exist)
if [[ -d "data/models" && \$(ls -A data/models) ]]; then
    cp -r data/models "\$BACKUP_DIR/"
    echo "✓ Models backed up"
fi

# Create archive
tar -czf "\$BACKUP_DIR.tar.gz" "\$BACKUP_DIR"
rm -rf "\$BACKUP_DIR"

echo "✓ Backup created: \$BACKUP_DIR.tar.gz"
EOL
    
    # Make scripts executable
    chmod +x *.sh
    
    echo "✓ Management scripts created"
}

build_and_start() {
    print_section "Building and Starting Services"
    
    # Pull latest images
    echo "Pulling base images..."
    $COMPOSE_CMD pull --ignore-pull-failures || true
    
    # Build Impetus image
    echo "Building Impetus image..."
    $COMPOSE_CMD build impetus-server
    
    # Start services
    echo "Starting services..."
    $COMPOSE_CMD up -d impetus-server
    
    # Wait for startup
    echo "Waiting for services to start..."
    sleep 15
    
    echo "✓ Services started"
}

run_health_check() {
    print_section "Running Health Checks"
    
    # Wait for API to be ready
    echo "Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:$EXPOSE_PORT/api/health/live > /dev/null 2>&1; then
            echo "✓ API is responding"
            break
        fi
        if [[ $i -eq 30 ]]; then
            echo "❌ API failed to start within 5 minutes"
            echo "Check logs with: $COMPOSE_CMD logs impetus-server"
            return 1
        fi
        sleep 10
    done
    
    # Test API endpoints
    echo "Testing API endpoints..."
    
    if curl -f http://localhost:$EXPOSE_PORT/api/health/status > /dev/null 2>&1; then
        echo "✓ Health status endpoint working"
    else
        echo "❌ Health status endpoint failed"
        return 1
    fi
    
    if curl -f http://localhost:$EXPOSE_PORT/v1/models > /dev/null 2>&1; then
        echo "✓ OpenAI API endpoint working"
    else
        echo "❌ OpenAI API endpoint failed"
        return 1
    fi
    
    echo -e "${GREEN}✓ All health checks passed${NC}"
}

print_success() {
    print_section "Docker Installation Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🎉 Docker Installation Successful! 🎉        ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📋 Installation Summary:${NC}
─────────────────────────
• Installation Directory: $INSTALL_DIR
• API Key: $API_KEY
• Server Port: $EXPOSE_PORT

${BLUE}🌐 Service Endpoints:${NC}
─────────────────────────
• API Documentation: http://localhost:$EXPOSE_PORT/docs
• Health Check: http://localhost:$EXPOSE_PORT/api/health/status
• OpenAI API: http://localhost:$EXPOSE_PORT/v1/
• Prometheus (optional): http://localhost:9090
• Grafana (optional): http://localhost:3000

${BLUE}🔧 Management Commands:${NC}
─────────────────────────
• Start: ./start.sh
• Stop: ./stop.sh
• Status: ./status.sh
• Logs: ./logs.sh [-f]
• Update: ./update.sh
• Backup: ./backup.sh

${BLUE}🐳 Docker Commands:${NC}
─────────────────────────
• View containers: $COMPOSE_CMD ps
• View logs: $COMPOSE_CMD logs -f impetus-server
• Restart: $COMPOSE_CMD restart impetus-server
• Rebuild: $COMPOSE_CMD build --no-cache impetus-server

${BLUE}📁 Directory Structure:${NC}
─────────────────────────
• Configuration: config/
• Models: data/models/
• Cache: data/cache/
• Logs: data/logs/

${BLUE}🔌 Optional Features:${NC}
─────────────────────────
• Nginx proxy: $COMPOSE_CMD --profile proxy up -d
• Monitoring: $COMPOSE_CMD --profile monitoring up -d

${BLUE}🚀 Next Steps:${NC}
─────────────────────────
1. Download a model: curl -X POST http://localhost:$EXPOSE_PORT/api/models/download \\
   -H "Authorization: Bearer $API_KEY" \\
   -H "Content-Type: application/json" \\
   -d '{"model_id": "$DEFAULT_MODEL", "auto_load": true}'

2. Test chat completion: curl -X POST http://localhost:$EXPOSE_PORT/v1/chat/completions \\
   -H "Authorization: Bearer $API_KEY" \\
   -H "Content-Type: application/json" \\
   -d '{"model": "$DEFAULT_MODEL", "messages": [{"role": "user", "content": "Hello!"}]}'

3. Visit http://localhost:$EXPOSE_PORT/docs for interactive API documentation

${GREEN}✨ Impetus LLM Server is now running in Docker! ✨${NC}

EOF
}

# Main installation flow
main() {
    print_header
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --port)
                EXPOSE_PORT="$2"
                shift 2
                ;;
            --dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --api-key KEY    Set custom API key"
                echo "  --port N         Set exposed port (default: 8080)"
                echo "  --dir PATH       Set installation directory"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_requirements
    setup_directory
    generate_config
    create_docker_compose
    create_nginx_config
    create_monitoring_config
    create_management_scripts
    build_and_start
    run_health_check
    print_success
}

# Run main function
main "$@"