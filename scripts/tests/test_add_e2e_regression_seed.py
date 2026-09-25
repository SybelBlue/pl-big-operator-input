from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPOSITORY_ROOT / "Makefile"
SCRIPT = REPOSITORY_ROOT / "scripts" / "add_e2e_regression_seed.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="jq is required")


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", repository],
        check=True,
    )
    (repository / "questions").mkdir()
    return repository


def _question(repository: Path, name: str = "chapter/example") -> Path:
    question = repository / "questions" / name
    question.mkdir(parents=True)
    (question / "info.json").write_text("{}", encoding="utf-8")
    return question


def _run_script(
    repository: Path, question_path: str, seed: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", SCRIPT, question_path, seed],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )


def test_adds_seed_to_new_config(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = _question(repository)

    result = _run_script(repository, "questions/chapter/example", "1843927501")

    assert result.returncode == 0
    assert json.loads((question / ".question-e2e.json").read_text()) == {
        "regression_seeds": [1843927501]
    }
    assert "Added regression seed 1843927501" in result.stdout


def test_make_target_adds_seed(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = _question(repository)
    (repository / "scripts").symlink_to(REPOSITORY_ROOT / "scripts")

    result = subprocess.run(
        [
            "make",
            "--file",
            MAKEFILE,
            "add-e2e-regression-seed",
            "QUESTION_PATH=questions/chapter/example",
            "VARIANT_SEED=23",
        ],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads((question / ".question-e2e.json").read_text()) == {
        "regression_seeds": [23]
    }


def test_preserves_config_and_sorts_seeds(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = _question(repository, "chapter/with space")
    config_path = question / ".question-e2e.json"
    config_path.write_text(
        json.dumps(
            {
                "skip_methods": {"grade": "Blocked"},
                "regression_seeds": [11],
            }
        ),
        encoding="utf-8",
    )

    result = _run_script(repository, "questions/chapter/with space", "7")

    assert result.returncode == 0
    assert json.loads(config_path.read_text()) == {
        "skip_methods": {"grade": "Blocked"},
        "regression_seeds": [7, 11],
    }


def test_existing_seed_is_unchanged(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = _question(repository)
    config_path = question / ".question-e2e.json"
    original = '{"regression_seeds":[7]}\n'
    config_path.write_text(original, encoding="utf-8")

    result = _run_script(repository, "questions/chapter/example", "7")

    assert result.returncode == 0
    assert config_path.read_text() == original
    assert "already recorded" in result.stdout


@pytest.mark.parametrize("seed", ["", "-1", "01", "1.5", "4294967296", "seed"])
def test_rejects_invalid_seed(tmp_path: Path, seed: str) -> None:
    repository = _repository(tmp_path)
    question = _question(repository)

    result = _run_script(repository, "questions/chapter/example", seed)

    assert result.returncode == 2
    assert not (question / ".question-e2e.json").exists()
    assert (
        "VARIANT_SEED must be an integer" in result.stderr or "Usage:" in result.stderr
    )


def test_rejects_directory_outside_questions(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = repository / "example"
    question.mkdir()
    (question / "info.json").write_text("{}", encoding="utf-8")

    result = _run_script(repository, "example", "7")

    assert result.returncode == 2
    assert "must be a directory beneath questions/" in result.stderr


def test_rejects_non_object_config_without_modifying_it(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    question = _question(repository)
    config_path = question / ".question-e2e.json"
    config_path.write_text("[]\n", encoding="utf-8")

    result = _run_script(repository, "questions/chapter/example", "7")

    assert result.returncode == 2
    assert config_path.read_text() == "[]\n"
    assert "must contain a JSON object" in result.stderr
