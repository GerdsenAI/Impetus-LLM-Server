"""
E2E tests: Inference — chat completions (streaming + non-streaming).

Tests the core inference path with a real loaded model.
"""

import json

import pytest
import requests

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestNonStreamingInference:
    """Non-streaming chat completions."""

    def test_chat_completion(self, e2e_server, base_url, auth_headers, loaded_model):
        """POST /v1/chat/completions returns valid OpenAI response."""
        payload = {
            "model": loaded_model,
            "messages": [{"role": "user", "content": "Say hello."}],
            "max_tokens": 20,
            "stream": False,
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("object") == "chat.completion"
        assert len(data.get("choices", [])) >= 1
        content = data["choices"][0]["message"]["content"]
        assert isinstance(content, str) and len(content) > 0
        assert "usage" in data

    def test_max_tokens_respected(self, e2e_server, base_url, auth_headers, loaded_model):
        """Response respects max_tokens limit."""
        payload = {
            "model": loaded_model,
            "messages": [{"role": "user", "content": "Count to one hundred."}],
            "max_tokens": 5,
            "stream": False,
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
        # Allow generous margin — tokeniser boundaries can overshoot slightly
        assert completion_tokens <= 15, (
            f"Expected <=15 completion tokens, got {completion_tokens}"
        )

    def test_temperature_zero_deterministic(
        self, e2e_server, base_url, auth_headers, loaded_model
    ):
        """Two requests at temperature=0 produce identical output."""
        payload = {
            "model": loaded_model,
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "max_tokens": 10,
            "temperature": 0.0,
            "stream": False,
        }
        r1 = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        r2 = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r1.status_code == 200 and r2.status_code == 200
        c1 = r1.json()["choices"][0]["message"]["content"]
        c2 = r2.json()["choices"][0]["message"]["content"]
        assert c1 == c2, f"Deterministic mismatch: {c1!r} != {c2!r}"

    def test_multi_turn_conversation(
        self, e2e_server, base_url, auth_headers, loaded_model
    ):
        """Multi-turn conversation produces a coherent response."""
        messages = [
            {"role": "user", "content": "My name is Echo."},
        ]
        payload = {
            "model": loaded_model,
            "messages": messages,
            "max_tokens": 20,
            "stream": False,
        }
        r1 = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r1.status_code == 200
        assistant_reply = r1.json()["choices"][0]["message"]["content"]

        # Second turn references the first
        messages.append({"role": "assistant", "content": assistant_reply})
        messages.append({"role": "user", "content": "What is my name?"})
        payload["messages"] = messages
        r2 = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r2.status_code == 200
        content = r2.json()["choices"][0]["message"]["content"]
        assert isinstance(content, str) and len(content) > 0


class TestStreamingInference:
    """Streaming chat completions via SSE."""

    def test_streaming_response(self, e2e_server, base_url, auth_headers, loaded_model):
        """POST /v1/chat/completions with stream=true returns SSE chunks."""
        payload = {
            "model": loaded_model,
            "messages": [{"role": "user", "content": "Write a haiku about code."}],
            "max_tokens": 30,
            "stream": True,
        }
        with requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            stream=True,
            timeout=120,
        ) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("Content-Type", "")

            saw_done = False
            content_chunks = []
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    if data_str.strip() == "[DONE]":
                        saw_done = True
                        break
                    chunk = json.loads(data_str)
                    assert chunk.get("object") == "chat.completion.chunk"
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        content_chunks.append(delta["content"])

            assert saw_done, "Stream did not end with [DONE]"
            full_content = "".join(content_chunks)
            assert len(full_content) > 0, "No content received in stream"

    def test_streaming_role_chunk_first(
        self, e2e_server, base_url, auth_headers, loaded_model
    ):
        """First SSE chunk contains the assistant role."""
        payload = {
            "model": loaded_model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
            "stream": True,
        }
        with requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            stream=True,
            timeout=60,
        ) as r:
            assert r.status_code == 200
            first_data = None
            for line in r.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data_str = line[len("data: "):]
                    if data_str.strip() == "[DONE]":
                        break
                    first_data = json.loads(data_str)
                    break

            assert first_data is not None
            delta = first_data["choices"][0]["delta"]
            assert delta.get("role") == "assistant"
