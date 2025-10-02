"""
Minimal CLI chat loop using a provider pattern.
Current provider = EchoProvider. We'll inject Qwen later with the same interface.
"""
import os
from typing import Dict, List
from dotenv import load_dotenv
from src.providers.echo_provider import EchoProvider

# Load .env (if present)
load_dotenv()

def build_provider():
    """
    Create the provider based on env (PROVIDER=echo/qwen/...).
    For now, only echo is implemented.
    """
    provider_name = os.getenv("PROVIDER", "echo").lower()
    if provider_name != "echo":
        print(f"PROVIDER={provider_name} not implemented yet; falling back to echo.")
    return EchoProvider(system_prompt="You are an echo bot. Repeat the user exactly.")

def main():
    provider = build_provider()
    messages: List[Dict[str, str]] = [{"role": "system", "content": provider.system_prompt}]

    print("Echo chat started. Type 'exit' to quit.")
    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if user.lower() in {"exit", "quit"}:
            print("Bye!")
            break
        messages.append({"role": "user", "content": user})
        reply = provider.chat(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"Bot: {reply}")

if __name__ == "__main__":
    main()
