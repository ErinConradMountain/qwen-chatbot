from core.agent import Agent
from core.manager import ConversationManager
from core.registry import AgentRegistry, ProviderRegistry


class MockProvider:
    def __init__(self, name: str):
        self.name = name

    def chat(self, model, messages, **kw) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[mock:{self.name}] {last_user}"


def boot_registry():
    prov = ProviderRegistry()
    prov.register("qwen", MockProvider("bootstrap"))
    prov.register("openai", MockProvider("openai"))
    prov.register("ollama", MockProvider("ollama"))

    agents = AgentRegistry()
    spec1 = {"id": "bootstrap", "provider": "qwen", "model": "m1", "system_template": ""}
    spec2 = {"id": "aux", "provider": "qwen", "model": "m1", "system_template": ""}
    agents.register(Agent(spec1, prov.get("qwen")))
    agents.register(Agent(spec2, prov.get("qwen")))
    return agents


def test_conversation_manager_basic():
    agents = boot_registry()
    cm = ConversationManager(agents)
    r1 = cm.handle("hello")
    assert isinstance(r1, str) and r1
    assert len(cm.history) == 2
    r2 = cm.handle("world")
    assert len(cm.history) == 4
    assert cm.active == "bootstrap"

