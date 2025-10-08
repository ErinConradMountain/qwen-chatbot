from typing import List, Dict, Any, Optional, Iterator
import os
import requests


class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    def chat(self, messages: List[Dict[str, Any]], model_override: Optional[str] = None) -> str:
        # Default to a Qwen instruct if not specified
        model = model_override or os.getenv("MODEL_NAME", "qwen2.5:7b-instruct")
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages, "stream": False}
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    def stream_generate(self, messages: List[Dict[str, Any]], model_override: Optional[str] = None):
        model = model_override or os.getenv("MODEL_NAME", "qwen2.5:7b-instruct")
        url = f"{self.base_url}/api/generate"
        # Compose a simple prompt from message history
        parts: List[str] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"[System] {content}\n")
            elif role == "assistant":
                parts.append(f"Assistant: {content}\n")
            else:
                parts.append(f"User: {content}\n")
        prompt = "".join(parts) + "Assistant: "
        payload = {"model": model, "prompt": prompt, "stream": True}
        resp = requests.post(url, json=payload, stream=True, timeout=0)
        resp.raise_for_status()
        return resp


def provider_instance():
    return OllamaProvider()
