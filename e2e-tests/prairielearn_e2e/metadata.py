from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import FormatChecker
from jsonschema.validators import validator_for

from .errors import HarnessError


def _reject_constant(value: str) -> None:
    raise ValueError(f"{value} is not a valid JSON value")


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise HarnessError(f"{path}: invalid JSON: {exc}") from exc


def validate_question_metadata(info_path: Path, course_root: Path) -> dict[str, Any]:
    metadata = load_json(info_path)
    if not isinstance(metadata, dict):
        raise HarnessError(f"{info_path}: top-level JSON value must be an object")

    schema_path = course_root / ".prairielearn" / "schemas" / "infoQuestion.json"
    schema = load_json(schema_path)
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    errors = sorted(
        validator_class(schema, format_checker=FormatChecker()).iter_errors(metadata),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        details = "; ".join(error.message for error in errors)
        raise HarnessError(f"{info_path}: metadata schema validation failed: {details}")
    return metadata


def default_preferences(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    preferences = metadata.get("preferences", {})
    if not isinstance(preferences, dict):
        return {}
    return {
        name: definition["default"]
        for name, definition in preferences.items()
        if isinstance(definition, dict) and "default" in definition
    }
