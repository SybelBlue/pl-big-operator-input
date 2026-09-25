from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from typing import Any, Literal

from prairielearn.internal.zygote_utils import assert_all_integers_within_limits

from .errors import HarnessError

type Phase = Literal["generate", "prepare", "render", "parse", "grade", "test", "file"]


@dataclass(frozen=True, slots=True)
class Field:
    kind: Literal["dict", "integer", "number", "string", "boolean"]


BASE_FIELDS = {
    "params": Field("dict"),
    "correct_answers": Field("dict"),
    "variant_seed": Field("integer"),
    "options": Field("dict"),
    "preferences": Field("dict"),
}

PHASE_FIELDS: dict[Phase, dict[str, Field]] = {
    "generate": BASE_FIELDS,
    "prepare": {**BASE_FIELDS, "answers_names": Field("dict")},
    "render": {
        **BASE_FIELDS,
        "submitted_answers": Field("dict"),
        "format_errors": Field("dict"),
        "raw_submitted_answers": Field("dict"),
        "partial_scores": Field("dict"),
        "score": Field("number"),
        "feedback": Field("dict"),
        "editable": Field("boolean"),
        "manual_grading": Field("boolean"),
        "ai_grading": Field("boolean"),
        "panel": Field("string"),
        "correct_answer_shown": Field("boolean"),
        "num_valid_submissions": Field("integer"),
    },
    "parse": {
        **BASE_FIELDS,
        "submitted_answers": Field("dict"),
        "format_errors": Field("dict"),
        "raw_submitted_answers": Field("dict"),
        "feedback": Field("dict"),
        "gradable": Field("boolean"),
    },
    "grade": {
        **BASE_FIELDS,
        "submitted_answers": Field("dict"),
        "format_errors": Field("dict"),
        "raw_submitted_answers": Field("dict"),
        "partial_scores": Field("dict"),
        "score": Field("number"),
        "feedback": Field("dict"),
        "gradable": Field("boolean"),
    },
    "test": {
        **BASE_FIELDS,
        "format_errors": Field("dict"),
        "raw_submitted_answers": Field("dict"),
        "partial_scores": Field("dict"),
        "score": Field("number"),
        "feedback": Field("dict"),
        "gradable": Field("boolean"),
        "test_type": Field("string"),
    },
    "file": {
        **BASE_FIELDS,
        "submitted_answers": Field("dict"),
        "format_errors": Field("dict"),
        "raw_submitted_answers": Field("dict"),
        "partial_scores": Field("dict"),
        "score": Field("number"),
        "feedback": Field("dict"),
        "num_valid_submissions": Field("integer"),
        "filename": Field("string"),
    },
}

EDITABLE_FIELDS: dict[Phase, frozenset[str]] = {
    "generate": frozenset({"params", "correct_answers"}),
    "prepare": frozenset({"params", "correct_answers", "answers_names"}),
    "render": frozenset(),
    "parse": frozenset(
        {"params", "correct_answers", "submitted_answers", "format_errors", "feedback"}
    ),
    "grade": frozenset(
        {
            "params",
            "correct_answers",
            "submitted_answers",
            "format_errors",
            "partial_scores",
            "score",
            "feedback",
        }
    ),
    "test": frozenset(
        {
            "raw_submitted_answers",
            "format_errors",
            "partial_scores",
            "score",
            "feedback",
        }
    ),
    "file": frozenset(),
}


def _valid_type(value: Any, kind: str) -> bool:
    if kind == "dict":
        return isinstance(value, dict)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    return False


def validate_shape(data: dict[str, Any], phase: Phase) -> None:
    fields = PHASE_FIELDS[phase]
    actual = set(data)
    expected = set(fields)
    if missing := expected - actual:
        raise HarnessError(
            f"{phase}: data is missing fields: {', '.join(sorted(missing))}"
        )
    if extra := actual - expected:
        raise HarnessError(
            f"{phase}: data has extra fields: {', '.join(sorted(extra))}"
        )
    for name, field in fields.items():
        if not _valid_type(data[name], field.kind):
            raise HarnessError(
                f"{phase}: data[{name!r}] must have type {field.kind}, "
                f"got {type(data[name]).__name__}"
            )


def validate_mutations(
    before: dict[str, Any], after: dict[str, Any], phase: Phase
) -> None:
    validate_shape(after, phase)
    editable = EDITABLE_FIELDS[phase]
    for name in PHASE_FIELDS[phase]:
        if name not in editable and before[name] != after[name]:
            raise HarnessError(f"{phase}: data[{name!r}] was illegally modified")


def validate_serializable(data: dict[str, Any], phase: Phase) -> None:
    def check_json(value: Any, path: str) -> None:
        if value is None or isinstance(value, (str, bool, int)):
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise TypeError(f"{path} contains NaN or infinity")
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                check_json(item, f"{path}[{index}]")
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise TypeError(f"{path} has a non-string object key")
                check_json(item, f"{path}[{key!r}]")
            return
        raise TypeError(f"{path} contains {type(value).__name__}, which is not JSON")

    try:
        check_json(data, "data")
        assert_all_integers_within_limits(data)
        json.dumps(data, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise HarnessError(
            f"{phase}: data is not PrairieLearn JSON serializable: {exc}"
        ) from exc


def snapshot(data: dict[str, Any], phase: Phase) -> dict[str, Any]:
    validate_shape(data, phase)
    return copy.deepcopy(data)
