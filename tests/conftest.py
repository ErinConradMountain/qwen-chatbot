"""Test configuration for ensuring package imports succeed."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is available for importing the chatbot module when
# pytest runs from a different working directory (e.g., coverage runs).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
