# Repository Guidelines

## Project Structure & Module Organization
- `chatbot.py` – CLI entry point and dispatcher.
- `src/` – Python package modules:
  - `src/config.py` – env/config loading (e.g., keys, model).
  - `src/providers/` – provider implementations: `mock`, `openai`, `ollama`, `qwen`.
- `tests/` – pytest suite covering dispatcher and mock flow.
- `requirements.txt` – base/runtime dependencies.
- `README.md` – usage examples and provider setup.

## Build, Test, and Development Commands
- Setup environment: `pip install -r requirements.txt`.
- Run tests: `python -m pytest` (from repo root).
- Quick mock run: `python .\chatbot.py --provider mock --once "Hello"`.
- Interactive chat: `python .\chatbot.py --provider mock`.
- Provider examples:
  - OpenAI: set `OPENAI_API_KEY`, then `python .\chatbot.py --provider openai --model gpt-4o-mini --once "Hi"`.
  - Qwen via OpenRouter: set `OPENROUTER_API_KEY`, optional `MODEL_NAME`.
  - Ollama local: ensure Ollama is running; pass `--provider ollama --model qwen2.5:7b-instruct`.

## Coding Style & Naming Conventions
- Language: Python 3.9+; 4‑space indentation.
- Prefer explicit imports and small, single‑purpose functions.
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE for constants/env keys.
- Module layout: each provider in `src/providers/<name>_provider.py` exposing a common `send_chat(messages, config)` API.

## Testing Guidelines
- Framework: `pytest` with plain asserts.
- Place tests in `tests/` as `test_*.py`; mirror provider/dispatcher behavior with mocks where external APIs are used.
- Aim to keep unit tests offline; the default `mock` provider should cover chat loop logic.
- Run: `python -m pytest`; add cases for new providers and edge conditions.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject (max ~72 chars), body for rationale when needed.
  - Example: `feat(qwen): support MODEL_NAME override via env`.
- PRs: include summary, linked issues (e.g., `Closes #123`), screenshots or logs for UX/CLI changes, and instructions to reproduce.
- Keep diffs focused; update `README.md` when user‑facing flags or env vars change.

## Security & Configuration Tips
- Never commit secrets. Use environment variables or a local `.env` (git‑ignored) for `OPENAI_API_KEY` / `OPENROUTER_API_KEY`.
- Default provider is `mock`; no network calls unless a networked provider is selected.

## Architecture Overview
- CLI parses flags, builds a `config`, and dispatches to the selected provider.
- Providers encapsulate API specifics; all share a minimal chat interface to keep the CLI stable.
