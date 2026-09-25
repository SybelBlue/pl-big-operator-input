"""Run question end-to-end fuzz tests for questions changed between two Git refs."""

from __future__ import annotations

import argparse
import os
import secrets
import shlex
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from prairielearn_e2e.discovery import variant_seeds

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_ROOT = Path("questions")
DEFAULT_E2E_DIFF_IGNORE_PATH = REPOSITORY_ROOT / ".question-e2e.diffignore"


def load_e2e_diff_ignore(config_path: Path) -> list[str]:
    """Load Git-style ignore rules used by E2E change detection."""
    try:
        return config_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Unable to read {config_path}: {exc}") from exc


def e2e_diff_ignored_files(
    changed_files: Sequence[Path], ignore_rules: Sequence[str]
) -> set[Path]:
    """Return changed files matched using Git's native ignore semantics."""
    if not changed_files:
        return set()

    with TemporaryDirectory(prefix="e2e-diff-ignore-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        repository = temporary_root / "repository"
        ignore_file = temporary_root / "exclude"
        ignore_file.write_text("\n".join(ignore_rules), encoding="utf-8")

        subprocess.run(
            ["git", "init", "--quiet", os.fspath(repository)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        result = subprocess.run(
            [
                "git",
                "-C",
                os.fspath(repository),
                "-c",
                f"core.excludesFile={ignore_file}",
                "check-ignore",
                "--no-index",
                "--stdin",
                "-z",
            ],
            check=False,
            capture_output=True,
            input=b"\0".join(os.fsencode(path) for path in changed_files) + b"\0",
        )
        if result.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                output=result.stdout,
                stderr=result.stderr,
            )

    return {Path(os.fsdecode(path)) for path in result.stdout.split(b"\0") if path}


def nonignored_files_outside_questions(
    changed_files: Sequence[Path], ignore_rules: Sequence[str]
) -> list[Path]:
    """Return sorted changed files that cause every question to be tested."""
    ignored_files = e2e_diff_ignored_files(changed_files, ignore_rules)
    return sorted(
        (
            path
            for path in changed_files
            if QUESTIONS_ROOT not in path.parents and path not in ignored_files
        ),
        key=lambda path: path.as_posix(),
    )


def log_full_question_run(
    changed_files: Sequence[Path], ignored_patterns: Sequence[str]
) -> None:
    """Log the changed files responsible for testing every question."""
    outside_files = nonignored_files_outside_questions(changed_files, ignored_patterns)
    print("Non-ignored changed files outside questions; testing every question:")
    for path in outside_files:
        print(f"  - {shlex.quote(path.as_posix())}")


def question_paths_from_changed_files(
    changed_files: Sequence[Path],
    repository_root: Path,
    ignore_rules: Sequence[str] = (),
) -> list[Path]:
    """Select changed questions, or all questions after a shared-file change."""
    ignored_files = e2e_diff_ignored_files(changed_files, ignore_rules)
    changed_files = [path for path in changed_files if path not in ignored_files]
    if any(QUESTIONS_ROOT not in path.parents for path in changed_files):
        return [QUESTIONS_ROOT]

    question_paths: set[Path] = set()
    for changed_file in changed_files:
        candidate = changed_file.parent
        while candidate != QUESTIONS_ROOT and QUESTIONS_ROOT in candidate.parents:
            if (repository_root / candidate / "info.json").is_file():
                question_paths.add(candidate)
                break
            candidate = candidate.parent

    return sorted(question_paths, key=lambda path: path.as_posix())


def changed_files_between(base: str, head: str) -> list[Path]:
    """Return files changed between two Git refs."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "-z",
            "--no-renames",
            "--diff-filter=ACDMRT",
            base,
            head,
            "--",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [Path(os.fsdecode(path)) for path in result.stdout.split(b"\0") if path]


def changed_question_paths(
    base: str, head: str, ignored_patterns: Sequence[str] = ()
) -> list[Path]:
    changed_files = changed_files_between(base, head)
    return question_paths_from_changed_files(
        changed_files, REPOSITORY_ROOT, ignored_patterns
    )


def positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    if parsed > 2**32:
        raise argparse.ArgumentTypeError("must not exceed 2**32")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="main", help="base Git ref (default: main)")
    parser.add_argument("--head", default="HEAD", help="head Git ref (default: HEAD)")
    parser.add_argument("--seed-count", type=positive_integer, default=10)
    parser.add_argument(
        "--fuzz-seed",
        type=int,
        help="master seed for reproducible pseudo-random variant seeds",
    )
    parser.add_argument("--prairielearn-path", type=Path, required=True)
    parser.add_argument(
        "--e2ediffignore",
        type=Path,
        default=DEFAULT_E2E_DIFF_IGNORE_PATH,
        help="path to the E2E change-detection ignore file",
    )
    args, pytest_args = parser.parse_known_args(argv)

    try:
        ignored_patterns = load_e2e_diff_ignore(args.e2ediffignore)
    except ValueError as exc:
        parser.error(str(exc))

    changed_files = changed_files_between(args.base, args.head)
    question_paths = question_paths_from_changed_files(
        changed_files, REPOSITORY_ROOT, ignored_patterns
    )
    if not question_paths:
        print("No non-ignored changed questions; skipping end-to-end fuzz tests.")
        return 0
    if question_paths == [QUESTIONS_ROOT]:
        log_full_question_run(changed_files, ignored_patterns)

    fuzz_seed = args.fuzz_seed
    if fuzz_seed is None:
        fuzz_seed = secrets.randbits(64)
    seeds = variant_seeds({}, args.seed_count, fuzz_seed)
    print(f"E2E fuzz seed: {fuzz_seed}")
    print(f"Variant seeds: {', '.join(str(seed) for seed in seeds)}")
    print(f"Replay with: E2E_FUZZ_SEED={fuzz_seed} make test-e2e-fuzz", flush=True)

    command = [
        sys.executable,
        "-m",
        "pytest",
        "e2e-tests/test_questions.py",
        "--prairielearn-path",
        os.fspath(args.prairielearn_path),
        "--seed-count",
        str(args.seed_count),
        "--fuzz-seed",
        str(fuzz_seed),
    ]
    for question_path in question_paths:
        print(
            f"Testing {shlex.quote(os.fspath(question_path))} "
            f"with {args.seed_count} fuzz seeds.",
            flush=True,
        )
        command.extend(("--question-path", os.fspath(question_path)))

    command.extend(pytest_args)
    return subprocess.call(command, cwd=REPOSITORY_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
