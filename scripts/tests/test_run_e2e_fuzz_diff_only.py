from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scripts import run_e2e_fuzz_diff_only


def test_seed_count_validation() -> None:
    assert run_e2e_fuzz_diff_only.positive_integer("1") == 1
    with pytest.raises(argparse.ArgumentTypeError, match="at least 1"):
        run_e2e_fuzz_diff_only.positive_integer("0")
    with pytest.raises(argparse.ArgumentTypeError, match="must not exceed"):
        run_e2e_fuzz_diff_only.positive_integer(str(2**32 + 1))


def test_finds_changed_question_directories(tmp_path: Path) -> None:
    first = tmp_path / "questions" / "chapter" / "first"
    first.mkdir(parents=True)
    (first / "info.json").write_text("{}", encoding="utf-8")
    spaced = tmp_path / "questions" / "chapter" / "with space "
    spaced.mkdir()
    (spaced / "info.json").write_text("{}", encoding="utf-8")

    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [
            Path("questions/chapter/first/server.py"),
            Path("questions/chapter/first/assets/image.svg"),
            Path("questions/chapter/removed/question.html"),
            Path("questions/chapter/with space /question.html"),
        ],
        tmp_path,
    )

    assert question_paths == [
        Path("questions/chapter/first"),
        Path("questions/chapter/with space "),
    ]


def test_selects_all_questions_for_shared_file_change(tmp_path: Path) -> None:
    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [Path("questions/chapter/first/server.py"), Path("serverFilesCourse/utils.py")],
        tmp_path,
    )

    assert question_paths == [Path("questions")]


def test_ignored_files_do_not_expand_question_selection(tmp_path: Path) -> None:
    question = tmp_path / "questions" / "chapter" / "first"
    question.mkdir(parents=True)
    (question / "info.json").write_text("{}", encoding="utf-8")

    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [Path("README.md"), Path("questions/chapter/first/server.py")],
        tmp_path,
        ["README.md"],
    )

    assert question_paths == [Path("questions/chapter/first")]


def test_glob_ignored_files_can_skip_question_tests(tmp_path: Path) -> None:
    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [
            Path(".github/workflows/ci.yml"),
            Path("nested/.github/actions/setup/action.yml"),
        ],
        tmp_path,
        [".github"],
    )

    assert question_paths == []


def test_gitignore_prefix_ignores_directory_descendants(tmp_path: Path) -> None:
    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [
            Path(".agents/SKILL.md"),
            Path(".agents/skills/nested/SKILL.md"),
            Path("somewhere/.agents/config.json"),
        ],
        tmp_path,
        [".agents"],
    )

    assert question_paths == []


def test_nonignored_shared_file_still_selects_all_questions(tmp_path: Path) -> None:
    question_paths = run_e2e_fuzz_diff_only.question_paths_from_changed_files(
        [Path("README.md"), Path("serverFilesCourse/utils.py")],
        tmp_path,
        ["README.md"],
    )

    assert question_paths == [Path("questions")]


def test_lists_nonignored_files_outside_questions() -> None:
    outside_files = run_e2e_fuzz_diff_only.nonignored_files_outside_questions(
        [
            Path("serverFilesCourse/utils.py"),
            Path("README.md"),
            Path("questions/chapter/first/server.py"),
            Path("elements/an element/controller.py"),
        ],
        ["README.md"],
    )

    assert outside_files == [
        Path("elements/an element/controller.py"),
        Path("serverFilesCourse/utils.py"),
    ]


def test_logs_nonignored_files_outside_questions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_e2e_fuzz_diff_only.log_full_question_run(
        [
            Path("serverFilesCourse/utils.py"),
            Path("README.md"),
            Path("elements/an element/controller.py"),
        ],
        ["README.md"],
    )

    assert capsys.readouterr().out.splitlines() == [
        "Non-ignored changed files outside questions; testing every question:",
        "  - 'elements/an element/controller.py'",
        "  - serverFilesCourse/utils.py",
    ]


def test_load_e2e_diff_ignore(tmp_path: Path) -> None:
    config_path = tmp_path / ".question-e2e.diffignore"
    config_path.write_text(
        "# Documentation and CI files\n\nREADME.md\n.github/**\n", encoding="utf-8"
    )

    assert run_e2e_fuzz_diff_only.load_e2e_diff_ignore(config_path) == [
        "# Documentation and CI files",
        "",
        "README.md",
        ".github/**",
    ]


def test_root_anchored_gitignore_pattern(tmp_path: Path) -> None:
    ignored_files = run_e2e_fuzz_diff_only.e2e_diff_ignored_files(
        [Path("README.md"), Path("docs/README.md")], ["/README.md"]
    )

    assert ignored_files == {Path("README.md")}


def test_explicit_fuzz_seed_is_reported_and_forwarded(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only,
        "changed_files_between",
        lambda base, head: [Path("questions/chapter/example/server.py")],
    )
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only,
        "question_paths_from_changed_files",
        lambda changed_files, repository_root, ignored_patterns: [
            Path("questions/chapter/example")
        ],
    )
    commands: list[list[str]] = []

    def fake_call(command: list[str], cwd: Path) -> int:
        commands.append(command)
        return 0

    monkeypatch.setattr(run_e2e_fuzz_diff_only.subprocess, "call", fake_call)

    result = run_e2e_fuzz_diff_only.main(
        [
            "--prairielearn-path",
            "/tmp/prairielearn",
            "--seed-count",
            "3",
            "--fuzz-seed",
            "12345",
            "-q",
        ]
    )

    expected_seeds = run_e2e_fuzz_diff_only.variant_seeds({}, 3, 12345)
    output = capsys.readouterr().out
    assert result == 0
    assert "E2E fuzz seed: 12345" in output
    assert f"Variant seeds: {', '.join(map(str, expected_seeds))}" in output
    assert "E2E_FUZZ_SEED=12345 make test-e2e-fuzz" in output
    assert len(commands) == 1
    command = commands[0]
    assert command[command.index("--fuzz-seed") + 1] == "12345"
    assert command[command.index("--seed-count") + 1] == "3"
    assert command[command.index("--question-path") + 1] == (
        "questions/chapter/example"
    )
    assert command[-1] == "-q"


def test_missing_fuzz_seed_generates_unsigned_64_bit_seed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only,
        "changed_files_between",
        lambda base, head: [Path("questions/chapter/example/server.py")],
    )
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only,
        "question_paths_from_changed_files",
        lambda changed_files, repository_root, ignored_patterns: [
            Path("questions/chapter/example")
        ],
    )
    requested_bits: list[int] = []

    def fake_randbits(bits: int) -> int:
        requested_bits.append(bits)
        return 98765

    monkeypatch.setattr(run_e2e_fuzz_diff_only.secrets, "randbits", fake_randbits)
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only.subprocess, "call", lambda command, cwd: 0
    )

    result = run_e2e_fuzz_diff_only.main(
        ["--prairielearn-path", "/tmp/prairielearn", "--seed-count", "2"]
    )

    assert result == 0
    assert requested_bits == [64]
    assert "E2E fuzz seed: 98765" in capsys.readouterr().out


def test_empty_diff_does_not_generate_fuzz_seed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only, "changed_files_between", lambda base, head: []
    )
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only,
        "question_paths_from_changed_files",
        lambda changed_files, repository_root, ignored_patterns: [],
    )
    monkeypatch.setattr(
        run_e2e_fuzz_diff_only.secrets,
        "randbits",
        lambda bits: pytest.fail("empty diff must not generate a fuzz seed"),
    )

    result = run_e2e_fuzz_diff_only.main(["--prairielearn-path", "/tmp/prairielearn"])

    assert result == 0
    assert capsys.readouterr().out == (
        "No non-ignored changed questions; skipping end-to-end fuzz tests.\n"
    )
