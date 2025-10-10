import json
import os
import sys
from typing import List, Dict
import urllib.request


class OpenRouterQwenProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        if not self.api_key:
            print("Missing OPENROUTER_API_KEY for Qwen provider", file=sys.stderr)

    def chat(self, model: str, messages: List[Dict[str, str]], **kw) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or "deepseek/deepseek-r1-0528-qwen3-8b:free",
            "messages": messages,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        timeout = kw.get("timeout", 20)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                parsed = json.loads(body)
        except Exception as e:
            return f"[error:qwen] {e}"

        try:
            return parsed["choices"][0]["message"]["content"]
        except Exception:
            return "[error:qwen] malformed response"


def provider_instance():
    return OpenRouterQwenProvider()
