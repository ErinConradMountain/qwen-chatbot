"""Tests for the OpenRouter Qwen provider used by the new framework."""

import pytest
from providers.openrouter_qwen import OpenRouterQwenProvider


def test_openrouter_qwen_requires_api_key(monkeypatch):
    """Test that OpenRouterQwenProvider raises error when API key is missing."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is not set"):
        OpenRouterQwenProvider()


def test_openrouter_qwen_initializes_with_api_key(monkeypatch):
    """Test that OpenRouterQwenProvider initializes successfully with API key."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    provider = OpenRouterQwenProvider()
    assert provider.api_key == "test_key"
    assert "openrouter.ai" in provider.base_url


def test_openrouter_qwen_custom_base_url(monkeypatch):
    """Test that OpenRouterQwenProvider respects custom base URL."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://custom.api.url/v1")
    provider = OpenRouterQwenProvider()
    assert provider.base_url == "https://custom.api.url/v1"


def test_openrouter_qwen_chat_raises_on_network_error(monkeypatch):
    """Test that chat method raises RuntimeError on network errors."""
    import urllib.request
    
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    provider = OpenRouterQwenProvider()
    
    def mock_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Network error")
    
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(RuntimeError, match="OpenRouter API request failed"):
        provider.chat("qwen/qwen3-4b:free", messages)


def test_openrouter_qwen_chat_raises_on_malformed_response(monkeypatch):
    """Test that chat method raises RuntimeError on malformed API response."""
    import urllib.request
    import json
    
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    provider = OpenRouterQwenProvider()
    
    class FakeResponse:
        def read(self):
            return json.dumps({"invalid": "response"}).encode("utf-8")
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    def mock_urlopen(*args, **kwargs):
        return FakeResponse()
    
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(RuntimeError, match="malformed response"):
        provider.chat("qwen/qwen3-4b:free", messages)


def test_openrouter_qwen_chat_success(monkeypatch):
    """Test that chat method returns content on successful API call."""
    import urllib.request
    import json
    
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    provider = OpenRouterQwenProvider()
    
    class FakeResponse:
        def read(self):
            return json.dumps({
                "choices": [
                    {"message": {"content": "Hello! How can I help?"}}
                ]
            }).encode("utf-8")
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    def mock_urlopen(*args, **kwargs):
        return FakeResponse()
    
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    messages = [{"role": "user", "content": "Hello"}]
    result = provider.chat("qwen/qwen3-4b:free", messages)
    assert result == "Hello! How can I help?"


def test_openrouter_qwen_uses_default_model(monkeypatch):
    """Test that chat method uses default model when none provided."""
    import urllib.request
    import json
    
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    provider = OpenRouterQwenProvider()
    
    captured_payload = {}
    
    class FakeResponse:
        def read(self):
            return json.dumps({
                "choices": [
                    {"message": {"content": "Response"}}
                ]
            }).encode("utf-8")
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    def mock_urlopen(request, *args, **kwargs):
        # Capture the payload
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        return FakeResponse()
    
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    messages = [{"role": "user", "content": "Hello"}]
    provider.chat(None, messages)
    
    assert captured_payload["model"] == "qwen/qwen3-4b:free"
