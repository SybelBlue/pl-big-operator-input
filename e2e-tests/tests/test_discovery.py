from __future__ import annotations

from pathlib import Path

import pytest
from prairielearn_e2e import QuestionCase, discover_questions
from prairielearn_e2e.discovery import (
    E2EConfig,
    load_e2e_config,
    variant_seeds,
)
from prairielearn_e2e.errors import HarnessError


def _question(root: Path, name: str) -> Path:
    directory = root / "questions" / name
    directory.mkdir(parents=True)
    (directory / "info.json").write_text("{}", encoding="utf-8")
    return directory


def test_discovery_is_recursive_stable_and_deduplicated(tmp_path: Path) -> None:
    second = _question(tmp_path, "chapter/b")
    first = _question(tmp_path, "chapter/a")

    discovered = discover_questions(
        ["questions/chapter", first, second / "info.json"], tmp_path
    )

    assert [question.qid for question in discovered] == ["chapter/a", "chapter/b"]


@pytest.mark.parametrize("name", ["missing", "empty"])
def test_explicit_path_without_info_json_is_an_error(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    if name == "empty":
        path.mkdir()

    with pytest.raises(ValueError, match="does not exist|no info.json"):
        discover_questions([path], tmp_path)


def test_non_info_file_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "question.html"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="expected an info.json"):
        discover_questions([path], tmp_path)


def test_seed_handling() -> None:
    assert variant_seeds({}, 3) == (0, 1, 2)
    assert variant_seeds({"singleVariant": True}, 10) == (0,)
    with pytest.raises(ValueError, match="at least 1"):
        variant_seeds({}, 0)


def test_fuzz_seed_handling() -> None:
    seeds = variant_seeds({}, 10, fuzz_seed=12345)

    assert seeds == variant_seeds({}, 10, fuzz_seed=12345)
    assert seeds != variant_seeds({}, 10, fuzz_seed=54321)
    assert len(seeds) == len(set(seeds)) == 10
    assert all(0 <= seed < 2**32 for seed in seeds)
    assert variant_seeds({"singleVariant": True}, 10, fuzz_seed=12345) == (0,)
    with pytest.raises(ValueError, match="cannot exceed"):
        variant_seeds({}, 2**32 + 1, fuzz_seed=12345)


def test_regression_seeds_precede_and_deduplicate_generated_seeds() -> None:
    assert variant_seeds({}, 3, regression_seeds=(2, 99)) == (2, 99, 0, 1)


def test_regression_seeds_are_independent_of_the_fuzz_seed() -> None:
    first = variant_seeds({}, 3, fuzz_seed=12345, regression_seeds=(99,))
    second = variant_seeds({}, 3, fuzz_seed=54321, regression_seeds=(99,))

    assert first[0] == second[0] == 99
    assert first[1:] != second[1:]


def test_single_variant_rejects_nonzero_regression_seed() -> None:
    with pytest.raises(ValueError, match="may only use regression seed 0"):
        variant_seeds({"singleVariant": True}, 3, regression_seeds=(1,))


def test_missing_question_local_e2e_config_uses_defaults(tmp_path: Path) -> None:
    assert load_e2e_config(tmp_path / ".question-e2e.json") == E2EConfig(
        skip_methods={}, regression_seeds=()
    )


def test_question_local_e2e_config_skips_individual_methods(tmp_path: Path) -> None:
    question = _question(tmp_path, "example")
    config_path = question / ".question-e2e.json"
    config_path.write_text(
        '{"skip_methods":{"grade":"Blocked by upstream issue"}}',
        encoding="utf-8",
    )
    case = QuestionCase(question, tmp_path)

    assert case.e2e_skip_reason("grade") == "Blocked by upstream issue"
    assert case.e2e_skip_reason("render") is None


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            '{"regression_seeds":[1843927501]}',
            E2EConfig(skip_methods={}, regression_seeds=(1843927501,)),
        ),
        (
            '{"skip_methods":{"grade":"Blocked"},"regression_seeds":[7,11]}',
            E2EConfig(skip_methods={"grade": "Blocked"}, regression_seeds=(7, 11)),
        ),
    ],
)
def test_question_local_e2e_config_loads_regression_seeds(
    tmp_path: Path, config: str, expected: E2EConfig
) -> None:
    config_path = tmp_path / ".question-e2e.json"
    config_path.write_text(config, encoding="utf-8")

    assert load_e2e_config(config_path) == expected


def test_question_local_regression_seeds_are_isolated(tmp_path: Path) -> None:
    first = _question(tmp_path, "first")
    second = _question(tmp_path, "second")
    (first / ".question-e2e.json").write_text(
        '{"regression_seeds":[7]}', encoding="utf-8"
    )
    (second / ".question-e2e.json").write_text(
        '{"regression_seeds":[11]}', encoding="utf-8"
    )

    first_config = QuestionCase(first, tmp_path).e2e_config()
    second_config = QuestionCase(second, tmp_path).e2e_config()

    assert variant_seeds({}, 2, regression_seeds=first_config.regression_seeds) == (
        7,
        0,
        1,
    )
    assert variant_seeds({}, 2, regression_seeds=second_config.regression_seeds) == (
        11,
        0,
        1,
    )


@pytest.mark.parametrize(
    ("config", "match"),
    [
        ("[]", "top-level JSON value must be an object"),
        ('{"extra":true}', "unknown keys: extra"),
        ('{"skip_methods":[]}', "skip_methods must be an object"),
        (
            '{"skip_methods":{"grading":"not a method"}}',
            "unknown skip methods: grading",
        ),
        ('{"skip_methods":{"grade":""}}', "must be a non-empty string"),
        ('{"regression_seeds":{}}', "regression_seeds must be an array"),
        ('{"regression_seeds":[true]}', r"regression_seeds\[0\] must be an integer"),
        ('{"regression_seeds":["1"]}', r"regression_seeds\[0\] must be an integer"),
        ('{"regression_seeds":[-1]}', r"regression_seeds\[0\] must be between"),
        (
            f'{{"regression_seeds":[{2**32}]}}',
            r"regression_seeds\[0\] must be between",
        ),
        ('{"regression_seeds":[7,7]}', "contains duplicate seed 7"),
    ],
)
def test_question_local_e2e_config_is_strict(
    tmp_path: Path, config: str, match: str
) -> None:
    config_path = tmp_path / ".question-e2e.json"
    config_path.write_text(config, encoding="utf-8")

    with pytest.raises(HarnessError, match=match):
        load_e2e_config(config_path)


def test_manual_grading_question_is_detected(tmp_path: Path) -> None:
    question = tmp_path / "question"
    question.mkdir()
    (question / "info.json").write_text(
        '{"type": "v3", "gradingMethod": "Manual"}', encoding="utf-8"
    )
    (question / "question.html").write_text(
        "<pl-manual-grading-only>guidance</pl-manual-grading-only>",
        encoding="utf-8",
    )

    assert QuestionCase(question, tmp_path).is_manual_grading()


def test_manual_grading_marker_requires_metadata(tmp_path: Path) -> None:
    question = tmp_path / "question"
    question.mkdir()
    (question / "info.json").write_text('{"type": "v3"}', encoding="utf-8")
    (question / "question.html").write_text(
        "<pl-manual-grading-only>guidance</pl-manual-grading-only>",
        encoding="utf-8",
    )

    with pytest.raises(HarnessError, match="does not declare gradingMethod"):
        QuestionCase(question, tmp_path).is_manual_grading()
