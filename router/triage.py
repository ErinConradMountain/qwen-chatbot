from typing import List, Optional

from core.types import AgentSpec


def select_agent(text: str, agent_specs: List[AgentSpec], active: Optional[str]) -> str:
    if active:
        return active
    if not agent_specs:
        raise RuntimeError("No agent specs available")
    return agent_specs[0].get("id", "")

