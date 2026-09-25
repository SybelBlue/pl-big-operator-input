from __future__ import annotations

from pathlib import Path

import pytest
from prairielearn_e2e.errors import HarnessError
from prairielearn_e2e.harness import _assert_full_credit
from prairielearn_e2e.server import ServerModule

from .test_contract import valid_data


def _server(tmp_path: Path, source: str) -> ServerModule:
    path = tmp_path / "server.py"
    path.write_text(source, encoding="utf-8")
    return ServerModule(path, tmp_path)


def test_hook_signature_is_checked(tmp_path: Path) -> None:
    with pytest.raises(HarnessError, match=r"generate must accept \(data\)"):
        _server(tmp_path, "def generate():\n    pass\n")
    with pytest.raises(HarnessError, match=r"render must accept \(data, html\)"):
        _server(tmp_path, "def render(data):\n    return ''\n")


def test_wrong_field_mutation_is_rejected(tmp_path: Path) -> None:
    server = _server(tmp_path, "def generate(data):\n    data['variant_seed'] = 12\n")
    with pytest.raises(HarnessError, match="variant_seed.*illegally modified"):
        server.invoke("generate", valid_data("generate"))  # type: ignore[arg-type]


def test_non_in_place_return_is_rejected(tmp_path: Path) -> None:
    server = _server(tmp_path, "def prepare(data):\n    return {}\n")
    with pytest.raises(HarnessError, match="mutate data in place"):
        server.invoke("prepare", valid_data("prepare"))  # type: ignore[arg-type]


def test_console_output_is_rejected(tmp_path: Path) -> None:
    server = _server(tmp_path, "def generate(data):\n    print('noise')\n")
    with pytest.raises(HarnessError, match="unexpected console output"):
        server.invoke("generate", valid_data("generate"))  # type: ignore[arg-type]


def test_render_return_and_mutation_contract(tmp_path: Path) -> None:
    bad_return = _server(tmp_path, "def render(data, html):\n    return None\n")
    with pytest.raises(HarnessError, match="render must return HTML text"):
        bad_return.invoke("render", valid_data("render"), "<p>x</p>")  # type: ignore[arg-type]

    mutating = _server(
        tmp_path,
        "def render(data, html):\n    data['panel'] = 'answer'\n    return html\n",
    )
    with pytest.raises(HarnessError, match="panel.*illegally modified"):
        mutating.invoke("render", valid_data("render"), "<p>x</p>")  # type: ignore[arg-type]


def test_file_accepts_documented_return_types(tmp_path: Path) -> None:
    server = _server(tmp_path, "def file(data):\n    return b'content'\n")
    assert server.invoke("file", valid_data("file")) == b"content"  # type: ignore[arg-type]


def test_wrong_correct_submission_fails_round_trip_assertion() -> None:
    data = {
        "format_errors": {},
        "gradable": True,
        "score": 0.5,
        "submitted_answers": {"x": "wrong"},
        "partial_scores": {"x": {"score": 0.5, "weight": 1}},
    }
    with pytest.raises(HarnessError, match="received score 0.5"):
        _assert_full_credit(data, ("x",))


def test_imported_sympy_test_function_is_not_a_server_hook(tmp_path: Path) -> None:
    server = _server(tmp_path, "from sympy import *\n")
    assert not server.has_hook("test")
