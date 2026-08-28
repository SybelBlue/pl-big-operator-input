from __future__ import annotations

import sys
from pathlib import Path

import pytest

pl_sum_input_root = Path(__file__).resolve().parents[1]
if str(pl_sum_input_root) not in sys.path:
    sys.path.insert(0, str(pl_sum_input_root))


def pytest_configure(config: pytest.Config) -> None:
    """Register local suite markers without publishing pytest configuration."""
    markers = {
        "smoke": "fast publication-critical lifecycle and documentation contracts",
        "regression": "named bug or compatibility contract",
        "unit": "focused project-owned unit and characterization tests",
        "vendor_contract": "project adapter compatibility with the pinned PrairieLearn snapshot",
        "browser": "DOM/CSS layout or accessibility behavior requiring a browser",
    }
    for name, description in markers.items():
        config.addinivalue_line("markers", f"{name}: {description}")
