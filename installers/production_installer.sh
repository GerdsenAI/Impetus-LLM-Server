#!/bin/bash
#
# Impetus LLM Server - Production Deployment Installer
# 
# This script installs Impetus LLM Server for production environments
# with Gunicorn, monitoring, and enterprise features
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
INSTALL_DIR="/opt/impetus-llm-server"
USER="impetus"
GROUP="impetus"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="/etc/impetus"
LOG_DIR="/var/log/impetus"
SYSTEMD_SERVICE_FILE="/etc/systemd/system/impetus.service"
DEFAULT_MODEL="mlx-community/Mistral-7B-Instruct-v0.3-4bit"

# Service configuration
SERVICE_PORT=8080
API_KEY=""
WORKERS_COUNT=""

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Impetus LLM Server - Production Installer         ║"
    echo "║     Enterprise-Grade LLM Server for Apple Silicon       ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run as root for production installation${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
}

check_requirements() {
    print_section "Checking System Requirements"
    
    # Check macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "✓ macOS detected"
        PACKAGE_MANAGER="brew"
        SERVICE_MANAGER="launchd"
        SERVICE_DIR="/Library/LaunchDaemons"
        CONFIG_DIR="/usr/local/etc/impetus"
        LOG_DIR="/usr/local/var/log/impetus"
        USER=$(whoami)
        GROUP="staff"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "✓ Linux detected"
        PACKAGE_MANAGER="apt"
        SERVICE_MANAGER="systemd"
        
        # Detect if we're on Apple Silicon Mac running Linux
        if [[ $(uname -m) == "arm64" ]]; then
            echo "⚠️  Warning: Linux on Apple Silicon detected"
            echo "   MLX performance may be limited outside of macOS"
        fi
    else
        echo -e "${RED}Error: Unsupported operating system${NC}"
        exit 1
    fi
    
    # Check Apple Silicon (if on macOS)
    if [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) != "arm64" ]]; then
        echo -e "${RED}Error: This installer requires Apple Silicon (M1/M2/M3/M4)${NC}"
        echo "For Intel Macs, use the standard installer with CPU-only mode"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        if [[ "$PACKAGE_MANAGER" == "brew" ]]; then
            echo "Install with: brew install python@3.11"
        else
            echo "Install with: apt update && apt install python3.11 python3.11-venv"
        fi
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.11"
    python3 -c "import sys; exit(0) if sys.version_info >= tuple(map(int, '$REQUIRED_VERSION'.split('.'))) else exit(1)"
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Error: Python $REQUIRED_VERSION+ is required (found $PYTHON_VERSION)${NC}"
        exit 1
    fi
    echo "✓ Python $PYTHON_VERSION found"
    
    # Check memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    else
        MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    fi
    
    if [[ $MEMORY_GB -lt 8 ]]; then
        echo -e "${YELLOW}Warning: System has ${MEMORY_GB}GB RAM. 16GB+ recommended for production${NC}"
    else
        echo "✓ Memory: ${MEMORY_GB}GB RAM"
    fi
    
    # Check disk space
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DISK_FREE_GB=$(df -H / | awk 'NR==2 {print int($4)}' | sed 's/G.*//')
    else
        DISK_FREE_GB=$(df -BG / | awk 'NR==2 {print int($4)}' | sed 's/G.*//')
    fi
    
    if [[ $DISK_FREE_GB -lt 20 ]]; then
        echo -e "${YELLOW}Warning: Only ${DISK_FREE_GB}GB free disk space. 20GB+ recommended for production${NC}"
    else
        echo "✓ Disk space: ${DISK_FREE_GB}GB available"
    fi
    
    # Check for conflicting processes
    if lsof -i :$SERVICE_PORT &> /dev/null; then
        echo -e "${YELLOW}Warning: Port $SERVICE_PORT is already in use${NC}"
        echo "Please stop the conflicting service or choose a different port"
        read -p "Continue anyway? (y/n): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}Error: Git is required${NC}"
        if [[ "$PACKAGE_MANAGER" == "brew" ]]; then
            echo "Install with: xcode-select --install"
        else
            echo "Install with: apt install git"
        fi
        exit 1
    fi
    echo "✓ Git found"
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

setup_user() {
    print_section "Setting Up System User"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Create system user for Linux
        if ! id "$USER" &>/dev/null; then
            echo "Creating system user: $USER"
            useradd -r -m -s /bin/bash -d "$INSTALL_DIR" "$USER"
            usermod -a -G "$GROUP" "$USER" 2>/dev/null || true
        else
            echo "✓ User $USER already exists"
        fi
    else
        # On macOS, use current user
        USER=$(whoami)
        echo "✓ Using current user: $USER"
    fi
}

create_directories() {
    print_section "Creating Directory Structure"
    
    # Create main installation directory
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$INSTALL_DIR/models"
    mkdir -p "$INSTALL_DIR/cache"
    
    # Set permissions
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        chown -R "$USER:$GROUP" "$INSTALL_DIR"
        chown -R "$USER:$GROUP" "$LOG_DIR"
        chown -R root:root "$CONFIG_DIR"
        chmod 755 "$CONFIG_DIR"
    else
        chown -R "$USER:$GROUP" "$INSTALL_DIR"
        chown -R "$USER:$GROUP" "$LOG_DIR"
        chown -R "$USER:$GROUP" "$CONFIG_DIR"
    fi
    
    echo "✓ Directory structure created"
}

install_dependencies() {
    print_section "Installing System Dependencies"
    
    if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
        apt update
        apt install -y \
            build-essential \
            curl \
            git \
            nginx \
            supervisor \
            htop \
            tree \
            jq
    elif [[ "$PACKAGE_MANAGER" == "brew" ]]; then
        # Install Homebrew dependencies
        brew install nginx jq || true
    fi
    
    echo "✓ System dependencies installed"
}

install_impetus() {
    print_section "Installing Impetus LLM Server"
    
    # Clone repository
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing installation..."
        cd "$INSTALL_DIR"
        sudo -u "$USER" git pull
    else
        echo "Cloning repository..."
        sudo -u "$USER" git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    # Create virtual environment
    echo "Creating Python virtual environment..."
    sudo -u "$USER" python3 -m venv "$VENV_DIR"
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    sudo -u "$USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$USER" "$VENV_DIR/bin/pip" install -r gerdsen_ai_server/requirements_production.txt
    
    # Install the package
    echo "Installing Impetus package..."
    sudo -u "$USER" "$VENV_DIR/bin/pip" install -e .
    
    echo "✓ Impetus LLM Server installed"
}

configure_production() {
    print_section "Configuring Production Environment"
    
    # Generate API key if not provided
    if [[ -z "$API_KEY" ]]; then
        API_KEY=$(openssl rand -hex 32)
        echo "Generated API key: $API_KEY"
        echo -e "${YELLOW}⚠️  Please save this API key securely!${NC}"
    fi
    
    # Calculate worker count based on CPU cores
    if [[ -z "$WORKERS_COUNT" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            CORES=$(sysctl -n hw.ncpu)
        else
            CORES=$(nproc)
        fi
        WORKERS_COUNT=$((CORES * 2 + 1))
        echo "Auto-calculated workers: $WORKERS_COUNT (based on $CORES cores)"
    fi
    
    # Create production configuration
    ENV_FILE="$CONFIG_DIR/.env"
    cat > "$ENV_FILE" << EOL
# Impetus LLM Server Production Configuration
IMPETUS_ENVIRONMENT=production
IMPETUS_HOST=127.0.0.1
IMPETUS_PORT=$SERVICE_PORT
IMPETUS_API_KEY=$API_KEY
IMPETUS_DEFAULT_MODEL=$DEFAULT_MODEL
IMPETUS_PERFORMANCE_MODE=performance
IMPETUS_LOG_LEVEL=INFO
IMPETUS_LOG_DIR=$LOG_DIR
IMPETUS_MODEL_DIR=$INSTALL_DIR/models
IMPETUS_CACHE_DIR=$INSTALL_DIR/cache
IMPETUS_WORKERS=$WORKERS_COUNT
IMPETUS_MAX_REQUESTS=1000
IMPETUS_TIMEOUT=300
IMPETUS_KEEPALIVE=30
EOL
    
    # Set permissions
    chmod 600 "$ENV_FILE"
    
    # Create symlink to application config
    ln -sf "$ENV_FILE" "$INSTALL_DIR/gerdsen_ai_server/.env"
    
    echo "✓ Production configuration created"
}

configure_nginx() {
    print_section "Configuring Nginx Reverse Proxy"
    
    # Create nginx configuration
    NGINX_CONFIG="/etc/nginx/sites-available/impetus"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        NGINX_CONFIG="/usr/local/etc/nginx/servers/impetus.conf"
    fi
    
    cat > "$NGINX_CONFIG" << EOL
# Impetus LLM Server - Nginx Configuration
upstream impetus_backend {
    server 127.0.0.1:$SERVICE_PORT;
    keepalive 32;
}

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone \$binary_remote_addr zone=health:10m rate=60r/m;
    
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
    
    # Static files (if any)
    location /static/ {
        alias $INSTALL_DIR/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Default location
    location / {
        return 301 /docs;
    }
}
EOL
    
    # Enable site
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/impetus
        # Remove default site
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    # Test nginx configuration
    nginx -t
    
    echo "✓ Nginx configuration created"
}

setup_service() {
    print_section "Setting Up System Service"
    
    if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
        # Create systemd service
        cat > "$SYSTEMD_SERVICE_FILE" << EOL
[Unit]
Description=Impetus LLM Server - High-performance local LLM server for Apple Silicon
Documentation=https://github.com/GerdsenAI/Impetus-LLM-Server
After=network.target

[Service]
Type=notify
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR/gerdsen_ai_server
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=$CONFIG_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn \\
    --config $INSTALL_DIR/gerdsen_ai_server/gunicorn_config.py \\
    --worker-class eventlet \\
    wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=impetus-llm-server

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR/models
ReadWritePaths=$INSTALL_DIR/cache
ReadWritePaths=$LOG_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOL
        
        # Reload systemd and enable service
        systemctl daemon-reload
        systemctl enable impetus
        
    elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
        # Create launchd plist
        LAUNCHD_PLIST="$SERVICE_DIR/com.gerdsenai.impetus.plist"
        cat > "$LAUNCHD_PLIST" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gerdsenai.impetus</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/gunicorn</string>
        <string>--config</string>
        <string>$INSTALL_DIR/gerdsen_ai_server/gunicorn_config.py</string>
        <string>--worker-class</string>
        <string>eventlet</string>
        <string>wsgi:application</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR/gerdsen_ai_server</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/impetus.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/impetus-error.log</string>
</dict>
</plist>
EOL
        
        # Load service
        launchctl load "$LAUNCHD_PLIST"
    fi
    
    echo "✓ System service configured"
}

setup_monitoring() {
    print_section "Setting Up Monitoring"
    
    # Create log rotation configuration
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        cat > /etc/logrotate.d/impetus << EOL
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        systemctl reload impetus
    endscript
}
EOL
    fi
    
    # Create monitoring script
    MONITOR_SCRIPT="$INSTALL_DIR/bin/monitor.sh"
    mkdir -p "$INSTALL_DIR/bin"
    cat > "$MONITOR_SCRIPT" << 'EOL'
#!/bin/bash
# Impetus Health Monitor Script

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/health/live)

if [ "$STATUS" = "200" ]; then
    echo "$(date): Impetus is healthy"
    exit 0
else
    echo "$(date): Impetus health check failed (HTTP $STATUS)"
    exit 1
fi
EOL
    
    chmod +x "$MONITOR_SCRIPT"
    
    echo "✓ Monitoring configured"
}

start_services() {
    print_section "Starting Services"
    
    # Start and enable nginx
    if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
        systemctl start nginx
        systemctl enable nginx
        systemctl start impetus
        echo "✓ Services started"
        
        # Show status
        echo -e "\n${BLUE}Service Status:${NC}"
        systemctl --no-pager status impetus nginx
        
    elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
        brew services start nginx
        echo "✓ Services started"
        
        # Show status
        echo -e "\n${BLUE}Service Status:${NC}"
        launchctl list | grep com.gerdsenai.impetus || echo "Service not yet loaded"
    fi
}

run_health_check() {
    print_section "Running Health Checks"
    
    echo "Waiting for services to start..."
    sleep 10
    
    # Test API health
    echo "Testing API health..."
    if curl -f http://localhost/api/health/live; then
        echo -e "\n✓ API health check passed"
    else
        echo -e "\n❌ API health check failed"
        return 1
    fi
    
    # Test OpenAI API
    echo "Testing OpenAI API..."
    if curl -f http://localhost/v1/models; then
        echo -e "\n✓ OpenAI API check passed"
    else
        echo -e "\n❌ OpenAI API check failed"
        return 1
    fi
    
    echo -e "${GREEN}✓ All health checks passed${NC}"
}

print_success() {
    print_section "Installation Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🎉 Installation Successful! 🎉              ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📋 Installation Summary:${NC}
─────────────────────────
• Installation Directory: $INSTALL_DIR
• Configuration Directory: $CONFIG_DIR
• Log Directory: $LOG_DIR
• API Key: $API_KEY
• Workers: $WORKERS_COUNT

${BLUE}🌐 Service Endpoints:${NC}
─────────────────────────
• API Documentation: http://localhost/docs
• Health Check: http://localhost/api/health/status
• OpenAI API: http://localhost/v1/
• Admin Panel: http://localhost/

${BLUE}🔧 Management Commands:${NC}
─────────────────────────
EOF

if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
    cat << EOF
• Start service: systemctl start impetus
• Stop service: systemctl stop impetus
• Restart service: systemctl restart impetus
• Service status: systemctl status impetus
• View logs: journalctl -u impetus -f
EOF
else
    cat << EOF
• Start service: launchctl load $SERVICE_DIR/com.gerdsenai.impetus.plist
• Stop service: launchctl unload $SERVICE_DIR/com.gerdsenai.impetus.plist
• Service status: launchctl list | grep impetus
• View logs: tail -f $LOG_DIR/impetus.log
EOF
fi

    cat << EOF

${BLUE}📁 Important Files:${NC}
─────────────────────────
• Configuration: $CONFIG_DIR/.env
• Nginx Config: /etc/nginx/sites-available/impetus
• Service File: $SYSTEMD_SERVICE_FILE
• Monitor Script: $INSTALL_DIR/bin/monitor.sh

${BLUE}🔒 Security Notes:${NC}
─────────────────────────
• API Key has been generated and saved to configuration
• Nginx is configured with security headers and rate limiting
• Service runs as unprivileged user '$USER'
• Logs are rotated automatically

${BLUE}🚀 Next Steps:${NC}
─────────────────────────
1. Download a model: curl -X POST http://localhost/api/models/download \\
   -H "Authorization: Bearer $API_KEY" \\
   -H "Content-Type: application/json" \\
   -d '{"model_id": "$DEFAULT_MODEL", "auto_load": true}'

2. Test chat completion: curl -X POST http://localhost/v1/chat/completions \\
   -H "Authorization: Bearer $API_KEY" \\
   -H "Content-Type: application/json" \\
   -d '{"model": "$DEFAULT_MODEL", "messages": [{"role": "user", "content": "Hello!"}]}'

3. Visit http://localhost/docs for interactive API documentation

${GREEN}✨ Impetus LLM Server is now running in production mode! ✨${NC}

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
            --workers)
                WORKERS_COUNT="$2"
                shift 2
                ;;
            --port)
                SERVICE_PORT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --api-key KEY    Set custom API key"
                echo "  --workers N      Set number of Gunicorn workers"
                echo "  --port N         Set service port (default: 8080)"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_root
    check_requirements
    setup_user
    create_directories
    install_dependencies
    install_impetus
    configure_production
    configure_nginx
    setup_service
    setup_monitoring
    start_services
    run_health_check
    print_success
}

# Run main function
main "$@"