from typing import List, Dict


class OllamaProvider:
    def chat(self, model: str, messages: List[Dict[str, str]], **kw) -> str:
        return "[stub:ollama] " + (messages[-1]["content"] if messages else "")


def provider_instance():
    return OllamaProvider()

