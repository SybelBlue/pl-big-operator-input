from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType as FrozenDict
from typing import Any, Final, Literal, Mapping, Sequence, cast, overload

import chevron  # type: ignore
import lxml.html as html
import prairielearn as pl  # type: ignore
import prairielearn.sympy_utils as psu  # type: ignore
import sympy

_CHILD_SUFFIXES: Final[Mapping[str, str]] = FrozenDict(
    {
        "start": "start",
        "end": "end",
        "summand": "summand",
    }
)
_REQUIRED_ATTRS: Final[tuple[str, ...]] = (
    "answers-name",
    "index-variable",
    "start-answer",
    "end-answer",
    "summand-answer",
)
_DEFAULT_VARIABLES: Final[str] = ""
_DEFAULT_INTEGRAL: Final[bool] = False
_DEFAULT_GRADING_SCHEME: Final[str] = "strict"
_DEFAULT_WEIGHT: Final[int] = 1
_DEFAULT_SUMMAND_RELATIVE_WEIGHT: Final[int] = 3
_OPTIONAL_ATTRS: Final[Mapping[str, str | bool | int]] = FrozenDict(
    {
        "variables": _DEFAULT_VARIABLES,
        "integral": _DEFAULT_INTEGRAL,
        "grading-scheme": _DEFAULT_GRADING_SCHEME,
        "weight": _DEFAULT_WEIGHT,
        "summand-relative-weight": _DEFAULT_SUMMAND_RELATIVE_WEIGHT,
    }
)
type GradingScheme = Literal["strict", "generous", "exact", "piecewise"]

_GRADING_SCHEMES: Final[frozenset[GradingScheme]] = frozenset(
    {"strict", "generous", "exact", "piecewise"}
)
_INTERACTIVE_TEMPLATE_NAME: Final[str] = "pl-sum-notation-input.mustache"
_TEX_TEMPLATE_NAME: Final[str] = "pl-sum-notation-input-submission.mustache"
_PARTIAL_TEMPLATE_NAMES: Final[Mapping[str, str]] = FrozenDict(
    {
        "bounds-math-field": "partials/bounds-math-field.mustache",
        "summand-math-field": "partials/summand-math-field.mustache",
    }
)


def _split_variables(variables: str) -> tuple[str, ...]:
    return tuple(
        variable
        for variable in (part.strip() for part in variables.split(","))
        if variable
    )


@dataclass(frozen=True, slots=True)
class Config:
    answers_name: str
    index_variable: str
    start_answer: str
    end_answer: str
    summand_answer: str
    variables: str
    integral: bool
    grading_scheme: GradingScheme
    weight: int
    summand_weight: int

    @property
    def summand_variables(self):
        return ", ".join(
            variable
            for variable in (self.index_variable, *_split_variables(self.variables))
            if variable
        )

    @property
    def start_answers_name(self) -> str:
        return f"{self.answers_name}-{_CHILD_SUFFIXES['start']}"

    @property
    def end_answers_name(self) -> str:
        return f"{self.answers_name}-{_CHILD_SUFFIXES['end']}"

    @property
    def summand_answers_name(self) -> str:
        return f"{self.answers_name}-{_CHILD_SUFFIXES['summand']}"

    def to_params(self) -> dict[str, str | int]:
        return {
            **asdict(self),
            "summand_answers_name": self.summand_answers_name,
            "start_answers_name": self.start_answers_name,
            "end_answers_name": self.end_answers_name,
        }


def _load_config_from_html(element_html: str) -> Config:
    element = html.fragment_fromstring(element_html)
    pl.check_attribs(element, list(_REQUIRED_ATTRS), list(_OPTIONAL_ATTRS))

    answers_name = pl.get_string_attrib(element, "answers-name")
    index_variable = pl.get_string_attrib(element, "index-variable")
    start_answer = pl.get_string_attrib(element, "start-answer")
    end_answer = pl.get_string_attrib(element, "end-answer")
    summand_answer = pl.get_string_attrib(element, "summand-answer")

    variables = pl.get_string_attrib(element, "variables", _DEFAULT_VARIABLES)
    normalized_variables = ", ".join(
        x for part in str(variables).split(",") if (x := part.strip()) != index_variable
    )

    integral = pl.get_boolean_attrib(element, "integral", _DEFAULT_INTEGRAL)
    if not isinstance(integral, bool):
        raise ValueError("Integral attribute must be a boolean")
    grading_scheme = pl.get_string_attrib(
        element, "grading-scheme", _DEFAULT_GRADING_SCHEME
    )
    if grading_scheme not in _GRADING_SCHEMES:
        raise ValueError(
            f'Invalid grading-scheme "{grading_scheme}". '
            f"Expected one of: {', '.join(sorted(_GRADING_SCHEMES))}."
        )
    grading_scheme = cast(GradingScheme, grading_scheme)

    weight = pl.get_integer_attrib(element, "weight", _DEFAULT_WEIGHT)
    summand_weight = pl.get_integer_attrib(
        element, "summand-relative-weight", _DEFAULT_SUMMAND_RELATIVE_WEIGHT
    )
    if not isinstance(weight, int) or not isinstance(summand_weight, int):
        raise ValueError("Weight attributes must be non-negative integers")
    if weight < 0 or summand_weight < 0:
        raise ValueError("Weight attributes must be non-negative integers")

    return Config(
        answers_name=answers_name,
        index_variable=index_variable,
        start_answer=str(start_answer),
        end_answer=str(end_answer),
        summand_answer=str(summand_answer),
        variables=normalized_variables,
        integral=integral,
        grading_scheme=grading_scheme,
        weight=weight,
        summand_weight=summand_weight,
    )


def _parse_sympy_expr(expr: str, variables: Sequence[str]):
    parsed = psu.try_parse_string_as_sympy(expr, variables)
    if isinstance(parsed, psu.SympyParseSuccess):
        return parsed.expr
    raise ValueError(parsed.error)


def _equiv(left: sympy.Basic, right: sympy.Basic) -> bool:
    return sympy.simplify(left - right) == 0  # type: ignore


def _try_load_config_from_data(data: pl.QuestionData) -> Config | None:
    config = data.get("params") if isinstance(data.get("params"), dict) else None
    requireds = tuple(Config.__slots__)
    if config and all(key in config for key in requireds):
        base = {k: config[k] for k in requireds}
        return Config(**base)
    return None


def _set_params(data: pl.QuestionData, config: Config) -> None:
    params = data.setdefault("params", {})
    params.update(config.to_params())

    data.setdefault("correct_answers", {}).update(
        {
            config.start_answers_name: config.start_answer,
            config.end_answers_name: config.end_answer,
            config.summand_answers_name: config.summand_answer,
        }
    )


@dataclass(slots=True, kw_only=True)
class ParseErrors:
    summand_err: str | None = None
    start_err: str | None = None
    end_err: str | None = None

    def __bool__(self):
        return (self.summand_err or self.start_err or self.end_err) is not None


def _into_sympy_sum(
    variables: Sequence[str],
    index_var: str,
    bounds: tuple[str, str],
    summand: str,
    integral: bool,
) -> sympy.Sum | ParseErrors:
    errors = ParseErrors()
    parsed_summand = psu.try_parse_string_as_sympy(summand, (index_var, *variables))
    if isinstance(parsed_summand, psu.SympyParseSuccess):
        smd = parsed_summand.expr
    else:
        errors.summand_err = parsed_summand.error

    parsed_start = psu.try_parse_string_as_sympy(bounds[0], variables)
    if isinstance(parsed_start, psu.SympyParseSuccess):
        start = parsed_start.expr
    else:
        errors.start_err = parsed_start.error

    parsed_end = psu.try_parse_string_as_sympy(bounds[1], variables)
    if isinstance(parsed_end, psu.SympyParseSuccess):
        end = parsed_end.expr
    else:
        errors.end_err = parsed_end.error

    if errors:
        return errors

    ctor = sympy.Integral if integral else sympy.Sum

    return ctor(smd, (sympy.Symbol(index_var), start, end))  # type: ignore


def _format_formula_editor_submission_for_sympy(
    sub: str,
    allow_trig: bool,
    variables: Sequence[str],
    custom_functions: list[str],
) -> str:
    """Normalize formula-editor output so SymPy can parse spaced-out names."""
    text = sub.replace("{:", "").replace(":}", "")
    known_tokens = _build_known_tokens(allow_trig, variables, custom_functions)
    text = "".join(_greek_transform(char) for char in text)
    text = _merge_spaced_tokens(text, known_tokens)
    text = _add_multiplication_spaces(text, known_tokens)
    return text


def _build_known_tokens(
    allow_trig: bool, variables: Sequence[str], custom_functions: list[str]
) -> list[str]:
    constants_class = psu._Constants
    tokens = [
        *psu.STANDARD_OPERATORS,
        *constants_class.functions.keys(),
        *custom_functions,
        *variables,
    ]
    if allow_trig:
        tokens += list(constants_class.trig_functions.keys())
    tokens += [
        psu.greek_unicode_transform(token)
        for token in tokens
        if psu.greek_unicode_transform(token) != token
    ]
    return [token for token in tokens if len(token) > 1]


def _greek_transform(text: str) -> str:
    transformed = psu.greek_unicode_transform(text)
    return (" " + " ".join(transformed) + " ") if transformed != text else text


def _merge_spaced_tokens(text: str, tokens: list[str]) -> str:
    result: list[str] = []
    i = 0
    n = len(text)
    spaced = [(token, " ".join(token), len(" ".join(token))) for token in tokens]
    spaced.sort(key=lambda x: -x[2])
    while i < n:
        matched = False
        for token, spaced_token, length in spaced:
            if text.startswith(spaced_token, i):
                result.append(token)
                i += length
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)


def _add_multiplication_spaces(text: str, protected_tokens: list[str]) -> str:
    protected_positions = set()
    for token in protected_tokens:
        if not re.search(r"\d", token):
            continue
        for match in re.finditer(re.escape(token), text):
            protected_positions.update(range(match.start(), match.end()))

    result: list[str] = []
    for i, char in enumerate(text):
        result.append(char)
        if i + 1 >= len(text):
            continue
        next_char = text[i + 1]
        next_position = i + 1
        if (
            char.isalpha()
            and next_char.isdigit()
            and next_position not in protected_positions
        ):
            result.append(" ")
    return "".join(result)


def _correct_sum(config: Config) -> sympy.Sum | ParseErrors:
    return _into_sympy_sum(
        _split_variables(config.variables),
        config.index_variable,
        (config.start_answer, config.end_answer),
        config.summand_answer,
        config.integral,
    )


def prepare(element_html: str, data: pl.QuestionData) -> None:
    config = _load_config_from_html(element_html)
    _set_params(data, config)

    correct = _correct_sum(config)
    if isinstance(correct, ParseErrors):
        raise ValueError("Error parsing correct answers") from SyntaxError(correct)

    data["correct_answers"][config.answers_name] = str(correct)


def _find_template_path(template_name: str | Path) -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        template_path = candidate / "elements" / "pl-sum-notation-input" / template_name
        if template_path.exists():
            return template_path
    raise FileNotFoundError(
        f"Could not locate {template_name} from the current working directory"
    )


def _render_question_template(config: Config, *, editable: bool) -> str:
    render_params = {
        "latex_symbol": r"\int" if config.integral else r"\sum",
        "index_label": sympy.latex(sympy.Symbol(config.index_variable)),
        "piecewise": config.grading_scheme == "piecewise",
        "upper_field": {
            "label": "largest index",
            "answers_name": config.end_answers_name,
            "variables": config.variables,
            "correct_answer": config.end_answer,
            "size": 6 if config.integral else 4,
        },
        "lower_field": {
            "label": "starting index",
            "answers_name": config.start_answers_name,
            "variables": config.variables,
            "correct_answer": config.start_answer,
            "size": 6,
            "prefix": (
                None
                if config.integral
                else rf"\({sympy.latex(sympy.Symbol(config.index_variable))} = \)"
            ),
        },
        "summand_field": {
            "label": "summand",
            "answers_name": config.summand_answers_name,
            "variables": config.summand_variables,
            "correct_answer": config.summand_answer,
            "size": 20,
        },
        **({"integral": True} if config.integral else {}),
        "editable": editable,
    }

    template = _find_template_path(_INTERACTIVE_TEMPLATE_NAME).read_text(
        encoding="utf-8"
    )
    partials = {
        name: _find_template_path(path).read_text(encoding="utf-8")
        for name, path in _PARTIAL_TEMPLATE_NAMES.items()
    }
    return chevron.render(template, render_params, partials_dict=partials)


def _render_tex_template(
    sum: sympy.Sum, *, trailing_score_badge: float | int | None
) -> str:
    render_params = {
        "tex": sympy.latex(sum).replace(r"\limits", "").replace(r"\,", r"\,\mathrm")
    }

    match trailing_score_badge:
        case int(x) | float(x) if math.isclose(x, 0.0):
            render_params["incorrect"] = True
        case int(x) | float(x) if math.isclose(x, 1.0):
            render_params["correct"] = True
        case int(x) | float(x):
            render_params["partial"] = f"{math.floor(100 * x)}"
        case None:
            pass

    template = _find_template_path(_TEX_TEMPLATE_NAME).read_text(encoding="utf-8")
    return chevron.render(template, render_params)


def render(element_html: str, data: pl.QuestionData) -> str:
    config = _try_load_config_from_data(data) or _load_config_from_html(element_html)

    match data["panel"]:
        case "answer":
            sum = _correct_sum(config)
            assert not isinstance(sum, ParseErrors)
            return _render_tex_template(sum, trailing_score_badge=None)
        case "submission" if not _getrec(data, "format_errors", config.answers_name):
            sum = _raw_submitted_sum(config, data)
            assert not isinstance(sum, ParseErrors)
            return _render_tex_template(
                sum,
                trailing_score_badge=_getrec(
                    data, "partial_scores", config.answers_name, "score", default=None
                ),
            )
        case _:
            return _render_question_template(
                config, editable=data.get("editable", True)
            )


def _raw_submitted_sum(config: Config, data: pl.QuestionData):
    raw_subs: dict[str, Any] = data["raw_submitted_answers"]
    return _into_sympy_sum(
        _split_variables(config.variables),
        config.index_variable,
        (raw_subs[config.start_answers_name], raw_subs[config.end_answers_name]),
        _format_formula_editor_submission_for_sympy(
            str(raw_subs[config.summand_answers_name]),
            allow_trig=True,
            variables=_split_variables(config.summand_variables),
            custom_functions=[],
        ),
        config.integral,
    )


def parse(element_html: str, data: pl.QuestionData):
    config = _try_load_config_from_data(data) or _load_config_from_html(element_html)

    submitted = _raw_submitted_sum(config, data)

    if isinstance(submitted, ParseErrors):
        ferrs = data.setdefault("format_errors", {})
        ferrs[config.answers_name] = "Your solution has formatting errors."
        if submitted.summand_err:
            ferrs[config.summand_answers_name] = submitted.summand_err
        if submitted.start_err:
            ferrs[config.start_answers_name] = submitted.start_err
        if submitted.end_err:
            ferrs[config.end_answers_name] = submitted.end_err
        return

    data["submitted_answers"][config.answers_name] = str(submitted)

    data["submitted_answers"][config.end_answers_name] = psu.sympy_to_json(
        cast(sympy.Expr | sympy.Set, submitted.limits[0][2])
    )
    data["submitted_answers"][config.start_answers_name] = psu.sympy_to_json(
        cast(sympy.Expr | sympy.Set, submitted.limits[0][1])
    )
    data["submitted_answers"][config.summand_answers_name] = psu.sympy_to_json(
        cast(sympy.Expr | sympy.Set, submitted.function)
    )


def _set_score(
    data: pl.QuestionData, answer_name: str, score: float, *, weight: int | None
) -> None:
    score_data = _setrec(data, "partial_scores", answer_name, default={})
    score_data["score"] = score
    if weight is not None:
        score_data["weight"] = weight


def _set_piecewise_partial_scores(config: Config, data: pl.QuestionData) -> float:
    raw_subs: dict[str, Any] = data["raw_submitted_answers"]
    raw_summand = _format_formula_editor_submission_for_sympy(
        str(raw_subs[config.summand_answers_name]),
        allow_trig=True,
        variables=_split_variables(config.summand_variables),
        custom_functions=[],
    )
    checks: Sequence[tuple[str, str, Sequence[str], int]] = (
        (
            config.start_answers_name,
            config.start_answer,
            _split_variables(config.variables),
            1,
        ),
        (
            config.end_answers_name,
            config.end_answer,
            _split_variables(config.variables),
            1,
        ),
        (
            config.summand_answers_name,
            config.summand_answer,
            _split_variables(config.summand_variables),
            config.summand_weight,
        ),
    )

    out, denom = 0.0, 0
    for subanswer_name, correct_src, variables, weight in checks:
        correct = _parse_sympy_expr(str(correct_src), variables)
        submitted_src = (
            raw_summand
            if subanswer_name == config.summand_answers_name
            else str(raw_subs[subanswer_name])
        )
        submitted = _parse_sympy_expr(str(submitted_src), variables)
        raw = 1.0 if _equiv(correct, submitted) else 0.0
        _set_score(data, subanswer_name, raw, weight=0)
        out += weight * raw
        denom += weight

    return denom and (out / denom)


def grade(element_html: str, data: pl.QuestionData):
    config = _try_load_config_from_data(data) or _load_config_from_html(element_html)

    submitted = _raw_submitted_sum(config, data)
    assert not isinstance(submitted, ParseErrors)

    correct = _correct_sum(config)
    assert not isinstance(correct, ParseErrors)

    def set_score(score):
        return _set_score(data, config.answers_name, score, weight=config.weight)

    if config.grading_scheme == "piecewise":
        score = _set_piecewise_partial_scores(config, data)
        return set_score(score)

    if submitted == correct:  # type: ignore
        return set_score(1.0)

    if config.grading_scheme == "exact":
        return set_score(0.0)

    # if the index was off by a translation, full credit
    _, correct_start, correct_end = correct.limits[0]
    _, submitted_start, submitted_end = submitted.limits[0]

    index_sym = sympy.Symbol(config.index_variable)

    if _equiv(
        correct_start - submitted_start,  # type: ignore
        correct_end - submitted_end,  # type: ignore
    ) and _equiv(
        correct.function.subs(index_sym, index_sym + (correct_start - submitted_start)),  # type: ignore
        submitted.function,
    ):
        return set_score(1.0)

    # if the computed final value was correct, partial credit
    if _equiv(submitted, correct):  # type: ignore
        return set_score(0.5 if config.grading_scheme == "strict" else 1.0)

    return set_score(0.0)


def _getrec(data: Any | None, *keys: Any, default: Any = None) -> Any:
    if data is None:
        return None

    curr = data
    for i, k in enumerate(keys):
        if not isinstance(curr, Mapping):
            key_chain = "][".join(map(repr, keys[:i]))
            prefix = f"data[{key_chain}]" if i else "data"
            raise TypeError(
                f"{prefix} (type {type(curr).__name__}) cannot be indexed by {repr(k)}"
            )
        if k not in curr:
            return default
        curr = curr[k]

    return curr


@overload
def _setrec[V](dict: Any, k0: str, *keys: str, v: V) -> V: ...
@overload
def _setrec[V](dict: Any, k0: str, *keys: str, default: V) -> V | Any: ...
def _setrec[V](
    dict: Any,
    k0: str,
    *keys: str,
    v: V | None = None,
    default: V | None = None,
) -> V | Any:
    """Set a nested value, creating intermediate dictionaries as needed.

    If ``default`` is used instead of ``v``, then the value will not replace
    an existing value.
    """
    ks = [k0, *keys]
    last = ks.pop()
    d = dict
    for k in ks:
        d = d.setdefault(k, {})
    if default is not None:
        return d.setdefault(last, default)
    d[last] = v
    return v
