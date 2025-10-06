"""Test configuration helpers for pytest.

Ensures the project root is importable when running tests so modules like
``chatbot`` can be imported without installing the package.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
