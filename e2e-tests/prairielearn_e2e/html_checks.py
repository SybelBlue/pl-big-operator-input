from __future__ import annotations

import re
from collections import Counter
from typing import Any

import lxml.html

from .config import ELEMENT_SOLUTION_ANSWER_SELECTORS, NON_GRADABLE_ANSWER_SELECTORS
from .errors import HarnessError

_SIMPLE_CSS_SELECTOR = re.compile(
    r"^(?P<tag>[A-Za-z][\w-]*)(?:\[(?P<attribute>[\w-]+)=(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\]]+))\])?$"
)


def _select_elements(fragment: Any, selector: str) -> list[Any]:
    """Apply configured CSS selectors, with a small dependency-free fallback."""

    try:
        return list(fragment.cssselect(selector))
    except ImportError:
        match = _SIMPLE_CSS_SELECTOR.fullmatch(selector.strip())
        if match is None:
            raise HarnessError(
                "CSS selector support requires the cssselect package for: " + selector
            ) from None
        expected_tag = match.group("tag").lower()
        expected_attribute = match.group("attribute")
        expected_value = None
        if expected_attribute is not None:
            expected_value = next(
                value
                for value in (
                    match.group("double"),
                    match.group("single"),
                    match.group("bare"),
                )
                if value is not None
            )
        candidates = [fragment, *fragment.iter()]
        return [
            element
            for element in candidates
            if element.tag.lower() == expected_tag
            and (
                expected_attribute is None
                or element.get(expected_attribute) == expected_value
            )
        ]


def declared_answer_names(html: str) -> tuple[str, ...]:
    fragments = lxml.html.fragments_fromstring(html)
    names: list[str] = []
    for fragment in fragments:
        if isinstance(fragment, str):
            continue
        for element in fragment.xpath(".//*[@answers-name] | self::*[@answers-name]"):
            name = element.get("answers-name")
            if name is None or not name.strip():
                raise HarnessError("question.html contains an empty answers-name")
            names.append(name)
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise HarnessError(
            "question.html declares duplicate answers-name values: "
            + ", ".join(duplicates)
        )
    return tuple(names)


def require_correct_answers(
    answer_names: tuple[str, ...], correct_answers: dict[str, Any]
) -> None:
    missing = [
        name
        for name in answer_names
        if name not in correct_answers or correct_answers[name] is None
    ]
    if missing:
        raise HarnessError(
            "showCorrectAnswer requires non-null correct answers for: "
            + ", ".join(missing)
        )


def _answer_names_matching_selectors(
    html: str, selectors: tuple[str, ...]
) -> frozenset[str]:
    fragments = lxml.html.fragments_fromstring(html)
    names: set[str] = set()
    for fragment in fragments:
        if isinstance(fragment, str):
            continue
        for selector in selectors:
            for element in _select_elements(fragment, selector):
                if name := element.get("answers-name"):
                    names.add(name)
    return frozenset(names)


def element_solution_answer_names(html: str) -> frozenset[str]:
    """Return answer names whose solution is owned by the element.

    These elements do not need an entry in ``correct_answers``, but they can
    still be graded and must remain part of the parse/grade lifecycle checks.
    """

    return _answer_names_matching_selectors(html, ELEMENT_SOLUTION_ANSWER_SELECTORS)


def non_gradable_answer_names(html: str) -> frozenset[str]:
    """Return answer names intentionally excluded from server-side grading.

    Configured display-only elements still carry an ``answers-name`` for
    client-side identity, but have no submitted answer, correct answer, or
    partial score.
    """

    return _answer_names_matching_selectors(html, NON_GRADABLE_ANSWER_SELECTORS)


def validate_declared_answers(
    html: str, correct_answers: dict[str, Any], show_correct_answer: bool
) -> tuple[str, ...]:
    names = declared_answer_names(html)
    if show_correct_answer:
        ignored = non_gradable_answer_names(html) | element_solution_answer_names(html)
        require_correct_answers(
            tuple(name for name in names if name not in ignored), correct_answers
        )
    return names
