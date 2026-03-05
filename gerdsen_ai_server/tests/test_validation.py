"""
Unit tests for request validation utilities (utils/validation.py).
"""

import json

import pytest
from flask import Flask
from pydantic import BaseModel, Field
from src.utils.validation import (
    ValidationConfig,
    create_response,
    validate_conversation_id,
    validate_json,
    validate_model_id,
    validate_path_params,
    validate_query_params,
)


class SampleSchema(BaseModel):
    """Test schema for validation decorator."""

    name: str
    value: int = Field(default=0)


class TestValidateJsonDecorator:
    """Tests for the validate_json decorator."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with decorated route."""
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.route("/test", methods=["POST"])
        @validate_json(SampleSchema)
        def test_route(validated_data):
            return {"name": validated_data.name, "value": validated_data.value}

        @app.route("/optional", methods=["POST"])
        @validate_json(SampleSchema, required=False)
        def optional_route(validated_data):
            if validated_data is None:
                return {"result": "no data"}
            return {"name": validated_data.name}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_valid_json_passes(self, client):
        """Valid JSON matching schema passes validation."""
        response = client.post("/test", json={"name": "test", "value": 42})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "test"
        assert data["value"] == 42

    def test_missing_required_json_body(self, client):
        """Missing JSON body returns 400 when required."""
        response = client.post("/test", content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_validation_error_missing_field(self, client):
        """Missing required field returns 400 with validation details."""
        response = client.post("/test", json={"value": 42})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["type"] == "validation_error"
        assert "details" in data

    def test_validation_error_wrong_type(self, client):
        """Wrong field type returns 400."""
        response = client.post("/test", json={"name": "test", "value": "not_int"})
        assert response.status_code == 400

    def test_optional_json_no_body(self, client):
        """Optional JSON body passes None when not provided."""
        response = client.post("/optional")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["result"] == "no data"

    def test_default_values_used(self, client):
        """Default values are applied for missing optional fields."""
        response = client.post("/test", json={"name": "test"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["value"] == 0


class TestCreateResponse:
    """Tests for create_response helper."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_dict_response(self, app):
        """Dict data serializes correctly."""
        with app.app_context():
            response, status = create_response({"key": "value"})
            data = json.loads(response.data)
            assert data["key"] == "value"
            assert status == 200

    def test_pydantic_model_response(self, app):
        """Pydantic model serializes via .dict()."""
        with app.app_context():
            model = SampleSchema(name="test", value=5)
            response, status = create_response(model)
            data = json.loads(response.data)
            assert data["name"] == "test"
            assert status == 200

    def test_custom_status_code(self, app):
        """Custom status code is returned."""
        with app.app_context():
            _, status = create_response({"error": "bad"}, 400)
            assert status == 400

    def test_list_response(self, app):
        """List data serializes correctly."""
        with app.app_context():
            response, _status = create_response([1, 2, 3])
            data = json.loads(response.data)
            assert data == [1, 2, 3]


class TestValidateModelId:
    """Tests for validate_model_id function."""

    def test_valid_huggingface_id(self):
        """Valid HuggingFace model ID passes."""
        result = validate_model_id("mlx-community/Mistral-7B")
        assert result == "mlx-community/Mistral-7B"

    def test_valid_simple_id(self):
        """Simple model ID without slash passes."""
        result = validate_model_id("my-model")
        assert result == "my-model"

    def test_empty_id_raises(self):
        """Empty model ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_model_id("")

    def test_whitespace_only_raises(self):
        """Whitespace-only model ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_model_id("   ")

    def test_too_long_raises(self):
        """Model ID over 255 chars raises ValueError."""
        with pytest.raises(ValueError, match="too long"):
            validate_model_id("a" * 256)

    def test_invalid_slug_format(self):
        """Invalid HuggingFace format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model ID format"):
            validate_model_id("org/repo/extra")

    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        result = validate_model_id("  my-model  ")
        assert result == "my-model"


class TestValidateConversationId:
    """Tests for validate_conversation_id function."""

    def test_valid_id(self):
        """Valid alphanumeric conversation ID passes."""
        result = validate_conversation_id("chat-123_abc")
        assert result == "chat-123_abc"

    def test_empty_raises(self):
        """Empty conversation ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_conversation_id("")

    def test_too_long_raises(self):
        """Conversation ID over 255 chars raises ValueError."""
        with pytest.raises(ValueError, match="too long"):
            validate_conversation_id("a" * 256)

    def test_invalid_characters_raises(self):
        """Special characters raise ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_conversation_id("chat@123!")


class TestValidateQueryParams:
    """Tests for validate_query_params decorator.

    Note: validate_query_params uses Pydantic v1 field_info.type_ which is
    broken in Pydantic v2. Tests verify the error handling paths.
    """

    @pytest.fixture
    def app(self):
        """Create test Flask app with query-param-decorated route."""
        app = Flask(__name__)
        app.config["TESTING"] = True

        class OptionalSchema(BaseModel):
            name: str = "default"

        @app.route("/search")
        @validate_query_params(SampleSchema)
        def search(validated_params):
            return {"name": validated_params.name, "value": validated_params.value}

        @app.route("/optional")
        @validate_query_params(OptionalSchema)
        def optional_search(validated_params):
            return {"name": validated_params.name}

        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_no_params_required_schema_returns_400(self, client):
        """Missing required params returns 400 validation error."""
        response = client.get("/search")
        assert response.status_code == 400

    def test_all_defaults_no_params_succeeds(self, client):
        """Schema with all-default fields works with no query params."""
        response = client.get("/optional")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "default"


class TestValidatePathParams:
    """Tests for validate_path_params decorator."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with path-param-validated route."""
        app = Flask(__name__)
        app.config["TESTING"] = True

        def positive_int(value):
            v = int(value)
            if v <= 0:
                raise ValueError("Must be positive")
            return v

        @app.route("/items/<item_id>")
        @validate_path_params(item_id=positive_int)
        def get_item(item_id, validated_path_params):
            return {"item_id": item_id}

        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_valid_path_param(self, client):
        """Valid path param passes validation."""
        response = client.get("/items/42")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["item_id"] == 42

    def test_invalid_path_param(self, client):
        """Negative value triggers error handler (callable validators
        don't catch ValueError internally — falls to outer except)."""
        response = client.get("/items/-1")
        assert response.status_code == 500

    def test_non_numeric_path_param(self, client):
        """Non-numeric string triggers error handler."""
        response = client.get("/items/abc")
        assert response.status_code == 500


class TestValidateModelIdExtras:
    """Additional tests for validate_model_id edge cases."""

    def test_invalid_characters_in_org(self):
        """Invalid characters in org part raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_model_id("org@bad/model")

    def test_empty_org_with_slash(self):
        """Empty org with slash raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            validate_model_id("/model")


class TestValidationConfig:
    """Tests for ValidationConfig constants."""

    def test_max_request_size(self):
        """MAX_REQUEST_SIZE is 10MB."""
        assert ValidationConfig.MAX_REQUEST_SIZE == 10 * 1024 * 1024

    def test_max_string_length(self):
        """MAX_STRING_LENGTH is 100000."""
        assert ValidationConfig.MAX_STRING_LENGTH == 100000
