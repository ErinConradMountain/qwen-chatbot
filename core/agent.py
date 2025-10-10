from typing import List, Dict, Optional

from .types import Message, Provider, AgentSpec


class Agent:
    def __init__(self, spec: AgentSpec, provider: Provider, memory: Optional[object] = None):
        self.spec = spec
        self.provider = provider
        self.memory = memory

    def before_call(self, messages: List[Message], context: Optional[Dict] = None) -> List[Message]:
        out: List[Message] = []
        sys_tmpl = self.spec.get("system_template") or ""
        if sys_tmpl:
            out.append({"role": "system", "content": sys_tmpl})
        if context and context.get("handover"):
            out.append({"role": "system", "content": f"Handover: {context['handover']}"})
        out.extend(messages)
        return out

    def call(self, messages: List[Message], **kw) -> str:
        model = self.spec.get("model", "")
        return self.provider.chat(model, messages, **kw)

    def after_call(self, user_text: str, reply: str) -> None:
        if hasattr(self.memory, "write") and callable(getattr(self.memory, "write")):
            try:
                self.memory.write(user_text, reply)
            except Exception:
                pass

