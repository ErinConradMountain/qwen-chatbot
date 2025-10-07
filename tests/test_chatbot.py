import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import chatbot
from chatbot import (
    Message,
    chat_loop,
    mock_infer,
    openai_infer,
    ollama_infer,
    parse_args,
    qwen_infer,
    run_inference,
    run_once,
)
from src.providers import qwen_provider


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Clear provider-related environment variables between tests."""
    for key in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENROUTER_API_KEY",
        "MODEL_NAME",
        "OLLAMA_BASE_URL",
    ]:
        monkeypatch.delenv(key, raising=False)


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


def test_run_inference_dispatches_to_qwen(monkeypatch):
    sentinel = "qwen response"

    def fake_qwen_infer(model, messages):
        assert model == "override"
        assert messages[-1].content == "hi"
        return sentinel

    monkeypatch.setattr("chatbot.qwen_infer", fake_qwen_infer)

    messages = [Message("system", "sys"), Message("user", "hi")]
    assert run_inference("qwen", "override", messages) == sentinel


def test_run_inference_rejects_unknown_provider():
    with pytest.raises(ValueError):
        run_inference("unknown", None, [])

def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["chatbot.py"])
    args = parse_args()
    assert args.provider == "mock"
    assert args.system == "You are a helpful assistant."
    assert args.once is None


def test_chat_loop_handles_conversation(monkeypatch, capsys):
    responses = iter(["reply"])
    inputs = iter(["", "Hello", "/exit"])

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(
        "chatbot.run_inference", lambda provider, model, messages: next(responses)
    )

    chat_loop("mock", "model-x", "system prompt")

    out = capsys.readouterr().out
    assert "Provider: mock" in out
    assert "Model: model-x" in out
    assert "Bot: reply" in out
    assert "Bye!" in out


def test_run_once_executes_single_prompt(monkeypatch, capsys):
    monkeypatch.setattr(
        "chatbot.run_inference", lambda provider, model, messages: "single reply"
    )
    run_once("mock", "model-x", "system prompt", "Hello")
    out = capsys.readouterr().out
    assert "single reply" in out


def test_openai_infer_requires_api_key(monkeypatch):
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        openai_infer("gpt", [Message("user", "hi")])


def test_openai_infer_requires_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    with pytest.raises(RuntimeError, match="--model is required"):
        openai_infer(None, [Message("user", "hi")])


def test_openai_infer_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com")

    class FakeResponse:
        def __init__(self):
            self.choices = [
                SimpleNamespace(message=SimpleNamespace(content=" success "))
            ]

    class FakeClient:
        def __init__(self, *_, **__):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **__: FakeResponse())
            )

    fake_module = SimpleNamespace(OpenAI=FakeClient)
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    result = openai_infer("gpt", [Message("user", "hi")])
    assert result == "success"


def test_openai_infer_raises_runtime_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")

    class FakeClient:
        def __init__(self, *_, **__):
            class FakeChat:
                def __init__(self):
                    self.completions = self

                def create(self, **_):
                    raise RuntimeError("boom")

            self.chat = FakeChat()

    fake_module = SimpleNamespace(OpenAI=FakeClient)
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    with pytest.raises(RuntimeError, match="OpenAI API error: boom"):
        openai_infer("gpt", [Message("user", "hi")])


def test_ollama_infer_requires_model():
    with pytest.raises(RuntimeError, match="--model is required"):
        ollama_infer(None, [Message("user", "hi")])


def test_ollama_infer_requires_requests(monkeypatch):
    monkeypatch.setattr(chatbot, "requests", None)
    with pytest.raises(RuntimeError, match="requests"):
        ollama_infer("model", [Message("user", "hi")])


def test_ollama_infer_success(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeRequests:
        def __init__(self):
            self.calls = []

        def post(self, url, data=None, headers=None, timeout=None):
            self.calls.append(
                {
                    "url": url,
                    "data": data,
                    "headers": headers,
                    "timeout": timeout,
                }
            )
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {"content": "hello"},
                        }
                    ]
                }
            )

    fake_requests = FakeRequests()
    monkeypatch.setattr(chatbot, "requests", fake_requests)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local")

    result = ollama_infer("model", [Message("user", "hi")])
    assert result == "hello"

    call = fake_requests.calls[0]
    assert call["url"].startswith("http://ollama.local")
    assert call["timeout"] == 120


def test_qwen_infer_uses_provider(monkeypatch):
    class FakeProvider:
        def __init__(self):
            self.calls = []

        def chat(self, messages, model_override=None):
            self.calls.append((messages, model_override))
            return "qwen says hi"

    monkeypatch.setattr(chatbot, "QwenProvider", FakeProvider)

    result = qwen_infer("qwen-model", [Message("user", "hi")])
    assert result == "qwen says hi"


def test_qwen_provider_requires_api_key(monkeypatch):
    provider = qwen_provider.QwenProvider()
    provider.api_key = None
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is not set"):
        provider.chat([{"role": "user", "content": "hi"}])


def test_qwen_provider_chat_success(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "token")
    monkeypatch.setenv("MODEL_NAME", "qwen-model")
    importlib.reload(importlib.import_module("src.config"))
    module = importlib.reload(qwen_provider)
    provider = module.QwenProvider()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "generated"}}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        assert url.endswith("/chat/completions")
        assert headers["Authorization"] == "Bearer token"
        assert json["model"] == "qwen-model"
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr(module.requests, "post", fake_post)

    result = provider.chat([{"role": "user", "content": "hi"}])
    assert result == "generated"


def test_config_loads_dotenv(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    env_path.write_text("OPENROUTER_API_KEY=token\nMODEL_NAME=custom\n")
    try:
        if "src.config" in sys.modules:
            del sys.modules["src.config"]
        config = importlib.import_module("src.config")
        importlib.reload(config)
        assert config.OPENROUTER_API_KEY == "token"
        assert config.MODEL_NAME == "custom"
    finally:
        env_path.unlink()
        if "src.config" in sys.modules:
            importlib.reload(importlib.import_module("src.config"))
