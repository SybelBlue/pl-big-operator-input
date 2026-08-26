from __future__ import annotations

import importlib.util
import json
import sys
import typing
from pathlib import Path

import prairielearn.sympy_utils as psu  # type: ignore
import pytest  # type: ignore
import sympy

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
            / "pl-big-operator-input"
            / "pl-big-operator-input.py"
        )
        if module_path.exists():
            return module_path
    raise FileNotFoundError("Could not locate the pl-big-operator-input module")


def _load_module():
    module_path = _find_module_path()
    spec = importlib.util.spec_from_file_location("pl_sum_notation_input", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_element_template(name: str) -> str:
    return (_find_module_path().parent / name).read_text(encoding="utf-8")


def _sum_correct_answer(
    index_name: str = "k",
    body: str = "k**2",
    start: int = 1,
    end: int = 4,
) -> sympy.Sum:
    index = sympy.Symbol(index_name)
    return typing.cast(sympy.Sum, sympy.Sum(sympy.sympify(body), (index, start, end)))


def test_bounds_partial_uses_formula_editor_with_inline_prefix():
    template = _read_element_template("partials/bounds-math-field.mustache")

    assert "<pl-symbolic-input" not in template
    assert "<math-field" in template
    assert 'name="{{ answers_name }}"' in template
    assert 'name="{{ answers_name }}-latex"' in template
    assert '<span class="input-group-text">{{{ prefix }}}</span>' in template
    assert '{{#label}}aria-label="{{ label }}"{{/label}}' in template
    assert "allow-trig" in template
    assert "virtual-keyboard-mode" not in template
    assert 'window.PLSumNotationInput("{{ answers_name }}")' in template


def test_summand_partial_uses_formula_editor():
    template = _read_element_template("partials/summand-math-field.mustache")

    assert "<pl-symbolic-input" not in template
    assert "<math-field" in template
    assert 'name="{{ answers_name }}"' in template
    assert 'name="{{ answers_name }}-latex"' in template
    assert "allow-trig" in template
    assert "virtual-keyboard-mode" not in template
    assert 'window.PLSumNotationInput("{{ answers_name }}")' in template


def test_math_field_dependencies_include_mathlive_and_initializer():
    element_dir = _find_module_path().parent
    info = (element_dir / "info.json").read_text(encoding="utf-8")
    initializer = (element_dir / "pl-big-operator-input.js").read_text(encoding="utf-8")

    assert '"mathlive/mathlive.min.js"' in info
    assert '"pl-big-operator-input.js"' in info
    assert "window.PLSumNotationInput" in initializer
    assert "getValue('plain-text')" in initializer
    assert "getValue('latex')" in initializer
    assert "mathVirtualKeyboard.layouts" in initializer
    assert "selection-change" in initializer


def test_prepare_serializes_only_the_combined_correct_answer():
    mod = _load_module()
    correct = _sum_correct_answer()
    data = {
        "params": {"existing": "unchanged"},
        "correct_answers": {"sigma1": correct},
    }
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="k"></pl-big-operator-input>'
    )

    mod.prepare(html, data)

    assert data["params"] == {"existing": "unchanged"}
    assert list(data["correct_answers"]) == ["sigma1"]
    assert data["correct_answers"]["sigma1"]["_type"] == "sympy"
    assert data["correct_answers"]["sigma1"]["_value"] == str(correct)
    json.dumps(data)


@pytest.mark.parametrize(
    "correct_answer",
    [
        "Sum(k**2, (k, 1, 4))",
        psu.sympy_to_json(_sum_correct_answer()),
        _sum_correct_answer(),
    ],
    ids=["string", "prairielearn-json", "sympy-object"],
)
def test_prepare_accepts_supported_sum_answer_formats(correct_answer):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" '
        'index-variable="k"></pl-big-operator-input>'
    )
    data = {"params": {}, "correct_answers": {"sigma1": correct_answer}}

    mod.prepare(html, data)

    assert list(data["correct_answers"]) == ["sigma1"]
    assert data["correct_answers"]["sigma1"]["_type"] == "sympy"
    assert data["correct_answers"]["sigma1"]["_value"] == "Sum(k**2, (k, 1, 4))"


@pytest.mark.parametrize(
    "correct_answer",
    [
        "Integral(x**2, (x, 0, 1))",
        psu.sympy_to_json(
            sympy.Integral(sympy.Symbol("x") ** 2, (sympy.Symbol("x"), 0, 1))  # type: ignore
        ),
        sympy.Integral(sympy.Symbol("x") ** 2, (sympy.Symbol("x"), 0, 1)),
    ],
    ids=["string", "prairielearn-json", "sympy-object"],
)
def test_prepare_accepts_supported_integral_answer_formats(correct_answer):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="int1" index-variable="x" '
        'integral="true"></pl-big-operator-input>'
    )
    data = {"params": {}, "correct_answers": {"int1": correct_answer}}

    mod.prepare(html, data)

    assert list(data["correct_answers"]) == ["int1"]
    assert data["correct_answers"]["int1"]["_type"] == "sympy"
    assert data["correct_answers"]["int1"]["_value"] == "Integral(x**2, (x, 0, 1))"


@pytest.mark.parametrize(
    ("integral_attribute", "correct_answer", "expected_body"),
    [
        ("", "Sum(k**2, (k, 1, 4))", "k**2"),
        (' integral="true"', "Integral(k**3, (k, 1, 4))", "k**3"),
    ],
    ids=["sum", "integral"],
)
def test_prepare_accepts_a_string_correct_answer_attribute(
    integral_attribute, correct_answer, expected_body
):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        f'correct-answer="{correct_answer}"{integral_attribute}'
        "></pl-big-operator-input>"
    )
    data = {"params": {}, "correct_answers": {}}

    mod.prepare(html, data)

    assert list(data["correct_answers"]) == ["sigma1"]
    correct = data["correct_answers"]["sigma1"]
    assert correct["_type"] == "sympy"
    assert expected_body in correct["_value"]


def test_prepare_rejects_a_non_sum_correct_answer_attribute():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'correct-answer="k**2"></pl-big-operator-input>'
    )

    with pytest.raises(TypeError, match="must be a SymPy Sum"):
        mod.prepare(html, {"params": {}, "correct_answers": {}})


def test_render_emits_a_sigma_layout_with_three_inputs():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n"></pl-big-operator-input>'
    )
    data = {
        "params": {},
        "correct_answers": {"sigma1": _sum_correct_answer()},
        "panel": "question",
    }
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert "∑" in rendered or r"\sum" in rendered
    assert rendered.count("<math-field") == 3
    assert rendered.count('type="text"') == 0
    assert 'name="sigma1-start"' in rendered
    assert 'name="sigma1-end"' in rendered
    assert 'name="sigma1-summand"' in rendered
    assert r"\(k = \)" in rendered
    assert rendered.index('class="pl-big-operator-input__lower"') < rendered.index(
        'class="pl-big-operator-input__upper"'
    )
    assert 'allow-trig="allow-trig"' in rendered


def test_render_supports_greek_latex_index_variables():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="theta" '
        'variables="x"></pl-big-operator-input>'
    )
    data = {
        "params": {},
        "correct_answers": {"sigma1": _sum_correct_answer("theta", "theta**2 + x")},
        "panel": "question",
    }
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert r"\(\theta = \)" in rendered


def test_render_does_not_require_correct_answers():
    mod = _load_module()
    html = '<pl-big-operator-input answers-name="sigma1" index-variable="theta" variables="x"></pl-big-operator-input>'
    data = {"params": {}, "correct_answers": {}, "panel": "question"}

    mod.prepare(html, data)
    rendered = mod.render(html, data)

    assert rendered


def test_parse_accepts_greek_latex_index_variables():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="theta" '
        'variables="x"></pl-big-operator-input>'
    )
    data = {
        "params": {},
        "correct_answers": {"sigma1": _sum_correct_answer("theta", "theta**2 + x")},
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
        '<pl-big-operator-input answers-name="sigma1" index-variable="x" '
        'variables="n" integral="true"></pl-big-operator-input>'
    )
    x = sympy.Symbol("x")
    data = {
        "params": {},
        "correct_answers": {"sigma1": sympy.Integral(x**2, (x, 0, 1))},
        "panel": "question",
    }
    mod.prepare(html, data)

    rendered = mod.render(html, data)

    assert "∫" in rendered or r"\int" in rendered
    assert 'aria-label="Integral notation input"' in rendered
    assert "pl-big-operator-input__sigma-stack--integral" in rendered
    assert "pl-big-operator-input__limits" in rendered
    assert rendered.index('class="pl-big-operator-input__lower"') < rendered.index(
        'class="pl-big-operator-input__upper"'
    )
    assert rendered.count("<math-field") == 3
    assert rendered.count('type="text"') == 0
    assert 'name="sigma1-start"' in rendered
    assert 'name="sigma1-end"' in rendered
    assert 'name="sigma1-summand"' in rendered


def test_render_emits_one_submission_badge_for_non_piecewise_grading():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n"></pl-big-operator-input>'
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
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n"></pl-big-operator-input>'
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


@pytest.mark.parametrize(
    ("allow_blank_attribute", "expects_format_error"),
    [("", True), (' allow-blank="true"', False)],
    ids=["blank-disallowed", "blank-allowed"],
)
def test_allow_blank_if_and_only_if_prevents_a_blank_format_error(
    allow_blank_attribute, expects_format_error
):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k"'
        f"{allow_blank_attribute}></pl-big-operator-input>"
    )
    data = {
        "raw_submitted_answers": {
            "sigma1-start": "",
            "sigma1-end": "  ",
            "sigma1-summand": "",
        },
        "submitted_answers": {},
        "format_errors": {},
    }

    mod.parse(html, data)

    assert ("sigma1" in data["format_errors"]) is expects_format_error
    assert data["submitted_answers"]["sigma1"] == (None if expects_format_error else "")


def test_schema_declares_allow_blank_as_a_boolean_attribute():
    schema_path = _find_module_path().with_suffix(".schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["allow-blank"] == {
        "default": "false",
        "enum": ["true", "false"],
    }


def test_parse_stores_child_answers_as_pl_json():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n"></pl-big-operator-input>'
    )
    data = {
        "params": {},
        "correct_answers": {"sigma1": _sum_correct_answer()},
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
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n"></pl-big-operator-input>'
    )
    data = {
        "params": {},
        "correct_answers": {"sigma1": _sum_correct_answer(body="sin(k)")},
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


def _prepare_grade_data(
    mod,
    html: str,
    raw_submitted_answers: dict[str, str],
    *,
    correct_answer: sympy.Expr | None = None,
):
    data = {
        "params": {},
        "correct_answers": {
            "sigma1": correct_answer
            if correct_answer is not None
            else _sum_correct_answer()
        },
        "panel": "question",
    }
    mod.prepare(html, data)
    data["raw_submitted_answers"] = raw_submitted_answers
    data["partial_scores"] = {}
    return data


@pytest.mark.parametrize("grading_method", [None, "exact", "piecewise", "equivalent"])
def test_grade_awards_full_credit_for_an_exact_match(grading_method):
    mod = _load_module()
    method_attribute = (
        "" if grading_method is None else f' grading-method="{grading_method}"'
    )
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        f'variables="n"{method_attribute}></pl-big-operator-input>'
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


@pytest.mark.parametrize(
    ("integral_attribute", "index_variable", "start", "body", "correct_answer"),
    [
        (
            "",
            "k",
            "1",
            "1 / k^2",
            sympy.Sum(1 / sympy.Symbol("k") ** 2, (sympy.Symbol("k"), 1, sympy.oo)),  # type: ignore
        ),
        (
            ' integral="true"',
            "x",
            "0",
            "e^(-x)",
            sympy.Integral(
                sympy.exp(-sympy.Symbol("x")),
                (sympy.Symbol("x"), 0, sympy.oo),
            ),
        ),
    ],
    ids=["infinite-sum", "improper-integral"],
)
def test_grade_accepts_an_infinite_upper_bound(
    integral_attribute, index_variable, start, body, correct_answer
):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" '
        f'index-variable="{index_variable}"{integral_attribute}'
        "></pl-big-operator-input>"
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": start,
            "sigma1-end": "infinity",
            "sigma1-summand": body,
        },
        correct_answer=correct_answer,
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


def test_exact_grading_rejects_an_equivalent_but_different_sum():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n" grading-method="exact"></pl-big-operator-input>'
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

    assert data["partial_scores"]["sigma1"]["score"] == 0.0


@pytest.mark.parametrize(
    ("start", "end", "body", "expected_score"),
    [
        ("1", "4", "k^2", 1.0),
        ("0", "4", "k^2", 4 / 5),
        ("1", "5", "k^2", 4 / 5),
        ("1", "4", "k", 2 / 5),
        ("0", "5", "k^2", 3 / 5),
        ("0", "4", "k", 1 / 5),
        ("1", "5", "k", 1 / 5),
        ("0", "5", "k", 0.0),
    ],
)
def test_piecewise_grading_uses_component_weights(start, end, body, expected_score):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'variables="n" grading-method="piecewise"></pl-big-operator-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {
            "sigma1-start": start,
            "sigma1-end": end,
            "sigma1-summand": body,
        },
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == pytest.approx(expected_score)


def test_piecewise_grading_honors_custom_summand_relative_weight():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'grading-method="piecewise" summand-relative-weight="2"'
        "></pl-big-operator-input>"
    )
    data = _prepare_grade_data(
        mod,
        html,
        {"sigma1-start": "1", "sigma1-end": "4", "sigma1-summand": "k"},
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"] == {"score": 0.5, "weight": 1}


@pytest.mark.parametrize(
    ("start", "end", "body"),
    [
        ("2", "5", "(k-1)^2"),
        ("1", "4", "(5-k)^2"),
        ("1", "5", "2*k"),
    ],
)
def test_equivalent_grading_accepts_evaluation_and_affine_reindexing(start, end, body):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'grading-method="equivalent"></pl-big-operator-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {"sigma1-start": start, "sigma1-end": end, "sigma1-summand": body},
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


def test_equivalent_grading_accepts_expanded_summand():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'grading-method="equivalent"></pl-big-operator-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {"sigma1-start": "1", "sigma1-end": "4", "sigma1-summand": "k^2+2*k+1"},
        correct_answer=_sum_correct_answer(body="(k + 1)**2"),
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


@pytest.mark.parametrize("body", ["-x^2", "-(1-x)^2"])
def test_equivalent_grading_accepts_signed_integral_bound_reversal(body):
    mod = _load_module()
    x = sympy.Symbol("x")
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="x" '
        'integral="true" grading-method="equivalent"></pl-big-operator-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {"sigma1-start": "1", "sigma1-end": "0", "sigma1-summand": body},
        correct_answer=sympy.Integral(x**2, (x, 0, 1)),  # type: ignore
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 1.0


@pytest.mark.parametrize(
    ("start", "end", "body"),
    [("1", "4", "k^2+1"), ("4", "1", "-k^2")],
)
def test_equivalent_grading_rejects_inequivalent_sums(start, end, body):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        'grading-method="equivalent"></pl-big-operator-input>'
    )
    data = _prepare_grade_data(
        mod,
        html,
        {"sigma1-start": start, "sigma1-end": end, "sigma1-summand": body},
    )

    mod.grade(html, data)

    assert data["partial_scores"]["sigma1"]["score"] == 0.0


@pytest.mark.parametrize(
    "attribute",
    ['grading-method="other"', 'summand-relative-weight="0"'],
)
def test_prepare_rejects_invalid_grading_configuration(attribute):
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" index-variable="k" '
        f"{attribute}></pl-big-operator-input>"
    )

    with pytest.raises(ValueError):
        mod.prepare(html, {"correct_answers": {"sigma1": _sum_correct_answer()}})


def test_prepare_rejects_missing_required_attributes():
    mod = _load_module()

    with pytest.raises(ValueError, match='Required attribute ".*?" missing'):
        mod.prepare(
            '<pl-big-operator-input index-variable="k"></pl-big-operator-input>',
            {"params": {}, "correct_answers": {}},
        )


def test_prepare_rejects_a_non_sum_correct_answer():
    mod = _load_module()

    with pytest.raises(TypeError, match="must be a SymPy Sum"):
        mod.prepare(
            '<pl-big-operator-input answers-name="sigma1" '
            'index-variable="k"></pl-big-operator-input>',
            {"params": {}, "correct_answers": {"sigma1": sympy.Integer(1)}},
        )


def test_grade_does_nothing_without_a_correct_answer():
    mod = _load_module()
    html = (
        '<pl-big-operator-input answers-name="sigma1" '
        'index-variable="k"></pl-big-operator-input>'
    )
    data = {
        "correct_answers": {},
        "partial_scores": {},
        "raw_submitted_answers": {
            "sigma1-start": "1",
            "sigma1-end": "4",
            "sigma1-summand": "k^2",
        },
    }

    mod.grade(html, data)

    assert data["partial_scores"] == {}


def test_prepare_rejects_missing_index_variable():
    mod = _load_module()

    with pytest.raises(ValueError, match='Required attribute ".*?" missing'):
        mod.prepare(
            '<pl-big-operator-input answers-name="sigma1" '
            'variables="k"></pl-big-operator-input>',
            {"params": {}, "correct_answers": {}},
        )
