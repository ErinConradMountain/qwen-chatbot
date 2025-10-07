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

## Notes

- The script defaults to the `mock` provider so it never sends network traffic unless you opt in.
- The OpenAI and Qwen providers import their SDKs lazily; install dependencies with `pip install -r requirements.txt` if you plan to use them.
- The Ollama and Qwen providers depend on the `requests` package for HTTP calls.

## Repository status

This starter is intentionally lightweight to make local iteration and remote CI easy. Extend it as you wish.
