from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import chevron  # type: ignore
import lxml.html
import prairielearn as pl  # type: ignore
import prairielearn.sympy_utils as psu  # type: ignore
import sympy

_ELEMENT_DIR = Path(__file__).parent
_TRIG_NAMES = ("sin", "cos", "tan", "sec", "csc", "cot")


@dataclass(frozen=True)
class ElementConfig:
    answers_name: str
    index_variable: str
    variables: tuple[str, ...]
    integral: bool
    weight: int
    grading_method: str
    summand_relative_weight: int
    correct_answer: str | None

    @property
    def start_name(self) -> str:
        return f"{self.answers_name}-start"

    @property
    def end_name(self) -> str:
        return f"{self.answers_name}-end"

    @property
    def summand_name(self) -> str:
        return f"{self.answers_name}-summand"

    @property
    def summand_variables(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.variables, self.index_variable)))


def _element(element_html: str):
    return lxml.html.fragment_fromstring(element_html)


def _required_string(element: Any, name: str) -> str:
    value = pl.get_string_attrib(element, name, None)
    if value is None or not value.strip():
        raise ValueError(f'Required attribute "{name}" missing')
    return value.strip()


def _config(element_html: str) -> ElementConfig:
    element = _element(element_html)
    answers_name = _required_string(element, "answers-name")
    index_variable = _required_string(element, "index-variable")
    variables_string = pl.get_string_attrib(element, "variables", "") or ""
    variables = tuple(
        value.strip() for value in variables_string.split(",") if value.strip()
    )
    grading_method = pl.get_string_attrib(element, "grading-method", "equivalent")
    if grading_method not in {"exact", "piecewise", "equivalent"}:
        raise ValueError(
            'Attribute "grading-method" must be one of "exact", "piecewise", '
            'or "equivalent".'
        )
    summand_relative_weight = pl.get_integer_attrib(
        element, "summand-relative-weight", 3
    )
    if summand_relative_weight is None or summand_relative_weight < 1:
        raise ValueError('Attribute "summand-relative-weight" must be positive.')
    return ElementConfig(
        answers_name=answers_name,
        index_variable=index_variable,
        variables=variables,
        integral=bool(pl.get_boolean_attrib(element, "integral", False)),
        weight=int(pl.get_integer_attrib(element, "weight", 1) or 1),
        grading_method=grading_method,
        summand_relative_weight=summand_relative_weight,
        correct_answer=pl.get_string_attrib(element, "correct-answer", None),
    )


def _parse_expression(source: str, variables: tuple[str, ...]) -> sympy.Expr:
    return psu.convert_string_to_sympy(
        source,
        variables,
        allow_hidden=True,
        allow_trig_functions=True,
    )


def _combined_expression(
    config: ElementConfig, start: sympy.Expr, end: sympy.Expr, body: sympy.Expr
) -> sympy.Expr:
    index = sympy.Symbol(config.index_variable)
    constructor = sympy.Integral if config.integral else sympy.Sum
    return cast(sympy.Expr, constructor(body, (index, start, end)))


def _normalize_correct_answer(value: Any) -> Any:
    source: str | None = None
    if isinstance(value, str):
        source = value
    elif psu.is_sympy_json(value):
        source = value["_value"]

    if source is None:
        return value

    try:
        return sympy.sympify(source)
    except (sympy.SympifyError, TypeError) as exc:
        raise ValueError("The correct answer is not a valid SymPy expression.") from exc


def _correct_components(
    config: ElementConfig, data: dict[str, Any]
) -> tuple[sympy.Expr, sympy.Expr, sympy.Expr] | None:
    correct_answers = data.get("correct_answers", {})
    if config.correct_answer is not None:
        raw_correct = config.correct_answer
    elif config.answers_name in correct_answers:
        raw_correct = correct_answers[config.answers_name]
    else:
        return None

    correct = _normalize_correct_answer(raw_correct)
    expected_type = sympy.Integral if config.integral else sympy.Sum
    if not isinstance(correct, expected_type):
        expected_name = "Integral" if config.integral else "Sum"
        raise TypeError(
            f'Correct answer "{config.answers_name}" must be a SymPy {expected_name}.'
        )
    if len(correct.limits) != 1:
        raise ValueError(
            f'Correct answer "{config.answers_name}" must have exactly one bounded index.'
        )

    limit = cast(tuple[Any, ...], correct.limits[0])
    if len(limit) != 3:
        raise ValueError(
            f'Correct answer "{config.answers_name}" must have exactly one bounded index.'
        )
    index, start, end = limit
    if index != sympy.Symbol(config.index_variable):
        raise ValueError(
            f'Correct answer "{config.answers_name}" uses index "{index}", '
            f'but index-variable is "{config.index_variable}".'
        )
    return (
        cast(sympy.Expr, start),
        cast(sympy.Expr, end),
        cast(sympy.Expr, correct.function),
    )


def prepare(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    correct_components = _correct_components(config, data)
    if correct_components is None:
        return

    start, end, body = correct_components
    data.setdefault("correct_answers", {})[config.answers_name] = psu.sympy_to_json(
        _combined_expression(config, start, end, body)
    )


def _field(
    answers_name: str,
    label: str,
    size: int,
    data: dict[str, Any],
    *,
    prefix: str | None = None,
) -> dict[str, Any]:
    raw_answers = data.get("raw_submitted_answers", {})
    return {
        "answers_name": answers_name,
        "label": label,
        "size": size,
        "prefix": prefix,
        "editable": data.get("panel", "question") == "question",
        "raw_submitted_answer": raw_answers.get(answers_name, ""),
        "raw_submitted_answer_latex": raw_answers.get(f"{answers_name}-latex", ""),
        "parse_error": data.get("format_errors", {}).get(answers_name),
        "custom_functions": "",
    }


def _render_question(config: ElementConfig, data: dict[str, Any]) -> str:
    index_label = sympy.latex(sympy.Symbol(config.index_variable))
    lower_prefix = None if config.integral else rf"\({index_label} = \)"
    context = {
        "integral": config.integral,
        "latex_symbol": r"\int" if config.integral else r"\sum",
        "index_label": index_label,
        "lower_field": _field(
            config.start_name, "Lower bound", 6, data, prefix=lower_prefix
        ),
        "upper_field": _field(
            config.end_name, "Upper bound", 6 if config.integral else 4, data
        ),
        "summand_field": _field(config.summand_name, "Summand", 20, data),
    }
    template = (_ELEMENT_DIR / "pl-sum-notation-input.mustache").read_text()
    return chevron.render(
        template,
        context,
        partials_path=str(_ELEMENT_DIR / "partials"),
        partials_ext="mustache",
    )


def _submission_tex(config: ElementConfig, data: dict[str, Any]) -> str:
    raw = data.get("raw_submitted_answers", {})
    start = raw.get(config.start_name, "?")
    end = raw.get(config.end_name, "?")
    body = raw.get(config.summand_name, "?")
    index = sympy.latex(sympy.Symbol(config.index_variable))
    if config.integral:
        return rf"\int_{{{start}}}^{{{end}}} {body}\,\mathrm{{d}}{index}"
    return rf"\sum_{{{index}={start}}}^{{{end}}} {body}"


def _render_submission(config: ElementConfig, data: dict[str, Any]) -> str:
    score = float(
        data.get("partial_scores", {}).get(config.answers_name, {}).get("score", 0)
    )
    context: dict[str, Any] = {"tex": _submission_tex(config, data)}
    if score >= 1:
        context["correct"] = True
    elif score <= 0:
        context["incorrect"] = True
    else:
        context["partial"] = round(100 * score)
    template = (_ELEMENT_DIR / "pl-sum-notation-input-submission.mustache").read_text()
    return chevron.render(template, context)


def render(element_html: str, data: dict[str, Any]) -> str:
    config = _config(element_html)
    if data.get("panel", "question") == "submission":
        return _render_submission(config, data)
    return _render_question(config, data)


def _despace_function_names(source: str) -> str:
    for name in _TRIG_NAMES:
        source = re.sub(rf"\b{' *'.join(name)}\b", name, source)
    return source


def parse(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    raw = data.get("raw_submitted_answers", {})
    submitted = data.setdefault("submitted_answers", {})
    start = _parse_expression(raw.get(config.start_name, ""), config.variables)
    end = _parse_expression(raw.get(config.end_name, ""), config.variables)
    body = _parse_expression(
        _despace_function_names(raw.get(config.summand_name, "")),
        config.summand_variables,
    )
    submitted[config.start_name] = psu.sympy_to_json(start)
    submitted[config.end_name] = psu.sympy_to_json(end)
    submitted[config.summand_name] = psu.sympy_to_json(body)
    submitted[config.answers_name] = str(_combined_expression(config, start, end, body))


def _submitted_components(
    config: ElementConfig, data: dict[str, Any]
) -> tuple[sympy.Expr, sympy.Expr, sympy.Expr]:
    raw = data.get("raw_submitted_answers", {})
    return (
        _parse_expression(raw.get(config.start_name, ""), config.variables),
        _parse_expression(raw.get(config.end_name, ""), config.variables),
        _parse_expression(
            _despace_function_names(raw.get(config.summand_name, "")),
            config.summand_variables,
        ),
    )


def _definitely_zero(expression: sympy.Expr) -> bool:
    simplified = sympy.simplify(sympy.expand(expression))
    return simplified == 0 or simplified.equals(0) is True


def _evaluates_equally(submitted: sympy.Expr, correct: sympy.Expr) -> bool:
    try:
        difference = cast(sympy.Expr, submitted.doit() - correct.doit())  # type: ignore
        return _definitely_zero(difference)
    except (NotImplementedError, TypeError, ValueError, ZeroDivisionError):
        return False


def _affine_reindex_match(
    config: ElementConfig,
    submitted_components: tuple[sympy.Expr, sympy.Expr, sympy.Expr],
    correct_components: tuple[sympy.Expr, sympy.Expr, sympy.Expr],
) -> bool:
    submitted_start, submitted_end, submitted_body = submitted_components
    correct_start, correct_end, correct_body = correct_components
    if config.integral:
        bounds_reversed = _definitely_zero(
            cast(sympy.Expr, submitted_start - correct_end)  # type: ignore
        ) and _definitely_zero(cast(sympy.Expr, submitted_end - correct_start))  # type: ignore
        body_negated = _definitely_zero(cast(sympy.Expr, submitted_body + correct_body))  # type: ignore
        if bounds_reversed and body_negated:
            return True

    index = sympy.Symbol(config.index_variable)
    for coefficient in (sympy.Integer(1), sympy.Integer(-1)):
        if config.integral or coefficient == 1:
            offset = cast(sympy.Expr, correct_start - submitted_start)  # type: ignore
            if coefficient == -1:
                offset = cast(
                    sympy.Expr,
                    correct_start - coefficient * submitted_start,  # type: ignore
                )
            bounds_match = _definitely_zero(
                cast(sympy.Expr, coefficient * submitted_end + offset - correct_end)  # type: ignore
            )
        else:
            offset = cast(sympy.Expr, correct_end + submitted_start)  # type: ignore
            bounds_match = _definitely_zero(
                cast(sympy.Expr, coefficient * submitted_end + offset - correct_start)  # type: ignore
            )
        if not bounds_match:
            continue  # type: ignore

        transformed_body = correct_body.subs(index, coefficient * index + offset)  # type: ignore
        if config.integral:
            transformed_body *= coefficient
        if _definitely_zero(cast(sympy.Expr, submitted_body - transformed_body)):  # type: ignore
            return True
    return False


def _equivalent_score(
    config: ElementConfig,
    submitted_components: tuple[sympy.Expr, sympy.Expr, sympy.Expr],
    correct_components: tuple[sympy.Expr, sympy.Expr, sympy.Expr],
) -> float:
    submitted = _combined_expression(config, *submitted_components)
    correct = _combined_expression(config, *correct_components)
    equivalent = (
        submitted == correct
        or _evaluates_equally(submitted, correct)
        or _affine_reindex_match(config, submitted_components, correct_components)
    )
    return 1.0 if equivalent else 0.0


def grade(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    correct_components = _correct_components(config, data)
    if correct_components is None:
        return

    submitted_components = _submitted_components(config, data)
    if config.grading_method == "exact":
        score = float(
            _combined_expression(config, *submitted_components)
            == _combined_expression(config, *correct_components)
        )
    elif config.grading_method == "piecewise":
        component_weights = (1, 1, config.summand_relative_weight)
        earned = sum(
            weight
            for submitted, correct, weight in zip(
                submitted_components, correct_components, component_weights
            )
            if submitted == correct
        )
        score = earned / sum(component_weights)
    else:
        score = _equivalent_score(config, submitted_components, correct_components)

    data.setdefault("partial_scores", {})[config.answers_name] = {
        "score": score,
        "weight": config.weight,
    }
