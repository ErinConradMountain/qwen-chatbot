#!/usr/bin/env python3
import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Optional
from core.load import build_registries
from core.manager import ConversationManager

# Import config early to trigger optional .env loading via python-dotenv
try:
    from src import config as _config  # noqa: F401
except Exception:
    _config = None  # OS env will still be used by providers

# Optional dependency for Ollama HTTP calls
try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

# Qwen provider (via OpenRouter)
try:
    from src.providers.qwen_provider import QwenProvider
except Exception:
    QwenProvider = None  # type: ignore


@dataclass
class Message:
    role: str
    content: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Minimal chatbot CLI supporting mock, openai, ollama, and qwen providers."
    )
    p.add_argument(
        "--provider",
        choices=["mock", "openai", "ollama", "qwen"],
        default="mock",
        help="Backend provider.",
    )
    p.add_argument(
        "--model",
        default=None,
        help=(
            "Model name (required for openai/ollama). Examples: gpt-4o-mini, qwen2.5:7b-instruct"
        ),
    )
    p.add_argument("--once", default=None, help="Send a single prompt and exit.")
    p.add_argument(
        "--system", default="You are a helpful assistant.", help="System prompt."
    )
    return p.parse_args()


def chat_loop(provider: str, model: Optional[str], system_prompt: str) -> None:
    messages: List[Message] = [Message("system", system_prompt)]
    print(f"Provider: {provider}")
    if model:
        print(f"Model: {model}")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user:
            continue
        if user.lower() in {"/exit", ":q", "quit", "exit"}:
            print("Bye!")
            break
        messages.append(Message("user", user))
        reply = run_inference(provider, model, messages)
        messages.append(Message("assistant", reply))
        print(f"Bot: {reply}")


def run_once(provider: str, model: Optional[str], system_prompt: str, prompt: str) -> None:
    messages = [Message("system", system_prompt), Message("user", prompt)]
    reply = run_inference(provider, model, messages)
    print(reply)


def run_inference(provider: str, model: Optional[str], messages: List[Message]) -> str:
    if provider == "mock":
        return mock_infer(messages)
    if provider == "openai":
        return openai_infer(model, messages)
    if provider == "ollama":
        return ollama_infer(model, messages)
    if provider == "qwen":
        return qwen_infer(model, messages)
    raise ValueError(f"Unknown provider: {provider}")


# --- Providers ---

def mock_infer(messages: List[Message]) -> str:
    user_messages = [
        m.content.strip() for m in messages if m.role == "user" and m.content.strip()
    ]
    if not user_messages:
        return (
            "[mock] Hello! I'm the built-in assistant. Ask me anything and we'll chat."
        )

    last_user = user_messages[-1]
    previous = user_messages[-2] if len(user_messages) > 1 else None
    normalized = last_user.strip().lower().rstrip("!.?")

    farewells = {"bye", "goodbye", "see you", "see ya"}
    if normalized in farewells:
        return "[mock] It was nice chatting. Talk soon!"

    response_parts: List[str] = []
    if previous:
        response_parts.append(f'[mock] Earlier you mentioned "{previous}".')
    else:
        response_parts.append("[mock] Nice to meet you!")

    response_parts.append(f'I hear you saying "{last_user}".')

    if last_user.endswith("?"):
        response_parts.append(
            "I can't access real data, but I'd love to hear your thoughts."
        )
    else:
        response_parts.append("Tell me more so we can keep the conversation going.")

    return " ".join(response_parts)


# Minimal provider class so the registry is valid.
class MockProvider:
    @staticmethod
    def infer(messages: List[Message]) -> str:
        return mock_infer(messages)


def openai_infer(model: Optional[str], messages: List[Message]) -> str:
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(
            "OpenAI provider requested but the 'openai' package is not installed. Run: pip install -r requirements.txt"
        ) from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    if not model:
        raise RuntimeError("--model is required for --provider openai.")

    base_url = os.getenv("OPENAI_BASE_URL")
    client = (
        OpenAI(api_key=api_key, base_url=base_url)
        if base_url
        else OpenAI(api_key=api_key)
    )

    chat_messages = [{"role": m.role, "content": m.content} for m in messages]

    try:
        resp = client.chat.completions.create(model=model, messages=chat_messages)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {e}")


def ollama_infer(model: Optional[str], messages: List[Message]) -> str:
    if not model:
        raise RuntimeError("--model is required for --provider ollama.")
    if requests is None:
        raise RuntimeError(
            "The 'requests' package is required for Ollama provider. Run: pip install requests"
        )

    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": False,
    }
    try:
        r = requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        # The exact shape may vary by Ollama version; handle common formats
        if isinstance(data, dict):
            if "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", "")
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                msg = choice.get("message") or {}
                return (msg.get("content") or "").strip()
        return "(No response)"
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")


def qwen_infer(model: Optional[str], messages: List[Message]) -> str:
    """Call Qwen via OpenRouter using QwenProvider.

    If model is provided via CLI, it overrides the configured/default model.
    """
    if QwenProvider is None:
        raise RuntimeError(
            "Qwen provider not available. Ensure project dependencies are installed."
        )

    provider = QwenProvider()
    chat_messages = [{"role": m.role, "content": m.content} for m in messages]
    return provider.chat(chat_messages, model_override=model)


# Provider registry
PROVIDERS = {
    "mock": MockProvider,
    "qwen": QwenProvider,
}


if __name__ == "__main__":
    args = parse_args()
    # Prefer new framework path if no legacy provider override was given
    if args.provider is None or args.provider == "qwen":
        agents = build_registries("agents/agents.yml")
        cm = ConversationManager(agents)
        if args.once:
            print(cm.handle(args.once))
            sys.exit(0)
        print("Chatbot started. Type 'exit' to quit.")
        while True:
            try:
                user = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            if not user:
                continue
            if user.lower() in {"/exit", ":q", "quit", "exit"}:
                print("Bye!")
                break
            print(cm.handle(user))
        sys.exit(0)
    # Fallback to legacy path
    if args.once:
        run_once(args.provider, args.model, args.system, args.once)
        sys.exit(0)
    chat_loop(args.provider, args.model, args.system)
