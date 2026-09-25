"""Load declarative configuration for the question harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).with_name("config.json")


def _load_config() -> dict[str, Any]:
    with _CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise TypeError("e2e-tests config must be a JSON object")
    return config


_CONFIG = _load_config()
ELEMENT_SOLUTION_ANSWER_SELECTORS: tuple[str, ...] = tuple(
    selector
    for selector in _CONFIG.get("element_solution_answer_selectors", [])
    if isinstance(selector, str) and selector.strip()
)
NON_GRADABLE_ANSWER_SELECTORS: tuple[str, ...] = tuple(
    selector
    for selector in _CONFIG.get("non_gradable_answer_selectors", [])
    if isinstance(selector, str) and selector.strip()
)
