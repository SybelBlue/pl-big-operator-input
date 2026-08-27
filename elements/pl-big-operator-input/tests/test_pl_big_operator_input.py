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
        "integral",
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
    "operator,correct",
    [
        ("sum", sympy.Sum(sympy.Symbol("k") ** 2, (sympy.Symbol("k"), 1, 4))),
        ("product", sympy.Product(sympy.Symbol("k"), (sympy.Symbol("k"), 1, 4))),
        ("integral", sympy.Integral(sympy.Symbol("k"), (sympy.Symbol("k"), 0, 1))),
    ],
)
def test_prepare_decodes_serialized_binders_without_interval_parsing(operator, correct):
    state = data(mod.psu.sympy_to_json(correct))
    mod.prepare(html(operator=operator), state)
    assert state["correct_answers"]["op"]["operator"] == operator


@pytest.mark.parametrize(
    "direction,sympy_direction",
    [("two-sided", "+-"), ("from-left", "-"), ("from-right", "+")],
)
def test_limit_directions(direction, sympy_direction):
    k = sympy.Symbol("k")
    state = data(sympy.Limit(sympy.sin(k) / k, k, 0, dir=sympy_direction))  # type: ignore
    mod.prepare(html(operator="limit", **{"limit-direction": direction}), state)
    assert state["correct_answers"]["op"]["direction"] == direction
    rendered = mod.render(
        html(operator="limit", **{"limit-direction": direction}), state
    )
    assert 'name="op-target"' in rendered and 'name="op-body"' in rendered
    assert "Approach target" in rendered and "Operator body" in rendered
    if direction == "two-sided":
        assert "pl-big-operator-input__suffix" not in rendered
    else:
        assert 'class="input-group-text pl-big-operator-input__suffix"' in rendered
        assert ("−" if direction == "from-left" else "+") in rendered


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


def test_prepare_parses_basic_component_correct_answer_strings():
    state = data()
    markup = html(
        variables="n",
        **{
            "correct-answer-start": "1",
            "correct-answer-end": "n",
            "correct-answer-body": "k^2 + sin(n)",
        },
    )

    mod.prepare(markup, state)

    answer = state["correct_answers"]["op"]
    values = mod._values(mod._config(markup), answer)
    k, n = sympy.symbols("k n")
    assert values == {"lower": 1, "upper": n, "body": k**2 + sympy.sin(n)}


def test_prepare_parses_set_component_correct_answer_strings():
    state = data()
    markup = html(
        operator="union",
        **{"correct-answer-domain": "{1, 2}", "correct-answer-body": "{k}"},
    )

    mod.prepare(markup, state)

    answer = state["correct_answers"]["op"]
    values = mod._values(mod._config(markup), answer)
    k = sympy.Symbol("k")
    assert values == {
        "domain": sympy.FiniteSet(1, 2),
        "body": sympy.FiniteSet(k),
    }


def test_prepare_component_correct_answer_requires_every_visible_attribute():
    with pytest.raises(ValueError, match="missing correct-answer-end"):
        mod.prepare(
            html(**{"correct-answer-start": "1", "correct-answer-body": "k"}),
            data(),
        )


def test_prepare_component_correct_answer_enforces_set_fields():
    with pytest.raises(ValueError, match='component "domain" must be a set'):
        mod.prepare(
            html(
                operator="union",
                **{"correct-answer-domain": "1", "correct-answer-body": "{k}"},
            ),
            data(),
        )


def test_prepare_rejects_irrelevant_component_correct_answer_attribute():
    with pytest.raises(ValueError, match="cannot be used"):
        mod.prepare(html(**{"correct-answer-domain": "{1}"}), data())


def test_prepare_rejects_combined_whole_and_component_correct_answers():
    with pytest.raises(ValueError, match="either"):
        mod.prepare(
            html(
                **{
                    "correct-answer": "Sum(k, (k, 1, 2))",
                    "correct-answer-start": "1",
                    "correct-answer-end": "2",
                    "correct-answer-body": "k",
                }
            ),
            data(),
        )


@pytest.mark.parametrize("operator", ["min", "max"])
def test_min_max_correct_answer_rendering(operator):
    answer = canonical(operator=operator)
    answer["body"] = mod._json(sympy.Symbol("k") ** 2)
    state = data(answer, panel="answer")

    rendered = mod.render(html(operator=operator), state)

    assert rf"\{operator}_{{k\in \left\{{1, 2\right\}}}} k^{{2}}" in rendered
    assert ">?</span>" not in rendered
    assert "badge" not in rendered


@pytest.mark.parametrize("operator", ["min", "max"])
def test_min_max_answer_rendering_uses_prepared_answer(operator):
    answer = canonical(operator=operator)
    answer["body"] = mod._json(sympy.Symbol("k") ** 2)
    state = data(answer)
    markup = html(operator=operator)
    mod.prepare(markup, state)
    state["correct_answers"].clear()
    state["panel"] = "answer"

    rendered = mod.render(markup, state)

    assert rf"\{operator}_{{k\in \left\{{1, 2\right\}}}} k^{{2}}" in rendered
    assert "?" not in rendered
    assert "badge" not in rendered


@pytest.mark.parametrize("operator", ["min", "max"])
def test_min_max_answer_panel_never_renders_question_mark_fallback(operator):
    rendered = mod.render(html(operator=operator), data(panel="answer"))

    assert "?" not in rendered


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


@pytest.mark.parametrize(
    "operator", ["sum", "product", "integral", "union", "and", "min"]
)
def test_domain_fields_reject_non_sets_at_parse_time(operator):
    state = data(raw={"op-domain": "1", "op-body": "FiniteSet(k)"})
    mod.parse(html(operator=operator, limits="domain"), state)

    assert state["submitted_answers"]["op"] is None
    assert state["format_errors"]["op-domain"] == "This field must be a set."


@pytest.mark.parametrize("operator", ["union", "intersection", "disjoint-union"])
def test_set_combinator_bodies_reject_non_sets_at_parse_time(operator):
    state = data(raw={"op-domain": "FiniteSet(1, 2)", "op-body": "k"})
    mod.parse(html(operator=operator), state)

    assert state["submitted_answers"]["op"] is None
    assert state["format_errors"]["op-body"] == "This field must be a set."


@pytest.mark.parametrize(
    ("invalid_field", "valid_field"),
    [("op-domain", "op-body"), ("op-body", "op-domain")],
)
def test_parse_errors_are_rendered_with_their_fields(invalid_field, valid_field):
    raw = {"op-domain": "FiniteSet(1, 2)", "op-body": "FiniteSet(k)"}
    raw[invalid_field] = "1"
    state = data(raw=raw)
    markup = html(operator="union")
    mod.parse(markup, state)

    rendered = mod.render(markup, state)
    error_id = f"big-operator-input-error-{invalid_field}"
    assert f'aria-describedby="{error_id}"' in rendered
    assert f'id="{error_id}"' in rendered
    assert (
        '<span id="' + error_id + '" class="invalid-feedback d-block" role="alert">'
        in rendered
    )
    assert "This field must be a set." in rendered
    assert f"big-operator-input-error-{valid_field}" not in rendered


def test_partially_blank_submission_has_a_descriptive_field_error():
    state = data(raw={"op-domain": "FiniteSet(1, 2)", "op-body": ""})
    markup = html(operator="union")
    mod.parse(markup, state)

    assert state["format_errors"]["op-body"] == "No submitted answer."
    rendered = mod.render(markup, state)
    assert ">No submitted answer.</span>" in rendered
    assert ">0</span>" not in rendered


def test_wholly_blank_required_submission_marks_every_field_invalid():
    state = data(raw={"op-start": "", "op-end": "", "op-body": ""})
    markup = html()

    mod.parse(markup, state)

    assert state["submitted_answers"]["op"] is None
    assert state["format_errors"] == {
        "op-start": "No submitted answer.",
        "op-end": "No submitted answer.",
        "op-body": "No submitted answer.",
    }
    rendered = mod.render(markup, state)
    assert rendered.count(">No submitted answer.</span>") == 3


def test_initial_latex_is_stored_outside_math_fields():
    state = data(
        raw={
            "op-domain-latex": r"\emptyset",
            "op-body-latex": r"\emptyset",
        }
    )

    document = mod.lxml.html.fragment_fromstring(
        mod.render(html(operator="union"), state)
    )

    for name in ("op-domain", "op-body"):
        math_field = document.get_element_by_id(f"big-operator-input-{name}")
        latex_input = document.get_element_by_id(f"big-operator-input-latex-{name}")
        assert (math_field.text or "").strip() == ""
        assert latex_input.get("value") == r"\emptyset"


def test_non_set_combinator_bodies_still_accept_expressions():
    state = data(raw={"op-domain": "FiniteSet(1, 2)", "op-body": "k"})
    mod.parse(html(operator="and"), state)

    assert state["submitted_answers"]["op"] is not None
    assert "format_errors" not in state


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


def test_allow_blank_submission_is_gradable_as_incorrect():
    k = sympy.Symbol("k")
    state = data(sympy.Sum(k**2, (k, 1, 4)))
    markup = html(**{"allow-blank": "true"})

    mod.prepare(markup, state)
    mod.parse(markup, state)
    mod.grade(markup, state)

    assert "format_errors" not in state
    assert state["submitted_answers"]["op"] == ""
    assert state["partial_scores"]["op"] == {"score": 0.0, "weight": 1}


def test_integral_and_submission_reconstruct_complete_notation():
    markup = html(operator="integral")
    state = data(
        raw={"op-start": "0", "op-end": "1", "op-body": "k^2"}, panel="submission"
    )
    state["partial_scores"] = {"op": {"score": 1}}
    rendered = mod.render(markup, state)
    assert r"\int_{0}^{1} k^2\,\mathrm{d}k" in rendered
    assert rendered.count("badge") == 1


@pytest.mark.parametrize(
    ("score", "badge_class", "label"),
    [
        (1, "text-bg-success", "100%"),
        (0.4, "text-bg-warning", "40%"),
        (0, "text-bg-danger", "0%"),
    ],
)
def test_question_view_shows_score_badge(score, badge_class, label):
    state = data()
    state["partial_scores"] = {"op": {"score": score}}

    rendered = mod.render(html(), state)

    assert rendered.count("badge") == 1
    assert badge_class in rendered
    assert label in rendered


def test_set_submission_renders_literal_braces():
    markup = html(operator="union")
    state = data(raw={"op-domain": "{1, 2}", "op-body": "{k}"})
    mod.parse(markup, state)
    state["panel"] = "submission"

    rendered = mod.render(markup, state)

    assert r"\bigcup_{k\in \left\{1, 2\right\}} \left\{k\right\}" in rendered


def test_integral_bounds_use_a_column_between_operator_and_body():
    rendered = mod.render(html(operator="integral"), data())
    assert "pl-big-operator-input__operator-stack--integral" in rendered
    operator_position = rendered.index('pl-big-operator-input__operator"')
    limits_position = rendered.index('pl-big-operator-input__limits"')
    body_position = rendered.index('pl-big-operator-input__body"')
    assert operator_position < limits_position < body_position
    css = (HERE / "pl-big-operator-input.css").read_text()
    assert "operator-stack--integral {\n  flex-direction: row" in css
    assert ".pl-big-operator-input__limits {" in css
    assert "flex-direction: column" in css
    assert ".pl-big-operator-input__limits > .pl-big-operator-input__upper" in css
    assert ".pl-big-operator-input__limits > .pl-big-operator-input__lower" in css


def test_domain_integral_renders_only_a_subscript_field_between_operator_and_body():
    markup = html(operator="integral", limits="domain")
    rendered = mod.render(markup, data())
    operator_position = rendered.index('pl-big-operator-input__operator"')
    domain_position = rendered.index('name="op-domain"')
    body_position = rendered.index('name="op-body"')
    assert operator_position < domain_position < body_position
    assert 'name="op-start"' not in rendered
    assert 'name="op-end"' not in rendered
    assert "Integration domain" in rendered
    assert r"\mathrm d k" in rendered
    assert rendered.index("pl-big-operator-input__domain-spacer") < domain_position
    css = (HERE / "pl-big-operator-input.css").read_text()
    assert ".pl-big-operator-input__domain-spacer" in css
    assert "height: calc(1.5rem + 0.75rem + 2px)" in css


def test_domain_integral_parses_and_reconstructs_notation():
    markup = html(
        operator="integral",
        limits="domain",
        **{"index-variable": "z", "grading-method": "exact"},
    )
    state = data(
        raw={"op-domain": "Interval(0, 1)", "op-body": "z"}, panel="submission"
    )
    state["partial_scores"] = {"op": {"score": 1}}
    mod.parse(markup, state)
    assert state["submitted_answers"]["op"]["limits"] == "domain"
    assert set(state["submitted_answers"]["op"]) == {
        "_type",
        "_version",
        "operator",
        "limits",
        "index",
        "domain",
        "body",
    }
    rendered = mod.render(markup, state)
    assert r"\int_{\left[0, 1\right]} z\,\mathrm{d}z" in rendered


@pytest.mark.parametrize("operator", ["union", "limit"])
def test_annotated_operator_stack_has_vertical_offset(operator):
    rendered = mod.render(html(operator=operator), data())
    assert "pl-big-operator-input__operator-stack--annotated" in rendered
    css = (HERE / "pl-big-operator-input.css").read_text()
    assert ".pl-big-operator-input__operator-stack--annotated" in css
    assert "margin-top: 1.5rem" in css
    assert (
        ".pl-big-operator-input__annotation math-field::part(virtual-keyboard-toggle)"
        in css
    )
