import builtins
import json
import sys
import types
from typing import Any, Dict, List

import pytest

import chatbot
from chatbot import Message


def test_parse_args_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "argv", ["chatbot"])

    args = chatbot.parse_args()

    assert args.provider == "mock"
    assert args.model is None
    assert args.once is None
    assert args.system == "You are a helpful assistant."


def test_parse_args_custom(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "chatbot",
            "--provider",
            "qwen",
            "--model",
            "test-model",
            "--once",
            "ping",
            "--system",
            "custom",
        ],
    )

    args = chatbot.parse_args()

    assert args.provider == "qwen"
    assert args.model == "test-model"
    assert args.once == "ping"
    assert args.system == "custom"


def test_run_once_prints_reply(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    seen_messages: list[list[Message]] = []

    def fake_run_inference(
        provider: str, model: str | None, messages: List[Message]
    ) -> str:
        seen_messages.append(list(messages))
        return "bot reply"

    monkeypatch.setattr(chatbot, "run_inference", fake_run_inference)

    chatbot.run_once("mock", None, "sys", "hi")

    captured = capsys.readouterr().out
    assert "bot reply" in captured
    assert seen_messages[0][-1].content == "hi"


def test_chat_loop_handles_exit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    inputs = iter(["Hello", "exit"])

    def fake_input(prompt: str = "") -> str:
        return next(inputs)

    def fake_run_inference(
        provider: str, model: str | None, messages: List[Message]
    ) -> str:
        assert messages[-1].role == "user"
        return "loop reply"

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(chatbot, "run_inference", fake_run_inference)

    chatbot.chat_loop("mock", "model-a", "sys")

    output = capsys.readouterr().out
    assert "Provider: mock" in output
    assert "Model: model-a" in output
    assert "Bot: loop reply" in output
    assert output.strip().endswith("Bye!")


def test_openai_infer_success(monkeypatch: pytest.MonkeyPatch):
    calls: dict[str, Any] = {}

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str | None = None):
            calls["params"] = {"api_key": api_key, "base_url": base_url}
            self.chat = types.SimpleNamespace(completions=self)

        def create(self, model: str, messages: List[Dict[str, str]]):
            calls["request"] = {"model": model, "messages": messages}
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content=" hi there ")
                    )
                ]
            )

    module = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", module)
    monkeypatch.setenv("OPENAI_API_KEY", "abc123")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    result = chatbot.openai_infer("gpt", [Message("user", "hi")])

    assert result.strip() == "hi there"
    assert calls["params"] == {"api_key": "abc123", "base_url": None}
    assert calls["request"]["model"] == "gpt"


def test_openai_infer_missing_package(monkeypatch: pytest.MonkeyPatch):
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "openai":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setenv("OPENAI_API_KEY", "abc123")

    with pytest.raises(RuntimeError) as exc:
        chatbot.openai_infer("gpt", [])

    assert "openai" in str(exc.value)


def test_openai_infer_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    module = types.SimpleNamespace(OpenAI=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "openai", module)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc:
        chatbot.openai_infer("gpt", [])

    assert "OPENAI_API_KEY" in str(exc.value)


def test_openai_infer_requires_model(monkeypatch: pytest.MonkeyPatch):
    module = types.SimpleNamespace(OpenAI=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "openai", module)
    monkeypatch.setenv("OPENAI_API_KEY", "abc123")

    with pytest.raises(RuntimeError) as exc:
        chatbot.openai_infer(None, [])

    assert "--model" in str(exc.value)


def test_ollama_infer_success(monkeypatch: pytest.MonkeyPatch):
    class DummyResponse:
        def __init__(self):
            self.calls: dict[str, Any] = {}

        def raise_for_status(self):
            self.calls["status"] = "ok"

        def json(self):
            return {"message": {"content": " hi there "}}

    response = DummyResponse()

    def fake_post(url: str, data: str, headers: Dict[str, str], timeout: int):
        body = json.loads(data)
        assert body["model"] == "llama"
        assert body["messages"][0]["role"] == "user"
        response.calls.update({"headers": headers, "timeout": timeout})
        return response

    monkeypatch.setattr(chatbot, "requests", types.SimpleNamespace(post=fake_post))

    result = chatbot.ollama_infer("llama", [Message("user", "hi")])

    assert result.strip() == "hi there"
    assert response.calls["timeout"] == 120
    assert "application/json" in response.calls["headers"]["Content-Type"]


def test_ollama_infer_requires_model():
    with pytest.raises(RuntimeError) as exc:
        chatbot.ollama_infer(None, [])

    assert "--model" in str(exc.value)


def test_ollama_infer_requires_requests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(chatbot, "requests", None)

    with pytest.raises(RuntimeError) as exc:
        chatbot.ollama_infer("model", [])

    assert "requests" in str(exc.value)


def test_qwen_infer_uses_provider(monkeypatch: pytest.MonkeyPatch):
    calls: dict[str, Any] = {}

    class FakeProvider:
        def chat(
            self, messages: List[Dict[str, str]], model_override: str | None = None
        ) -> str:
            calls["messages"] = messages
            calls["model_override"] = model_override
            return "ok"

    monkeypatch.setattr(chatbot, "QwenProvider", lambda: FakeProvider())

    result = chatbot.qwen_infer("override", [Message("user", "hi")])

    assert result == "ok"
    assert calls["model_override"] == "override"
    assert calls["messages"][0]["role"] == "user"


def test_mock_infer_handles_question():
    reply = chatbot.mock_infer(
        [
            Message("system", "sys"),
            Message("user", "What time is it?"),
        ]
    )

    assert "I can't access real data" in reply


def test_mock_infer_handles_farewell():
    reply = chatbot.mock_infer(
        [
            Message("user", "Bye"),
        ]
    )

    assert "Talk soon" in reply


def test_mock_provider_delegates():
    messages = [Message("user", "hi")]

    assert chatbot.MockProvider.infer(messages) == chatbot.mock_infer(messages)
