from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .errors import HarnessError
from .metadata import load_json

type LifecycleMethod = Literal["generate", "prepare", "render", "grade"]

E2E_CONFIG_FILENAME = ".question-e2e.json"
LIFECYCLE_METHODS: frozenset[str] = frozenset(
    {
        "generate",
        "prepare",
        "render",
        "grade",
    }
)


@dataclass(frozen=True, slots=True)
class E2EConfig:
    """Question-local end-to-end test configuration."""

    skip_methods: dict[str, str]
    regression_seeds: tuple[int, ...]


def load_e2e_config(config_path: Path) -> E2EConfig:
    """Load and validate a question-local E2E configuration file."""

    if not config_path.is_file():
        return E2EConfig(skip_methods={}, regression_seeds=())

    config = load_json(config_path)
    if not isinstance(config, dict):
        raise HarnessError(f"{config_path}: top-level JSON value must be an object")

    if unknown_keys := set(config) - {"regression_seeds", "skip_methods"}:
        raise HarnessError(
            f"{config_path}: unknown keys: {', '.join(sorted(unknown_keys))}"
        )

    skip_methods = config.get("skip_methods", {})
    if not isinstance(skip_methods, dict):
        raise HarnessError(f"{config_path}: skip_methods must be an object")

    if unknown_methods := set(skip_methods) - LIFECYCLE_METHODS:
        raise HarnessError(
            f"{config_path}: unknown skip methods: {', '.join(sorted(unknown_methods))}"
        )

    validated_skip_methods: dict[str, str] = {}
    for method, reason in skip_methods.items():
        if not isinstance(reason, str) or not reason.strip():
            raise HarnessError(
                f"{config_path}: skip reason for {method!r} must be a non-empty string"
            )
        validated_skip_methods[method] = reason.strip()

    regression_seeds = config.get("regression_seeds", [])
    if not isinstance(regression_seeds, list):
        raise HarnessError(f"{config_path}: regression_seeds must be an array")

    validated_regression_seeds: list[int] = []
    seen_regression_seeds: set[int] = set()
    for index, seed in enumerate(regression_seeds):
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise HarnessError(
                f"{config_path}: regression_seeds[{index}] must be an integer"
            )
        if not 0 <= seed < 2**32:
            raise HarnessError(
                f"{config_path}: regression_seeds[{index}] must be between "
                f"0 and {2**32 - 1}"
            )
        if seed in seen_regression_seeds:
            raise HarnessError(
                f"{config_path}: regression_seeds contains duplicate seed {seed}"
            )
        validated_regression_seeds.append(seed)
        seen_regression_seeds.add(seed)

    return E2EConfig(
        skip_methods=validated_skip_methods,
        regression_seeds=tuple(validated_regression_seeds),
    )


def load_e2e_skip_methods(config_path: Path) -> dict[str, str]:
    """Load method-specific E2E skips from a question-local config file."""

    return load_e2e_config(config_path).skip_methods


@dataclass(frozen=True, slots=True)
class QuestionCase:
    """A question directory discovered from an ``info.json`` file."""

    directory: Path
    course_root: Path

    @property
    def info_path(self) -> Path:
        return self.directory / "info.json"

    @property
    def qid(self) -> str:
        questions_root = self.course_root / "questions"
        try:
            return self.directory.relative_to(questions_root).as_posix()
        except ValueError:
            return self.directory.relative_to(self.course_root).as_posix()

    @property
    def e2e_config_path(self) -> Path:
        return self.directory / E2E_CONFIG_FILENAME

    def e2e_config(self) -> E2EConfig:
        return load_e2e_config(self.e2e_config_path)

    def e2e_skip_reason(self, method: LifecycleMethod) -> str | None:
        return self.e2e_config().skip_methods.get(method)

    def unvalidated_metadata(self) -> dict[str, Any]:
        value = load_json(self.info_path)
        return value if isinstance(value, dict) else {}

    def is_manual_grading(self) -> bool:
        """Whether this question contains instructor-only grading content."""

        metadata = self.unvalidated_metadata()
        declared = metadata.get("gradingMethod") == "Manual"
        question_path = self.directory / "question.html"
        if not question_path.is_file():
            return declared
        has_manual_content = (
            "<pl-manual-grading-only"
            in question_path.read_text(encoding="utf-8").lower()
        )
        if has_manual_content and not declared:
            raise HarnessError(
                f"{self.info_path}: question uses pl-manual-grading-only "
                'but info.json does not declare gradingMethod: "Manual"'
            )
        return declared or has_manual_content


def variant_seeds(
    metadata: dict[str, Any],
    seed_count: int,
    fuzz_seed: int | None = None,
    *,
    regression_seeds: Sequence[int] = (),
) -> tuple[int, ...]:
    """Return saved regressions followed by generated variant seeds."""
    if seed_count < 1:
        raise ValueError("seed count must be at least 1")
    if seed_count > 2**32:
        raise ValueError("fuzz seed count cannot exceed 2**32")
    if metadata.get("singleVariant") is True:
        if any(seed != 0 for seed in regression_seeds):
            raise ValueError("singleVariant questions may only use regression seed 0")
        generated_seeds = (0,)
    elif fuzz_seed is None:
        generated_seeds = tuple(range(seed_count))
    else:
        generated_seeds = tuple(
            random.Random(fuzz_seed).sample(range(2**32), seed_count)
        )
    return tuple(dict.fromkeys((*regression_seeds, *generated_seeds)))


def _info_paths(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.name != "info.json":
            raise ValueError(f"{input_path}: expected an info.json file")
        return [input_path]
    if not input_path.is_dir():
        raise ValueError(f"{input_path}: path does not exist")

    paths = list(input_path.rglob("info.json"))
    direct = input_path / "info.json"
    if direct.is_file() and direct not in paths:
        paths.append(direct)
    if not paths:
        raise ValueError(f"{input_path}: no info.json files found")
    return paths


def discover_questions(
    paths: Sequence[str | Path],
    course_root: str | Path,
) -> list[QuestionCase]:
    """Discover question directories beneath explicit files or directories."""

    root = Path(course_root).resolve()
    info_paths: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        info_paths.update(candidate.resolve() for candidate in _info_paths(path))

    return [
        QuestionCase(info_path.parent, root)
        for info_path in sorted(info_paths, key=lambda item: item.as_posix())
    ]
