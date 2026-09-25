#!/usr/bin/env python3

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import NoReturn

SOURCE_BRANCH = "main"
TARGET_BRANCH = "release"
CONFIG_FILE = "release.toml"


class ReleaseError(Exception):
    pass


@dataclass(frozen=True)
class Include:
    source: str
    destination: str


@dataclass(frozen=True)
class ReleaseConfig:
    history_source: str
    includes: list[Include]


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    object_type: str
    object_id: str
    path: str


def fail(message: str) -> NoReturn:
    raise ReleaseError(message)


def run_git(
    repo_root: Path,
    *arguments: str,
    input_data: bytes | None = None,
    environment: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    command = ["git", *arguments]
    process_environment = os.environ.copy()
    if environment is not None:
        process_environment.update(environment)

    result = subprocess.run(
        command,
        cwd=repo_root,
        input=input_data,
        capture_output=True,
        env=process_environment,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).decode(errors="replace").strip()
        message = f"{shlex.join(command)} failed"
        if detail:
            message = f"{message}: {detail}"
        fail(message)
    return result


def git_output(repo_root: Path, *arguments: str) -> str:
    return run_git(repo_root, *arguments).stdout.decode().strip()


def find_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail("Run this command from inside a Git repository.")
    return Path(result.stdout.decode().strip())


def validate_path(value: object, *, field: str, allow_dot: bool) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    if "\n" in value or "\r" in value:
        fail(f"{field} cannot contain a newline")

    path = PurePosixPath(value)
    if path.is_absolute():
        fail(f"{field} must be relative: {value!r}")
    if value == ".":
        if allow_dot:
            return value
        fail(f"{field} cannot be the repository root")
    if value != path.as_posix() or ".." in path.parts:
        fail(f"{field} must be a normalized path without '..': {value!r}")
    return value


def load_config(repo_root: Path) -> ReleaseConfig:
    config_object = f"{SOURCE_BRANCH}:{CONFIG_FILE}"
    result = run_git(repo_root, "show", config_object, check=False)
    if result.returncode != 0:
        fail(f"{SOURCE_BRANCH} does not contain {CONFIG_FILE}")

    try:
        config = tomllib.loads(result.stdout.decode())
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        fail(f"Invalid {CONFIG_FILE}: {error}")

    unexpected_keys = set(config) - {"version", "history_source", "include"}
    if unexpected_keys:
        fail(f"Unexpected keys in {CONFIG_FILE}: {', '.join(sorted(unexpected_keys))}")
    if type(config.get("version")) is not int or config["version"] != 1:
        fail(f"{CONFIG_FILE}: version must be 1")

    history_source = validate_path(
        config.get("history_source"), field="history_source", allow_dot=False
    )
    raw_includes = config.get("include")
    if not isinstance(raw_includes, list) or not raw_includes:
        fail(f"{CONFIG_FILE}: include must contain at least one mapping")

    includes: list[Include] = []
    for index, raw_include in enumerate(raw_includes, start=1):
        if not isinstance(raw_include, dict):
            fail(f"{CONFIG_FILE}: include entry {index} must be a table")
        if set(raw_include) != {"source", "destination"}:
            fail(
                f"{CONFIG_FILE}: include entry {index} must contain exactly "
                "source and destination"
            )
        includes.append(
            Include(
                source=validate_path(
                    raw_include["source"],
                    field=f"include entry {index} source",
                    allow_dot=False,
                ),
                destination=validate_path(
                    raw_include["destination"],
                    field=f"include entry {index} destination",
                    allow_dot=True,
                ),
            )
        )

    return ReleaseConfig(history_source=history_source, includes=includes)


def parse_tree_entries(data: bytes) -> list[TreeEntry]:
    entries: list[TreeEntry] = []
    for record in data.rstrip(b"\0").split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", maxsplit=1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        entries.append(
            TreeEntry(
                mode=mode,
                object_type=object_type,
                object_id=object_id,
                path=os.fsdecode(raw_path),
            )
        )
    return entries


def object_type(repo_root: Path, object_name: str) -> str | None:
    result = run_git(repo_root, "cat-file", "-t", object_name, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.decode().strip()


def ensure_destination_available(
    destinations: dict[str, str], destination: str, source: str
) -> None:
    for existing_destination, existing_source in destinations.items():
        if (
            destination == existing_destination
            or destination.startswith(f"{existing_destination}/")
            or existing_destination.startswith(f"{destination}/")
        ):
            fail(
                f"Release destination {destination!r} from {source!r} conflicts "
                f"with {existing_destination!r} from {existing_source!r}"
            )
    destinations[destination] = source


def build_release_tree(
    repo_root: Path, config: ReleaseConfig, target_index: Path
) -> tuple[str, int]:
    index_environment = {"GIT_INDEX_FILE": str(target_index)}
    run_git(repo_root, "read-tree", "--empty", environment=index_environment)

    destinations: dict[str, str] = {}
    included_file_count = 0

    for include in config.includes:
        source_object = f"{SOURCE_BRANCH}:{include.source}"
        source_type = object_type(repo_root, source_object)
        if source_type is None:
            fail(
                f"{SOURCE_BRANCH} does not contain configured release source "
                f"{include.source}"
            )

        if source_type == "blob":
            if include.destination == ".":
                fail(f"File source {include.source} must map to a file path, not '.'")
            tree_data = run_git(
                repo_root,
                "ls-tree",
                "-z",
                SOURCE_BRANCH,
                "--",
                f":(literal){include.source}",
            ).stdout
            entries = parse_tree_entries(tree_data)
            if len(entries) != 1:
                fail(f"Could not resolve release source {include.source}")
            source_entries = [(entries[0], include.destination, include.source)]
        elif source_type == "tree":
            tree_data = run_git(repo_root, "ls-tree", "-r", "-z", source_object).stdout
            source_entries = []
            for entry in parse_tree_entries(tree_data):
                destination = (
                    entry.path
                    if include.destination == "."
                    else f"{include.destination}/{entry.path}"
                )
                source_entries.append(
                    (entry, destination, f"{include.source}/{entry.path}")
                )
        else:
            fail(
                f"Configured release source {include.source} has unsupported "
                f"Git type {source_type}"
            )

        for entry, destination, source in source_entries:
            ensure_destination_available(destinations, destination, source)
            run_git(
                repo_root,
                "update-index",
                "--add",
                "--cacheinfo",
                f"{entry.mode},{entry.object_id},{destination}",
                environment=index_environment,
            )
            included_file_count += 1

    if included_file_count == 0:
        fail(f"{CONFIG_FILE} did not include any files")

    target_tree = git_output_with_environment(
        repo_root, index_environment, "write-tree"
    )
    return target_tree, included_file_count


def git_output_with_environment(
    repo_root: Path, environment: dict[str, str], *arguments: str
) -> str:
    return (
        run_git(repo_root, *arguments, environment=environment).stdout.decode().strip()
    )


def optional_revision(repo_root: Path, revision: str) -> str | None:
    result = run_git(
        repo_root, "rev-parse", "--verify", "--quiet", revision, check=False
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode().strip()


def source_commit_environment(repo_root: Path) -> dict[str, str]:
    format_string = "%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI"
    raw_metadata = run_git(
        repo_root, "show", "-s", f"--format={format_string}", SOURCE_BRANCH
    ).stdout.decode()
    fields = raw_metadata.rstrip("\n").split("\0")
    if len(fields) != 6:
        fail(f"Could not read commit metadata from {SOURCE_BRANCH}")
    (
        author_name,
        author_email,
        author_date,
        committer_name,
        committer_email,
        committer_date,
    ) = fields
    return {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_AUTHOR_DATE": author_date,
        "GIT_COMMITTER_NAME": committer_name,
        "GIT_COMMITTER_EMAIL": committer_email,
        "GIT_COMMITTER_DATE": committer_date,
    }


def release_branch_is_checked_out(repo_root: Path) -> bool:
    worktrees = git_output(repo_root, "worktree", "list", "--porcelain")
    return f"branch refs/heads/{TARGET_BRANCH}" in worktrees.splitlines()


def update_release(*, push: bool) -> None:
    repo_root = find_repo_root()
    if optional_revision(repo_root, f"{SOURCE_BRANCH}^{{commit}}") is None:
        fail(f"Branch {SOURCE_BRANCH} does not exist")

    config = load_config(repo_root)
    history_object = f"{SOURCE_BRANCH}:{config.history_source}"
    if object_type(repo_root, history_object) != "tree":
        fail(
            f"history_source must name a directory in {SOURCE_BRANCH}: "
            f"{config.history_source}"
        )
    if release_branch_is_checked_out(repo_root):
        fail(
            f"Branch {TARGET_BRANCH} is checked out in a worktree; switch that "
            "worktree to another branch first"
        )

    old_local_target = optional_revision(repo_root, f"refs/heads/{TARGET_BRANCH}")
    old_target = old_local_target or optional_revision(
        repo_root, f"refs/remotes/origin/{TARGET_BRANCH}"
    )
    split_commit = git_output(
        repo_root,
        "subtree",
        "split",
        f"--prefix={config.history_source}",
        SOURCE_BRANCH,
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        target_index = Path(temporary_directory) / "target-index"
        target_tree, included_file_count = build_release_tree(
            repo_root, config, target_index
        )

    if (
        old_target is not None
        and git_output(repo_root, "rev-parse", f"{old_target}^{{tree}}") == target_tree
    ):
        generated_commit = old_target
    else:
        generated_commit = (
            run_git(
                repo_root,
                "commit-tree",
                target_tree,
                "-p",
                split_commit,
                input_data=f"Prepare {TARGET_BRANCH} release tree\n".encode(),
                environment=source_commit_environment(repo_root),
            )
            .stdout.decode()
            .strip()
        )

    target_ref = f"refs/heads/{TARGET_BRANCH}"
    update_ref_arguments = ["update-ref", target_ref, generated_commit]
    if old_local_target is not None:
        update_ref_arguments.append(old_local_target)
    run_git(repo_root, *update_ref_arguments)

    actual_target_tree = git_output(repo_root, "rev-parse", f"{TARGET_BRANCH}^{{tree}}")
    if actual_target_tree != target_tree:
        fail(f"Generated tree does not match {TARGET_BRANCH}")

    print(
        f"Updated {TARGET_BRANCH} to {generated_commit} from {SOURCE_BRANCH} "
        f"using {CONFIG_FILE} ({included_file_count} files)."
    )

    if push:
        result = run_git(
            repo_root,
            "push",
            "--force-with-lease",
            "origin",
            f"{TARGET_BRANCH}:{TARGET_BRANCH}",
        )
        if result.stdout:
            print(result.stdout.decode().rstrip())
        if result.stderr:
            print(result.stderr.decode().rstrip(), file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            f"Rebuild {TARGET_BRANCH} from {SOURCE_BRANCH} according to {CONFIG_FILE}."
        )
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="force-push the rebuilt branch to origin using --force-with-lease",
    )
    arguments = parser.parse_args()

    try:
        update_release(push=arguments.push)
    except ReleaseError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
