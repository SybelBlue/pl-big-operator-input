from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from prairielearn_e2e import PrairieLearnBackend, QuestionHarness
from prairielearn_e2e.contract import Phase


class RecordingBackend:
    def __init__(self) -> None:
        self.phases: list[Phase] = []

    def process(
        self, phase: Phase, html: str, data: dict[str, Any]
    ) -> tuple[str | None, set[str]]:
        self.phases.append(phase)
        return (html if phase == "render" else None), set()

    def unresolved_elements(self, html: str) -> set[str]:
        return set()


def _harness(tmp_path: Path) -> tuple[QuestionHarness, RecordingBackend]:
    schemas = tmp_path / ".prairielearn" / "schemas"
    schemas.mkdir(parents=True)
    (schemas / "infoQuestion.json").write_text("{}", encoding="utf-8")

    question = tmp_path / "questions" / "example"
    question.mkdir(parents=True)
    (question / "info.json").write_text('{"type": "v3"}', encoding="utf-8")
    (question / "question.html").write_text("<p>Example</p>", encoding="utf-8")
    (question / "server.py").write_text(
        "def test(data):\n    raise RuntimeError('grading reached')\n",
        encoding="utf-8",
    )

    backend = RecordingBackend()
    harness = QuestionHarness(
        question,
        cast(PrairieLearnBackend, backend),
        course_root=tmp_path,
    )
    return harness, backend


@pytest.mark.parametrize(
    ("method_name", "expected_phases"),
    [
        ("run_generate", []),
        ("run_prepare", ["prepare"]),
        ("run_render", ["prepare", "render", "render"]),
    ],
)
def test_phase_checks_stop_before_grading(
    tmp_path: Path, method_name: str, expected_phases: list[Phase]
) -> None:
    harness, backend = _harness(tmp_path)

    getattr(harness, method_name)(0)

    assert backend.phases == expected_phases


def test_grade_check_reaches_grading_hooks(tmp_path: Path) -> None:
    harness, _ = _harness(tmp_path)

    with pytest.raises(RuntimeError, match="grading reached"):
        harness.run_grade(0)
