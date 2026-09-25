from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "scripts" / "run_e2e_fuzz_tests.sh"
SCRIPT_ENVIRONMENT_VARIABLES = {
    "CI_DEFAULT_BRANCH",
    "E2E_DIFF_BASE",
    "E2E_DIFF_HEAD",
    "E2E_FUZZ_SEED",
    "GH_TOKEN",
    "GITHUB_SHA",
    "MAKE_COMMAND",
    "PULL_REQUEST_BASE_SHA",
    "PYTEST_ARGS",
}


def run_e2e_fuzz_tests(tmp_path: Path, **environment: str) -> list[list[str]]:
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    command_log = tmp_path / "commands.log"

    git = bin_directory / "git"
    git.write_text(
        """#!/usr/bin/env bash
printf 'git' >> "$COMMAND_LOG"
printf '\\t%s' "$@" >> "$COMMAND_LOG"
printf '\\n' >> "$COMMAND_LOG"

case "$*" in
    "rev-parse --show-toplevel") printf '%s\\n' "$REPOSITORY_ROOT" ;;
    "merge-base "*) printf '%s\\n' "${FAKE_MERGE_BASE:-merge-base-sha}" ;;
esac
""",
        encoding="utf-8",
    )
    git.chmod(0o755)

    make = bin_directory / "make"
    make.write_text(
        """#!/usr/bin/env bash
printf 'make' >> "$COMMAND_LOG"
printf '\\t%s' "$@" >> "$COMMAND_LOG"
printf '\\n' >> "$COMMAND_LOG"
""",
        encoding="utf-8",
    )
    make.chmod(0o755)

    process_environment = {
        **{
            key: value
            for key, value in os.environ.items()
            if key not in SCRIPT_ENVIRONMENT_VARIABLES
        },
        "COMMAND_LOG": os.fspath(command_log),
        "PATH": f"{bin_directory}{os.pathsep}{os.environ['PATH']}",
        "REPOSITORY_ROOT": os.fspath(REPOSITORY_ROOT),
        **environment,
    }
    subprocess.run(["bash", os.fspath(SCRIPT)], check=True, env=process_environment)

    return [line.split("\t") for line in command_log.read_text().splitlines()]


def make_commands(commands: list[list[str]]) -> list[list[str]]:
    return [command for command in commands if command[0] == "make"]


def test_pull_request_runs_fuzz_tests_from_base(tmp_path: Path) -> None:
    commands = run_e2e_fuzz_tests(
        tmp_path,
        E2E_FUZZ_SEED="12345",
        GITHUB_SHA="pull-request-head",
        PULL_REQUEST_BASE_SHA="pull-request-base",
        GH_TOKEN="token",
    )

    assert make_commands(commands) == [
        [
            "make",
            "test-e2e-fuzz-diff-only",
            "E2E_DIFF_BASE=pull-request-base",
            "E2E_DIFF_HEAD=pull-request-head",
            "PYTEST_ARGS=",
            "E2E_FUZZ_SEED=12345",
        ]
    ]
    assert any(
        "fetch" in command and "pull-request-base" in command
        for command in commands
        if command[0] == "git"
    )


def test_local_run_uses_merge_base_with_default_branch(tmp_path: Path) -> None:
    commands = run_e2e_fuzz_tests(
        tmp_path,
        FAKE_MERGE_BASE="local-merge-base",
        PYTEST_ARGS="-q",
    )

    assert make_commands(commands) == [
        [
            "make",
            "test-e2e-fuzz-diff-only",
            "E2E_DIFF_BASE=local-merge-base",
            "E2E_DIFF_HEAD=HEAD",
            "PYTEST_ARGS=-q",
        ]
    ]
    assert ["git", "merge-base", "main", "HEAD"] in commands


def test_explicit_refs_are_resolved_to_their_merge_base(tmp_path: Path) -> None:
    commands = run_e2e_fuzz_tests(
        tmp_path,
        E2E_DIFF_BASE="origin/main",
        E2E_DIFF_HEAD="feature-head",
        FAKE_MERGE_BASE="explicit-merge-base",
    )

    assert make_commands(commands) == [
        [
            "make",
            "test-e2e-fuzz-diff-only",
            "E2E_DIFF_BASE=explicit-merge-base",
            "E2E_DIFF_HEAD=feature-head",
            "PYTEST_ARGS=",
        ]
    ]
    assert ["git", "merge-base", "origin/main", "feature-head"] in commands
