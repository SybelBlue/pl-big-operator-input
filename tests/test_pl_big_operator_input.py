from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import sympy

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pl_big_operator_input", HERE / "pl-big-operator-input.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def html(**attrs):
    values = {"answers-name": "op", "index-variable": "k", **attrs}
    text = " ".join(f'{key}="{value}"' for key, value in values.items())
    return f"<pl-big-operator-input {text}></pl-big-operator-input>"


def data(correct=None, raw=None, panel="question"):
    result = {
        "params": {},
        "correct_answers": {},
        "raw_submitted_answers": raw or {},
        "panel": panel,
    }
    if correct is not None:
        result["correct_answers"]["op"] = correct
    return result


@pytest.mark.parametrize(
    "operator,limits",
    [
        ("sum", "bounds"),
        ("product", "bounds"),
        ("integral", "bounds"),
        ("limit", "approach"),
        ("union", "domain"),
        ("intersection", "domain"),
        ("disjoint-union", "domain"),
        ("and", "domain"),
        ("or", "domain"),
        ("min", "domain"),
        ("max", "domain"),
    ],
)
def test_auto_limits(operator, limits):
    assert mod._config(html(operator=operator)).limits == limits


@pytest.mark.parametrize(
    "operator",
    [
        "sum",
        "product",
        "union",
        "intersection",
        "disjoint-union",
        "and",
        "or",
        "min",
        "max",
    ],
)
@pytest.mark.parametrize("limits", ["bounds", "domain"])
def test_flexible_operator_limit_forms(operator, limits):
    assert mod._config(html(operator=operator, limits=limits)).limits == limits


@pytest.mark.parametrize(
    "operator,limits",
    [
        ("integral", "domain"),
        ("integral", "approach"),
        ("limit", "bounds"),
        ("limit", "domain"),
        ("sum", "approach"),
    ],
)
def test_invalid_limit_forms(operator, limits):
    with pytest.raises(ValueError, match="does not support"):
        mod.prepare(html(operator=operator, limits=limits), data())


@pytest.mark.parametrize(
    "operator,correct",
    [
        ("sum", sympy.Sum(sympy.Symbol("k") ** 2, (sympy.Symbol("k"), 1, 4))),
        ("product", sympy.Product(sympy.Symbol("k"), (sympy.Symbol("k"), 1, 4))),
        ("integral", sympy.Integral(sympy.Symbol("k"), (sympy.Symbol("k"), 0, 1))),
    ],
)
def test_prepare_normalizes_binders(operator, correct):
    state = data(correct)
    mod.prepare(html(operator=operator), state)
    answer = state["correct_answers"]["op"]
    assert answer["_type"] == "operator_expression"
    assert answer["_version"] == 1
    assert answer["operator"] == operator
    assert set(answer) == {
        "_type",
        "_version",
        "operator",
        "limits",
        "index",
        "lower",
        "upper",
        "body",
    }
    assert all(
        answer[key]["_type"] == "sympy" for key in ("index", "lower", "upper", "body")
    )


@pytest.mark.parametrize(
    "direction,sympy_direction",
    [("two-sided", "+-"), ("from-left", "-"), ("from-right", "+")],
)
def test_limit_directions(direction, sympy_direction):
    k = sympy.Symbol("k")
    state = data(sympy.Limit(sympy.sin(k) / k, k, 0, dir=sympy_direction))
    mod.prepare(html(operator="limit", **{"limit-direction": direction}), state)
    assert state["correct_answers"]["op"]["direction"] == direction
    rendered = mod.render(
        html(operator="limit", **{"limit-direction": direction}), state
    )
    assert 'name="op-target"' in rendered and 'name="op-body"' in rendered
    assert "Approach target" in rendered and "Operator body" in rendered


def canonical(operator="union", limits="domain"):
    k = sympy.Symbol("k")
    return {
        "_type": "operator_expression",
        "_version": 1,
        "operator": operator,
        "limits": limits,
        "index": mod._json(k),
        "domain": mod._json(sympy.FiniteSet(1, 2)),
        "body": mod._json(sympy.FiniteSet(k)),
    }


def test_domain_structured_answer_and_rendering():
    state = data(canonical())
    mod.prepare(html(operator="union"), state)
    rendered = mod.render(html(operator="union"), state)
    assert r"\bigcup" in rendered
    assert 'name="op-domain"' in rendered and 'name="op-body"' in rendered
    assert 'name="op-start"' not in rendered
    assert "Index domain" in rendered and "Big operator expression input" in rendered


@pytest.mark.parametrize(
    "operator", ["union", "intersection", "disjoint-union", "and", "or", "min", "max"]
)
def test_variadic_operators_require_structured_answers(operator):
    with pytest.raises(TypeError, match="canonical structured"):
        mod.prepare(html(operator=operator), data(sympy.Integer(1)))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.pop("body"),
        lambda x: x.update(_version=2),
        lambda x: x.update(operator="intersection"),
        lambda x: x.update(index={"_type": "sympy", "_value": "j"}),
        lambda x: x.update(extra=1),
    ],
)
def test_rejects_malformed_structured_answers(mutation):
    answer = canonical()
    mutation(answer)
    with pytest.raises(ValueError):
        mod.prepare(html(operator="union"), data(answer))


def test_parse_only_relevant_fields_and_allows_index_in_body():
    state = data(
        raw={"op-domain": "FiniteSet(1,2)", "op-body": "FiniteSet(k)", "op-start": "99"}
    )
    mod.parse(html(operator="union"), state)
    answer = state["submitted_answers"]["op"]
    assert answer["limits"] == "domain" and "domain" in answer and "lower" not in answer
    assert "op-start" not in state["submitted_answers"]


def test_component_grading_weights_body():
    k = sympy.Symbol("k")
    correct = sympy.Sum(k**2, (k, 1, 4))
    state = data(correct, {"op-start": "1", "op-end": "5", "op-body": "k^2"})
    markup = html(**{"grading-method": "component", "body-relative-weight": "2"})
    mod.prepare(markup, state)
    mod.parse(markup, state)
    mod.grade(markup, state)
    assert state["partial_scores"]["op"]["score"] == pytest.approx(0.75)


@pytest.mark.parametrize("grading", ["exact", "equivalent"])
def test_exact_and_equivalent_grading(grading):
    k = sympy.Symbol("k")
    state = data(
        sympy.Sum(k**2, (k, 1, 4)), {"op-start": "1", "op-end": "4", "op-body": "k^2"}
    )
    markup = html(**{"grading-method": grading})
    mod.prepare(markup, state)
    mod.parse(markup, state)
    mod.grade(markup, state)
    assert state["partial_scores"]["op"] == {"score": 1.0, "weight": 1}


def test_allow_blank_and_independent_parse_errors():
    blank = data(raw={"op-start": "", "op-end": "", "op-body": ""})
    mod.parse(html(**{"allow-blank": "true"}), blank)
    assert blank["submitted_answers"]["op"] == ""
    broken = data(raw={"op-start": "1", "op-end": "@", "op-body": "k"})
    mod.parse(html(), broken)
    assert (
        "op-start" in broken["submitted_answers"]
        and "op-body" in broken["submitted_answers"]
    )
    assert (
        "op-end" in broken["format_errors"]
        and broken["submitted_answers"]["op"] is None
    )


def test_integral_and_submission_reconstruct_complete_notation():
    markup = html(operator="integral")
    state = data(
        raw={"op-start": "0", "op-end": "1", "op-body": "k^2"}, panel="submission"
    )
    state["partial_scores"] = {"op": {"score": 1}}
    rendered = mod.render(markup, state)
    assert r"\int_{0}^{1} k^2\,\mathrm{d}k" in rendered
    assert rendered.count("badge") == 1
