from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys

# Adjust the path to ensure imports work correctly in bundled environments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerdsen_ai_server.src.routes.models import models_bp
from gerdsen_ai_server.src.routes.hardware import hardware_bp
from gerdsen_ai_server.src.routes.optimization import optimization_bp
from gerdsen_ai_server.src.routes.openai_api import openai_bp
from gerdsen_ai_server.src.utils.logging_config import setup_structured_logging

# Setup logging
# setup_structured_logging()

app = Flask(__name__, static_folder='../../../gerdsen-ai-frontend/build', static_url_path='/')
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/v1/*": {"origins": "*"}})

# Register API blueprints for essential frontend functionalities
app.register_blueprint(models_bp, url_prefix='/api/models')
app.register_blueprint(hardware_bp, url_prefix='/api/hardware')
app.register_blueprint(optimization_bp, url_prefix='/api/optimization')
app.register_blueprint(openai_bp, url_prefix='/v1')

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
