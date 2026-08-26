from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import chevron  # type: ignore
import lxml.html
import prairielearn as pl  # type: ignore
import prairielearn.sympy_utils as psu  # type: ignore
import sympy
import sympy.sets

HERE = Path(__file__).parent
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


@dataclass(frozen=True)
class Config:
    answer: str
    operator: str
    limits: LimitFormat
    index: str
    variables: tuple[str, ...]
    direction: str
    allow_blank: bool
    grading: str
    body_weight: int
    weight: int
    correct_attribute: str | None

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
    if operator not in OPS:
        raise ValueError(f'Unknown operator "{operator}".')
    limits = pl.get_string_attrib(element, "limits", "auto") or "auto"
    limits = OPS[operator][1] if limits == "auto" else limits
    allowed = {"bounds", "domain"} if operator in FLEXIBLE else {OPS[operator][1]}
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
    return Config(
        required["answers-name"],
        operator,
        cast(LimitFormat, limits),
        required["index-variable"],
        tuple(x.strip() for x in variables.split(",") if x.strip()),
        direction,
        bool(pl.get_boolean_attrib(element, "allow-blank", False)),
        grading,
        body_weight,
        int(pl.get_integer_attrib(element, "weight", 1) or 1),
        pl.get_string_attrib(element, "correct-answer", None),
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
    result.update({key: _json(values[key]) for key in config.components})
    if config.limits == "approach":
        result["direction"] = config.direction
    return result


def _structured(config: Config, value: dict[str, Any]) -> dict[str, Any]:
    keys = {"_type", "_version", "operator", "limits", "index", *config.components}
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


def _correct(config: Config, data: dict[str, Any]) -> dict[str, Any] | None:
    prepared_key = f"_pl_big_operator_input_correct_{config.answer}"
    raw = (
        config.correct_attribute
        if config.correct_attribute is not None
        else data.get("correct_answers", {}).get(
            config.answer, data.get("params", {}).get(prepared_key)
        )
    )
    if raw is None:
        return None
    if isinstance(raw, dict) and raw.get("_type") == "operator_expression":
        return _structured(config, raw)
    value = _decode(raw)
    converted = _binder(config, value)
    if converted is not None:
        return converted
    raise TypeError(
        f'Correct answer "{config.answer}" must be a matching binder-aware object or canonical structured dictionary.'
    )


def prepare(element_html: str, data: dict[str, Any]) -> None:
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
    data: dict[str, Any],
    prefix: str | None = None,
    suffix: str | None = None,
) -> dict[str, Any]:
    name = config.name(component)
    raw = data.get("raw_submitted_answers", {})
    return {
        "answers_name": name,
        "error_id": f"big-operator-input-error-{name}",
        "label": label,
        "size": size,
        "prefix": prefix,
        "suffix": suffix,
        "editable": data.get("panel", "question") == "question",
        "raw_submitted_answer": raw.get(name, ""),
        "raw_submitted_answer_latex": raw.get(f"{name}-latex", ""),
        "parse_error": data.get("format_errors", {}).get(name),
        "custom_functions": "",
    }


def _question(config: Config, data: dict[str, Any]) -> str:
    index = sympy.latex(sympy.Symbol(config.index))
    context: dict[str, Any] = {
        config.limits: True,
        "integral": config.operator == "integral",
        "operator_latex": OPS[config.operator][0],
        "index_label": index,
        "body_field": _field(config, "body", "Operator body", 20, data),
    }
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


def _tex(config: Config, data: dict[str, Any]) -> str:
    raw = data.get("raw_submitted_answers", {})
    get = lambda c: raw.get(config.name(c), "?")
    index = sympy.latex(sympy.Symbol(config.index))
    op = OPS[config.operator][0]
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


def _correct_tex(config: Config, data: dict[str, Any]) -> str:
    structured = _correct(config, data)
    if structured is None:
        return ""
    return _structured_tex(config, structured)


def _structured_tex(config: Config, structured: dict[str, Any]) -> str:
    values = _values(config, structured)
    raw = {config.name(key): sympy.latex(value) for key, value in values.items()}
    return _tex(config, {"raw_submitted_answers": raw})


def _submitted_tex(config: Config, data: dict[str, Any]) -> str:
    structured = data.get("submitted_answers", {}).get(config.answer)
    if isinstance(structured, dict):
        return _structured_tex(config, structured)
    return _tex(config, data)


def render(element_html: str, data: dict[str, Any]) -> str:
    config = _config(element_html)
    panel = data.get("panel", "question")
    if panel == "question":
        return _question(config, data)
    if panel == "answer":
        return chevron.render(
            (HERE / "pl-big-operator-input-submission.mustache").read_text(),
            {"tex": _correct_tex(config, data)},
        )
    score = float(data.get("partial_scores", {}).get(config.answer, {}).get("score", 0))
    context: dict[str, Any] = {"tex": _submitted_tex(config, data)}
    if score >= 1:
        context["correct"] = True
    elif score <= 0:
        context["incorrect"] = True
    else:
        context["partial"] = round(score * 100)
    return chevron.render(
        (HERE / "pl-big-operator-input-submission.mustache").read_text(), context
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


def _blank(config: Config, data: dict[str, Any]) -> bool:
    raw = data.get("raw_submitted_answers", {})
    return all(not str(raw.get(config.name(c), "")).strip() for c in config.components)


def _parse_values(
    config: Config, data: dict[str, Any]
) -> dict[str, sympy.Basic] | None:
    raw = data.get("raw_submitted_answers", {})
    submitted = data.setdefault("submitted_answers", {})
    result = {}
    for component in config.components:
        name = config.name(component)
        variables = (
            tuple(dict.fromkeys((*config.variables, config.index)))
            if component == "body"
            else config.variables
        )
        try:
            source = str(raw.get(name, ""))
            if not source.strip():
                raise ValueError("No submitted answer.")
            value = _parse(source, variables)
            if _requires_set(config, component) and not isinstance(value, sympy.Set):
                raise ValueError("This field must be a set.")
            result[component] = value
            submitted[name] = _json(value)
        except Exception as exc:  # noqa: BLE001 -- PrairieLearn exposes several parser exception types.
            data.setdefault("format_errors", {})[name] = str(exc)
    return result if len(result) == len(config.components) else None


def parse(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    submitted = data.setdefault("submitted_answers", {})
    if _blank(config, data):
        submitted[config.answer] = "" if config.allow_blank else None
        if not config.allow_blank:
            data.setdefault("format_errors", {})[config.answer] = "No submitted answer."
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


def grade(element_html: str, data: dict[str, Any]) -> None:
    config = _config(element_html)
    correct_json = _correct(config, data)
    if correct_json is None:
        return
    if config.allow_blank and _blank(config, data):
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
