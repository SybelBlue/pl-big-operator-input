from __future__ import annotations

import copy
import io
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import chevron
import lxml.html
import numpy as np

from .backend import PrairieLearnBackend
from .contract import PHASE_FIELDS, Phase
from .discovery import QuestionCase
from .errors import HarnessError, UnsupportedQuestion
from .html_checks import non_gradable_answer_names, validate_declared_answers
from .metadata import default_preferences, validate_question_metadata
from .server import ServerModule


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    seed: int
    answer_names: tuple[str, ...]
    raw_submitted_answers: dict[str, Any]
    submitted_answers: dict[str, Any]
    partial_scores: dict[str, Any]
    score: float
    question_html: str
    answer_html: str | None
    submission_html: str


type LifecycleCheck = Literal["generate", "prepare", "render", "grade"]


def _aggregate_score(data: dict[str, Any], partial_credit: bool) -> None:
    parts = data["partial_scores"]
    if partial_credit:
        total_weight = 0.0
        weighted_score = 0.0
        for name, value in parts.items():
            if not isinstance(value, dict):
                raise HarnessError(f"partial_scores[{name!r}] must be an object")
            score = value.get("score")
            weight = value.get("weight", 1)
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise HarnessError(f"partial_scores[{name!r}].score must be numeric")
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise HarnessError(f"partial_scores[{name!r}].weight must be numeric")
            total_weight += float(weight)
            weighted_score += float(weight) * float(score)
        data["score"] = weighted_score / (total_weight or 1)
    else:
        data["score"] = float(
            bool(parts)
            and all(
                isinstance(part, dict)
                and isinstance(part.get("score"), (int, float))
                and not isinstance(part.get("score"), bool)
                and float(part["score"]) >= 1
                for part in parts.values()
            )
        )


def _assert_full_credit(data: dict[str, Any], answer_names: tuple[str, ...]) -> None:
    if data["format_errors"]:
        raise HarnessError(
            f"correct submission has format errors: {data['format_errors']!r}"
        )
    if not data["gradable"]:
        raise HarnessError("correct submission was marked ungradable")
    if float(data["score"]) != 1:
        raise HarnessError(
            f"correct submission received score {data['score']!r}, expected 1"
        )
    unparsed = [
        name
        for name in answer_names
        if name not in data["submitted_answers"]
        or data["submitted_answers"][name] is None
    ]
    if unparsed:
        raise HarnessError(
            "declared answers did not parse successfully: " + ", ".join(unparsed)
        )
    missing = [name for name in answer_names if name not in data["partial_scores"]]
    if missing:
        raise HarnessError(
            "declared answers have no partial score: " + ", ".join(missing)
        )
    not_full = [
        name
        for name in answer_names
        if not isinstance(data["partial_scores"][name], dict)
        or data["partial_scores"][name].get("score") != 1
    ]
    if not_full:
        raise HarnessError(
            "declared answers did not receive full credit: " + ", ".join(not_full)
        )


class QuestionHarness:
    def __init__(
        self,
        question: QuestionCase | str | Path,
        backend: PrairieLearnBackend,
        *,
        course_root: str | Path | None = None,
    ) -> None:
        if isinstance(question, QuestionCase):
            self.question = question
        else:
            root = Path(course_root or backend.course_root).resolve()
            directory = Path(question)
            if not directory.is_absolute():
                directory = root / directory
            if directory.name == "info.json":
                directory = directory.parent
            self.question = QuestionCase(directory.resolve(), root)
        self.backend = backend

    def _options(self) -> dict[str, Any]:
        directory = self.question.directory
        root = self.question.course_root
        return {
            "question_path": str(directory),
            "client_files_question_path": str(directory / "clientFilesQuestion"),
            "client_files_course_path": str(root / "clientFilesCourse"),
            "server_files_course_path": str(root / "serverFilesCourse"),
            "course_extensions_path": str(root / "elementExtensions"),
            "client_files_question_url": "/clientFilesQuestion",
            "client_files_course_url": "/clientFilesCourse",
            "client_files_question_dynamic_url": "/generatedFilesQuestion",
            "course_element_files_url": "/courseElements",
            "course_element_extension_files_url": "/courseElementExtensions",
            "submission_files_url": "/submissionFiles",
            "variant_id": 1,
            "external_image_capture_url": "/externalImageCapture",
            "base_url": "/pl",
            "workspace_url": None,
            "user": None,
            "group": None,
        }

    def _base(self, seed: int, preferences: dict[str, Any]) -> dict[str, Any]:
        return {
            "params": {},
            "correct_answers": {},
            "variant_seed": seed,
            "options": self._options(),
            "preferences": preferences,
        }

    @staticmethod
    def _phase_data(
        phase: Phase,
        base: dict[str, Any],
        **overrides: Any,
    ) -> dict[str, Any]:
        fields = PHASE_FIELDS[phase]
        defaults: dict[str, Any] = {
            "answers_names": {},
            "submitted_answers": {},
            "format_errors": {},
            "raw_submitted_answers": {},
            "partial_scores": {},
            "score": 0.0,
            "feedback": {},
            "gradable": True,
            "editable": True,
            "manual_grading": False,
            "ai_grading": False,
            "panel": "question",
            "correct_answer_shown": False,
            "num_valid_submissions": 0,
            "test_type": "correct",
            "filename": "__prairielearn_e2e_sentinel__",
        }
        result: dict[str, Any] = {}
        for name in fields:
            if name in overrides:
                value = overrides[name]
            elif name in base:
                value = base[name]
            else:
                value = defaults[name]
            result[name] = copy.deepcopy(value)
        return result

    @staticmethod
    def _template(source: str, data: dict[str, Any]) -> str:
        try:
            return chevron.render(source, data)
        except Exception as exc:
            raise HarnessError(
                f"question.html Mustache rendering failed: {exc}"
            ) from exc

    def _process(
        self,
        phase: Phase,
        source: str,
        data: dict[str, Any],
        server: ServerModule,
    ) -> tuple[str | None, set[str]]:
        html = self._template(source, data)
        result, processed = self.backend.process(phase, html, data)
        if phase == "render":
            assert isinstance(result, str)
            result = server.invoke("render", data, result)
        elif phase == "file":
            server_result = server.invoke("file", data)
            if self._file_has_content(result) and self._file_has_content(server_result):
                raise HarnessError(
                    "file: server.py attempted to overwrite nonempty element file data"
                )
        else:
            server.invoke(phase, data)
        return result, processed

    @staticmethod
    def _file_has_content(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (str, bytes, bytearray, memoryview)):
            return bool(value)
        if isinstance(value, io.IOBase):
            position = value.tell()
            value.seek(0)
            content = value.read()
            value.seek(position)
            return bool(content)
        return True

    def _render(
        self,
        source: str,
        base: dict[str, Any],
        server: ServerModule,
        *,
        panel: str,
        show_correct: bool,
        submission: dict[str, Any] | None = None,
    ) -> str:
        state = self._phase_data(
            "render",
            base,
            **(submission or {}),
            panel=panel,
            correct_answer_shown=show_correct,
            editable=panel == "question",
            num_valid_submissions=1 if submission else 0,
        )
        rendered, _ = self._process("render", source, state, server)
        assert isinstance(rendered, str)
        unresolved = self.backend.unresolved_elements(rendered)
        if unresolved:
            raise HarnessError(
                f"{panel} panel contains unresolved registered elements: "
                + ", ".join(sorted(unresolved))
            )
        return rendered

    @staticmethod
    def _dynamic_filenames(html: str) -> tuple[str, ...]:
        fragments = lxml.html.fragments_fromstring(html)
        result: set[str] = set()
        for fragment in fragments:
            if isinstance(fragment, str):
                continue
            for element in fragment.xpath('//*[@type="dynamic"][@file-name]'):
                filename = element.get("file-name")
                if filename:
                    result.add(filename)
            for element in fragment.xpath("//*[@src] | //*[@href]"):
                value = element.get("src") or element.get("href") or ""
                marker = "/generatedFilesQuestion/"
                if marker in value:
                    result.add(value.split(marker, 1)[1].split("?", 1)[0])
        return tuple(sorted(result))

    def _run(self, seed: int, through: LifecycleCheck) -> LifecycleResult | None:
        metadata = validate_question_metadata(
            self.question.info_path, self.question.course_root
        )
        if metadata.get("type") != "v3":
            raise UnsupportedQuestion(
                f"{self.question.qid}: only v3 questions are supported"
            )
        question_html = self.question.directory / "question.html"
        if not question_html.is_file():
            raise HarnessError(f"{question_html}: v3 questions require question.html")
        source = question_html.read_text(encoding="utf-8")
        if re.search(r"<\s*markdown(?:\s|>)", source, flags=re.IGNORECASE):
            raise HarnessError(
                f"{question_html}: <markdown> needs PrairieLearn's TypeScript preprocessor"
            )

        python_state = random.getstate()
        numpy_state = np.random.get_state()
        try:
            random.seed(seed)
            np.random.seed(seed)
            server = ServerModule(
                self.question.directory / "server.py", self.question.course_root
            )
            preferences = default_preferences(metadata)
            base = self._base(seed, preferences)

            generate = self._phase_data("generate", base)
            server.invoke("generate", generate)
            base.update(
                params=generate["params"], correct_answers=generate["correct_answers"]
            )
            if through == "generate":
                return None

            prepare = self._phase_data("prepare", base)
            prepared_html = self._template(source, prepare)
            self.backend.process("prepare", prepared_html, prepare)
            server.invoke("prepare", prepare)
            base.update(
                params=prepare["params"], correct_answers=prepare["correct_answers"]
            )
            if through == "prepare":
                return None

            show_correct = metadata.get("showCorrectAnswer", True)
            answer_names = validate_declared_answers(
                prepared_html, base["correct_answers"], show_correct
            )
            tested_answer_names = tuple(
                name
                for name in answer_names
                if name not in non_gradable_answer_names(prepared_html)
            )
            rendered_question = self._render(
                source, base, server, panel="question", show_correct=show_correct
            )
            rendered_answer = (
                self._render(
                    source, base, server, panel="answer", show_correct=show_correct
                )
                if show_correct
                else None
            )
            if through == "render":
                return None

            test = self._phase_data("test", base, test_type="correct")
            self._process("test", source, test, server)
            _aggregate_score(test, metadata.get("partialCredit", True))

            parse = self._phase_data(
                "parse",
                base,
                raw_submitted_answers=test["raw_submitted_answers"],
                submitted_answers=test["raw_submitted_answers"],
                format_errors=test["format_errors"],
                feedback=test["feedback"],
                gradable=test["gradable"],
            )
            self._process("parse", source, parse, server)
            if parse["format_errors"]:
                parse["gradable"] = False

            grade = self._phase_data(
                "grade",
                base,
                params=parse["params"],
                correct_answers=parse["correct_answers"],
                submitted_answers=parse["submitted_answers"],
                raw_submitted_answers=parse["raw_submitted_answers"],
                format_errors=parse["format_errors"],
                feedback=parse["feedback"],
                gradable=parse["gradable"],
                partial_scores=test["partial_scores"],
                score=test["score"],
            )
            self._process("grade", source, grade, server)
            if grade["format_errors"]:
                grade["gradable"] = False
            _aggregate_score(grade, metadata.get("partialCredit", True))
            _assert_full_credit(grade, tested_answer_names)

            graded_base = {
                **base,
                "params": grade["params"],
                "correct_answers": grade["correct_answers"],
            }

            submission = {
                name: grade[name]
                for name in (
                    "submitted_answers",
                    "format_errors",
                    "raw_submitted_answers",
                    "partial_scores",
                    "score",
                    "feedback",
                )
            }
            rendered_submission = self._render(
                source,
                graded_base,
                server,
                panel="submission",
                show_correct=show_correct,
                submission=submission,
            )

            prepared_render_html = self._template(source, graded_base)
            filenames = self._dynamic_filenames(prepared_render_html)
            for filename in filenames or ("__prairielearn_e2e_sentinel__",):
                file_data = self._phase_data(
                    "file", graded_base, **submission, filename=filename
                )
                self._process("file", source, file_data, server)

            return LifecycleResult(
                seed=seed,
                answer_names=answer_names,
                raw_submitted_answers=copy.deepcopy(grade["raw_submitted_answers"]),
                submitted_answers=copy.deepcopy(grade["submitted_answers"]),
                partial_scores=copy.deepcopy(grade["partial_scores"]),
                score=float(grade["score"]),
                question_html=rendered_question,
                answer_html=rendered_answer,
                submission_html=rendered_submission,
            )
        finally:
            random.setstate(python_state)
            np.random.set_state(numpy_state)

    def run_generate(self, seed: int) -> None:
        self._run(seed, "generate")

    def run_prepare(self, seed: int) -> None:
        self._run(seed, "prepare")

    def run_render(self, seed: int) -> None:
        self._run(seed, "render")

    def run_grade(self, seed: int) -> LifecycleResult:
        result = self._run(seed, "grade")
        assert result is not None
        return result

    def run_variant(self, seed: int) -> LifecycleResult:
        """Run the complete lifecycle (compatibility alias for ``run_grade``)."""
        return self.run_grade(seed)
