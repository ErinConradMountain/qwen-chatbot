# src/providers/qwen_provider.py
"""
QwenProvider – connects CLI chatbot to Qwen3-4B via OpenRouter API.
"""

import os
from types import ModuleType
from typing import Any, Dict, List

import requests

# Try to load config to ensure .env is read if available
_CONFIG_MODULE: ModuleType | None = None
_loaded_config: ModuleType | None
try:
    from src import config as _loaded_config
except Exception:
    _loaded_config = None

if isinstance(_loaded_config, ModuleType):
    _CONFIG_MODULE = _loaded_config


class QwenProvider:
    def __init__(self):
        # Prefer values from config if available (ensures .env is loaded), else fall back to OS env
        self.api_key = getattr(_CONFIG_MODULE, "OPENROUTER_API_KEY", None) or os.getenv(
            "OPENROUTER_API_KEY"
        )
        self.model = getattr(_CONFIG_MODULE, "MODEL_NAME", None) or os.getenv(
            "MODEL_NAME", "qwen/qwen3-4b:free"
        )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def chat(self, messages: List[Dict[str, Any]], model_override: str | None = None):
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
