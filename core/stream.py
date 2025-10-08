from typing import Dict, Any, Iterator, Optional


class Delta:
    def __init__(self, text: str = "", finish_reason: Optional[str] = None, usage: Optional[Dict[str, Any]] = None):
        self.text = text
        self.finish_reason = finish_reason
        self.usage = usage or None


def normalize_openai_sse(obj: Dict[str, Any]) -> Optional[Delta]:
    choices = obj.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    finish = choices[0].get("finish_reason")
    if content or finish:
        return Delta(text=content or "", finish_reason=finish)
    return None


def normalize_ollama_ndjson(obj: Dict[str, Any]) -> Optional[Delta]:
    # When streaming generate: each line has `response` tokens until done=true
    if obj.get("done"):
        return Delta(text="", finish_reason=obj.get("done_reason"))
    txt = obj.get("response") or ""
    return Delta(text=txt)

