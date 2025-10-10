from typing import List, Dict


class OpenAIProvider:
    def chat(self, model: str, messages: List[Dict[str, str]], **kw) -> str:
        return "[stub:openai] " + (messages[-1]["content"] if messages else "")


def provider_instance():
    return OpenAIProvider()

