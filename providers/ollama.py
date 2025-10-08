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
        # Compose a clearer dialogue-style prompt to reduce parroting
        sys_text = None
        turns: List[str] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                sys_text = content
            elif role == "assistant":
                turns.append(f"Assistant: {content}\n")
            else:
                turns.append(f"User: {content}\n")
        if not sys_text:
            sys_text = (
                "You are a helpful assistant. Answer concisely in complete sentences. "
                "Do not repeat the user's words unless explicitly asked."
            )
        prompt = f"System: {sys_text}\n" + "".join(turns) + "Assistant: "
        payload = {"model": model, "prompt": prompt, "stream": True}
        # Use no overall timeout for the stream; the client can cancel
        resp = requests.post(url, json=payload, stream=True, timeout=None)
        resp.raise_for_status()
        return resp


def provider_instance():
    return OllamaProvider()
