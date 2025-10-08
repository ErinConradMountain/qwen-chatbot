# src/providers/qwen_provider.py
"""QwenProvider – connects CLI chatbot to Qwen3-4B via OpenRouter API."""

from __future__ import annotations

import os
from types import ModuleType
from typing import Any, Dict, List, Optional

import requests

# Try to load config to ensure .env is read if available
_config_module: Optional[ModuleType]
try:
    from src import config as _config_module
except Exception:
    _config_module = None

_config = _config_module


class QwenProvider:
    def __init__(self):
        # Prefer values from config if available (ensures .env is loaded), else fall back to OS env
        self.api_key = getattr(_config, "OPENROUTER_API_KEY", None) or os.getenv(
            "OPENROUTER_API_KEY"
        )
        self.model = getattr(_config, "MODEL_NAME", None) or os.getenv(
            "MODEL_NAME", "qwen/qwen3-4b:free"
        )
        base = getattr(_config, "OPENROUTER_BASE_URL", None) or os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.base_url = f"{base.rstrip('/')}/chat/completions"
        self.http_referer = getattr(_config, "OPENROUTER_HTTP_REFERER", None) or os.getenv(
            "OPENROUTER_HTTP_REFERER", "http://localhost:8000"
        )
        self.x_title = getattr(_config, "OPENROUTER_X_TITLE", None) or os.getenv(
            "OPENROUTER_X_TITLE", "QwenBot"
        )

    def chat(
        self, messages: List[Dict[str, Any]], model_override: str | None = None
    ) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Set it in OS env or in a .env file."
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.x_title,
        }
        model = model_override or self.model
        payload = {"model": model, "messages": messages}
        resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
