from __future__ import annotations

import sys
from pathlib import Path

import pytest


pl_sum_input_root = Path(__file__).resolve().parents[1]
if str(pl_sum_input_root) not in sys.path:
    sys.path.insert(0, str(pl_sum_input_root))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Classify otherwise-unmarked project tests as focused unit tests."""
    classifications = {"smoke", "regression", "browser"}
    for item in items:
        if not classifications.intersection(item.keywords):
            item.add_marker(pytest.mark.unit)
