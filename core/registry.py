from typing import Dict, Optional

from .agent import Agent
from .types import AgentSpec


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, object] = {}

    def register(self, name: str, provider: object) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> object:
        return self._providers[name]


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._specs: Dict[str, AgentSpec] = {}

    def register(self, agent: Agent) -> None:
        spec = agent.spec
        aid = spec.get("id", "")
        self._agents[aid] = agent
        self._specs[aid] = spec

    def get(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def all_specs(self):
        return list(self._specs.values())

