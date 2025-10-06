import importlib
from typing import Any, Dict

import pytest

from src.providers import qwen_provider


def _reload_provider():
    import src.config as config

    importlib.reload(config)
    importlib.reload(qwen_provider)
    return qwen_provider


def test_qwen_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    provider_module = _reload_provider()

    provider = provider_module.QwenProvider()

    with pytest.raises(RuntimeError):
        provider.chat([{"role": "user", "content": "hi"}])


def test_qwen_provider_chat_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("MODEL_NAME", "configured-model")
    provider_module = _reload_provider()

    provider = provider_module.QwenProvider()
    calls: dict[str, Any] = {}

    class DummyResponse:
        def raise_for_status(self) -> None:
            calls["status"] = "ok"

        def json(self) -> Dict[str, Any]:
            return {"choices": [{"message": {"content": "Hello"}}]}

    def fake_post(
        url: str, json: Dict[str, Any], headers: Dict[str, str], timeout: int
    ):
        calls.update({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return DummyResponse()

    monkeypatch.setattr(provider_module.requests, "post", fake_post)

    result = provider.chat(
        [{"role": "user", "content": "hi"}], model_override="override-model"
    )

    assert result == "Hello"
    assert calls["json"]["model"] == "override-model"
    assert calls["headers"]["Authorization"] == "Bearer key"
    assert calls["timeout"] == 30
