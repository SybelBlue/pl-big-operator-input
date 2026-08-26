# `pl-sum-notation-input` element

Fill in the parts of a summation or integral expression.

## Sample element

question.html

```html
<pl-sum-notation-input
  answers-name="sigma1"
  index-variable="k"
  variables="x"
></pl-sum-notation-input>
```

server.py

```python
import sympy
import prairielearn.sympy_utils as psu


def generate(data):
    k, x = sympy.symbols("k x")
    data["correct_answers"]["sigma1"] = psu.sympy_to_json(
        sympy.Sum(k**2 + x, (k, 1, 4))
    )
```

This renders a sigma-style input with separate fields for the lower limit, upper limit, and summand.

### Integral mode

If `integral="true"`, the element switches to integral notation and appends the differential automatically.

```html
<pl-sum-notation-input
  answers-name="int1"
  index-variable="x"
  variables="a, b"
  integral="true"
></pl-sum-notation-input>
```

```python
def generate(data):
    a, x = sympy.symbols("a x")
    data["correct_answers"]["int1"] = psu.sympy_to_json(
        sympy.Integral(x**2 + a, (x, 0, 1))
    )
```

## Customizations

Attribute | Type | Default | Description
--- | --- | --- | ---
`answers-name` | string | — | Base answer name used for the combined sum or integral. The element also creates `-start`, `-end`, and `-summand` answer names internally.
`index-variable` | string | — | The summation or integration variable shown in the notation. This symbol is added automatically to the summand field's allowed variables.
`correct-answer` | string | — | Optional string representation of a bounded SymPy `Sum` or `Integral`. Takes precedence over `data["correct_answers"][answers-name]`.
`variables` | string | `""` | Comma-delimited list of extra symbols allowed in the bounds and summand. Whitespace around commas is ignored.
`integral` | boolean | `false` | Render integral notation instead of summation notation.
`grading-method` | string | `equivalent` | Grading behavior: `exact`, `piecewise`, or `equivalent`.
`weight` | integer | `1` | Weight used for the combined answer score.
`summand-relative-weight` | positive integer | `3` | Weight of the summand relative to each bound in `piecewise` grading.

## Grading methods

`exact` compares the complete parsed SymPy `Sum` or `Integral` object with the
correct answer. This compares normalized symbolic objects, rather than the raw text
entered by the student, and awards either full or zero credit.

`piecewise` compares the lower bound, upper bound, and summand independently with
exact SymPy equality. Each bound has weight 1 and the summand has weight
`summand-relative-weight`, so the score is the weight of the matching components
divided by `2 + summand-relative-weight`.

`equivalent`, the default, awards full or zero credit by comparing the complete
expression. It accepts direct equality, equality after symbolic evaluation and
expansion, and affine reindexing of the form `k -> k + c` or `k -> -k + c`.
Signed reversal of integral bounds is supported through the usual change of
variables. Discrete sums do not use a generic “swap bounds and negate” shortcut;
they must be equal under finite-sum evaluation or a valid affine reindexing.

## Rendering and badges

In the question panel, the element renders plain-text lower- and upper-bound fields and a MathLive summand field.

In the submission panel, it renders the submitted sum or integral with one combined score badge.

## Details

The correct answer may be assigned in `server.py` as a bounded, one-dimensional `sympy.Sum` or `sympy.Integral`, its string representation, or a dictionary produced by `prairielearn.sympy_utils.sympy_to_json`. Its index must match `index-variable`; the element derives the correct lower bound, upper bound, and summand from that expression.

When `index-variable` is a Greek LaTeX symbol name, the displayed notation is rendered from the normalized SymPy symbol so the label stays correct while the internal symbolic input still accepts the corresponding typed variable name without requiring the formula editor.

The controller stores only the combined expression in `data["correct_answers"][answers-name]`, normalized to a JSON-serializable PrairieLearn SymPy dictionary. The namespaced field names such as `sigma1-start` are derived as needed and are not added to `correct_answers`.

During parsing, the nested child inputs are also written back to `data["submitted_answers"]` in PrairieLearn JSON form.

## Example implementations

* `questions/reviewed/ch5-integration/q5-56/question.html`

## See also

* `pl-symbolic-input` for the internal math-expression inputs used by this element
