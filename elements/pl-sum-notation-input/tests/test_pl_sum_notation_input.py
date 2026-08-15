from __future__ import annotations

import importlib.util
import sys
import typing
from pathlib import Path

import pytest  # type: ignore

if not hasattr(typing, "assert_never"):

    def _assert_never(value):
        raise AssertionError(f"Expected code to be unreachable, got {value!r}")

    typing.assert_never = _assert_never  # type: ignore[attr-defined]


def _find_module_path() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        module_path = (
            candidate
            / "elements"
            / "pl-sum-notation-input"
            / "pl-sum-notation-input.py"
        )
        if module_path.exists():
            return module_path
    raise FileNotFoundError("Could not locate the pl-sum-notation-input module")


def _load_module():
    module_path = _find_module_path()
    spec = importlib.util.spec_from_file_location("pl_sum_notation_input", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_element_css() -> str:
    return _find_module_path().with_suffix(".css").read_text(encoding="utf-8")


def _css_order(css: str, selector: str) -> int:
    block_start = css.index(selector)
    order_start = css.index("order:", block_start)
    value_start = order_start + len("order:")
    value_end = css.index(";", value_start)
    return int(css[value_start:value_end].strip())


def test_prepare_populates_namespaced_answers():
    mod = _load_module()
    data = {"params": {}, "correct_answers": {}}
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="k" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )

    mod.prepare(html, data)

    assert data["params"]["index_variable"] == "k"
    assert data["params"]["start_answers_name"] == "sigma1-start"
    assert data["params"]["end_answers_name"] == "sigma1-end"
    assert data["params"]["summand_answers_name"] == "sigma1-summand"
    assert "sigma1" in data["correct_answers"]


def test_sigma_css_places_upper_bound_above_lower_bound():
    css = _read_element_css()

    assert (
        _css_order(css, ".pl-sum-notation-input__sum > .pl-sum-notation-input__upper")
        < _css_order(css, ".pl-sum-notation-input__sum > .pl-sum-notation-input__sigma")
        < _css_order(css, ".pl-sum-notation-input__sum > .pl-sum-notation-input__lower")
    )


def test_render_emits_a_sigma_layout_with_three_inputs():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = {"params": {}, "correct_answers": {}, "panel": "question"}
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert "∑" in rendered or r"\sum" in rendered
    assert rendered.count("<pl-symbolic-input") == 3
    assert 'answers-name="sigma1-start"' in rendered
    assert 'answers-name="sigma1-end"' in rendered
    assert 'answers-name="sigma1-summand"' in rendered
    assert r'label="\(k = \)"' in rendered
    assert rendered.index('class="pl-sum-notation-input__lower"') < rendered.index(
        'class="pl-sum-notation-input__upper"'
    )
    assert 'variables="k, n"' in rendered


def test_render_supports_greek_latex_index_variables():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="theta" variables="x" '
        'start-answer="1" end-answer="4" summand-answer="theta^2 + x"></pl-sum-notation-input>'
    )
    data = {"params": {}, "correct_answers": {}, "panel": "question"}
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert r'label="\(\theta = \)"' in rendered
    assert 'variables="theta, x"' in rendered
    assert data["params"]["index_variable"] == "theta"


def test_parse_accepts_greek_latex_index_variables():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="theta" variables="x" '
        'start-answer="1" end-answer="4" summand-answer="theta^2 + x"></pl-sum-notation-input>'
    )
    data = {
        "params": {},
        "correct_answers": {},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "theta^2 + x",
        },
        "submitted_answers": {},
        "panel": "question",
    }
    mod.prepare(html, data)

    mod.parse(html, data)

    assert data["submitted_answers"]["sigma1"] == "Sum(theta**2 + x, (theta, 1, 4))"


def test_render_emits_an_integral_layout_with_horizontal_limits():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="x" variables="n" '
        'start-answer="0" end-answer="1" summand-answer="x^2" integral="true"></pl-sum-notation-input>'
    )
    data = {"params": {}, "correct_answers": {}, "panel": "question"}
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert "∫" in rendered or r"\int" in rendered
    assert 'aria-label="Integral notation input"' in rendered
    assert "pl-sum-notation-input__sigma-stack--integral" in rendered
    assert "pl-sum-notation-input__limits" in rendered
    assert rendered.index('class="pl-sum-notation-input__lower"') < rendered.index(
        'class="pl-sum-notation-input__upper"'
    )
    assert rendered.count("<pl-symbolic-input") == 3
    assert 'answers-name="sigma1-start"' in rendered
    assert 'answers-name="sigma1-end"' in rendered
    assert 'answers-name="sigma1-summand"' in rendered


def test_render_emits_one_submission_badge_for_non_piecewise_grading():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = {
        "panel": "submission",
        "partial_scores": {"sigma1": {"score": 1.0}},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
    }
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert r"\( \displaystyle" in rendered
    assert rendered.count("%") == 1


def test_parse_builds_the_submitted_sympy_sum():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = {
        "params": {},
        "correct_answers": {},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
        "submitted_answers": {},
        "panel": "question",
    }
    mod.prepare(html, data)

    mod.parse(html, data)

    assert data["submitted_answers"]["sigma1"] == "Sum(k**2, (k, 1, 4))"


def test_parse_stores_child_answers_as_pl_json():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = {
        "params": {},
        "correct_answers": {},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
        "submitted_answers": {},
        "panel": "question",
    }
    mod.prepare(html, data)

    mod.parse(html, data)

    assert data["submitted_answers"]["sigma1-start"] == {
        "_type": "sympy",
        "_value": "1",
        "_variables": [],
        "_assumptions": {},
        "_custom_functions": [],
    }
    assert data["submitted_answers"]["sigma1-end"] == {
        "_type": "sympy",
        "_value": "4",
        "_variables": [],
        "_assumptions": {},
        "_custom_functions": [],
    }
    assert data["submitted_answers"]["sigma1-summand"] == {
        "_type": "sympy",
        "_value": "k**2",
        "_variables": ["k"],
        "_assumptions": {"k": {"commutative": True}},
        "_custom_functions": [],
    }


def test_parse_despaces_formula_editor_trig_names_in_summand():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="sin(k)"></pl-sum-notation-input>'
    )
    data = {
        "params": {},
        "correct_answers": {},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "s i n ( k )",
        },
        "submitted_answers": {},
        "panel": "question",
    }
    mod.prepare(html, data)

    mod.parse(html, data)

    assert data["submitted_answers"]["sigma1"] == "Sum(sin(k), (k, 1, 4))"
    assert data["submitted_answers"]["sigma1-summand"]["_value"] == "sin(k)"


def _prepare_grade_data(mod, html: str, raw_submitted_answers: dict[str, str]):
    data = {"params": {}, "correct_answers": {}, "panel": "question"}
    mod.prepare(html, data)
    data["raw_submitted_answers"] = raw_submitted_answers
    data["partial_scores"] = {}
    return data


def test_grade_awards_full_credit_for_an_exact_match():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


def test_grade_awards_full_credit_for_a_translated_sum():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "2",
            "sigma1-end": "5",
            "sigma1-summand": "(k-1)^2",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


def test_grade_awards_partial_credit_for_numeric_equivalence():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "5",
            "sigma1-summand": "2*k",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == pytest.approx(0.5)


def test_grade_exact_scheme_rejects_numeric_equivalence():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2" '
        'grading-scheme="exact"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "5",
            "sigma1-summand": "2*k",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 0.0


def test_grade_exact_scheme_still_awards_exact_match():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2" '
        'grading-scheme="exact"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


def test_grade_piecewise_awards_fractional_credit_per_correct_subfield():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2" summand-relative-weight=3 '
        'grading-scheme="piecewise"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "5",
            "sigma1-summand": "k^2",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1-start"]["score"] == 1.0
    assert data["partial_scores"]["sigma1-start"]["weight"] == 0
    assert data["partial_scores"]["sigma1-end"]["score"] == 0.0
    assert data["partial_scores"]["sigma1-end"]["weight"] == 0
    assert data["partial_scores"]["sigma1-summand"]["score"] == 1.0
    assert data["partial_scores"]["sigma1-summand"]["weight"] == 0
    assert data["partial_scores"]["sigma1"]["score"] == pytest.approx(0.8)
    assert data["partial_scores"]["sigma1"]["weight"] == 1


def test_grade_piecewise_awards_full_credit_for_three_correct_subfields():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="k^2" '
        'grading-scheme="piecewise"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1-start"]["score"] == 1.0
    assert data["partial_scores"]["sigma1-end"]["score"] == 1.0
    assert data["partial_scores"]["sigma1-summand"]["score"] == 1.0
    assert all(
        data["partial_scores"][name]["weight"] == 0.0
        for name in ("sigma1-start", "sigma1-end", "sigma1-summand")
    )
    assert data["partial_scores"]["sigma1"]["score"] == 1.0
    assert data["partial_scores"]["sigma1"]["weight"] == 1


def test_grade_piecewise_handles_spaced_trig_name_in_formula_editor_summand():
    mod = _load_module()
    html = (
        '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="n" '
        'start-answer="1" end-answer="4" summand-answer="sin(k)" '
        'grading-scheme="piecewise"></pl-sum-notation-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "s i n ( k )",
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0
    assert data["partial_scores"]["sigma1-summand"]["score"] == 1.0


def test_prepare_rejects_missing_required_attributes():
    mod = _load_module()

    with pytest.raises(ValueError, match='Required attribute ".*?" missing'):
        mod.prepare(
            '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="k" '
            'correct-answer-start="1" correct-answer-end="4"></pl-sum-notation-input>',
            {"params": {}, "correct_answers": {}},
        )


def test_prepare_rejects_invalid_grading_scheme():
    mod = _load_module()

    with pytest.raises(ValueError, match='Invalid grading-scheme ".*?"'):
        mod.prepare(
            '<pl-sum-notation-input answers-name="sigma1" index-variable="k" variables="k" '
            'start-answer="1" end-answer="4" summand-answer="k^2" '
            'grading-scheme="approximate"></pl-sum-notation-input>',
            {"params": {}, "correct_answers": {}},
        )


def test_prepare_rejects_missing_index_variable():
    mod = _load_module()

    with pytest.raises(ValueError, match='Required attribute ".*?" missing'):
        mod.prepare(
            '<pl-sum-notation-input answers-name="sigma1" variables="k" '
            'correct-answer-start="1" correct-answer-end="4" '
            'correct-answer-summand="k^2"></pl-sum-notation-input>',
            {"params": {}, "correct_answers": {}},
        )
