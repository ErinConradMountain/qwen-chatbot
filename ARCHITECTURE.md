# Agentic Framework Status Report

- Date: 2025-10-07
- Repository: qwen-chatbot-https
- Environment: Python 3.9+, pytest; OpenRouter for Qwen (optional)

## Executive Summary

We introduced a role-agnostic, provider-pluggable agent framework that moves roles/prompts into configuration rather than code. The core is stable and minimal: Providers adapt to a common interface; Agents are lightweight shells; a ConversationManager handles history and switching; routing is a simple triage function ready for future intelligence. Adding agents or swapping models requires no code changes—only YAML edits.

Tests pass (20/20), including a new boot test for the framework path. The CLI defaults to the new path and can run single-turn or interactive chats.

## Current Architecture

### Directory Structure

```
core/
  types.py          # Protocols & type aliases
  agent.py          # Agent class (lifecycle hooks)
  registry.py       # ProviderRegistry & AgentRegistry
  manager.py        # ConversationManager (history + handoff)
  load.py           # YAML loader -> registries
providers/
  openrouter_qwen.py
  openai.py         # stub now; fill later
  ollama.py         # stub now; fill later
router/
  triage.py         # select_agent() trivial first pass
agents/
  agents.yml        # data-only specs (no roles yet)
tests/
  test_agent_boot.py
chatbot.py          # wire CLI to ConversationManager
```

### Core Modules

- core/types.py
  - `Message`: `Dict[str, str]` with `role` in `{system,user,assistant}` and `content`.
  - `Provider` Protocol: `chat(model: str, messages: List[Message], **kw) -> str`.
  - `Memory` Protocol (stub): `write(user_text, reply, context?) -> None`.
  - `AgentSpec` TypedDict: `id, name, system_template, provider, model, policies, capabilities, routing, metadata` (all optional).

- core/agent.py
  - `Agent(spec, provider, memory=None)`.
  - `before_call(messages, context)`: prepends `system_template` and single `Handover:` system message if present.
  - `call(messages, **kw)`: delegates to `provider.chat(model, messages)`.
  - `after_call(user_text, reply)`: future memory hook (noop now).

- core/registry.py
  - `ProviderRegistry`: register/get provider instances by name.
  - `AgentRegistry`: register/get agents; expose `all_specs()`.

- core/manager.py
  - `ConversationManager(agents)`
  - State: `history` (`List[Message]`), `active` (`Optional[str]`).
  - `handle(user_text)`: selects agent (via router), builds optional handover (last ~4 turns, ~600 chars cap), calls agent, updates history/active.

- core/load.py
  - `build_registries(path)`: parses `agents/agents.yml`; registers providers ("qwen", "openai", "ollama"); builds `AgentRegistry`.

### Providers

- providers/openrouter_qwen.py
  - `OpenRouterQwenProvider`: stdlib HTTP client to POST `/chat/completions`, reads `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`).
  - `chat(model, messages, **kw) -> str`: returns first choice content; returns readable error strings on failure.

- providers/openai.py, providers/ollama.py
  - Stubs implementing `chat()`; return deterministic strings for tests.

### Router

- router/triage.py
  - `select_agent(text, agent_specs, active)`: returns `active` if present; otherwise first spec id. Hook for upgrades (keywords/embeddings/metadata).

### Configuration (Agents as Data)

- agents/agents.yml
  - `default: "bootstrap"`
  - Two sample agents (`bootstrap`, `aux`) using Qwen via OpenRouter, empty `system_template`.
  - Extend by adding entries for different Qwen models or other providers; no code changes needed.

### CLI

- chatbot.py
  - Framework path by default:
    - `agents = build_registries("agents/agents.yml")`; `cm = ConversationManager(agents)`.
    - `--once "msg"` prints `cm.handle(msg)`.
    - Interactive loop reads input and prints `cm.handle(input)`.
  - Legacy provider paths retained when explicitly selected.

## Testing and Quality

- Tests: `20 passed`.
  - `tests/test_agent_boot.py` validates ConversationManager with a MockProvider:
    - `handle()` returns string.
    - History increments by 2 per turn.
    - Active agent remains stable across turns.

- Error handling:
  - Qwen provider returns readable error messages on network/parse failures.
  - CLI remains usable offline (stubs/legacy mock keep flow offline).

## Design Principles

- Role-neutral core: Prompts are data, not code; `system_template` defaults empty.
- Provider abstraction: Model choice is a config concern.
- Minimal, testable units: Small classes/functions; easy mocks; deterministic tests.
- Extensibility hooks: Memory (future), routing metadata, capabilities for tools.

## How to Extend

- Add an agent (e.g., different Qwen model):
  1. Edit `agents/agents.yml` and duplicate an entry.
  2. Set a unique `id`/`name`, `provider: "qwen"`, and desired `model` string.
  3. Optionally update `routing.tags` and `metadata`.

- Add a provider:
  1. Create `providers/<name>.py` implementing `provider_instance()` that returns an object with `chat(model, messages, **kw) -> str`.
  2. Register it in `core/load.py` (or adopt auto-discovery later).

- Improve routing:
  1. Populate `spec["routing"]` with keywords, tags, or embedding references.
  2. Implement logic in `router/triage.select_agent` to pick agents based on content/metadata.

- Introduce prompts/roles later:
  - Fill `system_template` per agent; optionally support templating with safe `.format(**context)` in `Agent.before_call`.

- Memory or tools:
  - Add a `Memory` implementation and inject into `Agent`; write entries in `after_call`.
  - Use `spec["capabilities"]` to enable tool dispatch from `Agent.call` or a dedicated ToolRouter.

## Roadmap

- Short-term
  - Add `ARCHITECTURE.md` (this file) and expand README to explain agent YAML usage.
  - CLI `--agent <id>` and `--agents <path>` flags.
  - Add test: handover appears once on agent switch.
  - Optional: auto-discover providers in `providers/`.

- Mid-term
  - Rich routing (keywords; optional embedding-backed selection).
  - Implement real OpenAI and Ollama providers (timeouts/retries).
  - Prompt templates and variables.

- Long-term
  - Pluggable Memory; optional vector memory.
  - ToolRouter layer gated by `spec["capabilities"]`.
  - Observability hooks and optional CI smoke test using OpenRouter secret.

## Operational Guidance

- Offline/dev:
  - `pip install -r requirements.txt`
  - `python -m pytest -q`
  - `python .\\chatbot.py --once "Hi"`

- Qwen via OpenRouter:
  - `$env:OPENROUTER_API_KEY="or-…"`
  - `python .\\chatbot.py --once "Quick smoke test"`

## Acceptance Criteria Status

- Pytest green with mock provider: Achieved.
- CLI `--once` and interactive mode produce replies via Qwen: Supported (with key).
- Swapping `agents.yml` requires no code changes: Achieved.
- Router can switch agents; handover system message appears once: Mechanism implemented; dedicated test pending.

