#!/bin/bash
#
# Impetus LLM Server - Complete Uninstaller
# 
# This script removes all traces of Impetus LLM Server
# from the system including services, files, and configurations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIRM_DELETE="false"
KEEP_MODELS="false"
KEEP_CONFIG="false"

# Possible installation locations
INSTALL_LOCATIONS=(
    "/opt/impetus-llm-server"
    "/Applications/Impetus LLM Server"
    "$HOME/impetus-llm-server"
    "$HOME/Impetus-LLM-Server"
    "$HOME/impetus-docker"
)

# Functions
print_header() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Impetus LLM Server - Complete Uninstaller         ║"
    echo "║              ⚠️  This will remove ALL data  ⚠️           ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

confirm_uninstall() {
    if [[ "$CONFIRM_DELETE" != "true" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: This will completely remove Impetus LLM Server!${NC}"
        echo
        echo "This will delete:"
        echo "• All installation files and directories"
        echo "• System services (systemd/launchd)"
        echo "• Configuration files"
        echo "• Log files"
        if [[ "$KEEP_MODELS" != "true" ]]; then
            echo "• Downloaded models (unless --keep-models is used)"
        fi
        if [[ "$KEEP_CONFIG" != "true" ]]; then
            echo "• User configuration and cache"
        fi
        echo
        read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
        if [[ $REPLY != "yes" ]]; then
            echo "Uninstall cancelled."
            exit 0
        fi
    fi
}

detect_installations() {
    print_section "Detecting Impetus Installations"
    
    FOUND_INSTALLATIONS=()
    
    for location in "${INSTALL_LOCATIONS[@]}"; do
        if [[ -d "$location" ]]; then
            # Check if it's actually an Impetus installation
            if [[ -f "$location/gerdsen_ai_server/src/main.py" ]] || 
               [[ -f "$location/Contents/SharedSupport/gerdsen_ai_server/src/main.py" ]] ||
               [[ -f "$location/docker-compose.yml" ]]; then
                FOUND_INSTALLATIONS+=("$location")
                echo "✓ Found installation: $location"
            fi
        fi
    done
    
    if [[ ${#FOUND_INSTALLATIONS[@]} -eq 0 ]]; then
        echo "No Impetus installations found in standard locations."
        return 1
    fi
    
    echo "Found ${#FOUND_INSTALLATIONS[@]} installation(s)"
}

stop_services() {
    print_section "Stopping Services"
    
    # Stop systemd service
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet impetus 2>/dev/null; then
            echo "Stopping systemd service..."
            systemctl stop impetus || true
            systemctl disable impetus || true
            echo "✓ systemd service stopped"
        fi
    fi
    
    # Stop launchd service
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLIST_LOCATIONS=(
            "/Library/LaunchDaemons/com.gerdsenai.impetus.plist"
            "/Library/LaunchAgents/com.gerdsenai.impetus.plist"
            "$HOME/Library/LaunchAgents/com.gerdsenai.impetus.plist"
        )
        
        for plist in "${PLIST_LOCATIONS[@]}"; do
            if [[ -f "$plist" ]]; then
                echo "Unloading launchd service: $plist"
                launchctl unload "$plist" 2>/dev/null || true
                echo "✓ launchd service unloaded"
            fi
        done
    fi
    
    # Stop Docker containers
    if command -v docker &> /dev/null; then
        echo "Stopping Docker containers..."
        # Stop containers with impetus in the name
        docker ps -a --filter "name=impetus" --format "{{.Names}}" | while read -r container; do
            if [[ -n "$container" ]]; then
                echo "Stopping container: $container"
                docker stop "$container" 2>/dev/null || true
                docker rm "$container" 2>/dev/null || true
            fi
        done
        
        # Stop Docker Compose projects
        for installation in "${FOUND_INSTALLATIONS[@]}"; do
            if [[ -f "$installation/docker-compose.yml" ]]; then
                echo "Stopping Docker Compose in: $installation"
                cd "$installation"
                docker-compose down --remove-orphans 2>/dev/null || true
                docker compose down --remove-orphans 2>/dev/null || true
            fi
        done
        echo "✓ Docker containers stopped"
    fi
    
    # Kill any running processes
    echo "Stopping any running Impetus processes..."
    # Kill only processes whose command line matches known installation locations
    # Kill processes by known executable names (more precise)
    for proc_name in "gerdsen_ai_server" "impetus-llm-server" "impetus_server"; do
        pgrep -x "$proc_name" | while read -r pid; do
            if [[ -n "$pid" ]]; then
                echo "Killing process with PID $pid (name: $proc_name)"
                kill "$pid" 2>/dev/null || true
            fi
        done
    done
    # Also kill specific known process names, but with more precise patterns
    pkill -f "gerdsen_ai_server" 2>/dev/null || true
    pkill -f "gunicorn.*wsgi:application" 2>/dev/null || true
    
    echo "✓ All services stopped"
}

remove_service_files() {
    print_section "Removing Service Files"
    
    # Remove systemd service files
    if command -v systemctl &> /dev/null; then
        SERVICE_FILES=(
            "/etc/systemd/system/impetus.service"
            "/lib/systemd/system/impetus.service"
        )
        
        for service_file in "${SERVICE_FILES[@]}"; do
            if [[ -f "$service_file" ]]; then
                echo "Removing systemd service: $service_file"
                rm -f "$service_file"
            fi
        done
        
        # Reload systemd
        systemctl daemon-reload 2>/dev/null || true
        echo "✓ systemd service files removed"
    fi
    
    # Remove launchd plist files
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLIST_LOCATIONS=(
            "/Library/LaunchDaemons/com.gerdsenai.impetus.plist"
            "/Library/LaunchAgents/com.gerdsenai.impetus.plist"
            "$HOME/Library/LaunchAgents/com.gerdsenai.impetus.plist"
        )
        
        for plist in "${PLIST_LOCATIONS[@]}"; do
            if [[ -f "$plist" ]]; then
                echo "Removing launchd plist: $plist"
                rm -f "$plist"
            fi
        done
        echo "✓ launchd plist files removed"
    fi
}

remove_installations() {
    print_section "Removing Installation Directories"
    
    for installation in "${FOUND_INSTALLATIONS[@]}"; do
        echo "Removing installation: $installation"
        
        # Special handling for models if keeping them
        if [[ "$KEEP_MODELS" == "true" ]]; then
            MODELS_BACKUP="$HOME/impetus-models-backup-$(date +%Y%m%d_%H%M%S)"
            if [[ -d "$installation/models" ]] || [[ -d "$installation/data/models" ]]; then
                echo "Backing up models to: $MODELS_BACKUP"
                mkdir -p "$MODELS_BACKUP"
                cp -r "$installation/models"/* "$MODELS_BACKUP/" 2>/dev/null || true
                cp -r "$installation/data/models"/* "$MODELS_BACKUP/" 2>/dev/null || true
                echo "✓ Models backed up"
            fi
        fi
        
        # Remove the installation
        rm -rf "$installation"
        echo "✓ Removed: $installation"
    done
}

remove_user_data() {
    print_section "Removing User Data and Configuration"
    
    if [[ "$KEEP_CONFIG" != "true" ]]; then
        # Remove user configuration directories
        USER_DIRS=(
            "$HOME/.impetus"
            "$HOME/.config/impetus"
        )
        
        for dir in "${USER_DIRS[@]}"; do
            if [[ -d "$dir" ]]; then
                if [[ "$KEEP_MODELS" == "true" && "$dir" == "$HOME/.impetus" ]]; then
                    # Keep models but remove other data
                    rm -rf "$dir/cache" "$dir/logs" "$dir/config" 2>/dev/null || true
                    echo "✓ Removed config/cache from: $dir (kept models)"
                else
                    rm -rf "$dir"
                    echo "✓ Removed: $dir"
                fi
            fi
        done
    else
        echo "Skipping user configuration (--keep-config specified)"
    fi
}

remove_system_files() {
    print_section "Removing System Files"
    
    # Remove system configuration
    SYSTEM_DIRS=(
        "/etc/impetus"
        "/usr/local/etc/impetus"
    )
    
    for dir in "${SYSTEM_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "Removing system config: $dir"
            rm -rf "$dir"
        fi
    done
    
    # Remove log files
    LOG_DIRS=(
        "/var/log/impetus"
        "/usr/local/var/log/impetus"
    )
    
    for dir in "${LOG_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "Removing logs: $dir"
            rm -rf "$dir"
        fi
    done
    
    # Remove logrotate configuration
    if [[ -f "/etc/logrotate.d/impetus" ]]; then
        echo "Removing logrotate config"
        rm -f "/etc/logrotate.d/impetus"
    fi
    
    echo "✓ System files removed"
}

remove_management_commands() {
    print_section "Removing Management Commands"
    
    COMMANDS=(
        "/usr/local/bin/impetus-start"
        "/usr/local/bin/impetus-stop"
        "/usr/local/bin/impetus-restart"
        "/usr/local/bin/impetus-status"
        "/usr/local/bin/impetus-logs"
        "/usr/local/bin/impetus"
    )
    
    for cmd in "${COMMANDS[@]}"; do
        if [[ -f "$cmd" ]]; then
            echo "Removing command: $cmd"
            rm -f "$cmd"
        fi
    done
    
    echo "✓ Management commands removed"
}

remove_docker_images() {
    print_section "Removing Docker Images"
    
    if command -v docker &> /dev/null; then
        echo "Removing Impetus Docker images..."
        
        # Remove images with impetus in the name
        docker images --format "{{.Repository}}:{{.Tag}}" | grep -i impetus | while read -r image; do
            if [[ -n "$image" ]]; then
                echo "Removing image: $image"
                docker rmi "$image" 2>/dev/null || true
            fi
        done
        
        # Remove dangling images
        docker image prune -f 2>/dev/null || true
        
        echo "✓ Docker images removed"
    fi
}

remove_desktop_shortcuts() {
    print_section "Removing Desktop Shortcuts"
    
    SHORTCUTS=(
        "$HOME/Desktop/Impetus LLM Server.command"
        "$HOME/Desktop/Impetus.app"
        "/Applications/Impetus.app"
    )
    
    for shortcut in "${SHORTCUTS[@]}"; do
        if [[ -e "$shortcut" ]]; then
            echo "Removing shortcut: $shortcut"
            rm -rf "$shortcut"
        fi
    done
    
    echo "✓ Desktop shortcuts removed"
}

cleanup_package_cache() {
    print_section "Cleaning Package Cache"
    
    # Clean pip cache
    if command -v pip &> /dev/null; then
        echo "Cleaning pip cache..."
        pip cache purge 2>/dev/null || true
    fi
    
    # Clean Homebrew cache (if applicable)
    if command -v brew &> /dev/null; then
        echo "Cleaning Homebrew cache..."
        brew cleanup 2>/dev/null || true
    fi
    
    echo "✓ Package cache cleaned"
}

print_summary() {
    print_section "Uninstall Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🗑️  Uninstall Successful! 🗑️                ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📋 What was removed:${NC}
─────────────────────────
• Installation directories: ${#FOUND_INSTALLATIONS[@]} found and removed
• System services (systemd/launchd)
• Configuration files
• Log files and rotation
• Management commands
• Desktop shortcuts
• Docker containers and images
EOF

    if [[ "$KEEP_MODELS" == "true" ]]; then
        echo "• Models: Backed up to ~/impetus-models-backup-*"
    else
        echo "• Downloaded models"
    fi
    
    if [[ "$KEEP_CONFIG" == "true" ]]; then
        echo "• User configuration: Preserved"
    else
        echo "• User configuration and cache"
    fi
    
    cat << EOF

${BLUE}🔍 Manual cleanup (if needed):${NC}
─────────────────────────────────
If you installed Impetus in a custom location, you may need to manually remove:
• Custom installation directories
• Modified system configurations
• Custom service files

${BLUE}💾 Preserved data:${NC}
─────────────────
EOF

    if [[ "$KEEP_MODELS" == "true" ]]; then
        echo "Models have been backed up to: ~/impetus-models-backup-*"
    fi
    
    if [[ "$KEEP_CONFIG" == "true" ]]; then
        echo "User configuration preserved in: ~/.impetus"
    fi
    
    cat << EOF

${GREEN}✨ Impetus LLM Server has been completely removed! ✨${NC}

Thank you for using Impetus LLM Server! 🚀

EOF
}

# Main uninstall flow
main() {
    print_header
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --yes)
                CONFIRM_DELETE="true"
                shift
                ;;
            --keep-models)
                KEEP_MODELS="true"
                shift
                ;;
            --keep-config)
                KEEP_CONFIG="true"
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --yes           Skip confirmation prompt"
                echo "  --keep-models   Backup models before removal"
                echo "  --keep-config   Preserve user configuration"
                echo "  --help         Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check if running as root when needed
    if [[ $EUID -eq 0 ]]; then
        echo -e "${YELLOW}Running as root - will remove system-wide installations${NC}"
    fi
    
    confirm_uninstall
    
    if ! detect_installations; then
        echo "No installations found. Nothing to remove."
        exit 0
    fi
    
    stop_services
    remove_service_files
    remove_installations
    remove_user_data
    
    # Only remove system files if running as root
    if [[ $EUID -eq 0 ]]; then
        remove_system_files
        remove_management_commands
    fi
    
    remove_docker_images
    remove_desktop_shortcuts
    cleanup_package_cache
    print_summary
}

# Run main function
main "$@"