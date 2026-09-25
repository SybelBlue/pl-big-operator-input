from __future__ import annotations

import inspect
import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from prairielearn.internal.zygote_utils import get_module_function

from .contract import Phase, snapshot, validate_mutations, validate_serializable
from .errors import HarnessError

HOOKS: tuple[Phase, ...] = (
    "generate",
    "prepare",
    "render",
    "parse",
    "grade",
    "test",
    "file",
)


class ServerModule:
    def __init__(self, path: Path, course_root: Path) -> None:
        self.path = path
        self.course_root = course_root
        self.namespace: dict[str, Any] = {}
        if path.is_file():
            self.namespace = self._execute()
        self._validate_signatures()

    def _environment(self) -> tuple[Path, list[str]]:
        old_cwd = Path.cwd()
        old_path = sys.path.copy()
        os.chdir(self.path.parent)
        sys.path.insert(0, str(self.course_root / "serverFilesCourse"))
        sys.path.insert(0, str(self.path.parent))
        return old_cwd, old_path

    @staticmethod
    def _restore(old_cwd: Path, old_path: list[str]) -> None:
        os.chdir(old_cwd)
        sys.path[:] = old_path

    def _execute(self) -> dict[str, Any]:
        namespace: dict[str, Any] = {"__file__": str(self.path)}
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_cwd, old_path = self._environment()
        try:
            source = self.path.read_text(encoding="utf-8")
            code = compile(source, self.path, "exec")
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(code, namespace)  # noqa: S102 -- server.py is the code under test.
        finally:
            self._restore(old_cwd, old_path)
        output = stdout.getvalue() + stderr.getvalue()
        if output:
            raise HarnessError(
                f"{self.path}: import emitted unexpected console output: {output!r}"
            )
        return namespace

    def _validate_signatures(self) -> None:
        for phase in HOOKS:
            declared = self.namespace.get(phase)
            if declared is None:
                continue
            if not callable(declared):
                raise HarnessError(f"{self.path}: {phase} must be callable")
            function = get_module_function(self.namespace, phase)
            if function is None:
                continue
            expected = 2 if phase == "render" else 1
            try:
                inspect.signature(function).bind(*([object()] * expected))
            except TypeError as exc:
                arguments = "data, html" if phase == "render" else "data"
                raise HarnessError(
                    f"{self.path}: {phase} must accept ({arguments}): {exc}"
                ) from exc

    def has_hook(self, phase: Phase) -> bool:
        return get_module_function(self.namespace, phase) is not None

    def invoke(
        self,
        phase: Phase,
        data: dict[str, Any],
        html: str | None = None,
    ) -> Any:
        function = get_module_function(self.namespace, phase)
        if function is None:
            return html if phase == "render" else None
        before = snapshot(data, phase)
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_cwd, old_path = self._environment()
        try:
            args = (data, html) if phase == "render" else (data,)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = function(*args)
        finally:
            self._restore(old_cwd, old_path)
        output = stdout.getvalue() + stderr.getvalue()
        if output:
            raise HarnessError(
                f"{self.path}: {phase} emitted unexpected console output: {output!r}"
            )
        if phase == "render":
            if not isinstance(result, str):
                raise HarnessError(f"{self.path}: render must return HTML text")
        elif phase == "file":
            if result is not None and not isinstance(
                result, (str, bytes, bytearray, memoryview, io.IOBase)
            ):
                raise HarnessError(f"{self.path}: file returned an unsupported value")
        elif result is not None and result is not data:
            raise HarnessError(
                f"{self.path}: {phase} must mutate data in place and return None"
            )
        validate_mutations(before, data, phase)
        validate_serializable(data, phase)
        return result
