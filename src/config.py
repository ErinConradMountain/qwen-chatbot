"""Helpers for loading configuration from environment variables."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Callable, Optional, cast

LoadDotenvCallable = Callable[..., bool]

_dotenv_spec = importlib.util.find_spec("dotenv")
if _dotenv_spec is not None:
    from dotenv import load_dotenv as _actual_load_dotenv

    _load_dotenv: LoadDotenvCallable | None = cast(
        LoadDotenvCallable, _actual_load_dotenv
    )
else:  # pragma: no cover - exercised via load_env in tests
    _load_dotenv = None


def load_env(env_path: Optional[Path] = None) -> None:
    """Learner Note: This is the expected format.

    Load environment variables from a ``.env`` file when python-dotenv is available.

    Args:
        env_path: Optional custom path to a ``.env`` file. When ``None``, the project
            root (two levels above this file) is inspected.
    """

    if _load_dotenv is None:
        return

    candidate = env_path or Path(__file__).resolve().parents[1] / ".env"
    if candidate.exists():
        _load_dotenv(candidate)


load_env()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-4b:free")


__all__ = ["load_env", "OPENROUTER_API_KEY", "MODEL_NAME"]
