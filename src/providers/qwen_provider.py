"""HTTP provider for routing messages to the Qwen API via OpenRouter."""

from __future__ import annotations

import importlib.util
import os
from typing import Any, Dict, List

import requests  # type: ignore[import-untyped]

if importlib.util.find_spec("src.config") is not None:
    from src import config as _config
else:  # pragma: no cover - exercised when config import fails
    _config = None  # type: ignore[assignment]


class QwenProvider:
    """Minimal wrapper around OpenRouter's Qwen endpoint."""

    def __init__(self) -> None:
        """Capture configuration values at instantiation time."""

        self.api_key = getattr(_config, "OPENROUTER_API_KEY", None) or os.getenv(
            "OPENROUTER_API_KEY"
        )
        self.model = getattr(_config, "MODEL_NAME", None) or os.getenv(
            "MODEL_NAME", "qwen/qwen3-4b:free"
        )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def chat(
        self, messages: List[Dict[str, Any]], model_override: str | None = None
    ) -> str:
        """Send the chat request and return the assistant text."""

        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Set it in OS env or in a .env file."
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        model = model_override or self.model
        payload = {"model": model, "messages": messages}
        resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


__all__ = ["QwenProvider"]
