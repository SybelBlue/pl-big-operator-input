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
FUNCTION_BINDERS = {
    "union": "Union",
    "intersection": "Intersection",
    "disjoint-union": "DisjointUnion",
    "and": "And",
    "or": "Or",
    "min": "Min",
    "max": "Max",
}
STRING_OPERATORS = {
    "Sum": "sum",
    "Product": "product",
    "Integral": "integral",
    "Limit": "limit",
    **{name: operator for operator, name in FUNCTION_BINDERS.items()},
}
OPERATOR_FUNCTIONS = {
    operator: function for function, operator in STRING_OPERATORS.items()
}
OPERATOR_FUNCTIONS["custom"] = "Custom"
type LimitFormat = Literal["bounds", "domain", "approach"]
type Component = Literal["lower", "upper", "domain", "target", "body"]
type AllowedBlank = Literal["none", "limits", "body", "all"]
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
    allowed_blank: AllowedBlank
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


def _raw_correct_answer(
    answer: str,
    correct_attribute: str | None,
    correct_components: dict[Component, str],
    data: Any | None,
) -> Any:
    if correct_components:
        return correct_components
    if correct_attribute is not None:
        return correct_attribute
    if data is None:
        return None
    return data.get("correct_answers", {}).get(answer)


def _binder_limits(value: Any) -> LimitFormat | None:
    if isinstance(value, sympy.Limit):
        return "approach"
    if isinstance(value, (sympy.Sum, sympy.Product, sympy.Integral)):
        if len(value.limits) != 1:
            return None
        binder_length = len(cast(Sequence[Any], value.limits[0]))
        if binder_length == 2:
            return "domain"
        if binder_length == 3:
            return "bounds"
    return None


def _split_top_level(source: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for position, character in enumerate(source):
        if quote is not None:
            if character == quote and (position == 0 or source[position - 1] != "\\"):
                quote = None
        elif character in {"'", '"'}:
            quote = character
        elif character in "([{":
            depth += 1
        elif character in ")]}":
            depth -= 1
        elif character == "," and depth == 0:
            parts.append(source[start:position].strip())
            start = position + 1
    parts.append(source[start:].strip())
    return parts


def _formatted_call(source: str, function_name: str) -> tuple[str, list[str]] | None:
    match = re.fullmatch(
        rf"\s*{re.escape(function_name)}\s*\((.*)\)\s*", source, re.DOTALL
    )
    if match is None:
        return None
    arguments = _split_top_level(match.group(1))
    if len(arguments) != 2:
        return None
    limits_source = arguments[1].strip()
    if not (limits_source.startswith("(") and limits_source.endswith(")")):
        return None
    limits = _split_top_level(limits_source[1:-1])
    return arguments[0], limits


def _formatted_direction(limits: list[str]) -> str | None:
    if len(limits) != 3:
        return None
    source = limits[2].strip()
    if len(source) < 2 or source[0] not in {"'", '"'} or source[-1] != source[0]:
        return None
    return source[1:-1]


def _symbol_name(value: Any) -> str | None:
    return str(value) if isinstance(value, sympy.Symbol) else None


def _binder_index(value: Any) -> str | None:
    if isinstance(value, sympy.Limit):
        return _symbol_name(value.args[1])
    if (
        isinstance(value, (sympy.Sum, sympy.Product, sympy.Integral))
        and len(value.limits) == 1
    ):
        return _symbol_name(value.limits[0][0])  # type: ignore
    return None


def _infer_spec(
    raw: Any,
) -> tuple[str | None, LimitFormat | None, str | None]:
    if isinstance(raw, str):
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(", raw)
        function = match.group(1) if match else None
        parsed_operator = (
            "custom" if function == "Custom" else STRING_OPERATORS.get(function or "")
        )
        if parsed_operator is None:
            return None, None, None
        operator = parsed_operator
        formatted = _formatted_call(raw, OPERATOR_FUNCTIONS[parsed_operator])
        if formatted is not None:
            try:
                index = _symbol_name(sympy.sympify(formatted[1][0]))
            except (IndexError, sympy.SympifyError, TypeError):
                index = None
            if parsed_operator == "limit":
                return operator, "approach", index
            limit_count = len(formatted[1])
            if limit_count == 2:
                return operator, "domain", index
            if limit_count == 3:
                return (
                    operator,
                    "approach"
                    if _formatted_direction(formatted[1]) is not None
                    else "bounds",
                    index,
                )
            return operator, None, index
        try:
            value = _decode(raw)
        except Exception:  # noqa: BLE001 -- malformed author strings fail during normalization.
            return operator, None, None
        return operator, _binder_limits(value), _binder_index(value)
    if not isinstance(raw, dict):
        return None, None, None
    if raw.get("_type") == "operator_expression":
        operator = raw.get("operator")
        limits = raw.get("limits")
        try:
            index = _symbol_name(_decode(raw.get("index")))
        except Exception:  # noqa: BLE001 -- malformed canonical answers fail later.
            index = None
        return (
            operator if operator in OPS else None,
            cast(LimitFormat, limits) if limits in COMPONENT_MAP else None,
            index,
        )
    if raw.get("_type") == "sympy":
        try:
            value = _decode(raw)
        except Exception:  # noqa: BLE001 -- malformed author JSON can fail in several decoders.
            return None, None, None
        for operator, expected in {
            "sum": sympy.Sum,
            "product": sympy.Product,
            "integral": sympy.Integral,
            "limit": sympy.Limit,
        }.items():
            if isinstance(value, expected):
                return operator, _binder_limits(value), _binder_index(value)
    return None, None, None


def _infer_direction(raw: Any, operator: str) -> str | None:
    if isinstance(raw, dict):
        if raw.get("_type") == "operator_expression":
            direction = raw.get("direction")
            return direction if direction in DIRECTIONS else None
        if raw.get("_type") == "sympy":
            try:
                value = _decode(raw)
            except Exception:  # noqa: BLE001 -- malformed author JSON is validated later.
                return None
            if isinstance(value, sympy.Limit):
                return {value: key for key, value in DIRECTIONS.items()}.get(
                    str(value.args[3])
                )
        return None
    if not isinstance(raw, str):
        return None
    function_name = OPERATOR_FUNCTIONS.get(operator)
    if function_name is None:
        return None
    formatted = _formatted_call(raw, function_name)
    if formatted is None:
        try:
            value = _decode(raw)
        except Exception:  # noqa: BLE001 -- malformed author strings fail during normalization.
            return None
        if isinstance(value, sympy.Limit):
            return {value: key for key, value in DIRECTIONS.items()}.get(
                str(value.args[3])
            )
        return None
    if len(formatted[1]) != 3:
        return None
    direction = _formatted_direction(formatted[1])
    if direction is None:
        return None
    return {value: key for key, value in DIRECTIONS.items()}.get(direction)


def _config(html: str, data: Any | None = None) -> Config:
    element = lxml.html.fragment_fromstring(html)
    answer = pl.get_string_attrib(element, "answers-name", None)
    if answer is None or not answer.strip():
        raise ValueError('Required attribute "answers-name" missing')
    answer = answer.strip()
    explicit_index = pl.get_string_attrib(element, "index-variable", None)
    explicit_index = explicit_index.strip() if explicit_index else None
    explicit_operator = pl.get_string_attrib(element, "operator", None)
    if explicit_operator is not None:
        explicit_operator = explicit_operator[:1].lower() + explicit_operator[1:]
    custom_latex = pl.get_string_attrib(element, "operator-latex", None)
    correct_attribute = pl.get_string_attrib(element, "correct-answer", None)
    supplied_components: dict[Component, str] = {
        component: value
        for component, attribute in CORRECT_COMPONENT_ATTRIBUTES.items()
        if (value := pl.get_string_attrib(element, attribute, None)) is not None
    }
    raw_correct = _raw_correct_answer(
        answer, correct_attribute, supplied_components, data
    )
    inferred_operator, inferred_limits, inferred_index = None, None, None
    if not supplied_components and isinstance(raw_correct, (str, dict)):
        inferred_operator, inferred_limits, inferred_index = _infer_spec(raw_correct)
    index = explicit_index or inferred_index
    if index is None:
        raise ValueError(
            'The "index-variable" attribute is required; it cannot be inferred from the provided correct-answer.'
        )
    if explicit_operator is None and custom_latex is None and inferred_operator is None:
        raise ValueError(
            'The "operator" attribute is required; it cannot be inferred from the provided correct-answer.'
        )
    if (
        operator := (
            explicit_operator
            or ("custom" if custom_latex is not None else None)
            or inferred_operator
        )
    ) is None:
        raise ValueError(
            'The "operator" attribute is required; it cannot be inferred from the provided correct-answer.'
        )
    if operator not in {*OPS, "custom"}:
        raise ValueError(f'Unknown operator "{operator}".')
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
    if limits == "auto":
        if inferred_operator == operator and inferred_limits:
            limits = inferred_limits
        elif operator == "custom":
            raise ValueError(
                'Custom operators require a parseable whole correct answer or explicit limits="bounds", limits="domain", or limits="approach".'
            )
        else:
            limits = OPS[operator][1]
    allowed = (
        {"bounds", "domain", "approach"}
        if operator == "custom"
        else {"bounds", "domain"}
        if operator in FLEXIBLE
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
    direction_attribute = pl.get_string_attrib(element, "limit-direction", None)
    direction = (
        direction_attribute
        or (
            _infer_direction(raw_correct, operator)
            if limits == "approach" and not supplied_components
            else None
        )
        or "two-sided"
    )
    if direction not in DIRECTIONS:
        raise ValueError(f'Unknown limit-direction "{direction}".')
    variables = pl.get_string_attrib(element, "variables", "") or ""
    allowed_blank = pl.get_string_attrib(element, "allowed-blank", "none") or "none"
    if allowed_blank not in {"none", "limits", "body", "all"}:
        raise ValueError(
            'Attribute "allowed-blank" must be none, limits, body, or all.'
        )
    components = COMPONENT_MAP[cast(LimitFormat, limits)]
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
    if correct_attribute is not None and supplied_components:
        raise ValueError(
            'Use either "correct-answer" or component correct-answer attributes, not both.'
        )
    if (
        operator == "custom"
        and (correct_attribute is not None or supplied_components)
        and grading not in {"exact", "component"}
    ):
        raise ValueError(
            'Custom operators with a correct answer require grading-method="exact" or "component".'
        )
    return Config(
        answer,
        operator,
        operator_latex,
        cast(LimitFormat, limits),
        index,
        tuple(x.strip() for x in variables.split(",") if x.strip()),
        direction,
        cast(AllowedBlank, allowed_blank),
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
        if _requires_set(config, component) and not _is_set_input(parsed):
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
    expected_length = 3 if config.limits == "bounds" else 2
    if len(value.limits) != 1 or len(value.limits[0]) != expected_length:
        raise ValueError(
            f'Correct answer for limits="{config.limits}" must have exactly one '
            f"{expected_length}-item limits tuple."
        )
    variable, *binder_values = value.limits[0]
    if variable != index:
        raise ValueError("Correct answer index does not match index-variable.")
    if config.limits == "bounds":
        return _canonical(
            config,
            {
                "lower": binder_values[0],
                "upper": binder_values[1],
                "body": value.function,
            },
        )
    return _canonical(config, {"domain": binder_values[0], "body": value.function})


def _formatted_answer(config: Config, source: str) -> dict[str, Any] | None:
    formatted = _formatted_call(source, OPERATOR_FUNCTIONS[config.operator])
    if formatted is None:
        return None
    body_source, limits = formatted
    expected_length = 2 if config.limits == "domain" else 3
    if len(limits) != expected_length:
        raise ValueError(
            f'Correct answer for limits="{config.limits}" requires a '
            f"{expected_length}-item limits tuple."
        )
    try:
        body = _parse(
            body_source, tuple(dict.fromkeys((*config.variables, config.index)))
        )
        index = sympy.sympify(limits[0])
    except (sympy.SympifyError, TypeError, ValueError) as exc:
        raise ValueError("The correct answer contains invalid SymPy data.") from exc
    if index != sympy.Symbol(config.index):
        raise ValueError("Correct answer index does not match index-variable.")
    if config.limits == "approach":
        direction = _formatted_direction(limits)
        if direction is None:
            raise ValueError('Limit direction must be "+", "-", or "+-".')
        public_direction = {value: key for key, value in DIRECTIONS.items()}.get(
            direction
        )
        if public_direction is None:
            raise ValueError('Limit direction must be "+", "-", or "+-".')
        if public_direction != config.direction:
            raise ValueError("Correct answer direction does not match limit-direction.")
        try:
            target = _parse(limits[1], config.variables)
        except (sympy.SympifyError, TypeError, ValueError) as exc:
            raise ValueError("The correct answer contains invalid SymPy data.") from exc
        return _canonical(config, {"target": target, "body": body})
    if config.limits == "bounds":
        try:
            lower = _parse(limits[1], config.variables)
            upper = _parse(limits[2], config.variables)
        except (sympy.SympifyError, TypeError, ValueError) as exc:
            raise ValueError("The correct answer contains invalid SymPy data.") from exc
        return _canonical(config, {"lower": lower, "upper": upper, "body": body})
    try:
        domain = _parse(limits[1], config.variables)
    except (sympy.SympifyError, TypeError, ValueError) as exc:
        raise ValueError("The correct answer contains invalid SymPy data.") from exc
    return _canonical(config, {"domain": domain, "body": body})


def _correct(config: Config, data: pl.QuestionData) -> dict[str, Any] | None:
    raw = _raw_correct_answer(
        config.answer,
        config.correct_attribute,
        dict(config.correct_components),
        data,
    )
    if (
        config.operator == "custom"
        and raw is not None
        and config.grading not in {"exact", "component"}
    ):
        raise ValueError(
            'Custom operators with a correct answer require grading-method="exact" or "component".'
        )
    if raw is None:
        return None
    if isinstance(raw, dict) and raw.get("_type") == "operator_expression":  # type: ignore
        return _structured(config, raw)  # type: ignore
    if config.correct_components:
        return _component_values(config, cast(dict[Component, Any], raw))
    if isinstance(raw, str):
        converted = _formatted_answer(config, raw)
        if converted is not None:
            return converted
    value = _decode(raw)
    converted = _binder(config, value)
    if converted is not None:
        return converted
    raise TypeError(
        f'Correct answer "{config.answer}" must be a matching formatted object or canonical structured dictionary.'
    )


def prepare(element_html: str, data: pl.QuestionData) -> None:
    config = _config(element_html, data)
    correct = _correct(config, data)
    if correct is not None:
        data.setdefault("correct_answers", {})[config.answer] = correct


def _field(
    config: Config,
    component: str,
    label: str,
    size: int,
    data: dict[str, Any] | pl.QuestionData,
    prefix: str | None = None,
    suffix: str | None = None,
    score: float | None = None,
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
        show_score=config.grading == "component",
        prefix=prefix,
        suffix=suffix,
    )
    return {
        "html": symbolic_input_adapter.render(
            field_markup, data, aria_label=label, score=score
        ),
    }


def _component_scores(config: Config, data: pl.QuestionData) -> dict[Component, float]:
    if config.grading != "component" or config.answer not in data.get(
        "partial_scores", {}
    ):
        return {}
    submitted_json = data.get("submitted_answers", {}).get(config.answer)
    correct_json = _correct(config, data)
    if not isinstance(submitted_json, dict) or correct_json is None:
        return {}
    submitted = _values(config, submitted_json)
    correct = _values(config, correct_json)
    return {
        component: float(submitted[component] == correct[component])
        for component in config.components
    }


def _question(config: Config, data: pl.QuestionData) -> str:
    index = sympy.latex(sympy.Symbol(config.index))
    component_scores = _component_scores(config, data)
    context: dict[str, Any] = {
        config.limits: True,
        "integral": config.operator == "integral",
        "operator_latex": config.operator_latex,
        "index_label": index,
        "body_field": _field(
            config,
            "body",
            "Operator body",
            16,
            data,
            score=component_scores.get("body"),
        ),
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
            score=component_scores.get("lower"),
        )
        context["upper_field"] = _field(
            config, "upper", "Upper bound", 7, data, score=component_scores.get("upper")
        )
    elif config.limits == "domain":
        context["annotation_field"] = _field(
            config,
            "domain",
            "Integration domain" if config.operator == "integral" else "Index domain",
            10,
            data,
            None if config.operator == "integral" else rf"\({index} \in \)",
            score=component_scores.get("domain"),
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
            score=component_scores.get("target"),
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
    config = _config(element_html, data)
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


def _component_allows_blank(config: Config, component: Component) -> bool:
    return config.allowed_blank == "all" or (
        config.allowed_blank == "body"
        if component == "body"
        else config.allowed_blank == "limits"
    )


def _parse_values(
    config: Config, data: dict[str, Any]
) -> dict[str, sympy.Basic] | None:
    submitted = data.setdefault("submitted_answers", {})
    result: dict[str, sympy.Basic] = {}
    raw_answers = data.get("raw_submitted_answers", {})
    for component in config.components:
        name = config.name(component)
        if not str(raw_answers.get(name, "")).strip() and _component_allows_blank(
            config, component
        ):
            submitted[name] = ""
            continue
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
    config = _config(element_html, data)
    submitted = data.setdefault("submitted_answers", {})
    raw = data.get("raw_submitted_answers", {})
    blank_components: list[Component] = [
        component
        for component in config.components
        if not str(raw.get(config.name(component), "")).strip()
    ]
    if blank_components and all(
        _component_allows_blank(config, component) for component in blank_components
    ):
        _parse_values(config, data)
        errors = data.get("format_errors", {})
        has_component_error = any(
            config.name(component) in errors for component in config.components
        )
        submitted[config.answer] = None if has_component_error else ""
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
    config = _config(element_html, data)
    correct_json = _correct(config, data)
    if correct_json is None:
        return
    if data.get("submitted_answers", {}).get(config.answer) == "":
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
