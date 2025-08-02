"""
WSGI entry point for Gunicorn
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.main import app, socketio, create_app

# Create and initialize the application
app, socketio = create_app()

# Export the application and socketio for Gunicorn
application = app

if __name__ == "__main__":
    # This won't be called when running under Gunicorn
    # but allows for testing the WSGI entry point directly
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)