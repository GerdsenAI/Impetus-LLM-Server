# Lightweight Web Server Service Setup for Impetus-LLM-Server Frontend

## Purpose
This document provides detailed instructions for setting up a lightweight web server service to support the frontend of the Impetus-LLM-Server project. This service is designed to efficiently deliver APIs and static files for the Vite and Ant Design-based frontend, focusing on VectorDB and MCP service dashboards while minimizing resource usage.

## Overview
The lightweight web server service leverages the existing Flask backend located in 'gerdsen_ai_server/src'. It is optimized to:
- Serve static files for the frontend built with Vite.
- Handle API requests for model management, hardware metrics, and optimization settings.
- Maintain OpenAI API compatibility for seamless integration with VS Code extensions like Cline.
- Operate with reduced overhead compared to the full production server, ensuring efficient resource usage for frontend support.

## Prerequisites
- **Python 3.8+**: Ensure Python is installed on your system.
- **Virtual Environment**: It's recommended to use a virtual environment to manage dependencies.
- **Project Dependencies**: Install the required packages listed in 'requirements_production.txt' for the backend.

## Setup Steps

### 1. Prepare the Environment
Ensure you are in the project root directory '/Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server'. Activate a virtual environment if desired:

```bash
source .venv/bin/activate
```

Install the necessary dependencies:

```bash
pip install -r requirements_production.txt
```

### 2. Create or Modify the Lightweight Service Script
Create a new script or modify an existing one to run a lightweight version of the Flask server. For this purpose, we'll use a new file named 'lightweight_frontend_server.py' in the 'gerdsen_ai_server/src' directory. Below is an example configuration for this script:

```python
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
```

This script:
- Sets up a Flask app to serve static files from the Vite-built frontend located in 'gerdsen-ai-frontend/build'.
- Registers essential API blueprints for model management, hardware metrics, and OpenAI-compatible endpoints.
- Configures CORS to allow cross-origin requests from the frontend.
- Runs on port 8080 by default, which can be adjusted if needed.

### 3. Build the Frontend
Ensure the frontend is built using Vite. Navigate to the frontend directory (if it exists) and run the build command:

```bash
cd gerdsen-ai-frontend
npm run build
```

This will generate the static files in 'gerdsen-ai-frontend/build' (adjust the path if your frontend build output directory differs).

### 4. Run the Lightweight Service
Start the lightweight web server service with the following command from the project root:

```bash
python gerdsen_ai_server/src/lightweight_frontend_server.py
```

This will launch the server on port 8080, serving the frontend static files and handling API requests.

### 5. Test the Integration
- Open a browser and navigate to `http://localhost:8080` to verify that the frontend loads correctly.
- Use tools like Puppeteer or manual testing to ensure API endpoints are accessible and responsive. For automated testing, refer to the test suite in 'tests/puppeteer'.

### 6. Troubleshooting
- **Port Conflicts**: If port 8080 is in use, modify the port in 'lightweight_frontend_server.py' to an available one.
- **Static Files Not Loading**: Verify the 'static_folder' path in the script points to the correct build directory of your frontend.
- **API Errors**: Check server logs for errors related to blueprint registration or CORS issues. Ensure all necessary modules are imported and dependencies are installed.

## Configuration Options
- **Port**: Adjust the port in the `app.run()` call to change where the server listens.
- **Static Folder**: Modify 'static_folder' in the Flask app setup to point to a different frontend build directory if needed.
- **API Blueprints**: Add or remove blueprints in the script to include only the necessary API endpoints for your frontend.

## Performance Optimization
- **Minimize Blueprints**: Only register the API blueprints required by the frontend to reduce server load.
- **Use Production Settings**: Ensure `debug=False` and `use_reloader=False` in `app.run()` to avoid unnecessary overhead in production.
- **Caching**: Consider adding caching mechanisms for static files and API responses if performance becomes an issue.

## Notes
- This lightweight service is intended for frontend support and may not include all functionalities of the full production server. For full backend capabilities, use 'production_main.py' or other comprehensive server scripts.
- Ensure the frontend build process is complete before starting the service to avoid serving incomplete or missing static files.
- Regularly update this document as the project evolves to reflect any changes in the setup process or configuration requirements.

## Future Enhancements
- **SSL/HTTPS Support**: Add SSL configuration for secure communication, especially for remote access scenarios.
- **Load Balancing**: Implement basic load balancing if multiple frontend instances are needed.
- **Integration with Electron App**: Ensure this lightweight service can be bundled or invoked by the Electron app for a seamless desktop experience.

This setup guide ensures developers can quickly deploy a lightweight web server service to support the Impetus-LLM-Server frontend, facilitating efficient development and testing of VectorDB and MCP service dashboards.
