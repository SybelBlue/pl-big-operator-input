from __future__ import annotations

import pytest
from prairielearn_e2e.errors import HarnessError
from prairielearn_e2e.html_checks import (
    element_solution_answer_names,
    non_gradable_answer_names,
    validate_declared_answers,
)


def test_declared_answers_require_correct_values_by_default() -> None:
    html = '<pl-integer-input answers-name="x"></pl-integer-input>'

    with pytest.raises(HarnessError, match="non-null correct answers for: x"):
        validate_declared_answers(html, {}, True)
    with pytest.raises(HarnessError, match="non-null correct answers for: x"):
        validate_declared_answers(html, {"x": None}, True)


def test_show_correct_answer_false_exempts_missing_value() -> None:
    html = '<pl-integer-input answers-name="x"></pl-integer-input>'
    assert validate_declared_answers(html, {}, False) == ("x",)


def test_read_only_sketch_is_not_a_server_graded_answer() -> None:
    html = '<pl-sketch answers-name="graph" read-only="true"></pl-sketch>'

    assert non_gradable_answer_names(html) == {"graph"}
    assert validate_declared_answers(html, {}, True) == ("graph",)


def test_gradable_sketch_uses_its_element_solution() -> None:
    html = '<pl-sketch answers-name="graph"></pl-sketch>'

    assert element_solution_answer_names(html) == {"graph"}
    assert non_gradable_answer_names(html) == set()
    assert validate_declared_answers(html, {}, True) == ("graph",)


@pytest.mark.parametrize(
    "html,match",
    [
        ('<pl-input answers-name=""></pl-input>', "empty answers-name"),
        (
            '<pl-input answers-name="x"></pl-input><pl-input answers-name="x"></pl-input>',
            "duplicate answers-name values: x",
        ),
    ],
)
def test_malformed_or_duplicate_answer_names_are_rejected(
    html: str, match: str
) -> None:
    with pytest.raises(HarnessError, match=match):
        validate_declared_answers(html, {}, False)
