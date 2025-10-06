import pytest

from chatbot import Message, mock_infer, run_inference


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
