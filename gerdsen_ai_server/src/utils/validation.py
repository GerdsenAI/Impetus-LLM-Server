"""
Request validation utilities using Pydantic schemas
"""

from functools import wraps
from typing import TypeVar

from flask import jsonify, request
from loguru import logger
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)


def validate_json(schema: type[T], required: bool = True) -> T | dict:
    """
    Decorator to validate JSON request body using Pydantic schema
    
    Args:
        schema: Pydantic model class to validate against
        required: Whether JSON body is required
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get JSON data
                json_data = request.get_json()

                # Check if JSON is required
                if required and json_data is None:
                    return jsonify({
                        'error': 'Request body must be valid JSON',
                        'type': 'invalid_request_error'
                    }), 400

                # If JSON is not required and not provided, pass None
                if not required and json_data is None:
                    validated_data = None
                else:
                    # Validate using Pydantic schema
                    validated_data = schema(**json_data)

                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data

                return f(*args, **kwargs)

            except ValidationError as e:
                logger.warning(f"Validation error in {f.__name__}: {e}")

                # Format validation errors
                errors = []
                for error in e.errors():
                    field = '.'.join(str(x) for x in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")

                return jsonify({
                    'error': 'Invalid request data',
                    'type': 'validation_error',
                    'details': errors
                }), 400

            except Exception as e:
                logger.error(f"Unexpected error in validation for {f.__name__}: {e}")
                return jsonify({
                    'error': 'Internal server error during validation',
                    'type': 'internal_error'
                }), 500

        return decorated_function
    return decorator


def validate_query_params(schema: type[T]) -> T | dict:
    """
    Decorator to validate query parameters using Pydantic schema
    
    Args:
        schema: Pydantic model class to validate against
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get query parameters
                query_data = request.args.to_dict()

                # Convert string values to appropriate types based on schema
                # This is a simple approach - for complex types, you might need custom conversion
                for field_name, field_info in schema.__fields__.items():
                    if field_name in query_data:
                        value = query_data[field_name]
                        field_type = field_info.type_

                        # Handle common type conversions
                        if field_type == bool:
                            query_data[field_name] = value.lower() in ('true', '1', 'yes', 'on')
                        elif field_type == int:
                            query_data[field_name] = int(value)
                        elif field_type == float:
                            query_data[field_name] = float(value)
                        # Lists from comma-separated strings
                        elif hasattr(field_type, '__origin__') and field_type.__origin__ == list:
                            query_data[field_name] = value.split(',') if value else []

                # Validate using Pydantic schema
                validated_data = schema(**query_data)

                # Add validated data to kwargs
                kwargs['validated_params'] = validated_data

                return f(*args, **kwargs)

            except ValidationError as e:
                logger.warning(f"Query parameter validation error in {f.__name__}: {e}")

                # Format validation errors
                errors = []
                for error in e.errors():
                    field = '.'.join(str(x) for x in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")

                return jsonify({
                    'error': 'Invalid query parameters',
                    'type': 'validation_error',
                    'details': errors
                }), 400

            except (ValueError, TypeError) as e:
                logger.warning(f"Type conversion error in {f.__name__}: {e}")
                return jsonify({
                    'error': 'Invalid parameter types',
                    'type': 'type_error',
                    'details': [str(e)]
                }), 400

            except Exception as e:
                logger.error(f"Unexpected error in query validation for {f.__name__}: {e}")
                return jsonify({
                    'error': 'Internal server error during validation',
                    'type': 'internal_error'
                }), 500

        return decorated_function
    return decorator


def validate_path_params(**param_schemas):
    """
    Decorator to validate path parameters using Pydantic field validators
    
    Args:
        **param_schemas: Dict of parameter name to validation function
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validated_params = {}

                for param_name, validator in param_schemas.items():
                    if param_name in kwargs:
                        value = kwargs[param_name]

                        # Apply validation
                        if callable(validator):
                            validated_value = validator(value)
                            validated_params[param_name] = validated_value
                            kwargs[param_name] = validated_value
                        else:
                            # If not callable, treat as a type
                            try:
                                validated_value = validator(value)
                                validated_params[param_name] = validated_value
                                kwargs[param_name] = validated_value
                            except (ValueError, TypeError) as e:
                                return jsonify({
                                    'error': f'Invalid path parameter {param_name}',
                                    'type': 'validation_error',
                                    'details': [str(e)]
                                }), 400

                # Add validated params to kwargs
                kwargs['validated_path_params'] = validated_params

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Unexpected error in path validation for {f.__name__}: {e}")
                return jsonify({
                    'error': 'Internal server error during validation',
                    'type': 'internal_error'
                }), 500

        return decorated_function
    return decorator


def create_response(data: BaseModel | dict | list, status_code: int = 200) -> tuple:
    """
    Create a JSON response from Pydantic model or dict
    
    Args:
        data: Data to serialize
        status_code: HTTP status code
    
    Returns:
        Tuple of (response, status_code)
    """
    try:
        if isinstance(data, BaseModel):
            # Use Pydantic's JSON serialization
            return jsonify(data.dict()), status_code
        else:
            return jsonify(data), status_code
    except Exception as e:
        logger.error(f"Error creating response: {e}")
        return jsonify({
            'error': 'Internal server error during response serialization',
            'type': 'internal_error'
        }), 500


def validate_model_id(model_id: str) -> str:
    """
    Validate model ID format
    
    Args:
        model_id: Model identifier to validate
    
    Returns:
        Validated model ID
    
    Raises:
        ValueError: If model ID is invalid
    """
    if not model_id or not model_id.strip():
        raise ValueError("Model ID cannot be empty")

    model_id = model_id.strip()

    # Check length
    if len(model_id) > 255:
        raise ValueError("Model ID too long (max 255 characters)")

    # Basic format validation for HuggingFace model IDs
    if '/' in model_id:
        parts = model_id.split('/')
        if len(parts) != 2:
            raise ValueError("Invalid model ID format (should be 'organization/model-name')")

        organization, model_name = parts
        if not organization or not model_name:
            raise ValueError("Both organization and model name must be non-empty")

        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', organization) or not re.match(r'^[a-zA-Z0-9_.-]+$', model_name):
            raise ValueError("Model ID contains invalid characters")

    return model_id


def validate_conversation_id(conversation_id: str) -> str:
    """
    Validate conversation ID format
    
    Args:
        conversation_id: Conversation identifier to validate
    
    Returns:
        Validated conversation ID
    
    Raises:
        ValueError: If conversation ID is invalid
    """
    if not conversation_id or not conversation_id.strip():
        raise ValueError("Conversation ID cannot be empty")

    conversation_id = conversation_id.strip()

    # Check length
    if len(conversation_id) > 255:
        raise ValueError("Conversation ID too long (max 255 characters)")

    # Allow alphanumeric, hyphens, and underscores
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', conversation_id):
        raise ValueError("Conversation ID contains invalid characters")

    return conversation_id


class ValidationConfig:
    """Configuration for validation behavior"""

    # Maximum request size in bytes (10MB default)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024

    # Maximum string field length
    MAX_STRING_LENGTH = 100000

    # Maximum array length
    MAX_ARRAY_LENGTH = 1000

    # Enable strict validation
    STRICT_VALIDATION = True

    # Log validation errors
    LOG_VALIDATION_ERRORS = True
