from __future__ import annotations

import importlib.util
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import chevron
import lxml.html
import prairielearn as pl
import prairielearn.sympy_utils as psu
import sympy
import sympy.sets

HERE = Path(__file__).parent
ADAPTER_SPEC = importlib.util.spec_from_file_location(
    "pl_big_operator_input_symbolic_adapter", HERE / "symbolic_input_adapter.py"
)
if ADAPTER_SPEC is None or ADAPTER_SPEC.loader is None:
    raise RuntimeError("Could not load the pl-symbolic-input adapter.")
symbolic_input_adapter = importlib.util.module_from_spec(ADAPTER_SPEC)
sys.modules[ADAPTER_SPEC.name] = symbolic_input_adapter
ADAPTER_SPEC.loader.exec_module(symbolic_input_adapter)
OPS = {
    "sum": (r"\sum", "bounds"),
    "product": (r"\prod", "bounds"),
    "integral": (r"\int", "bounds"),
    "limit": (r"\lim", "approach"),
    "union": (r"\bigcup", "domain"),
    "intersection": (r"\bigcap", "domain"),
    "disjoint-union": (r"\bigsqcup", "domain"),
    "and": (r"\bigwedge", "domain"),
    "or": (r"\bigvee", "domain"),
    "min": (r"\min", "domain"),
    "max": (r"\max", "domain"),
}
FLEXIBLE = {
    "sum",
    "product",
    "integral",
    "union",
    "intersection",
    "disjoint-union",
    "and",
    "or",
    "min",
    "max",
}
DIRECTIONS = {"two-sided": "+-", "from-left": "-", "from-right": "+"}
SYMPY_CONSTRUCTORS: dict[str, type[sympy.Basic]] = {
    "sum": sympy.Sum,
    "product": sympy.Product,
    "integral": sympy.Integral,
    "union": sympy.Union,
    "intersection": sympy.Intersection,
    "disjoint-union": sympy.sets.DisjointUnion,
    "and": sympy.And,
    "or": sympy.Or,
    "min": sympy.Min,
    "max": sympy.Max,
}
type LimitFormat = Literal["bounds", "domain", "approach"]
type Component = Literal["lower", "upper", "domain", "target", "body"]
COMPONENT_MAP: dict[LimitFormat, Sequence[Component]] = {
    "bounds": ("lower", "upper", "body"),
    "domain": ("domain", "body"),
    "approach": ("target", "body"),
}
CORRECT_COMPONENT_ATTRIBUTES: dict[Component, str] = {
    "lower": "correct-answer-start",
    "upper": "correct-answer-end",
    "domain": "correct-answer-domain",
    "target": "correct-answer-target",
    "body": "correct-answer-body",
}


@dataclass(frozen=True)
class Config:
    answer: str
    operator: str
    operator_latex: str
    limits: LimitFormat
    index: str
    variables: tuple[str, ...]
    direction: str
    allow_blank: bool
    allow_complex: bool
    show_help_text: bool
    grading: str
    body_weight: int
    weight: int
    correct_attribute: str | None
    correct_components: tuple[tuple[Component, str], ...]

    @property
    def components(self):
        return COMPONENT_MAP[self.limits]

    def name(self, component: str) -> str:
        return f"{self.answer}-{ {'lower': 'start', 'upper': 'end'}.get(component, component) }"


def _config(html: str) -> Config:
    element = lxml.html.fragment_fromstring(html)
    required = {}
    for name in ("answers-name", "index-variable"):
        value = pl.get_string_attrib(element, name, None)
        if value is None or not value.strip():
            raise ValueError(f'Required attribute "{name}" missing')
        required[name] = value.strip()
    operator = pl.get_string_attrib(element, "operator", "sum") or "sum"
    if operator not in {*OPS, "custom"}:
        raise ValueError(f'Unknown operator "{operator}".')
    custom_latex = pl.get_string_attrib(element, "operator-latex", None)
    if operator == "custom":
        if custom_latex is None or not custom_latex.strip():
            raise ValueError(
                'Attribute "operator-latex" is required when operator="custom".'
            )
        operator_latex = custom_latex.strip()
    else:
        if custom_latex is not None:
            raise ValueError(
                'Attribute "operator-latex" can only be used when operator="custom".'
            )
        operator_latex = OPS[operator][0]
    limits = pl.get_string_attrib(element, "limits", "auto") or "auto"
    if operator == "custom" and limits == "auto":
        raise ValueError(
            'Custom operators require explicit limits="bounds" or limits="domain".'
        )
    limits = OPS[operator][1] if limits == "auto" else limits
    allowed = (
        {"bounds", "domain"}
        if operator in FLEXIBLE or operator == "custom"
        else {OPS[operator][1]}
    )
    if limits not in allowed:
        raise ValueError(
            f'Operator "{operator}" does not support limits="{limits}"; use {", ".join(sorted(allowed))}.'
        )
    grading = (
        pl.get_string_attrib(element, "grading-method", "equivalent") or "equivalent"
    )
    if grading not in {"exact", "component", "equivalent"}:
        raise ValueError(
            'Attribute "grading-method" must be exact, component, or equivalent.'
        )
    body_weight = pl.get_integer_attrib(element, "body-relative-weight", 3)
    if body_weight is None or body_weight < 1:
        raise ValueError('Attribute "body-relative-weight" must be positive.')
    direction = (
        pl.get_string_attrib(element, "limit-direction", "two-sided") or "two-sided"
    )
    if direction not in DIRECTIONS:
        raise ValueError(f'Unknown limit-direction "{direction}".')
    variables = pl.get_string_attrib(element, "variables", "") or ""
    components = COMPONENT_MAP[cast(LimitFormat, limits)]
    supplied_components = {
        component: value
        for component, attribute in CORRECT_COMPONENT_ATTRIBUTES.items()
        if (value := pl.get_string_attrib(element, attribute, None)) is not None
    }
    irrelevant = set(supplied_components) - set(components)
    if irrelevant:
        attributes = ", ".join(
            CORRECT_COMPONENT_ATTRIBUTES[component]  # type: ignore
            for component in irrelevant
        )
        raise ValueError(
            f'Correct-answer attribute(s) {attributes} cannot be used with limits="{limits}".'
        )
    if supplied_components and set(supplied_components) != set(components):
        missing = ", ".join(
            CORRECT_COMPONENT_ATTRIBUTES[component]
            for component in components
            if component not in supplied_components
        )
        raise ValueError(
            f"Component correct answers must supply every visible field; missing {missing}."
        )
    correct_attribute = pl.get_string_attrib(element, "correct-answer", None)
    if correct_attribute is not None and supplied_components:
        raise ValueError(
            'Use either "correct-answer" or component correct-answer attributes, not both.'
        )
    if (
        operator == "custom"
        and (correct_attribute is not None or supplied_components)
        and grading != "exact"
    ):
        raise ValueError(
            'Custom operators with a correct answer require grading-method="exact".'
        )
    return Config(
        required["answers-name"],
        operator,
        operator_latex,
        cast(LimitFormat, limits),
        required["index-variable"],
        tuple(x.strip() for x in variables.split(",") if x.strip()),
        direction,
        bool(pl.get_boolean_attrib(element, "allow-blank", False)),
        bool(pl.get_boolean_attrib(element, "allow-complex", False)),
        bool(pl.get_boolean_attrib(element, "show-help-text", True)),
        grading,
        body_weight,
        int(pl.get_integer_attrib(element, "weight", 1) or 1),
        correct_attribute,
        tuple((component, supplied_components[component]) for component in components)
        if supplied_components
        else (),
    )


def _decode(value: Any) -> Any:
    if isinstance(value, dict) and value.get("_type") == "sympy" and "_value" in value:
        source = value["_value"]
        if isinstance(source, str):
            # Canonical leaves are trusted author answers. PrairieLearn's
            # student-input parser cannot round-trip every value emitted by
            # sympy_to_json: binder tuples look like intervals, and Boolean
            # relations are rejected by its expression allowlist.
            if (
                source.lstrip().startswith(("{", "["))
                or " ∪ " in source
                or " ∩ " in source
            ):
                return psu.json_to_sympy(cast(Any, value), allow_sets=True)
            return sympy.sympify(  # type: ignore[call-overload]
                source, locals={"_Exp1": sympy.E, "_ImaginaryUnit": sympy.I}
            )
    if isinstance(value, str):
        try:
            return sympy.sympify(  # type: ignore[call-overload]
                value, locals={"_Exp1": sympy.E, "_ImaginaryUnit": sympy.I}
            )
        except (sympy.SympifyError, TypeError) as exc:
            raise ValueError("The correct answer contains invalid SymPy data.") from exc
    return value


def _json(value: sympy.Basic) -> dict[str, Any]:
    return cast(dict[str, Any], psu.sympy_to_json(cast(Any, value), allow_sets=True))


def _canonical(config: Config, values: dict[str, sympy.Basic]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "_type": "operator_expression",
        "_version": 1,
        "operator": config.operator,
        "limits": config.limits,
        "index": _json(sympy.Symbol(config.index)),
    }
    if config.operator == "custom":
        result["operator_latex"] = config.operator_latex
    result.update({key: _json(values[key]) for key in config.components})
    if config.limits == "approach":
        result["direction"] = config.direction
    return result


def _structured(config: Config, value: dict[str, Any]) -> dict[str, Any]:
    keys = {"_type", "_version", "operator", "limits", "index", *config.components}
    if config.operator == "custom":
        keys.add("operator_latex")
    if config.limits == "approach":
        keys.add("direction")
    if (
        set(value) != keys
        or value.get("_type") != "operator_expression"
        or value.get("_version") != 1
    ):
        raise ValueError(
            "Correct answer is not a well-formed version 1 operator expression."
        )
    if value["operator"] != config.operator or value["limits"] != config.limits:
        raise ValueError(
            "Correct answer operator or limits form does not match the element."
        )
    if config.operator == "custom" and value["operator_latex"] != config.operator_latex:
        raise ValueError(
            "Correct answer custom operator does not match operator-latex."
        )
    if config.limits == "approach" and value["direction"] != config.direction:
        raise ValueError("Correct answer direction does not match limit-direction.")
    if _decode(value["index"]) != sympy.Symbol(config.index):
        raise ValueError("Correct answer index does not match index-variable.")
    values = {key: _decode(value[key]) for key in config.components}
    if not all(isinstance(item, sympy.Basic) for item in values.values()):
        raise ValueError(
            "Every mathematical component must be PrairieLearn SymPy JSON."
        )
    return _canonical(config, cast(dict[str, sympy.Basic], values))


def _component_values(config: Config, value: dict[Component, Any]) -> dict[str, Any]:
    values: dict[str, sympy.Basic] = {}
    for component in config.components:
        raw = value[component]
        variables = (
            tuple(dict.fromkeys((*config.variables, config.index)))
            if component == "body"
            else config.variables
        )
        try:
            parsed = _parse(raw, variables) if isinstance(raw, str) else _decode(raw)
        except Exception as exc:
            raise ValueError(
                f'Parsing correct answer component "{component}" failed.'
            ) from exc
        if not isinstance(parsed, sympy.Basic):
            raise TypeError(
                f'Correct answer component "{component}" must be a SymPy value or parseable string.'
            )
        if _requires_set(config, component) and not isinstance(parsed, sympy.Set):
            raise ValueError(f'Correct answer component "{component}" must be a set.')
        values[component] = parsed
    return _canonical(config, values)


def _binder(config: Config, value: Any) -> dict[str, Any] | None:
    expected = {
        "sum": sympy.Sum,
        "product": sympy.Product,
        "integral": sympy.Integral,
        "limit": sympy.Limit,
    }.get(config.operator)
    if expected is None or not isinstance(value, expected):
        return None
    index = sympy.Symbol(config.index)
    if config.operator == "limit":
        body, variable, target, direction = value.args
        if variable != index:
            raise ValueError("Correct answer index does not match index-variable.")
        public = {v: k for k, v in DIRECTIONS.items()}.get(str(direction))
        if public != config.direction:
            raise ValueError(
                "Correct answer Limit direction does not match limit-direction."
            )
        return _canonical(config, {"target": target, "body": body})
    if len(value.limits) != 1 or len(value.limits[0]) != 3:
        raise ValueError("Correct answer must have exactly one bounded index.")
    variable, lower, upper = value.limits[0]
    if variable != index:
        raise ValueError("Correct answer index does not match index-variable.")
    return _canonical(config, {"lower": lower, "upper": upper, "body": value.function})


def _correct(config: Config, data: pl.QuestionData) -> dict[str, Any] | None:
    prepared_key = f"_pl_big_operator_input_correct_{config.answer}"
    raw = (
        dict(config.correct_components)
        if config.correct_components
        else (
            config.correct_attribute
            if config.correct_attribute is not None
            else data.get("correct_answers", {}).get(
                config.answer, data.get("params", {}).get(prepared_key)
            )
        )
    )
    if config.operator == "custom" and raw is not None and config.grading != "exact":
        raise ValueError(
            'Custom operators with a correct answer require grading-method="exact".'
        )
    if raw is None:
        return None
    if isinstance(raw, dict) and raw.get("_type") == "operator_expression":  # type: ignore
        return _structured(config, raw)  # type: ignore
    if config.correct_components:
        return _component_values(config, cast(dict[Component, Any], raw))
    value = _decode(raw)
    converted = _binder(config, value)
    if converted is not None:
        return converted
    raise TypeError(
        f'Correct answer "{config.answer}" must be a matching binder-aware object or canonical structured dictionary.'
    )


def prepare(element_html: str, data: pl.QuestionData) -> None:
    config = _config(element_html)
    correct = _correct(config, data)
    if correct is not None:
        data.setdefault("correct_answers", {})[config.answer] = correct
        data.setdefault("params", {})[
            f"_pl_big_operator_input_correct_{config.answer}"
        ] = correct


def _field(
    config: Config,
    component: str,
    label: str,
    size: int,
    data: dict[str, Any] | pl.QuestionData,
    prefix: str | None = None,
    suffix: str | None = None,
) -> dict[str, Any]:
    name = config.name(component)
    variables = (
        tuple(dict.fromkeys((*config.variables, config.index)))
        if component == "body"
        else config.variables
    )
    field_markup = symbolic_input_adapter.markup(
        name=name,
        variables=variables,
        label=label,
        size=size,
        allow_sets=_requires_set(config, cast(Component, component)),
        allow_complex=config.allow_complex,
        show_help_text=component == "body" and config.show_help_text,
        prefix=prefix,
        suffix=suffix,
    )
    return {
        "html": symbolic_input_adapter.render(field_markup, data, aria_label=label),
    }


def _question(config: Config, data: pl.QuestionData) -> str:
    index = sympy.latex(sympy.Symbol(config.index))
    context: dict[str, Any] = {
        config.limits: True,
        "integral": config.operator == "integral",
        "operator_latex": config.operator_latex,
        "index_label": index,
        "body_field": _field(config, "body", "Operator body", 16, data),
    }
    partial_score = data.get("partial_scores", {}).get(config.answer)
    if partial_score is not None:
        context["score_badge"] = _score_badge(float(partial_score.get("score") or 0))
    if config.limits == "bounds":
        context["lower_field"] = _field(
            config,
            "lower",
            "Lower bound",
            7,
            data,
            None if config.operator == "integral" else rf"\({index} = \)",
        )
        context["upper_field"] = _field(config, "upper", "Upper bound", 7, data)
    elif config.limits == "domain":
        context["annotation_field"] = _field(
            config,
            "domain",
            "Integration domain" if config.operator == "integral" else "Index domain",
            10,
            data,
            None if config.operator == "integral" else rf"\({index} \in \)",
        )
    else:
        dir = {"two-sided": None, "from-left": "−", "from-right": "+"}[config.direction]
        context["annotation_field"] = _field(
            config,
            "target",
            "Approach target",
            10,
            data,
            rf"\({index} \to \)",
            dir and rf"\({{}}^{dir}\)",
        )
    return chevron.render(
        (HERE / "pl-big-operator-input.mustache").read_text(),
        context,
        partials_path=str(HERE / "partials"),
        partials_ext="mustache",
    )


def _tex(config: Config, raw: dict[str, Any] | None) -> str:
    raw = raw or {}
    get = lambda c: raw.get(config.name(c), "?")
    index = sympy.latex(sympy.Symbol(config.index))
    op = config.operator_latex
    if config.limits == "bounds":
        if config.operator == "integral":
            return rf"{op}_{{{get('lower')}}}^{{{get('upper')}}} {get('body')}\,\mathrm{{d}}{index}"
        return rf"{op}_{{{index}={get('lower')}}}^{{{get('upper')}}} {get('body')}"
    if config.limits == "domain":
        if config.operator == "integral":
            return rf"{op}_{{{get('domain')}}} {get('body')}\,\mathrm{{d}}{index}"
        return rf"{op}_{{{index}\in {get('domain')}}} {get('body')}"
    direction = {"two-sided": "", "from-left": "^-", "from-right": "^+"}[
        config.direction
    ]
    return rf"{op}_{{{index}\to {get('target')}{direction}}} {get('body')}"


def _structured_tex(config: Config, structured: dict[str, Any]) -> str:
    values = _values(config, structured)
    raw = {config.name(key): sympy.latex(value) for key, value in values.items()}
    return _tex(config, raw)


def _submitted_tex(config: Config, data: pl.QuestionData) -> str:
    structured = data.get("submitted_answers", {}).get(config.answer)
    if isinstance(structured, dict):
        return _structured_tex(config, structured)
    return _tex(config, data.get("raw_submitted_answers"))


def _score_badge(score: float) -> dict[str, Any]:
    if score >= 1:
        return {"correct": True}
    if score <= 0:
        return {"incorrect": True}
    return {"partial": round(score * 100)}


def render(element_html: str, data: pl.QuestionData) -> str:
    config = _config(element_html)
    panel = data.get("panel", "question")
    if panel == "question":
        return _question(config, data)
    if panel == "answer":
        correct = _correct(config, data)
        if correct is None:
            return ""
        return chevron.render(
            (HERE / "pl-big-operator-input-submission.mustache").read_text(),
            {"tex": _structured_tex(config, correct)},
            partials_path=str(HERE / "partials"),
            partials_ext="mustache",
        )
    context: dict[str, Any] = {"tex": _submitted_tex(config, data)}
    partial_score = data.get("partial_scores", {}).get(config.answer)
    if partial_score is not None:
        context.update(_score_badge(float(partial_score.get("score") or 0)))
    return chevron.render(
        (HERE / "pl-big-operator-input-submission.mustache").read_text(),
        context,
        partials_path=str(HERE / "partials"),
        partials_ext="mustache",
    )


def _parse(source: str, variables: tuple[str, ...]) -> sympy.Basic:
    source = re.sub(r"\binfinity\b", "infty", source)
    for name in ("sin", "cos", "tan", "sec", "csc", "cot"):
        source = re.sub(rf"\b{' *'.join(name)}\b", name, source)
    return psu.convert_string_to_sympy(
        source, variables, allow_hidden=True, allow_sets=True, allow_trig_functions=True
    )


def _requires_set(config: Config, component: Component) -> bool:
    return component == "domain" or (
        component == "body"
        and config.operator in {"union", "intersection", "disjoint-union"}
    )


def _is_set_input(value: sympy.Basic) -> bool:
    # A bare symbol may denote a set whose members are not known at parse time.
    return isinstance(value, (sympy.Set, sympy.Symbol))


def _blank(config: Config, raw: dict[str, Any] | None) -> bool:
    raw = raw or {}
    return all(not str(raw.get(config.name(c), "")).strip() for c in config.components)


def _parse_values(
    config: Config, data: dict[str, Any]
) -> dict[str, sympy.Basic] | None:
    submitted = data.setdefault("submitted_answers", {})
    result: dict[str, sympy.Basic] = {}
    for component in config.components:
        name = config.name(component)
        variables = (
            tuple(dict.fromkeys((*config.variables, config.index)))
            if component == "body"
            else config.variables
        )
        field_markup = symbolic_input_adapter.markup(
            name=name,
            variables=variables,
            label={
                "lower": "Lower bound",
                "upper": "Upper bound",
                "domain": "Index domain",
                "target": "Approach target",
                "body": "Operator body",
            }[component],
            size=16 if component == "body" else 10,
            allow_sets=_requires_set(config, component),
            allow_complex=config.allow_complex,
        )
        symbolic_input_adapter.parse(field_markup, data)
        raw_value = submitted.get(name)
        if not isinstance(raw_value, dict):
            continue
        try:
            value = cast(
                sympy.Basic,
                psu.json_to_sympy(
                    cast(Any, raw_value),
                    allow_sets=True,
                    allow_complex=config.allow_complex,
                ),
            )
            if _requires_set(config, component) and not _is_set_input(value):
                data.setdefault("format_errors", {})[name] = "This field must be a set."
                continue
            result[component] = value
        except Exception as exc:  # noqa: BLE001 -- delegated JSON decoding can expose parser errors.
            data.setdefault("format_errors", {})[name] = str(exc)
    return result if len(result) == len(config.components) else None


def parse(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    submitted = data.setdefault("submitted_answers", {})
    if _blank(config, data.get("raw_submitted_answers")):
        submitted[config.answer] = "" if config.allow_blank else None
        if not config.allow_blank:
            errors = data.setdefault("format_errors", {})
            for component in config.components:
                name = config.name(component)
                submitted[name] = None
                errors[name] = "No submitted answer."
        return
    values = _parse_values(config, data)
    submitted[config.answer] = _canonical(config, values) if values else None


def _values(config: Config, structured: dict[str, Any]) -> dict[str, sympy.Basic]:
    return {
        key: cast(sympy.Basic, _decode(structured[key])) for key in config.components
    }


def _construct(config: Config, values: dict[str, sympy.Basic]) -> sympy.Basic:
    index = sympy.Symbol(config.index)
    body = values["body"]
    if config.limits == "bounds":
        bound_constructor = SYMPY_CONSTRUCTORS.get(config.operator)
        if bound_constructor is None:
            raise NotImplementedError(
                f"Equivalent grading for bounded {config.operator} is unsupported."
            )
        return bound_constructor(body, (index, values["lower"], values["upper"]))
    if config.limits == "approach":
        return sympy.Limit(
            body, index, values["target"], dir=DIRECTIONS[config.direction]
        )
    domain = values["domain"]
    if config.operator == "integral":
        raise NotImplementedError(
            "Equivalent grading for domain integrals is unsupported; use exact or component grading."
        )
    if not isinstance(domain, sympy.FiniteSet):
        raise NotImplementedError(
            "Equivalent grading of domain forms requires a concrete FiniteSet domain."
        )
    terms = [body.subs(index, item) for item in domain]
    return SYMPY_CONSTRUCTORS[config.operator](*terms)


def _equivalent(
    config: Config,
    left_values: dict[str, sympy.Basic],
    right_values: dict[str, sympy.Basic],
) -> bool:
    left, right = _construct(config, left_values), _construct(config, right_values)
    if left == right:
        return True
    try:
        left, right = left.doit(), right.doit()
        if left == right:
            return True
        difference = sympy.simplify(sympy.expand(cast(Any, left) - cast(Any, right)))
        return difference == 0 or difference.equals(0) is True
    except (NotImplementedError, TypeError, ValueError, ZeroDivisionError):
        return False


def grade(element_html: str, data: pl.QuestionData) -> None:
    config = _config(element_html)
    correct_json = _correct(config, data)
    if correct_json is None:
        return
    if config.allow_blank and _blank(config, data.get("raw_submitted_answers")):
        score = 0.0
    else:
        submitted_json = data.get("submitted_answers", {}).get(config.answer)
        if not isinstance(submitted_json, dict):
            return
        submitted, correct = (
            _values(config, submitted_json),
            _values(config, correct_json),
        )
        if config.grading == "exact":
            score = float(submitted_json == correct_json)
        elif config.grading == "component":
            weights = [
                config.body_weight if c == "body" else 1 for c in config.components
            ]
            score = sum(
                w
                for c, w in zip(config.components, weights)
                if submitted[c] == correct[c]
            ) / sum(weights)
        else:
            score = float(_equivalent(config, submitted, correct))
    data.setdefault("partial_scores", {})[config.answer] = {
        "score": score,
        "weight": config.weight,
    }
    pl.set_weighted_score_data(data)
