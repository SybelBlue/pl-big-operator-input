from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any, cast

import pytest
from prairielearn_e2e import PrairieLearnBackend, QuestionCase, discover_questions
from prairielearn_e2e.discovery import variant_seeds
from prairielearn_e2e.errors import HarnessError

COURSE_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("prairielearn-e2e")
    group.addoption(
        "--question-path",
        action="append",
        default=[],
        metavar="PATH",
        help="info.json, question directory, or parent directory (repeatable)",
    )
    group.addoption(
        "--prairielearn-path",
        metavar="PATH",
        help="PrairieLearn Git clone containing the installed pinned revision",
    )
    group.addoption(
        "--seed-count",
        type=int,
        default=3,
        metavar="N",
        help="number of variant seeds to test (default: 3)",
    )
    group.addoption(
        "--fuzz-seed",
        type=int,
        metavar="N",
        help="master seed used to generate reproducible pseudo-random variant seeds",
    )
    group.addoption(
        "--fuzz-seeds",
        action="store_true",
        help="generate a master seed when --fuzz-seed is not provided",
    )
    group.addoption(
        "--seed-replay-target",
        default="test-e2e",
        metavar="TARGET",
        help="Make target shown in the fuzz-seed replay command",
    )


def pytest_configure(config: pytest.Config) -> None:
    fuzz_seeds = cast(bool, config.getoption("fuzz_seeds"))
    fuzz_seed = cast(int | None, config.getoption("fuzz_seed"))
    if fuzz_seeds and fuzz_seed is None:
        config.option.fuzz_seed = secrets.randbits(64)


def pytest_report_header(config: pytest.Config) -> str | None:
    paths = cast(list[str], config.getoption("question_path"))
    fuzz_seeds = cast(bool, config.getoption("fuzz_seeds"))
    fuzz_seed = cast(int | None, config.getoption("fuzz_seed"))
    replay_target = cast(str, config.getoption("seed_replay_target"))
    if not paths:
        return None

    seed_count = cast(int, config.getoption("seed_count"))
    try:
        seeds = variant_seeds({}, seed_count, fuzz_seed)
    except ValueError:
        return None
    seed_list = f"E2E variant seeds: {', '.join(str(seed) for seed in seeds)}"
    if fuzz_seed is None:
        return seed_list
    if not fuzz_seeds:
        return None
    return "\n".join(
        (
            f"E2E fuzz seed: {fuzz_seed}",
            seed_list,
            f"Replay with: E2E_FUZZ_SEED={fuzz_seed} make {replay_target}",
        )
    )


def _cases(config: pytest.Config) -> list[tuple[QuestionCase | None, int]]:
    paths = cast(list[str], config.getoption("question_path"))
    if not paths:
        return [(None, 0)]
    seed_count = cast(int, config.getoption("seed_count"))
    fuzz_seed = cast(int | None, config.getoption("fuzz_seed"))
    if seed_count < 1:
        raise pytest.UsageError("--seed-count must be at least 1")
    try:
        questions = discover_questions(paths, COURSE_ROOT)
    except (HarnessError, ValueError) as exc:
        raise pytest.UsageError(str(exc)) from exc

    result: list[tuple[QuestionCase | None, int]] = []
    for question in questions:
        try:
            metadata: dict[str, Any] = question.unvalidated_metadata()
        except HarnessError:
            metadata = {}
        try:
            e2e_config = question.e2e_config()
            seeds = variant_seeds(
                metadata,
                seed_count,
                fuzz_seed,
                regression_seeds=e2e_config.regression_seeds,
            )
        except HarnessError as exc:
            raise pytest.UsageError(str(exc)) from exc
        except ValueError as exc:
            raise pytest.UsageError(f"{question.qid}: {exc}") from exc
        result.extend((question, seed) for seed in seeds)
    return result


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "question_variant" not in metafunc.fixturenames:
        return
    cases = _cases(metafunc.config)
    ids = [
        "no-question-paths" if question is None else f"{question.qid}[seed={seed}]"
        for question, seed in cases
    ]
    metafunc.parametrize("question_variant", cases, ids=ids)


@pytest.fixture(scope="session")
def prairielearn_backend(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> PrairieLearnBackend:
    clone = request.config.getoption("prairielearn_path")
    if not clone:
        raise pytest.UsageError(
            "--prairielearn-path is required when --question-path is provided"
        )
    return PrairieLearnBackend.from_clone(
        clone,
        COURSE_ROOT,
        tmp_path_factory.mktemp("prairielearn-core"),
    )
