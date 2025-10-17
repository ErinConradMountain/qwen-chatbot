"""Tests for multimodal (text + image) message handling."""

import pytest
from src.providers.qwen_provider import QwenProvider


def test_qwen_provider_accepts_multimodal_messages(monkeypatch):
    """Verify QwenProvider accepts messages with image_url content."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    
    # Mock the requests.post to capture what's being sent
    class FakeResponse:
        def raise_for_status(self):
            pass
        
        def json(self):
            return {"choices": [{"message": {"content": "I see an image"}}]}
    
    captured_payload = {}
    
    def fake_post(url, json=None, headers=None, timeout=None):
        captured_payload.update(json or {})
        return FakeResponse()
    
    import requests
    monkeypatch.setattr(requests, "post", fake_post)
    
    # Create a multimodal message (text + image)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What do you see?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="}
                }
            ]
        }
    ]
    
    provider = QwenProvider()
    result = provider.chat(messages)
    
    assert result == "I see an image"
    # Verify the multimodal structure was passed through
    assert "messages" in captured_payload
    assert captured_payload["messages"] == messages
    assert isinstance(captured_payload["messages"][0]["content"], list)
    assert captured_payload["messages"][0]["content"][0]["type"] == "text"
    assert captured_payload["messages"][0]["content"][1]["type"] == "image_url"


def test_qwen_provider_accepts_simple_text_messages(monkeypatch):
    """Verify QwenProvider still works with simple text messages."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    
    class FakeResponse:
        def raise_for_status(self):
            pass
        
        def json(self):
            return {"choices": [{"message": {"content": "Hello!"}}]}
    
    def fake_post(url, json=None, headers=None, timeout=None):
        return FakeResponse()
    
    import requests
    monkeypatch.setattr(requests, "post", fake_post)
    
    # Simple text message
    messages = [{"role": "user", "content": "Hello"}]
    
    provider = QwenProvider()
    result = provider.chat(messages)
    
    assert result == "Hello!"
