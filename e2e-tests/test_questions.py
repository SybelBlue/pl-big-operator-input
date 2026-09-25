from __future__ import annotations

from collections.abc import Callable

import pytest
from prairielearn_e2e import PrairieLearnBackend, QuestionCase, QuestionHarness
from prairielearn_e2e.discovery import LifecycleMethod
from prairielearn_e2e.errors import UnsupportedQuestion

type LifecycleCheck = Callable[[QuestionHarness, int], object]


def _run_check(
    question_variant: tuple[QuestionCase | None, int],
    request: pytest.FixtureRequest,
    method: LifecycleMethod,
    check: LifecycleCheck,
) -> None:
    question, seed = question_variant
    if question is None:
        pytest.skip("pass one or more --question-path values to select content")
    assert question is not None
    if reason := question.e2e_skip_reason(method):
        pytest.skip(reason)
    backend: PrairieLearnBackend = request.getfixturevalue("prairielearn_backend")
    try:
        check(QuestionHarness(question, backend), seed)
    except UnsupportedQuestion as exc:
        pytest.skip(str(exc))


@pytest.mark.generate
def test_question_generate(
    question_variant: tuple[QuestionCase | None, int],
    request: pytest.FixtureRequest,
) -> None:
    _run_check(question_variant, request, "generate", QuestionHarness.run_generate)


@pytest.mark.prepare
def test_question_prepare(
    question_variant: tuple[QuestionCase | None, int],
    request: pytest.FixtureRequest,
) -> None:
    _run_check(question_variant, request, "prepare", QuestionHarness.run_prepare)


@pytest.mark.render
def test_question_render(
    question_variant: tuple[QuestionCase | None, int],
    request: pytest.FixtureRequest,
) -> None:
    _run_check(question_variant, request, "render", QuestionHarness.run_render)


@pytest.mark.grade
def test_question_grade(
    question_variant: tuple[QuestionCase | None, int],
    request: pytest.FixtureRequest,
) -> None:
    question, _ = question_variant
    if question is not None and question.is_manual_grading():
        pytest.skip("question is configured for manual grading")
    _run_check(question_variant, request, "grade", QuestionHarness.run_grade)
