# src/providers/qwen_provider.py
"""
QwenProvider – connects CLI chatbot to Qwen3-4B via OpenRouter API.
"""

import os
from types import ModuleType
from typing import Any, Dict, List, cast

import requests

try:
    from src import config as _config_module
except Exception:
    _CONFIG: ModuleType | None = None
else:
    _CONFIG = cast(ModuleType, _config_module)


class QwenProvider:
    def __init__(self):
        # Prefer values from config if available (ensures .env is loaded), else fall back to OS env
        self.api_key = getattr(_CONFIG, "OPENROUTER_API_KEY", None) or os.getenv(
            "OPENROUTER_API_KEY"
        )
        self.model = getattr(_CONFIG, "MODEL_NAME", None) or os.getenv(
            "MODEL_NAME", "qwen/qwen3-4b:free"
        )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

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
        }
        model = model_override or self.model
        payload = {"model": model, "messages": messages}
        resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
