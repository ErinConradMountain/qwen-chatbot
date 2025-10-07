from typing import Dict, List, Protocol, Optional, TypedDict


Message = Dict[str, str]  # expects keys: role, content


class Provider(Protocol):
    def chat(self, model: str, messages: List[Message], **kw) -> str:
        ...


class Memory(Protocol):
    def write(self, user_text: str, reply: str, context: Optional[Dict] = None) -> None:
        ...


class AgentSpec(TypedDict, total=False):
    id: str
    name: str
    system_template: str
    provider: str
    model: str
    policies: Dict
    capabilities: Dict
    routing: Dict
    metadata: Dict

