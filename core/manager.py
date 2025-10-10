from typing import List, Optional, Dict

from .types import Message
from .agent import Agent
from .registry import AgentRegistry
from router.triage import select_agent


class ConversationManager:
    def __init__(self, agents: AgentRegistry):
        self.agents = agents
        self.history: List[Message] = []
        self.active: Optional[str] = None

    def _build_handover(self) -> str:
        turns = self.history[-8:]  # approx 4 user/assistant pairs
        text = []
        for m in turns:
            role = m.get("role", "")
            content = m.get("content", "")
            text.append(f"{role}: {content}")
        s = " | ".join(text)
        if len(s) > 600:
            s = s[-600:]
        return s

    def handle(self, user_text: str) -> str:
        agent_id = select_agent(user_text, self.agents.all_specs(), self.active)
        handover = None
        if self.active and agent_id != self.active and self.history:
            handover = self._build_handover()

        agent: Agent = self.agents.get(agent_id)
        msgs = self.history + [{"role": "user", "content": user_text}]
        msgs = agent.before_call(msgs, {"handover": handover} if handover else None)
        reply = agent.call(msgs)
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": reply})
        agent.after_call(user_text, reply)
        self.active = agent_id
        return reply

