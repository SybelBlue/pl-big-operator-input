from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
import tomllib
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import distribution
from pathlib import Path
from typing import Any, cast

from prairielearn.internal import question_phases
from prairielearn.internal.question_phases import ElementInfo, RenderContext

from .contract import Phase, snapshot, validate_mutations, validate_serializable
from .errors import HarnessError
from .metadata import load_json


def installed_prairielearn_commit(course_root: Path) -> str:
    """Return the exact PrairieLearn Git revision used by this environment."""

    direct_url = distribution("prairielearn").read_text("direct_url.json")
    if direct_url:
        parsed = json.loads(direct_url)
        commit = parsed.get("vcs_info", {}).get("commit_id")
        if isinstance(commit, str) and commit:
            return commit

    lock = tomllib.loads((course_root / "uv.lock").read_text(encoding="utf-8"))
    for package in lock.get("package", []):
        if package.get("name") != "prairielearn":
            continue
        git = package.get("source", {}).get("git")
        if isinstance(git, str) and "#" in git:
            return git.rsplit("#", 1)[1]
    raise HarnessError("Could not determine the installed PrairieLearn Git revision")


def _run_git(
    clone: Path, *args: str, stdout: int | None = None
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", str(clone), *args],
            check=True,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            detail = f": {exc.stderr.decode(errors='replace').strip()}"
        raise HarnessError(
            f"Unable to read PrairieLearn clone {clone}{detail}"
        ) from exc


def _load_elements(root: Path, element_type: str) -> dict[str, ElementInfo]:
    result: dict[str, ElementInfo] = {}
    if not root.is_dir():
        return result
    for directory in sorted(root.iterdir()):
        info_path = directory / "info.json"
        if not directory.is_dir() or not info_path.is_file():
            continue
        raw = load_json(info_path)
        if not isinstance(raw, dict) or not isinstance(raw.get("controller"), str):
            raise HarnessError(f"{info_path}: element info must declare a controller")
        info = cast(
            ElementInfo,
            {
                "name": directory.name,
                "controller": raw["controller"],
                "type": element_type,
            },
        )
        result[directory.name] = info
        if element_type == "core":
            result[directory.name.replace("-", "_")] = info
            for alias in raw.get("additionalNames", []):
                if not isinstance(alias, str):
                    raise HarnessError(
                        f"{info_path}: additionalNames must contain strings"
                    )
                result[alias] = info
                result[alias.replace("-", "_")] = info
    return result


def _load_extensions(course_root: Path) -> dict[str, dict[str, dict[Any, Any]]]:
    result: dict[str, dict[str, dict[Any, Any]]] = {}
    root = course_root / "elementExtensions"
    if not root.is_dir():
        return result
    for info_path in sorted(root.glob("*/*/info.json")):
        raw = load_json(info_path)
        if not isinstance(raw, dict) or not isinstance(raw.get("controller"), str):
            raise HarnessError(f"{info_path}: extension info must declare a controller")
        element_name = info_path.parent.parent.name
        extension_name = info_path.parent.name
        result.setdefault(element_name, {})[extension_name] = {
            "name": extension_name,
            "directory": str(info_path.parent),
            **raw,
        }
    return result


class PrairieLearnBackend:
    """Real PrairieLearn Python element phases backed by a pinned clone archive."""

    def __init__(
        self,
        *,
        course_root: Path,
        core_elements_path: Path,
        commit: str,
    ) -> None:
        self.course_root = course_root.resolve()
        self.core_elements_path = core_elements_path.resolve()
        self.commit = commit
        core = _load_elements(self.core_elements_path, "core")
        course = _load_elements(self.course_root / "elements", "course")
        self.elements = {**core, **course}
        self.element_extensions = _load_extensions(self.course_root)
        question_phases.CORE_ELEMENTS_PATH = self.core_elements_path

    @classmethod
    def from_clone(
        cls,
        clone_path: str | Path,
        course_root: str | Path,
        materialize_root: str | Path,
    ) -> PrairieLearnBackend:
        clone = Path(clone_path).resolve()
        root = Path(course_root).resolve()
        destination = Path(materialize_root).resolve()
        if not (clone / ".git").exists():
            raise HarnessError(f"{clone}: --prairielearn-path must name a Git clone")

        commit = installed_prairielearn_commit(root)
        _run_git(clone, "cat-file", "-e", f"{commit}^{{commit}}")
        destination.mkdir(parents=True, exist_ok=True)
        archive = _run_git(
            clone,
            "archive",
            "--format=tar",
            f"{commit}:apps/prairielearn",
            "elements",
            stdout=subprocess.PIPE,
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
            tar.extractall(destination, filter="data")
        elements = destination / "elements"
        if not elements.is_dir():
            raise HarnessError(
                f"PrairieLearn revision {commit} contains no core elements"
            )
        return cls(course_root=root, core_elements_path=elements, commit=commit)

    def context(self, html: str) -> RenderContext:
        return {
            "html": html,
            "elements": self.elements,
            "element_extensions": self.element_extensions,
            "course_path": str(self.course_root),
        }

    def process(
        self, phase: Phase, html: str, data: dict[str, Any]
    ) -> tuple[str | None, set[str]]:
        before = snapshot(data, phase)
        old_cwd = Path.cwd()
        old_path = sys.path.copy()
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result, processed = question_phases.process(
                    phase, data, self.context(html)
                )
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
        output = stdout.getvalue() + stderr.getvalue()
        if output:
            raise HarnessError(
                f"{phase}: PrairieLearn element emitted unexpected console output: {output!r}"
            )
        validate_mutations(before, data, phase)
        validate_serializable(data, phase)
        return result, processed

    def unresolved_elements(self, html: str) -> set[str]:
        from lxml import html as lxml_html

        fragments = lxml_html.fragments_fromstring(html)
        registered = set(self.elements)
        return {
            node.tag
            for fragment in fragments
            if not isinstance(fragment, str)
            for node in fragment.iter()
            if isinstance(node.tag, str) and node.tag in registered
        }
