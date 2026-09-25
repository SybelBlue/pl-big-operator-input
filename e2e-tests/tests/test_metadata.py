from __future__ import annotations

from pathlib import Path

import pytest
from prairielearn_e2e.errors import HarnessError
from prairielearn_e2e.metadata import load_json, validate_question_metadata

COURSE_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("invalid", ["{", '{"value": NaN}', "[] trailing"])
def test_json_loading_is_strict(tmp_path: Path, invalid: str) -> None:
    path = tmp_path / "info.json"
    path.write_text(invalid, encoding="utf-8")
    with pytest.raises(HarnessError, match="invalid JSON"):
        load_json(path)


def test_info_json_is_validated_against_local_schema(tmp_path: Path) -> None:
    path = tmp_path / "info.json"
    path.write_text('{"type": "v3"}', encoding="utf-8")

    with pytest.raises(HarnessError, match="metadata schema validation failed"):
        validate_question_metadata(path, COURSE_ROOT)


def test_course_question_metadata_is_valid() -> None:
    path = COURSE_ROOT / "questions/s.1/info.json"
    metadata = validate_question_metadata(path, COURSE_ROOT)
    assert metadata["singleVariant"] is True
