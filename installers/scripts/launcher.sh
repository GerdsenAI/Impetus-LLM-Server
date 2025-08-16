#!/bin/bash
#
# Impetus LLM Server - Application Launcher
# This script is the main executable inside the .app bundle
#

# Get the directory where this script is located (Contents/MacOS)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENTS_DIR="$(dirname "$SCRIPT_DIR")"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
APP_DIR="$(dirname "$CONTENTS_DIR")"

# Set up paths
PYTHON_RUNTIME="$CONTENTS_DIR/Frameworks/Python.framework/Versions/Current/bin/python3"
IMPETUS_CODE="$RESOURCES_DIR/gerdsen_ai_server"
FIRST_RUN_SCRIPT="$RESOURCES_DIR/first_run.py"
MENUBAR_SCRIPT="$RESOURCES_DIR/run_menubar.py"

# Log file for debugging
LOG_FILE="$HOME/Library/Logs/Impetus/launcher.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to show error dialog
show_error() {
    local title="$1"
    local message="$2"
    
    osascript -e "display dialog \"$message\" with title \"$title\" buttons {\"OK\"} default button \"OK\" with icon stop"
    log_message "ERROR: $title - $message"
}

# Function to show info dialog
show_info() {
    local title="$1"
    local message="$2"
    
    osascript -e "display dialog \"$message\" with title \"$title\" buttons {\"OK\"} default button \"OK\" with icon note"
    log_message "INFO: $title - $message"
}

# Function to check if this is the first run
is_first_run() {
    local prefs_file="$HOME/Library/Preferences/com.gerdsenai.impetus.plist"
    if [[ ! -f "$prefs_file" ]]; then
        return 0  # First run
    fi
    
    # Check if first run flag exists
    local first_run_completed=$(defaults read com.gerdsenai.impetus FirstRunCompleted 2>/dev/null || echo "0")
    if [[ "$first_run_completed" != "1" ]]; then
        return 0  # First run
    fi
    
    return 1  # Not first run
}

# Function to mark first run as completed
mark_first_run_completed() {
    defaults write com.gerdsenai.impetus FirstRunCompleted -bool true
    log_message "First run marked as completed"
}

# Function to check system requirements
check_system_requirements() {
    log_message "Checking system requirements..."
    
    # Check macOS version
    local macos_version=$(sw_vers -productVersion)
    local major_version=$(echo "$macos_version" | cut -d. -f1)
    local minor_version=$(echo "$macos_version" | cut -d. -f2)
    
    if [[ $major_version -lt 13 ]]; then
        show_error "System Requirements" "Impetus requires macOS 13.0 (Ventura) or later. You have macOS $macos_version."
        return 1
    fi
    
    # Check architecture
    local arch=$(uname -m)
    if [[ "$arch" != "arm64" ]]; then
        show_error "System Requirements" "Impetus requires Apple Silicon (M1/M2/M3/M4). Your system architecture is $arch."
        return 1
    fi
    
    # Check available memory
    local memory_gb=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    if [[ $memory_gb -lt 8 ]]; then
        show_info "System Requirements" "Impetus recommends at least 8GB of RAM for optimal performance. You have ${memory_gb}GB."
    fi
    
    log_message "System requirements check passed"
    return 0
}

# Function to ensure Python runtime is available
check_python_runtime() {
    log_message "Checking Python runtime..."
    
    if [[ ! -f "$PYTHON_RUNTIME" ]]; then
        show_error "Python Runtime" "Python runtime not found at $PYTHON_RUNTIME. Please reinstall Impetus."
        return 1
    fi
    
    # Test Python execution
    if ! "$PYTHON_RUNTIME" -c "import sys; print(f'Python {sys.version}' )" >> "$LOG_FILE" 2>&1; then
        show_error "Python Runtime" "Python runtime failed to execute. Please reinstall Impetus."
        return 1
    fi
    
    log_message "Python runtime check passed"
    return 0
}

# Function to run first-time setup
run_first_setup() {
    log_message "Running first-time setup..."
    
    if [[ ! -f "$FIRST_RUN_SCRIPT" ]]; then
        log_message "First run script not found, skipping setup"
        return 0
    fi
    
    # Run first-time setup
    if "$PYTHON_RUNTIME" "$FIRST_RUN_SCRIPT" >> "$LOG_FILE" 2>&1; then
        mark_first_run_completed
        log_message "First-time setup completed successfully"
        return 0
    else
        show_error "Setup Failed" "First-time setup failed. Check the log file at $LOG_FILE for details."
        return 1
    fi
}

# Function to launch the menu bar application
launch_menubar_app() {
    log_message "Launching menu bar application..."
    
    if [[ ! -f "$MENUBAR_SCRIPT" ]]; then
        show_error "Application Error" "Menu bar application not found at $MENUBAR_SCRIPT. Please reinstall Impetus."
        return 1
    fi
    
    # Set up isolated Python environment for bundled libraries
    BUNDLED_SITE_PACKAGES="$CONTENTS_DIR/Frameworks/Python.framework/Versions/Current/lib/python3.13/site-packages"
    unset PYTHONPATH  # Clear any existing Python path
    export PYTHONPATH="$BUNDLED_SITE_PACKAGES:$RESOURCES_DIR"
    export IMPETUS_APP_MODE="bundled"
    export IMPETUS_ENVIRONMENT="production"
    export IMPETUS_RESOURCES_DIR="$RESOURCES_DIR"
    
    # Secure production settings
    export IMPETUS_HOST="127.0.0.1"  # Force localhost-only binding
    export IMPETUS_PORT="8080"
    export IMPETUS_DEBUG="false"
    export IMPETUS_LOG_LEVEL="info"
    
    # Force Python to use only bundled libraries
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONOPTIMIZE=1
    export PYTHONNOUSERSITE=1
    
    log_message "Set PYTHONPATH to: $PYTHONPATH"
    
    # Change to the application directory
    cd "$RESOURCES_DIR"
    
    # Apply production configuration if available (fail gracefully)
    if [[ -f "$RESOURCES_DIR/gerdsen_ai_server/src/config/production.py" ]]; then
        log_message "Applying production configuration..."
        if "$PYTHON_RUNTIME" -c "
import sys
sys.path.insert(0, '$RESOURCES_DIR/gerdsen_ai_server/src')
try:
    from config.production import configure_production_environment, validate_production_security
    configure_production_environment()
    validate_production_security()
    print('✅ Production configuration applied successfully')
except ImportError as e:
    print(f'⚠️ Production configuration skipped: {e}')
except Exception as e:
    print(f'⚠️ Production configuration failed: {e}')
" >> "$LOG_FILE" 2>&1; then
            log_message "Production configuration applied successfully"
        else
            log_message "Production configuration failed, continuing without it"
        fi
    fi
    
    # Launch the menu bar application
    log_message "Executing: $PYTHON_RUNTIME $MENUBAR_SCRIPT"
    exec "$PYTHON_RUNTIME" "$MENUBAR_SCRIPT"
}

# Function to handle application termination
cleanup() {
    log_message "Application terminating..."
    # Kill any background processes if needed
    pkill -f "gerdsen_ai_server" 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    log_message "=== Impetus LLM Server Starting ==="
    log_message "Script directory: $SCRIPT_DIR"
    log_message "Resources directory: $RESOURCES_DIR"
    log_message "Python runtime: $PYTHON_RUNTIME"
    
    # Check system requirements
    if ! check_system_requirements; then
        exit 1
    fi
    
    # Check Python runtime
    if ! check_python_runtime; then
        exit 1
    fi
    
    # Run first-time setup if needed
    if is_first_run; then
        log_message "First run detected, running setup..."
        if ! run_first_setup; then
            exit 1
        fi
    fi
    
    # Launch the main application
    launch_menubar_app
}

# Execute main function
main "$@"