"""Unit tests for the chatbot module.

The tests exercise the lightweight mock provider and the inference dispatcher.

Learner Note: This is the expected format.
"""

import builtins
import importlib
import json
import sys
import types
from pathlib import Path

import pytest

# Ensure the project root (which contains chatbot.py) is importable when tests
# are executed directly or via pytest from the tests directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_chatbot_module():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    return importlib.import_module("chatbot")


chatbot_module = _load_chatbot_module()
qwen_provider_module = importlib.import_module("src.providers.qwen_provider")
Message = chatbot_module.Message
mock_infer = chatbot_module.mock_infer
run_inference = chatbot_module.run_inference
parse_args = chatbot_module.parse_args
run_once = chatbot_module.run_once
openai_infer = chatbot_module.openai_infer
ollama_infer = chatbot_module.ollama_infer
qwen_infer = chatbot_module.qwen_infer


def test_mock_infer_without_user_messages():
    reply = mock_infer([Message("system", "You are helpful.")])
    assert "Hello" in reply


def test_mock_infer_tracks_conversation_context():
    messages = [
        Message("system", "You are helpful."),
        Message("user", "Hello bot"),
        Message("assistant", "Hi human"),
        Message("user", "What can you do?"),
    ]

    reply = mock_infer(messages)

    assert 'Earlier you mentioned "Hello bot".' in reply
    assert 'I hear you saying "What can you do?".' in reply
    assert "love to hear your thoughts" in reply


def test_run_inference_dispatches_to_mock(monkeypatch):
    messages = [Message("system", "sys"), Message("user", "ping")]
    sentinel = "mock says hi"

    def fake_mock_infer(seen_messages):
        assert seen_messages is messages
        return sentinel

    monkeypatch.setattr("chatbot.mock_infer", fake_mock_infer)

    result = run_inference("mock", None, messages)
    assert result == sentinel


def test_run_inference_rejects_unknown_provider():
    with pytest.raises(ValueError):
        run_inference("unknown", None, [])


def test_parse_args_uses_defaults(monkeypatch):
    monkeypatch.setenv("PYTHONWARNINGS", "")
    monkeypatch.setattr(sys, "argv", ["chatbot.py"])

    args = parse_args()

    assert args.provider == "mock"
    assert args.model is None
    assert args.system == "You are a helpful assistant."


def test_run_once_prints_response(monkeypatch, capsys):
    sentinel = "mock reply"

    def fake_run_inference(provider, model, messages):
        assert provider == "mock"
        assert model is None
        assert messages[-1].content == "Hello"
        return sentinel

    monkeypatch.setattr(chatbot_module, "run_inference", fake_run_inference)

    run_once("mock", None, "sys", "Hello")

    captured = capsys.readouterr()
    assert sentinel in captured.out


def test_run_inference_dispatches_openai(monkeypatch):
    messages = [Message("system", "s"), Message("user", "hi")]
    sentinel = "openai reply"

    def fake_openai(model, seen_messages):
        assert model == "gpt"
        assert seen_messages is messages
        return sentinel

    monkeypatch.setattr(chatbot_module, "openai_infer", fake_openai)

    result = run_inference("openai", "gpt", messages)
    assert result == sentinel


def test_run_inference_dispatches_ollama(monkeypatch):
    messages = [Message("system", "s"), Message("user", "hi")]
    sentinel = "ollama reply"

    def fake_ollama(model, seen_messages):
        assert model == "llama"
        assert seen_messages is messages
        return sentinel

    monkeypatch.setattr(chatbot_module, "ollama_infer", fake_ollama)

    result = run_inference("ollama", "llama", messages)
    assert result == sentinel


def test_run_inference_dispatches_qwen(monkeypatch):
    messages = [Message("system", "s"), Message("user", "hi")]
    sentinel = "qwen reply"

    def fake_qwen(model, seen_messages):
        assert model == "qwen-model"
        assert seen_messages is messages
        return sentinel

    monkeypatch.setattr(chatbot_module, "qwen_infer", fake_qwen)

    result = run_inference("qwen", "qwen-model", messages)
    assert result == sentinel


def test_openai_infer_requires_api_key(monkeypatch):
    class DummyCompletions:
        @staticmethod
        def create(*, model, messages):
            raise AssertionError("Should not call API when key missing")

    class DummyChat:
        completions = DummyCompletions()

    class DummyClient:
        chat = DummyChat()

        def __init__(self, *args, **kwargs):
            pass

    dummy_module = types.SimpleNamespace(OpenAI=DummyClient)
    monkeypatch.setitem(sys.modules, "openai", dummy_module)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        openai_infer("demo", [Message("user", "hi")])

    assert "OPENAI_API_KEY" in str(excinfo.value)


def test_ollama_infer_success(monkeypatch):
    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class DummyRequests:
        def __init__(self):
            self.captured = None

        def post(self, url, data, headers, timeout):
            self.captured = {
                "url": url,
                "data": json.loads(data),
                "headers": headers,
                "timeout": timeout,
            }
            return DummyResponse({"message": {"content": "ok"}})

    dummy_requests = DummyRequests()
    monkeypatch.setattr(chatbot_module, "requests", dummy_requests)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    result = ollama_infer("llama", [Message("user", "hi")])

    assert result == "ok"
    assert dummy_requests.captured["data"]["model"] == "llama"


def test_ollama_infer_requires_requests(monkeypatch):
    monkeypatch.setattr(chatbot_module, "requests", None)

    with pytest.raises(RuntimeError) as excinfo:
        ollama_infer("llama", [Message("user", "hi")])

    assert "requests" in str(excinfo.value)


def test_qwen_infer_uses_provider(monkeypatch):
    captured = {}

    class DummyProvider:
        def __init__(self):
            captured["created"] = True

        def chat(self, messages, model_override=None):
            captured["messages"] = messages
            captured["override"] = model_override
            return "provider reply"

    monkeypatch.setattr(chatbot_module, "QwenProvider", DummyProvider)

    result = qwen_infer("override", [Message("user", "hi")])

    assert result == "provider reply"
    assert captured["override"] == "override"
    assert captured["messages"][0]["role"] == "user"


def test_chat_loop_handles_exit(monkeypatch, capsys):
    inputs = iter(["", "Hello", "/exit"])

    def fake_input(prompt):
        return next(inputs)

    def fake_run_inference(provider, model, messages):
        return "loop reply"

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(chatbot_module, "run_inference", fake_run_inference)

    chatbot_module.chat_loop("mock", None, "Sys")

    output = capsys.readouterr().out
    assert "Provider: mock" in output
    assert "loop reply" in output


def test_openai_infer_success(monkeypatch):
    class DummyResponse:
        def __init__(self):
            message = types.SimpleNamespace(content=" hi ")
            self.choices = [types.SimpleNamespace(message=message)]

    class DummyClient:
        def __init__(self, *args, **kwargs):
            def create(*, model, messages):
                DummyClient.captured = {"model": model, "messages": messages}
                return DummyResponse()

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    dummy_module = types.SimpleNamespace(OpenAI=DummyClient)
    monkeypatch.setitem(sys.modules, "openai", dummy_module)
    monkeypatch.setenv("OPENAI_API_KEY", "token")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    result = openai_infer("demo", [Message("user", "hi")])

    assert result == "hi"
    assert DummyClient.captured["model"] == "demo"
    assert DummyClient.captured["messages"][0]["role"] == "user"


def test_qwen_provider_chat(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.called = False

        def raise_for_status(self):
            self.called = True

        def json(self):
            return {"choices": [{"message": {"content": "qwen says hi"}}]}

    dummy_response = DummyResponse()

    def fake_post(url, json=None, headers=None, timeout=None):
        assert "Authorization" in headers
        assert json["messages"][0]["role"] == "user"
        return dummy_response

    monkeypatch.setattr(qwen_provider_module.requests, "post", fake_post)
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("MODEL_NAME", "configured")

    provider = qwen_provider_module.QwenProvider()
    result = provider.chat(
        [{"role": "user", "content": "hi"}], model_override="override"
    )

    assert result == "qwen says hi"
    assert dummy_response.called is True
