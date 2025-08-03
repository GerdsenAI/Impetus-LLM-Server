#!/bin/bash
#
# Impetus LLM Server - Service Integration Installer
# 
# This script configures Impetus as a system service
# with auto-start capabilities and monitoring
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="impetus"
INSTALL_DIR=""
USER=""
SERVICE_PORT="8080"
AUTO_START="true"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Impetus LLM Server - Service Installer            ║"
    echo "║      Configure Impetus as System Service                ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

detect_system() {
    print_section "Detecting System Configuration"
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM_TYPE="macos"
        SERVICE_MANAGER="launchd"
        SERVICE_DIR="/Library/LaunchDaemons"
        echo "✓ macOS detected - using launchd"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        SYSTEM_TYPE="linux"
        if command -v systemctl &> /dev/null; then
            SERVICE_MANAGER="systemd"
            SERVICE_DIR="/etc/systemd/system"
            echo "✓ Linux with systemd detected"
        else
            echo -e "${RED}Error: systemd is required for Linux installation${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Error: Unsupported operating system${NC}"
        exit 1
    fi
    
    # Find Impetus installation
    if [[ -n "$INSTALL_DIR" ]]; then
        if [[ ! -d "$INSTALL_DIR" ]]; then
            echo -e "${RED}Error: Installation directory not found: $INSTALL_DIR${NC}"
            exit 1
        fi
    else
        # Try to auto-detect
        POSSIBLE_DIRS=(
            "/opt/impetus-llm-server"
            "/Applications/Impetus LLM Server/Contents/SharedSupport"
            "$HOME/impetus-llm-server"
            "$HOME/Impetus-LLM-Server"
            "$(pwd)"
        )
        
        for dir in "${POSSIBLE_DIRS[@]}"; do
            if [[ -f "$dir/gerdsen_ai_server/src/main.py" ]]; then
                INSTALL_DIR="$dir"
                echo "✓ Found Impetus installation: $INSTALL_DIR"
                break
            fi
        done
        
        if [[ -z "$INSTALL_DIR" ]]; then
            echo -e "${RED}Error: Could not find Impetus installation${NC}"
            echo "Please specify with --install-dir option"
            exit 1
        fi
    fi
    
    # Determine user
    if [[ -z "$USER" ]]; then
        if [[ "$SYSTEM_TYPE" == "macos" ]]; then
            USER=$(stat -f "%Su" /dev/console)
        else
            USER="impetus"
        fi
    fi
    
    echo "✓ Service user: $USER"
}

check_requirements() {
    print_section "Checking Service Requirements"
    
    # Check if running as root (needed for system service)
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run as root to install system services${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
    
    # Check Python installation
    if [[ ! -f "$INSTALL_DIR/venv/bin/python" ]] && [[ ! -f "$INSTALL_DIR/.venv/bin/python" ]]; then
        echo -e "${RED}Error: Python virtual environment not found${NC}"
        echo "Please run the main installer first"
        exit 1
    fi
    
    # Check if service already exists
    if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
        if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
            echo -e "${YELLOW}Warning: Service $SERVICE_NAME already exists${NC}"
            echo "It will be updated with new configuration"
        fi
    elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
        PLIST_PATH="$SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist"
        if [[ -f "$PLIST_PATH" ]]; then
            echo -e "${YELLOW}Warning: Service already exists at $PLIST_PATH${NC}"
            echo "It will be updated with new configuration"
        fi
    fi
    
    echo "✓ Requirements checked"
}

create_systemd_service() {
    print_section "Creating systemd Service"
    
    # Find Python and virtual environment
    VENV_DIR="$INSTALL_DIR/venv"
    if [[ ! -d "$VENV_DIR" ]]; then
        VENV_DIR="$INSTALL_DIR/.venv"
    fi
    
    SERVICE_FILE="$SERVICE_DIR/$SERVICE_NAME.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Impetus LLM Server - High-performance local LLM server for Apple Silicon
Documentation=https://github.com/GerdsenAI/Impetus-LLM-Server
After=network.target

[Service]
Type=notify
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR/gerdsen_ai_server
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="IMPETUS_ENVIRONMENT=production"
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
ReadWritePaths=/var/log/impetus

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service if auto-start is requested
    if [[ "$AUTO_START" == "true" ]]; then
        systemctl enable "$SERVICE_NAME"
        echo "✓ Service enabled for auto-start"
    fi
    
    echo "✓ systemd service created: $SERVICE_FILE"
}

create_launchd_service() {
    print_section "Creating launchd Service"
    
    # Find Python and virtual environment
    VENV_DIR="$INSTALL_DIR/venv"
    if [[ ! -d "$VENV_DIR" ]]; then
        VENV_DIR="$INSTALL_DIR/.venv"
    fi
    
    PLIST_FILE="$SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gerdsenai.$SERVICE_NAME</string>
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
        <key>IMPETUS_ENVIRONMENT</key>
        <string>production</string>
    </dict>
    <key>RunAtLoad</key>
    <$(echo "$AUTO_START" | tr '[:upper:]' '[:lower:]')/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/impetus.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/impetus-error.log</string>
    <key>UserName</key>
    <string>$USER</string>
</dict>
</plist>
EOF
    
    # Set proper permissions
    chmod 644 "$PLIST_FILE"
    chown root:wheel "$PLIST_FILE"
    
    # Load service if auto-start is requested
    if [[ "$AUTO_START" == "true" ]]; then
        launchctl load "$PLIST_FILE"
        echo "✓ Service loaded and will start automatically"
    fi
    
    echo "✓ launchd service created: $PLIST_FILE"
}

setup_logging() {
    print_section "Setting Up Logging"
    
    # Create log directory
    LOG_DIR="/var/log/impetus"
    mkdir -p "$LOG_DIR"
    chown "$USER:$(id -gn "$USER")" "$LOG_DIR" 2>/dev/null || chown "$USER:staff" "$LOG_DIR"
    
    if [[ "$SYSTEM_TYPE" == "linux" ]]; then
        # Create logrotate configuration
        cat > /etc/logrotate.d/impetus << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $(id -gn "$USER")
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
        echo "✓ Log rotation configured"
    fi
    
    echo "✓ Logging configured in $LOG_DIR"
}

create_management_commands() {
    print_section "Creating Management Commands"
    
    # Create management script directory
    BIN_DIR="/usr/local/bin"
    
    if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
        # Create systemd management commands
        cat > "$BIN_DIR/impetus-start" << 'EOF'
#!/bin/bash
systemctl start impetus
echo "✓ Impetus started"
EOF
        
        cat > "$BIN_DIR/impetus-stop" << 'EOF'
#!/bin/bash
systemctl stop impetus
echo "✓ Impetus stopped"
EOF
        
        cat > "$BIN_DIR/impetus-restart" << 'EOF'
#!/bin/bash
systemctl restart impetus
echo "✓ Impetus restarted"
EOF
        
        cat > "$BIN_DIR/impetus-status" << 'EOF'
#!/bin/bash
echo "=== Impetus Service Status ==="
systemctl --no-pager status impetus

echo -e "\n=== API Health Check ==="
if curl -f http://localhost:8080/api/health/status 2>/dev/null | jq .; then
    echo "✓ API is healthy"
else
    echo "❌ API is not responding"
fi
EOF
        
        cat > "$BIN_DIR/impetus-logs" << 'EOF'
#!/bin/bash
if [[ "$1" == "-f" ]]; then
    journalctl -u impetus -f
else
    journalctl -u impetus --no-pager -n 50
fi
EOF
        
    elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
        # Create launchd management commands
        PLIST_PATH="$SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist"
        
        cat > "$BIN_DIR/impetus-start" << EOF
#!/bin/bash
launchctl load "$PLIST_PATH"
echo "✓ Impetus started"
EOF
        
        cat > "$BIN_DIR/impetus-stop" << EOF
#!/bin/bash
launchctl unload "$PLIST_PATH"
echo "✓ Impetus stopped"
EOF
        
        cat > "$BIN_DIR/impetus-restart" << EOF
#!/bin/bash
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo "✓ Impetus restarted"
EOF
        
        cat > "$BIN_DIR/impetus-status" << 'EOF'
#!/bin/bash
echo "=== Impetus Service Status ==="
if launchctl list | grep -q "com.gerdsenai.impetus"; then
    echo "✓ Service is loaded"
    launchctl list | grep "com.gerdsenai.impetus"
else
    echo "❌ Service is not loaded"
fi

echo -e "\n=== API Health Check ==="
if curl -f http://localhost:8080/api/health/status 2>/dev/null | jq .; then
    echo "✓ API is healthy"
else
    echo "❌ API is not responding"
fi
EOF
        
        cat > "$BIN_DIR/impetus-logs" << 'EOF'
#!/bin/bash
if [[ "$1" == "-f" ]]; then
    tail -f /var/log/impetus.log
else
    tail -n 50 /var/log/impetus.log
fi
EOF
    fi
    
    # Make commands executable
    chmod +x "$BIN_DIR"/impetus-*
    
    echo "✓ Management commands created in $BIN_DIR"
}

start_service() {
    print_section "Starting Service"
    
    if [[ "$AUTO_START" == "true" ]]; then
        if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
            systemctl start "$SERVICE_NAME"
            echo "✓ Service started with systemd"
        elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
            # Service should already be loaded
            echo "✓ Service started with launchd"
        fi
        
        # Wait for service to be ready
        echo "Waiting for service to be ready..."
        sleep 10
        
        # Health check
        if curl -f http://localhost:$SERVICE_PORT/api/health/live > /dev/null 2>&1; then
            echo "✓ Service is healthy and responding"
        else
            echo "⚠️  Service started but health check failed"
            echo "Check logs with: impetus-logs"
        fi
    else
        echo "Service created but not started (auto-start disabled)"
        echo "Start manually with: impetus-start"
    fi
}

print_success() {
    print_section "Service Installation Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🎉 Service Installation Successful! 🎉       ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📋 Service Configuration:${NC}
─────────────────────────
• Service Name: $SERVICE_NAME
• Service Manager: $SERVICE_MANAGER
• Installation Directory: $INSTALL_DIR
• Service User: $USER
• Auto-start: $AUTO_START

${BLUE}🔧 Management Commands:${NC}
─────────────────────────
• Start service: impetus-start
• Stop service: impetus-stop
• Restart service: impetus-restart
• Service status: impetus-status
• View logs: impetus-logs [-f]

${BLUE}🌐 Service Endpoints:${NC}
─────────────────────────
• API Documentation: http://localhost:$SERVICE_PORT/docs
• Health Check: http://localhost:$SERVICE_PORT/api/health/status
• OpenAI API: http://localhost:$SERVICE_PORT/v1/

EOF

if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
    cat << EOF
${BLUE}🐧 systemd Commands:${NC}
─────────────────────────
• systemctl start $SERVICE_NAME
• systemctl stop $SERVICE_NAME
• systemctl status $SERVICE_NAME
• systemctl enable $SERVICE_NAME
• systemctl disable $SERVICE_NAME
• journalctl -u $SERVICE_NAME -f

EOF
elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
    cat << EOF
${BLUE}🍎 launchd Commands:${NC}
─────────────────────────
• launchctl load $SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist
• launchctl unload $SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist
• launchctl list | grep impetus

EOF
fi

    cat << EOF
${BLUE}📁 Important Files:${NC}
─────────────────────────
EOF

if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
    cat << EOF
• Service file: $SERVICE_DIR/$SERVICE_NAME.service
• Log rotation: /etc/logrotate.d/impetus
EOF
elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
    cat << EOF
• Service file: $SERVICE_DIR/com.gerdsenai.$SERVICE_NAME.plist
EOF
fi

    cat << EOF
• Log directory: /var/log/impetus/
• Management commands: /usr/local/bin/impetus-*

${BLUE}🔒 Security Notes:${NC}
─────────────────────────
• Service runs as user '$USER'
• System service with restricted permissions
• Logs are automatically rotated
• Health monitoring enabled

${GREEN}✨ Impetus is now configured as a system service! ✨${NC}

EOF
}

# Main installation flow
main() {
    print_header
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --user)
                USER="$2"
                shift 2
                ;;
            --port)
                SERVICE_PORT="$2"
                shift 2
                ;;
            --no-auto-start)
                AUTO_START="false"
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --install-dir DIR    Impetus installation directory"
                echo "  --user USER         Service user (default: auto-detect)"
                echo "  --port PORT         Service port (default: 8080)"
                echo "  --no-auto-start     Don't start service automatically"
                echo "  --help             Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    detect_system
    check_requirements
    
    if [[ "$SERVICE_MANAGER" == "systemd" ]]; then
        create_systemd_service
    elif [[ "$SERVICE_MANAGER" == "launchd" ]]; then
        create_launchd_service
    fi
    
    setup_logging
    create_management_commands
    start_service
    print_success
}

# Run main function
main "$@"