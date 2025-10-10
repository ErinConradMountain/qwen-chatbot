"""Default role placeholder.

Keeps behavior unchanged by returning an empty postprocess and a generic
system prompt. Repositories can add new `<name>_role.py` files here and
select them via config/CLI in a future change.
"""

from typing import Dict


def get_system_prompt() -> str:
    return "You are a helpful assistant."


def postprocess(reply: str, context: Dict) -> str:
    # No-op for the default role
    return reply


# Optional ROLE object so dynamic loaders can fetch a single attr.
class _Role:
    @staticmethod
    def get_system_prompt() -> str:
        return get_system_prompt()

    @staticmethod
    def postprocess(reply: str, context: Dict) -> str:
        return postprocess(reply, context)


ROLE = _Role()

