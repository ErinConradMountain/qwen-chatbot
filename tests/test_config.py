import importlib
from pathlib import Path

import pytest

from src import config


def test_load_env_invokes_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=file-key\n")
    calls: dict[str, Path] = {}

    def fake_load(path: Path) -> None:
        calls["path"] = path

    monkeypatch.setattr(config, "_load_dotenv", fake_load)

    config.load_env(env_file)

    assert calls["path"] == env_file


def test_load_env_without_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("")
    monkeypatch.setattr(config, "_load_dotenv", None)

    # Should return gracefully without raising.
    config.load_env(env_file)


def test_config_values_follow_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    monkeypatch.setenv("MODEL_NAME", "env-model")

    importlib.reload(config)

    assert config.OPENROUTER_API_KEY == "env-key"
    assert config.MODEL_NAME == "env-model"
