from typing import Tuple
import yaml

from .registry import ProviderRegistry, AgentRegistry
from .agent import Agent


def build_registries(path: str) -> AgentRegistry:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    providers = ProviderRegistry()

    from providers.openrouter_qwen import provider_instance as qwen_instance
    from providers.openai import provider_instance as openai_instance
    from providers.ollama import provider_instance as ollama_instance

    providers.register("qwen", qwen_instance())
    providers.register("openai", openai_instance())
    providers.register("ollama", ollama_instance())

    agents = AgentRegistry()
    for spec in cfg.get("agents", []) or []:
        prov_name = spec.get("provider", "qwen")
        agent = Agent(spec, providers.get(prov_name))
        agents.register(agent)

    return agents

