import pytest

from chatbot import Message, mock_infer, qwen_infer, run_inference


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


def test_qwen_infer_uses_provider(monkeypatch):
    calls = {}

    class DummyProvider:
        def __init__(self):
            calls.setdefault("inits", 0)
            calls["inits"] += 1

        def chat(self, chat_messages, model_override=None):
            calls["payload"] = chat_messages
            calls["model_override"] = model_override
            return "qwen says hi"

    monkeypatch.setattr("chatbot.QwenProvider", DummyProvider)

    messages = [
        Message("system", "You are helpful."),
        Message("user", "Tell me a joke"),
    ]
    result = qwen_infer("qwen/custom", messages)

    assert result == "qwen says hi"
    assert calls["inits"] == 1
    assert calls["payload"] == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Tell me a joke"},
    ]
    assert calls["model_override"] == "qwen/custom"

