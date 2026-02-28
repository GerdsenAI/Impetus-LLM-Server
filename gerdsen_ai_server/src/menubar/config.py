"""
Configuration for the Impetus Menu Bar Application
"""

from pathlib import Path

# Application Info
APP_NAME = "Impetus"
APP_VERSION = "1.0.0"
BUNDLE_ID = "com.gerdsenai.impetus"

# Server Configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
API_BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

# Paths
HOME_DIR = Path.home()
APP_SUPPORT_DIR = HOME_DIR / "Library" / "Application Support" / "Impetus"
CONFIG_DIR = APP_SUPPORT_DIR / "config"
MODELS_DIR = APP_SUPPORT_DIR / "models"
LOGS_DIR = APP_SUPPORT_DIR / "logs"
CACHE_DIR = APP_SUPPORT_DIR / "cache"

# Preferences file
PREFERENCES_FILE = HOME_DIR / "Library" / "Preferences" / f"{BUNDLE_ID}.plist"

# Server paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SERVER_DIR = PROJECT_ROOT / "gerdsen_ai_server"
SERVER_MAIN = SERVER_DIR / "src" / "main.py"
DASHBOARD_DIR = PROJECT_ROOT / "impetus-dashboard"

# Menu Bar Icons (will be created as text-based icons using rumps)
ICON_IDLE = "🧠"  # Brain emoji for idle state
ICON_ACTIVE = "🟢"  # Green circle for active
ICON_ERROR = "🔴"  # Red circle for error
ICON_LOADING = "🟡"  # Yellow circle for loading

# API Endpoints
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/health"
MODELS_ENDPOINT = f"{API_BASE_URL}/v1/models"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
LOAD_MODEL_ENDPOINT = f"{API_BASE_URL}/api/models/load"
UNLOAD_MODEL_ENDPOINT = f"{API_BASE_URL}/api/models/unload"

# Health check settings
HEALTH_CHECK_INTERVAL = 5  # seconds
SERVER_STARTUP_TIMEOUT = 30  # seconds
SERVER_SHUTDOWN_TIMEOUT = 10  # seconds

# Default models to show in menu
DEFAULT_MODELS = [
    {
        "id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
        "name": "Mistral 7B (4-bit)",
        "size_gb": 3.8
    },
    {
        "id": "mlx-community/Llama-3.2-3B-Instruct-4bit",
        "name": "Llama 3.2 3B (4-bit)",
        "size_gb": 1.8
    },
    {
        "id": "mlx-community/Phi-3.5-mini-instruct-4bit",
        "name": "Phi 3.5 Mini (4-bit)",
        "size_gb": 2.2
    },
    {
        "id": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        "name": "Qwen 2.5 Coder 7B (4-bit)",
        "size_gb": 4.0
    }
]

# Performance modes
PERFORMANCE_MODES = {
    "efficiency": "Efficiency Mode",
    "balanced": "Balanced Mode",
    "performance": "Performance Mode"
}

# Create necessary directories
def ensure_directories():
    """Create application directories if they don't exist"""
    for directory in [APP_SUPPORT_DIR, CONFIG_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
