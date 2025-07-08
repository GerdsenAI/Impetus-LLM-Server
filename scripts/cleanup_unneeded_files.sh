#!/bin/bash

# Script to clean up unneeded files, scripts, and directories in Impetus-LLM-Server
# This script creates a backup before deletion and logs all actions
# Use with caution and review the list of files to be deleted

# Set up logging
LOG_FILE="cleanup_log_$(date +%Y%m%d_%H%M%S).txt"
echo "Cleanup started at $(date)" > "$LOG_FILE"

# Create a backup directory with timestamp
BACKUP_DIR="/tmp/impetus_cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup directory created at $BACKUP_DIR" >> "$LOG_FILE"

# Function to backup and log
backup_and_log() {
    local item="$1"
    if [ -e "$item" ]; then
        echo "Backing up $item to $BACKUP_DIR" >> "$LOG_FILE"
        cp -r "$item" "$BACKUP_DIR/"
    else
        echo "Item $item does not exist, skipping backup" >> "$LOG_FILE"
    fi
}

# Function to remove item after backup
remove_item() {
    local item="$1"
    backup_and_log "$item"
    if [ -e "$item" ]; then
        echo "Removing $item" >> "$LOG_FILE"
        rm -rf "$item"
    else
        echo "Item $item does not exist, skipping removal" >> "$LOG_FILE"
    fi
}

# List of items to remove (add or modify as needed)
# These are considered unneeded based on project status and MVP completion
# Focus is on preserving core backend and server functionality in 'gerdsen_ai_server/src'
UNNEEDED_ITEMS=(
    "config/models"                    # Non-essential model configurations
    "docs/API_REFERENCE.md"            # Potentially outdated documentation
    "docs/ENHANCEMENT_SUMMARY.md"      # Potentially outdated documentation
    "docs/INSTALLATION.md"             # Potentially outdated documentation
    "docs/vscode_integration.md"       # Potentially outdated documentation
    "instance"                         # Old instance data
    "scripts/build_macos.sh"           # Old build script
    "scripts/build_with_pyinstaller.sh" # Old build script
    "scripts/download_example_model.py" # Non-essential script
    "scripts/generate_ssl_certs.sh"    # Old script for certificates
    "scripts/install.sh"               # Old installation script
    "scripts/setup_user_models.py"     # Non-essential setup script
    "scripts/start_production.sh"      # Old start script
    "tests/conftest.py"                # Non-critical test configuration
    "tests/test_gguf_inference.py"     # Old test script
    "tests/test_gguf_integration.py"   # Old test script
    "tests/test_model_loader_factory.py" # Old test script
    "tests/test_production_functionality.py" # Old test script
    "tests/model_loaders"              # Non-critical test directory
    "tests/puppeteer/e2e"              # Non-critical test directory
    "tests/puppeteer/integration"      # Non-critical test directory
    "tests/puppeteer/performance"      # Non-critical test directory
    "tests/puppeteer/setup"            # Non-critical test directory
    "tests/puppeteer/utils"            # Non-critical test directory
    "tests/puppeteer/package.json"     # Old test dependency file
    "tests/puppeteer/README.md"        # Non-essential documentation
    "tests/puppeteer/run-tests.js"     # Old test runner
    "tests/puppeteer/SETUP_COMPLETE.md" # Non-essential documentation
    "tests/puppeteer/test-report.html" # Old test report
    "research_findings.md"             # Potentially outdated documentation
    "todo.md"                          # Potentially outdated task list
    ".env.example"                     # Non-essential configuration example
    ".gitignore"                       # Can be regenerated if needed
    "cleanup_log_20250708_003924.txt"  # Old log file
    "cleanup_log_20250708_004923.txt"  # Old log file
    "INSTALLATION.md"                  # Potentially outdated documentation
    "README.md"                        # Potentially outdated documentation
)

echo "WARNING: This script will remove files and directories that may be unneeded." >> "$LOG_FILE"
echo "Please review the list of items to be removed in the script before proceeding." >> "$LOG_FILE"
echo "A backup will be created at $BACKUP_DIR before any deletion." >> "$LOG_FILE"

# Prompt for confirmation (comment out if running in non-interactive mode)
read -p "Do you want to proceed with the cleanup? (y/N): " confirm
if [[ "$confirm" != [yY] ]]; then
    echo "Cleanup aborted by user at $(date)" >> "$LOG_FILE"
    exit 1
fi

# Perform cleanup
for item in "${UNNEEDED_ITEMS[@]}"; do
    remove_item "$item"
done

echo "Cleanup completed at $(date)" >> "$LOG_FILE"
echo "All actions logged to $LOG_FILE"
echo "Backup of removed files available at $BACKUP_DIR"

# End of script
