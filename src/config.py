# src/config.py
from pathlib import Path
import os

try:
    from dotenv import load_dotenv  # pip install python-dotenv

    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except Exception:
    # If python-dotenv isn't installed, OS env still works.
    pass

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv(
    "MODEL_NAME", "deepseek/deepseek-r1-0528-qwen3-8b:free"
)
