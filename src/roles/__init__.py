"""
Role system scaffolding.

Roles define system prompts and optional post-processing hooks to
influence chatbot responses without changing providers.

Contract (stable):
- Each role exposes `get_system_prompt()` -> str
- Optional: `postprocess(reply: str, context: dict) -> str`

Runtime wiring will import a selected role and apply its prompt/hook.
Until configured, the default prompt remains CLI `--system`.
"""

from typing import Protocol, runtime_checkable, Dict


@runtime_checkable
class Role(Protocol):
    def get_system_prompt(self) -> str:  # pragma: no cover - interface
        ...

    def postprocess(self, reply: str, context: Dict) -> str:  # pragma: no cover
        ...


def load_role(name: str):
    """Dynamically import a role by name from `src.roles`.

    Example names: "default", "product_support".
    """
    module_name = f"src.roles.{name}_role"
    mod = __import__(module_name, fromlist=["*"])
    return getattr(mod, "ROLE", mod)

