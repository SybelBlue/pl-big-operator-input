from __future__ import annotations

import copy
import math

import pytest
from prairielearn_e2e.contract import (
    PHASE_FIELDS,
    Phase,
    snapshot,
    validate_mutations,
    validate_serializable,
    validate_shape,
)
from prairielearn_e2e.errors import HarnessError


def valid_data(phase: Phase) -> dict[str, object]:
    values: dict[str, object] = {
        "params": {},
        "correct_answers": {},
        "variant_seed": 0,
        "options": {},
        "preferences": {},
        "answers_names": {},
        "submitted_answers": {},
        "format_errors": {},
        "raw_submitted_answers": {},
        "partial_scores": {},
        "score": 0.0,
        "feedback": {},
        "gradable": True,
        "editable": True,
        "manual_grading": False,
        "ai_grading": False,
        "panel": "question",
        "correct_answer_shown": False,
        "num_valid_submissions": 0,
        "test_type": "correct",
        "filename": "test.txt",
    }
    return {name: copy.deepcopy(values[name]) for name in PHASE_FIELDS[phase]}


@pytest.mark.parametrize("phase", PHASE_FIELDS)
def test_all_phase_shapes_are_accepted(phase: Phase) -> None:
    validate_shape(valid_data(phase), phase)  # type: ignore[arg-type]


def test_missing_extra_and_wrong_type_are_rejected() -> None:
    missing = valid_data("generate")
    missing.pop("params")
    with pytest.raises(HarnessError, match="missing fields: params"):
        validate_shape(missing, "generate")  # type: ignore[arg-type]

    extra = valid_data("generate")
    extra["surprise"] = True
    with pytest.raises(HarnessError, match="extra fields: surprise"):
        validate_shape(extra, "generate")  # type: ignore[arg-type]

    wrong = valid_data("generate")
    wrong["variant_seed"] = True
    with pytest.raises(HarnessError, match="must have type integer"):
        validate_shape(wrong, "generate")  # type: ignore[arg-type]


def test_nested_read_only_mutation_is_rejected() -> None:
    data = valid_data("generate")
    data["options"] = {"nested": {"value": 1}}
    before = snapshot(data, "generate")  # type: ignore[arg-type]
    data["options"]["nested"]["value"] = 2  # type: ignore[index]

    with pytest.raises(HarnessError, match="options.*illegally modified"):
        validate_mutations(before, data, "generate")  # type: ignore[arg-type]


def test_editable_field_mutation_is_accepted() -> None:
    data = valid_data("parse")
    before = snapshot(data, "parse")  # type: ignore[arg-type]
    data["submitted_answers"] = {"x": 1}
    validate_mutations(before, data, "parse")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value", [{1, 2}, (1, 2), {1: "bad key"}, math.nan, math.inf, 2**64]
)
def test_non_json_and_out_of_range_values_are_rejected(value: object) -> None:
    data = valid_data("generate")
    data["params"] = {"bad": value}

    with pytest.raises(HarnessError, match="not PrairieLearn JSON serializable"):
        validate_serializable(data, "generate")  # type: ignore[arg-type]
