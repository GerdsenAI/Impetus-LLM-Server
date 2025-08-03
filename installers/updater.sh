#!/bin/bash
#
# Impetus LLM Server - Automatic Updater
# 
# This script updates Impetus LLM Server to the latest version
# with zero-downtime rolling updates and automatic rollback
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
INSTALL_DIR=""
BRANCH="main"
FORCE_UPDATE="false"
BACKUP_CONFIG="true"
RUN_TESTS="true"
AUTO_RESTART="true"
TARGET_VERSION=""
ROLLBACK_VERSION=""

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Impetus LLM Server - Automatic Updater           ║"
    echo "║      Zero-Downtime Updates with Automatic Rollback     ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

detect_installation() {
    print_section "Detecting Installation"
    
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
            "$HOME/impetus-docker"
            "$(pwd)"
        )
        
        for dir in "${POSSIBLE_DIRS[@]}"; do
            if [[ -f "$dir/gerdsen_ai_server/src/main.py" ]]; then
                INSTALL_DIR="$dir"
                echo "✓ Found installation: $INSTALL_DIR"
                break
            fi
        done
        
        if [[ -z "$INSTALL_DIR" ]]; then
            echo -e "${RED}Error: Could not find Impetus installation${NC}"
            echo "Please specify with --install-dir option"
            exit 1
        fi
    fi
    
    # Detect installation type
    if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
        INSTALL_TYPE="docker"
        echo "✓ Detected Docker installation"
    elif [[ -f "$INSTALL_DIR/gerdsen_ai_server/src/main.py" ]]; then
        INSTALL_TYPE="native"
        echo "✓ Detected native installation"
    else
        echo -e "${RED}Error: Unknown installation type${NC}"
        exit 1
    fi
}

check_current_version() {
    print_section "Checking Current Version"
    
    cd "$INSTALL_DIR"
    
    # Get current version/commit
    if git rev-parse --git-dir > /dev/null 2>&1; then
        CURRENT_COMMIT=$(git rev-parse HEAD)
        CURRENT_BRANCH=$(git branch --show-current)
        CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")
        
        echo "Current branch: $CURRENT_BRANCH"
        echo "Current commit: ${CURRENT_COMMIT:0:8}"
        if [[ -n "$CURRENT_TAG" ]]; then
            echo "Current tag: $CURRENT_TAG"
            CURRENT_VERSION="$CURRENT_TAG"
        else
            CURRENT_VERSION="${CURRENT_COMMIT:0:8}"
        fi
    else
        echo -e "${RED}Error: Installation is not a git repository${NC}"
        exit 1
    fi
}

check_available_updates() {
    print_section "Checking for Updates"
    
    # Fetch latest changes
    echo "Fetching latest changes..."
    git fetch origin
    
    # Check if there are updates
    LATEST_COMMIT=$(git rev-parse "origin/$BRANCH")
    LATEST_TAG=$(git describe --tags "origin/$BRANCH" 2>/dev/null | head -1 || echo "")
    
    if [[ -n "$LATEST_TAG" ]]; then
        AVAILABLE_VERSION="$LATEST_TAG"
    else
        AVAILABLE_VERSION="${LATEST_COMMIT:0:8}"
    fi
    
    echo "Available version: $AVAILABLE_VERSION"
    
    if [[ "$CURRENT_COMMIT" == "$LATEST_COMMIT" ]]; then
        if [[ "$FORCE_UPDATE" != "true" ]]; then
            echo -e "${GREEN}✓ Already up to date!${NC}"
            exit 0
        else
            echo -e "${YELLOW}⚠ Forcing update even though already up to date${NC}"
        fi
    else
        echo "Updates available!"
        
        # Show what's new
        echo "
Changes since current version:"
        git log --oneline "$CURRENT_COMMIT..origin/$BRANCH" | head -10
    fi
}

backup_current_state() {
    print_section "Creating Backup"
    
    BACKUP_DIR="$INSTALL_DIR/.backups/$(date +%Y%m%d_%H%M%S)_${CURRENT_VERSION}"
    mkdir -p "$BACKUP_DIR"
    
    echo "Creating backup in: $BACKUP_DIR"
    
    # Backup configuration files
    if [[ "$BACKUP_CONFIG" == "true" ]]; then
        echo "Backing up configuration..."
        
        if [[ -f "$INSTALL_DIR/.env" ]]; then
            cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
        fi
        
        if [[ -d "$INSTALL_DIR/config" ]]; then
            cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/"
        fi
        
        if [[ -f "$INSTALL_DIR/gerdsen_ai_server/.env" ]]; then
            cp "$INSTALL_DIR/gerdsen_ai_server/.env" "$BACKUP_DIR/"
        fi
    fi
    
    # Backup current commit info
    echo "$CURRENT_COMMIT" > "$BACKUP_DIR/commit.txt"
    echo "$CURRENT_BRANCH" > "$BACKUP_DIR/branch.txt"
    
    # Backup service status
    if systemctl is-active --quiet impetus 2>/dev/null; then
        echo "active" > "$BACKUP_DIR/service_status.txt"
    elif [[ "$INSTALL_TYPE" == "docker" ]]; then
        cd "$INSTALL_DIR"
        if docker-compose ps | grep -q "Up"; then
            echo "docker_active" > "$BACKUP_DIR/service_status.txt"
        fi
    fi
    
    echo "✓ Backup created"
}

stop_services() {
    print_section "Stopping Services"
    
    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        echo "Stopping Docker services..."
        cd "$INSTALL_DIR"
        docker-compose stop 2>/dev/null || docker compose stop 2>/dev/null || true
        echo "✓ Docker services stopped"
    else
        # Stop systemd service
        if systemctl is-active --quiet impetus 2>/dev/null; then
            echo "Stopping systemd service..."
            systemctl stop impetus
            echo "✓ systemd service stopped"
        fi
        
        # Stop launchd service (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            PLIST_FILE="/Library/LaunchDaemons/com.gerdsenai.impetus.plist"
            if [[ -f "$PLIST_FILE" ]]; then
                echo "Stopping launchd service..."
                launchctl unload "$PLIST_FILE" 2>/dev/null || true
                echo "✓ launchd service stopped"
            fi
        fi
        
        # Kill any remaining processes
        # Try to kill by PID file if exists
        if [[ -f "$INSTALL_DIR/impetus.pid" ]]; then
            IMPETUS_PID=$(cat "$INSTALL_DIR/impetus.pid")
            if ps -p "$IMPETUS_PID" > /dev/null 2>&1; then
                kill "$IMPETUS_PID" 2>/dev/null || true
                echo "✓ Killed Impetus process (PID: $IMPETUS_PID)"
            fi
        else
            # Fallback: kill by exact command path
            IMPETUS_BIN="$INSTALL_DIR/impetus"
            if [[ -f "$IMPETUS_BIN" ]]; then
                pgrep -x "$(basename "$IMPETUS_BIN")" | while read -r pid; do
                    CMD=$(ps -p "$pid" -o args=)
                    if [[ "$CMD" == "$IMPETUS_BIN"* ]]; then
                        kill "$pid" 2>/dev/null || true
                        echo "✓ Killed Impetus process (PID: $pid)"
                    fi
                done
            else
                echo -e "${YELLOW}Impetus binary not found at $IMPETUS_BIN; skipping process kill.${NC}"
            fi
        fi
        # Also kill gerdsen_ai_server by exact match
        GERDSEN_BIN="$INSTALL_DIR/gerdsen_ai_server"
        pgrep -x "$(basename "$GERDSEN_BIN")" | while read -r pid; do
            CMD=$(ps -p "$pid" -o args=)
            if [[ "$CMD" == "$GERDSEN_BIN"* ]]; then
                kill "$pid" 2>/dev/null || true
                echo "✓ Killed gerdsen_ai_server process (PID: $pid)"
            fi
        done
    fi
}

perform_update() {
    print_section "Performing Update"
    
    cd "$INSTALL_DIR"
    
    # Stash any local changes
    echo "Stashing local changes..."
    git stash push -m "Auto-stash before update $(date)" || true
    
    # Switch to target branch/version
    if [[ -n "$TARGET_VERSION" ]]; then
        echo "Checking out version: $TARGET_VERSION"
        git checkout "$TARGET_VERSION"
    else
        echo "Updating to latest $BRANCH..."
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    fi
    
    NEW_COMMIT=$(git rev-parse HEAD)
    NEW_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")
    
    if [[ -n "$NEW_TAG" ]]; then
        NEW_VERSION="$NEW_TAG"
    else
        NEW_VERSION="${NEW_COMMIT:0:8}"
    fi
    
    echo "✓ Updated to version: $NEW_VERSION"
}

update_dependencies() {
    print_section "Updating Dependencies"
    
    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        echo "Rebuilding Docker images..."
        cd "$INSTALL_DIR"
        docker-compose build --pull 2>/dev/null || docker compose build --pull 2>/dev/null
        echo "✓ Docker images rebuilt"
    else
        # Update Python dependencies
        if [[ -f "$INSTALL_DIR/venv/bin/pip" ]]; then
            VENV_PATH="$INSTALL_DIR/venv"
        elif [[ -f "$INSTALL_DIR/.venv/bin/pip" ]]; then
            VENV_PATH="$INSTALL_DIR/.venv"
        else
            echo -e "${RED}Error: Virtual environment not found${NC}"
            return 1
        fi
        
        echo "Updating Python dependencies..."
        source "$VENV_PATH/bin/activate"
        pip install --upgrade pip
        
        # Install production requirements if they exist
        if [[ -f "$INSTALL_DIR/gerdsen_ai_server/requirements_production.txt" ]]; then
            pip install -r "$INSTALL_DIR/gerdsen_ai_server/requirements_production.txt"
        else
            pip install -r "$INSTALL_DIR/gerdsen_ai_server/requirements.txt"
        fi
        
        # Reinstall package in development mode
        pip install -e .
        
        echo "✓ Python dependencies updated"
        
        # Update frontend dependencies (if dashboard exists)
        if [[ -d "$INSTALL_DIR/impetus-dashboard" ]]; then
            echo "Updating frontend dependencies..."
            cd "$INSTALL_DIR/impetus-dashboard"
            if command -v pnpm &> /dev/null; then
                pnpm install
                pnpm build
            else
                npm install
                npm run build
            fi
            echo "✓ Frontend dependencies updated"
        fi
    fi
}

run_tests() {
    if [[ "$RUN_TESTS" == "true" ]]; then
        print_section "Running Tests"
        
        cd "$INSTALL_DIR"
        
        if [[ "$INSTALL_TYPE" == "docker" ]]; then
            echo "Running tests in Docker..."
            # Start services temporarily for testing
            docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
            sleep 10
            
            # Basic health check
            if curl -f http://localhost:8080/api/health/live 2>/dev/null; then
                echo "✓ Health check passed"
                TEST_RESULT=0
            else
                echo "❌ Health check failed"
                TEST_RESULT=1
            fi
            
            # Stop services
            docker-compose stop 2>/dev/null || docker compose stop 2>/dev/null
        else
            # Run Python tests if they exist
            if [[ -d "$INSTALL_DIR/gerdsen_ai_server/tests" ]]; then
                echo "Running Python tests..."
                cd "$INSTALL_DIR/gerdsen_ai_server"
                source "$VENV_PATH/bin/activate"
                
                if command -v pytest &> /dev/null; then
                    pytest tests/ -v --tb=short
                    TEST_RESULT=$?
                else
                    echo "pytest not found, skipping tests"
                    TEST_RESULT=0
                fi
            else
                echo "No tests found, skipping"
                TEST_RESULT=0
            fi
        fi
        
        if [[ $TEST_RESULT -ne 0 ]]; then
            echo -e "${RED}❌ Tests failed!${NC}"
            return 1
        else
            echo -e "${GREEN}✓ All tests passed${NC}"
        fi
    fi
}

start_services() {
    print_section "Starting Services"
    
    if [[ "$AUTO_RESTART" == "true" ]]; then
        if [[ "$INSTALL_TYPE" == "docker" ]]; then
            echo "Starting Docker services..."
            cd "$INSTALL_DIR"
            docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null
            echo "✓ Docker services started"
        else
            # Start systemd service
            if [[ -f "/etc/systemd/system/impetus.service" ]]; then
                echo "Starting systemd service..."
                systemctl start impetus
                echo "✓ systemd service started"
            fi
            
            # Start launchd service (macOS)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                PLIST_FILE="/Library/LaunchDaemons/com.gerdsenai.impetus.plist"
                if [[ -f "$PLIST_FILE" ]]; then
                    echo "Starting launchd service..."
                    launchctl load "$PLIST_FILE" 2>/dev/null || true
                    echo "✓ launchd service started"
                fi
            fi
        fi
        
        # Wait for service to be ready
        echo "Waiting for service to be ready..."
        sleep 10
        
        # Health check
        for i in {1..30}; do
            if curl -f http://localhost:8080/api/health/live 2>/dev/null; then
                echo "✓ Service is healthy and responding"
                return 0
            fi
            sleep 2
        done
        
        echo -e "${YELLOW}⚠ Service started but health check failed${NC}"
        echo "Manual verification may be required"
    else
        echo "Auto-restart disabled. Start services manually if needed."
    fi
}

perform_rollback() {
    print_section "Rolling Back to Previous Version"
    
    if [[ -z "$ROLLBACK_VERSION" ]]; then
        # Find the most recent backup
        BACKUP_DIRS=("$INSTALL_DIR"/.backups/*/)
        if [[ ${#BACKUP_DIRS[@]} -eq 0 ]]; then
            echo -e "${RED}Error: No backups found for rollback${NC}"
            return 1
        fi
        
        # Get the most recent backup
        LATEST_BACKUP=$(ls -td "$INSTALL_DIR"/.backups/*/ | head -1)
        ROLLBACK_COMMIT=$(cat "$LATEST_BACKUP/commit.txt" 2>/dev/null || echo "")
        
        if [[ -z "$ROLLBACK_COMMIT" ]]; then
            echo -e "${RED}Error: Cannot determine rollback version${NC}"
            return 1
        fi
        
        ROLLBACK_VERSION="$ROLLBACK_COMMIT"
    fi
    
    echo "Rolling back to: $ROLLBACK_VERSION"
    
    cd "$INSTALL_DIR"
    
    # Stop services
    stop_services
    
    # Checkout previous version
    git checkout "$ROLLBACK_VERSION"
    
    # Restore configuration if available
    if [[ -f "$LATEST_BACKUP/.env" ]]; then
        cp "$LATEST_BACKUP/.env" "$INSTALL_DIR/"
    fi
    
    # Update dependencies
    update_dependencies
    
    # Start services
    start_services
    
    echo -e "${GREEN}✓ Rollback completed${NC}"
}

cleanup_backups() {
    print_section "Cleaning Up Old Backups"
    
    BACKUP_BASE_DIR="$INSTALL_DIR/.backups"
    
    if [[ -d "$BACKUP_BASE_DIR" ]]; then
        # Keep only the last 5 backups
        cd "$BACKUP_BASE_DIR"
        ls -t | tail -n +6 | xargs -r rm -rf
        echo "✓ Old backups cleaned up (kept last 5)"
    fi
}

print_success() {
    print_section "Update Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🎉 Update Successful! 🎉                   ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📋 Update Summary:${NC}
─────────────────
• Previous version: $CURRENT_VERSION
• New version: $NEW_VERSION
• Installation type: $INSTALL_TYPE
• Backup created: Yes

${BLUE}🌐 Service Status:${NC}
─────────────────
• API Documentation: http://localhost:8080/docs
• Health Check: http://localhost:8080/api/health/status
• OpenAI API: http://localhost:8080/v1/

${BLUE}🔧 Post-Update Commands:${NC}
─────────────────────────
• Check status: curl http://localhost:8080/api/health/status
• View logs: 
EOF

    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        echo "  docker-compose logs -f impetus-server"
    else
        echo "  journalctl -u impetus -f  # Linux"
        echo "  tail -f /var/log/impetus.log  # macOS"
    fi
    
    cat << EOF
• Restart if needed: 
EOF

    if [[ "$INSTALL_TYPE" == "docker" ]]; then
        echo "  docker-compose restart impetus-server"
    else
        echo "  systemctl restart impetus  # Linux"
        echo "  launchctl unload/load service  # macOS"
    fi
    
    cat << EOF

${BLUE}🔄 Rollback (if needed):${NC}
─────────────────────────
• To rollback: $0 --rollback
• Manual rollback: git checkout $CURRENT_COMMIT

${GREEN}✨ Impetus LLM Server has been successfully updated! ✨${NC}

EOF
}

# Main update flow
main() {
    print_header
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --branch)
                BRANCH="$2"
                shift 2
                ;;
            --version)
                TARGET_VERSION="$2"
                shift 2
                ;;
            --force)
                FORCE_UPDATE="true"
                shift
                ;;
            --no-backup)
                BACKUP_CONFIG="false"
                shift
                ;;
            --no-tests)
                RUN_TESTS="false"
                shift
                ;;
            --no-restart)
                AUTO_RESTART="false"
                shift
                ;;
            --rollback)
                ROLLBACK_VERSION="$2"
                ACTION="rollback"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --install-dir DIR   Installation directory"
                echo "  --branch BRANCH     Git branch to update from (default: main)"
                echo "  --version VERSION   Specific version/tag to update to"
                echo "  --force            Force update even if up to date"
                echo "  --no-backup        Skip configuration backup"
                echo "  --no-tests         Skip running tests"
                echo "  --no-restart       Don't restart services automatically"
                echo "  --rollback [VER]   Rollback to previous or specific version"
                echo "  --help             Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    detect_installation
    
    if [[ "$ACTION" == "rollback" ]]; then
        perform_rollback
        exit 0
    fi
    
    check_current_version
    check_available_updates
    backup_current_state
    
    # Perform update with rollback on failure
    if ! (
        stop_services &&
        perform_update &&
        update_dependencies &&
        run_tests &&
        start_services
    ); then
        echo -e "${RED}❌ Update failed! Initiating automatic rollback...${NC}"
        perform_rollback
        exit 1
    fi
    
    cleanup_backups
    print_success
}

# Run main function
main "$@"