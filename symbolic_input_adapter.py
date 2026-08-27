from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import lxml.html

HERE = Path(__file__).parent
VENDOR_DIR = HERE / "vendor" / "prairielearn" / "pl-symbolic-input"
CONTROLLER_PATH = VENDOR_DIR / "pl-symbolic-input.py"
TEMPLATE_PATH = VENDOR_DIR / "pl-symbolic-input.mustache"


def _load_controller() -> ModuleType:
    module_name = "pl_big_operator_input_vendored_symbolic_input"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, CONTROLLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load vendored controller at {CONTROLLER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    # Upstream normally runs with the element directory as its working directory.
    # Use an absolute template path so this adapter does not mutate process-global cwd.
    setattr(module, "SYMBOLIC_INPUT_MUSTACHE_TEMPLATE_NAME", str(TEMPLATE_PATH))
    return module


CONTROLLER = _load_controller()


def markup(
    *,
    name: str,
    variables: tuple[str, ...],
    label: str,
    size: int,
    allow_sets: bool,
    prefix: str | None = None,
    suffix: str | None = None,
) -> str:
    element = lxml.html.Element("pl-symbolic-input")
    attributes = {
        "answers-name": name,
        "variables": ",".join(variables),
        "formula-editor": "true",
        "show-help-text": "false",
        "show-score": "false",
        "placeholder": "",
        "size": str(size),
        "aria-label": label,
        "allow-sets": str(allow_sets).lower(),
    }
    if prefix is not None:
        attributes["label"] = prefix
    if suffix is not None:
        attributes["suffix"] = suffix
    for key, value in attributes.items():
        element.set(key, value)
    return cast(str, lxml.html.tostring(element, encoding="unicode"))


def _render_data_view(data: dict[str, Any]) -> dict[str, Any]:
    view = dict(data)
    view.setdefault("correct_answers", {})
    view.setdefault("format_errors", {})
    view.setdefault("partial_scores", {})
    view.setdefault("raw_submitted_answers", {})
    view.setdefault("submitted_answers", {})
    view.setdefault("panel", "question")
    view.setdefault("editable", view["panel"] == "question")
    return view


def render(field_markup: str, data: dict[str, Any], *, aria_label: str) -> str:
    rendered = CONTROLLER.render(field_markup, _render_data_view(data))
    # The pinned upstream formula-editor template does not apply its aria-label
    # parameter to the math-field. Keep the vendored files pristine and bridge
    # that accessibility gap in the adapter.
    return rendered.replace("<math-field", f'<math-field aria-label="{aria_label}"', 1)


def parse(field_markup: str, data: dict[str, Any]) -> None:
    had_format_errors = "format_errors" in data
    data.setdefault("correct_answers", {})
    data.setdefault("format_errors", {})
    data.setdefault("raw_submitted_answers", {})
    data.setdefault("submitted_answers", {})
    view = data
    element = lxml.html.fragment_fromstring(field_markup)
    name = element.get("answers-name")
    if not name:
        raise ValueError("Delegated symbolic input is missing answers-name.")
    view["submitted_answers"][name] = view["raw_submitted_answers"].get(name)
    CONTROLLER.parse(field_markup, view)
    if not had_format_errors and not view["format_errors"]:
        del view["format_errors"]
