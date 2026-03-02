"""
Unit tests for OpenAI-compatible chat completions API endpoints
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.routes.openai_api import bp, convert_messages_to_prompt
from src.schemas.openai_schemas import ChatMessage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_model(model_id="test-model", response_text="Hello from the model"):
    """Create a mock model object with generate() and tokenize() methods."""
    model = MagicMock()
    model.model_id = model_id
    model.generate.return_value = response_text
    model.tokenize.return_value = list(range(5))  # 5 fake tokens
    return model


def _chat_payload(model="test-model", messages=None, **overrides):
    """Return a minimal valid chat-completion request body."""
    if messages is None:
        messages = [{"role": "user", "content": "Hi"}]
    payload = {"model": model, "messages": messages, **overrides}
    return payload


# ---------------------------------------------------------------------------
# TestAuth
# ---------------------------------------------------------------------------


class TestAuth:
    """Tests for API-key authentication on the OpenAI blueprint."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with no auth bypass."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp, url_prefix="/v1")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {},
            "model_inference_counts": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_no_auth_header_returns_401(self, client):
        """A request without an Authorization header must receive 401."""
        with patch("src.routes.openai_api.settings") as mock_settings:
            mock_settings.server.api_key = "secret-key"
            response = client.get("/v1/models")

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_bearer_returns_401(self, client):
        """A request with a wrong Bearer token must receive 401."""
        with patch("src.routes.openai_api.settings") as mock_settings:
            mock_settings.server.api_key = "secret-key"
            response = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer wrong-key"},
            )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_valid_bearer_passes(self, client):
        """A request with the correct Bearer token must be accepted."""
        with patch("src.routes.openai_api.settings") as mock_settings:
            mock_settings.server.api_key = "secret-key"
            mock_settings.model.default_model = "default-model"
            response = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer secret-key"},
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# TestListModels
# ---------------------------------------------------------------------------


class TestListModels:
    """Tests for the GET /v1/models endpoint."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp, url_prefix="/v1")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {},
            "model_inference_counts": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture(autouse=True)
    def disable_auth(self):
        """Bypass authentication for model-listing tests."""
        with patch("src.routes.openai_api.verify_api_key", return_value=True):
            yield

    def test_list_models_empty(self, client):
        """When no models are loaded the response should contain the default model."""
        response = client.get("/v1/models")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        model_entry = data["data"][0]
        assert model_entry["object"] == "model"
        assert model_entry["owned_by"] == "impetus"
        assert "id" in model_entry

    def test_list_models_with_loaded(self, app, client):
        """Loaded models should be listed with correct OpenAI-compatible fields."""
        mock_model_a = _make_mock_model("model-a")
        mock_model_b = _make_mock_model("model-b")
        app.config["app_state"]["loaded_models"] = {
            "model-a": mock_model_a,
            "model-b": mock_model_b,
        }

        response = client.get("/v1/models")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["object"] == "list"
        assert len(data["data"]) == 2
        ids = {m["id"] for m in data["data"]}
        assert ids == {"model-a", "model-b"}
        for entry in data["data"]:
            assert entry["object"] == "model"
            assert entry["owned_by"] == "impetus"
            assert "created" in entry


# ---------------------------------------------------------------------------
# TestChatCompletions
# ---------------------------------------------------------------------------


class TestChatCompletions:
    """Tests for the POST /v1/chat/completions endpoint."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp, url_prefix="/v1")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {},
            "model_inference_counts": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture(autouse=True)
    def disable_auth(self):
        """Bypass authentication for chat-completion tests."""
        with patch("src.routes.openai_api.verify_api_key", return_value=True):
            yield

    # ---- non-streaming ----

    def test_non_streaming_response_shape(self, app, client):
        """Non-streaming response must contain id, object, choices, and usage fields."""
        mock_model = _make_mock_model()
        app.config["app_state"]["loaded_models"]["test-model"] = mock_model

        response = client.post(
            "/v1/chat/completions",
            json=_chat_payload(stream=False),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Top-level fields
        assert data["id"].startswith("chatcmpl-")
        assert data["object"] == "chat.completion"
        assert "created" in data
        assert data["model"] == "test-model"

        # Choices
        assert len(data["choices"]) == 1
        choice = data["choices"][0]
        assert choice["index"] == 0
        assert choice["message"]["role"] == "assistant"
        assert isinstance(choice["message"]["content"], str)
        assert choice["finish_reason"] == "stop"

        # Usage
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    # ---- streaming ----

    def test_streaming_returns_sse(self, app, client):
        """Streaming response must have text/event-stream content-type and data: prefixed lines."""
        mock_model = _make_mock_model(response_text="OK")
        app.config["app_state"]["loaded_models"]["test-model"] = mock_model

        response = client.post(
            "/v1/chat/completions",
            json=_chat_payload(stream=True),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.content_type

        raw = response.get_data(as_text=True)
        lines = [line for line in raw.split("\n") if line.strip()]
        # Every non-empty line must start with "data: "
        for line in lines:
            assert line.startswith("data: "), f"Unexpected SSE line format: {line!r}"

        # The stream must end with [DONE]
        assert lines[-1] == "data: [DONE]"

        # First data chunk should have the role delta
        first_chunk = json.loads(lines[0].removeprefix("data: "))
        assert first_chunk["object"] == "chat.completion.chunk"
        assert first_chunk["choices"][0]["delta"]["role"] == "assistant"

    # ---- model not loaded ----

    def test_model_not_loaded_auto_load_fails(self, client):
        """If the requested model is not loaded and auto-load fails, return 404."""
        with patch("src.model_loaders.mlx_loader.MLXModelLoader") as mock_loader_cls:
            loader_instance = MagicMock()
            loader_instance.load_model.side_effect = RuntimeError("model not found")
            mock_loader_cls.return_value = loader_instance

            response = client.post(
                "/v1/chat/completions",
                json=_chat_payload(model="missing-model"),
                content_type="application/json",
            )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_model_not_loaded_auto_load_succeeds(self, app, client):
        """If the model is not loaded but auto-load succeeds, the request should complete."""
        mock_model = _make_mock_model("auto-model", "Auto loaded response")

        with patch("src.model_loaders.mlx_loader.MLXModelLoader") as mock_loader_cls:
            loader_instance = MagicMock()
            loader_instance.load_model.return_value = mock_model
            mock_loader_cls.return_value = loader_instance

            response = client.post(
                "/v1/chat/completions",
                json=_chat_payload(model="auto-model", stream=False),
                content_type="application/json",
            )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["model"] == "auto-model"
        assert data["choices"][0]["message"]["content"] == "Auto loaded response"
        # Model should now be registered in loaded_models
        assert "auto-model" in app.config["app_state"]["loaded_models"]

    # ---- validation errors ----

    def test_validation_error_missing_messages(self, client):
        """A request without messages must return 400."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "test-model"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["type"] == "validation_error"

    def test_validation_error_missing_model(self, client):
        """A request without model must return 400."""
        response = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["type"] == "validation_error"

    # ---- RAG injection ----

    def test_rag_injection(self, app, client):
        """When use_rag=True, build_rag_context should be called and a system message prepended."""
        mock_model = _make_mock_model()
        app.config["app_state"]["loaded_models"]["test-model"] = mock_model

        # The function is lazily imported inside chat_completions via a relative import
        # that resolves to gerdsen_ai_server.src.services.rag_pipeline.  We patch both
        # the long-form and short-form module paths so the mock is found regardless of
        # which sys.modules entry the runtime resolves.
        with patch(
            "gerdsen_ai_server.src.services.rag_pipeline.build_rag_context",
            return_value=("Relevant context from docs", [{"source": "doc.txt"}]),
        ) as mock_rag:
            response = client.post(
                "/v1/chat/completions",
                json=_chat_payload(use_rag=True, stream=False),
                content_type="application/json",
            )

        assert response.status_code == 200
        mock_rag.assert_called_once()

        # Verify the prompt sent to generate() includes the RAG context
        call_args = mock_model.generate.call_args
        prompt = call_args[0][0]  # first positional arg
        assert "Relevant context from docs" in prompt

        # Verify rag_sources appear in the response
        data = json.loads(response.data)
        assert "rag_sources" in data
        assert data["rag_sources"][0]["source"] == "doc.txt"

    def test_context_documents_injection(self, app, client):
        """When context_documents are provided, a system message containing them should be prepended."""
        mock_model = _make_mock_model()
        app.config["app_state"]["loaded_models"]["test-model"] = mock_model

        docs = ["First context snippet", "Second context snippet"]
        response = client.post(
            "/v1/chat/completions",
            json=_chat_payload(context_documents=docs, stream=False),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify the prompt includes the context documents
        call_args = mock_model.generate.call_args
        prompt = call_args[0][0]
        assert "First context snippet" in prompt
        assert "Second context snippet" in prompt
        assert "Use this context" in prompt


# ---------------------------------------------------------------------------
# TestConvertMessages
# ---------------------------------------------------------------------------


class TestConvertMessages:
    """Tests for the convert_messages_to_prompt() utility function."""

    def test_empty_messages(self):
        """An empty message list should produce an empty string."""
        result = convert_messages_to_prompt([])
        assert result == ""

    def test_user_message_only(self):
        """A single user message should produce 'User: ...' followed by 'Assistant:' prompt."""
        result = convert_messages_to_prompt([{"role": "user", "content": "Hello"}])
        assert "User: Hello" in result
        assert result.endswith("Assistant:")

    def test_system_and_user(self):
        """A system message followed by a user message should include the system prefix."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        result = convert_messages_to_prompt(messages)
        assert "System: You are helpful." in result
        assert "User: Hi" in result
        assert result.endswith("Assistant:")

    def test_multi_turn_conversation(self):
        """A multi-turn conversation should contain all user and assistant turns and end with 'Assistant:'."""
        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
            {"role": "user", "content": "And 3+3?"},
        ]
        result = convert_messages_to_prompt(messages)
        assert "User: What is 2+2?" in result
        assert "Assistant: 4" in result
        assert "User: And 3+3?" in result
        # The final prompt must end with the assistant prompt
        assert result.strip().endswith("Assistant:")

    def test_dict_and_pydantic_messages(self):
        """Both plain dicts and ChatMessage Pydantic objects should produce identical prompts."""
        dict_messages = [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Summarize this."},
        ]
        pydantic_messages = [
            ChatMessage(role="system", content="Be concise."),
            ChatMessage(role="user", content="Summarize this."),
        ]
        result_dict = convert_messages_to_prompt(dict_messages)
        result_pydantic = convert_messages_to_prompt(pydantic_messages)
        assert result_dict == result_pydantic
        assert "System: Be concise." in result_dict
        assert "User: Summarize this." in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
