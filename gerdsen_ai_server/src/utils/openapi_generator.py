"""
OpenAPI documentation generator for Flask routes with Pydantic schemas
"""

import inspect
import json
import re
from typing import Any, get_type_hints

from flask import Flask
from pydantic import BaseModel

from ..config.settings import settings


class OpenAPIGenerator:
    """Generate OpenAPI 3.0 specification from Flask app and Pydantic schemas"""

    def __init__(self, app: Flask):
        self.app = app
        self.spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Impetus LLM Server API",
                "description": "High-performance local LLM server optimized for Apple Silicon",
                "version": settings.version,
                "contact": {
                    "name": "GerdsenAI",
                    "url": "https://github.com/GerdsenAI/Impetus-LLM-Server",
                    "email": "support@gerdsenai.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": f"http://localhost:{settings.server.port}",
                    "description": "Local development server"
                },
                {
                    "url": "https://api.impetus.local",
                    "description": "Production server"
                }
            ],
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "API key authentication"
                    }
                }
            },
            "paths": {},
            "security": [{"bearerAuth": []}],
            "tags": [
                {
                    "name": "OpenAI Compatible",
                    "description": "OpenAI-compatible endpoints for AI assistants"
                },
                {
                    "name": "Model Management",
                    "description": "Model discovery, download, loading, and management"
                },
                {
                    "name": "Hardware Monitoring",
                    "description": "Apple Silicon hardware monitoring and optimization"
                },
                {
                    "name": "Health Checks",
                    "description": "Health checks and monitoring endpoints"
                }
            ]
        }

    def generate_schema_from_pydantic(self, model: BaseModel) -> dict[str, Any]:
        """Generate OpenAPI schema from Pydantic model"""
        if hasattr(model, 'schema'):
            return model.schema()
        return {}

    def get_pydantic_model_name(self, model: BaseModel) -> str:
        """Get the name of a Pydantic model for schema reference"""
        return model.__name__

    def add_pydantic_schema(self, model: BaseModel) -> str:
        """Add Pydantic model to components/schemas and return reference"""
        model_name = self.get_pydantic_model_name(model)
        if model_name not in self.spec["components"]["schemas"]:
            schema = self.generate_schema_from_pydantic(model)
            self.spec["components"]["schemas"][model_name] = schema
        return f"#/components/schemas/{model_name}"

    def extract_route_info(self, rule, endpoint):
        """Extract information from Flask route"""
        view_func = self.app.view_functions.get(endpoint)
        if not view_func:
            return None

        # Get HTTP methods
        methods = list(rule.methods - {'OPTIONS', 'HEAD'})
        if not methods:
            return None

        # Get docstring
        description = view_func.__doc__ or ""

        # Get function signature for parameters
        sig = inspect.signature(view_func)

        # Extract validation decorators
        validation_info = self.extract_validation_info(view_func)

        return {
            "methods": methods,
            "description": description.strip(),
            "parameters": self.extract_parameters(rule, sig),
            "validation": validation_info,
            "tags": self.determine_tags(rule.rule)
        }

    def extract_validation_info(self, view_func) -> dict[str, Any]:
        """Extract Pydantic validation information from decorated function"""
        validation_info = {
            "request_schema": None,
            "response_schema": None,
            "path_params": {},
            "query_params": None
        }

        # Check for validation decorators by examining the function's closure
        if hasattr(view_func, '__closure__') and view_func.__closure__:
            for cell in view_func.__closure__:
                cell_contents = cell.cell_contents
                if inspect.isclass(cell_contents) and issubclass(cell_contents, BaseModel):
                    # This is likely a Pydantic schema used in validation
                    validation_info["request_schema"] = cell_contents
                    break

        # Try to extract from function annotations
        type_hints = get_type_hints(view_func)
        for param_name, param_type in type_hints.items():
            if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                if 'validated_data' in param_name:
                    validation_info["request_schema"] = param_type
                elif 'validated_params' in param_name:
                    validation_info["query_params"] = param_type

        return validation_info

    def extract_parameters(self, rule, signature) -> list[dict[str, Any]]:
        """Extract path and query parameters"""
        parameters = []

        # Path parameters
        for param in rule.arguments:
            parameters.append({
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"Path parameter: {param}"
            })

        return parameters

    def determine_tags(self, path: str) -> list[str]:
        """Determine appropriate tags based on the path"""
        if path.startswith('/v1'):
            return ["OpenAI Compatible"]
        elif '/models' in path:
            return ["Model Management"]
        elif '/hardware' in path:
            return ["Hardware Monitoring"]
        elif '/health' in path:
            return ["Health Checks"]
        else:
            return ["General"]

    def generate_request_body(self, validation_info: dict[str, Any]) -> dict[str, Any] | None:
        """Generate request body specification"""
        if not validation_info.get("request_schema"):
            return None

        schema_ref = self.add_pydantic_schema(validation_info["request_schema"])

        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": schema_ref}
                }
            }
        }

    def generate_responses(self, validation_info: dict[str, Any], method: str) -> dict[str, Any]:
        """Generate response specifications"""
        responses = {
            "400": {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "type": {"type": "string"},
                                "details": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "Authentication required",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }

        # Success response
        if method in ['GET', 'POST']:
            success_schema = {"type": "object"}

            if validation_info.get("response_schema"):
                schema_ref = self.add_pydantic_schema(validation_info["response_schema"])
                success_schema = {"$ref": schema_ref}

            responses["200"] = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": success_schema
                    }
                }
            }

        return responses

    def add_route_to_spec(self, rule, route_info: dict[str, Any]):
        """Add a route to the OpenAPI specification"""
        path = rule.rule

        # Convert Flask path parameters to OpenAPI format
        openapi_path = re.sub(r'<(?:int:)?([^>]+)>', r'{\1}', path)

        if openapi_path not in self.spec["paths"]:
            self.spec["paths"][openapi_path] = {}

        for method in route_info["methods"]:
            operation = {
                "summary": route_info["description"].split('\n')[0] if route_info["description"] else f"{method} {openapi_path}",
                "description": route_info["description"],
                "tags": route_info["tags"],
                "parameters": route_info["parameters"],
                "responses": self.generate_responses(route_info["validation"], method)
            }

            # Add request body for POST/PUT/PATCH
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                request_body = self.generate_request_body(route_info["validation"])
                if request_body:
                    operation["requestBody"] = request_body

            # Add security requirement
            operation["security"] = [{"bearerAuth": []}]

            self.spec["paths"][openapi_path][method.lower()] = operation

    def generate_spec(self) -> dict[str, Any]:
        """Generate complete OpenAPI specification"""
        # Add common schemas first
        self.add_common_schemas()

        # Process all routes
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint and not rule.endpoint.startswith('static'):
                route_info = self.extract_route_info(rule, rule.endpoint)
                if route_info:
                    self.add_route_to_spec(rule, route_info)

        return self.spec

    def add_common_schemas(self):
        """Add common schemas used across the API"""
        # Import and add common schemas
        try:
            from ..schemas.hardware_schemas import HardwareInfo, OptimizationResponse, SystemMetrics
            from ..schemas.health_schemas import (
                DetailedHealthResponse,
                HealthStatus,
                LivenessResponse,
                ReadinessResponse,
            )
            from ..schemas.model_schemas import BenchmarkResult, ModelDownloadRequest, ModelLoadRequest, WarmupResult
            from ..schemas.model_schemas import ModelListResponse as ModelManagementResponse
            from ..schemas.openai_schemas import (
                ChatCompletionRequest,
                ChatCompletionResponse,
                CompletionRequest,
                CompletionResponse,
                ErrorResponse,
                ModelListResponse,
            )

            # Add schemas
            schemas_to_add = [
                ChatCompletionRequest, ChatCompletionResponse,
                CompletionRequest, CompletionResponse,
                ModelListResponse, ErrorResponse,
                ModelDownloadRequest, ModelLoadRequest,
                ModelManagementResponse, BenchmarkResult, WarmupResult,
                HealthStatus, DetailedHealthResponse,
                ReadinessResponse, LivenessResponse,
                HardwareInfo, SystemMetrics, OptimizationResponse
            ]

            for schema in schemas_to_add:
                self.add_pydantic_schema(schema)

        except ImportError as e:
            print(f"Warning: Could not import some schemas: {e}")

    def save_spec(self, filename: str = "openapi.json"):
        """Save OpenAPI specification to file"""
        spec = self.generate_spec()
        with open(filename, 'w') as f:
            json.dump(spec, f, indent=2)
        return spec


def generate_openapi_spec(app: Flask) -> dict[str, Any]:
    """Generate OpenAPI specification for the Flask app"""
    generator = OpenAPIGenerator(app)
    return generator.generate_spec()


def create_swagger_ui_route(app: Flask, spec_url: str = "/api/docs/openapi.json"):
    """Create Swagger UI route for the Flask app"""

    @app.route('/api/docs')
    @app.route('/docs')
    def swagger_ui():
        """Swagger UI for API documentation"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Impetus LLM Server API Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
            <style>
                html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                *, *:before, *:after {{ box-sizing: inherit; }}
                body {{ margin:0; background: #fafafa; }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        url: '{spec_url}',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        defaultModelsExpandDepth: 1,
                        defaultModelExpandDepth: 1,
                        docExpansion: "list",
                        filter: true,
                        showExtensions: true,
                        showCommonExtensions: true
                    }});
                }};
            </script>
        </body>
        </html>
        '''

    @app.route(spec_url)
    def openapi_spec():
        """OpenAPI specification endpoint"""
        spec = generate_openapi_spec(app)
        return spec
