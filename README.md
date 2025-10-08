# qwen-chatbot

A minimal local chatbot starter you can run locally or wire up to hosted APIs. It now supports four providers:

- mock (no network, default) - useful to verify the CLI works
- OpenAI-compatible API - set `OPENAI_API_KEY` and specify a model
- Ollama (local) - if you have Ollama installed (http://localhost:11434)
- Qwen via OpenRouter - set `OPENROUTER_API_KEY` or keep it in a `.env` file

## Quick start (no API needed)

Run a one-off prompt in mock mode:

```powershell
cd $PSScriptRoot
python .\chatbot.py --provider mock --once "Hello there"
```

Interactive chat loop (mock):

```powershell
python .\chatbot.py --provider mock
```

The mock provider keeps lightweight conversational context so you can exercise the chat loop without external APIs.

## Use an OpenAI-compatible API

Requirements:
- Python 3.9+
- Environment variable `OPENAI_API_KEY` set

Example (OpenAI):

```powershell
$env:OPENAI_API_KEY = "sk-..."
python .\chatbot.py --provider openai --model gpt-4o-mini --once "Explain Qwen models in one sentence"
```

Example (any OpenAI-compatible endpoint):

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_BASE_URL = "https://your-endpoint/v1"
python .\chatbot.py --provider openai --model your-model-name --once "Hello"
```

## Use Qwen via OpenRouter

Requirements:
- `OPENROUTER_API_KEY` exported or placed in a `.env` file (python-dotenv is supported)
- Optional: set `MODEL_NAME` to override the default `qwen/qwen3-4b:free`

Example:

```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."
python .\chatbot.py --provider qwen --once "Write a limerick about testing"
```

Override the model on the CLI:

```powershell
python .\chatbot.py --provider qwen --model qwen/qwen2.5-7b-instruct --once "Explain unit tests"
```

## Use Ollama (local)

Requirements:
- Ollama running locally (https://ollama.com/)

Example with Qwen 2.5 7B instruct:

```powershell
python .\chatbot.py --provider ollama --model qwen2.5:7b-instruct --once "Write a haiku about autumn"
```

Interactive session (any provider):

```powershell
python .\chatbot.py --provider ollama --model qwen2.5:7b-instruct
```

## Run tests

Install the optional dependencies and run pytest to exercise the conversational mock provider plus dispatcher logic:

```powershell
pip install -r requirements.txt
python -m pytest
```

## Web Chat (local UI)

This repo includes a simple web UI served via FastAPI.

- Install server deps: `pip install fastapi uvicorn`
- Set `OPENROUTER_API_KEY` (or add `.env`) for Qwen via OpenRouter.
- Start server: `python webserver.py`
- Open: `http://127.0.0.1:8000/`

In the sidebar you can switch Provider: Qwen (OpenRouter) or Ollama (local). The UI calls `/api/chat/qwen` or `/api/chat/ollama` accordingly and streams the full text as it’s generated (concatenated server-side for now). Static assets live under `web/`.

Streaming details:
- Ollama: true token streaming via `/api/generate` with `stream: true` (NDJSON parsed server-side and flushed to the client).
- Qwen via LiteLLM proxy: unified OpenAI-compatible streaming from `http://localhost:4000/v1/chat/completions`. Use the included `litellm_config.yaml` and scripts to start the proxy locally. The UI calls `/api/llm/stream` which forwards tokens.

Start LiteLLM locally:

```powershell
scripts\run_litellm.ps1
```

or on macOS/Linux:

```bash
scripts/run_litellm.sh
```

Environment variables:
- `LITELLM_BASE_URL` (default `http://127.0.0.1:4000`)
- `CHATKIT_AUTH_TOKEN` optional; if set, routes require `X-Auth-Token` header
- `MODEL_NAME` default model for Ollama
- `OPENROUTER_API_KEY` for OpenRouter Qwen if you use that path

Dev proxy management:
- Start: `scripts/run_litellm.sh` (Linux/mac) or `scripts\run_litellm.ps1` (Windows)
- Stop: `scripts/stop_litellm.sh` (Linux/mac) or kill the PID from `.run/litellm.pid` on Windows

Troubleshooting:
- Port in use: change port via `PORT=4001 scripts/run_litellm.sh`
- Model not pulled: `ollama pull qwen2.5-7b-instruct`
- Proxy not running: verify `.run/litellm.pid` and check `pip show litellm`
 - Windows: if scripts fail to run, set execution policy for current user: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Health checks:
- Server: `GET /api/health` (requires X-Auth-Token if set) returns status for LiteLLM and Ollama.
- LiteLLM: default at `http://127.0.0.1:4000`; change with `LITELLM_BASE_URL`.

Planned improvements:
- Token streaming (SSE) for live responses
- Provider/model switcher in the sidebar
- Chat history and export
- Better error surfaces and retries

## Notes

- The script defaults to the `mock` provider so it never sends network traffic unless you opt in.
- The OpenAI and Qwen providers import their SDKs lazily; install dependencies with `pip install -r requirements.txt` if you plan to use them.
- The Ollama and Qwen providers depend on the `requests` package for HTTP calls.

## Architecture

See `ARCHITECTURE.md` for a detailed report on the agentic framework, directory layout, extension points, and roadmap.

## Roles (scaffolding)

A role system is scaffolded under `src/roles/` to centralize chatbot behavior.

- Add a new role by creating `src/roles/<name>_role.py` that exports:
  - `get_system_prompt() -> str`
  - optional `postprocess(reply: str, context: dict) -> str`
- A default placeholder exists at `src/roles/default_role.py`.

Wiring to select a role via CLI/env will be added later; current behavior remains unchanged.

## Repository status

This starter is intentionally lightweight to make local iteration and remote CI easy. Extend it as you wish.
