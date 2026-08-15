# `pl-sum-notation-input` element

Fill in the parts of a summation or integral expression.

## Sample element

question.html

```html
<pl-sum-notation-input
  answers-name="sigma1"
  index-variable="k"
  variables="x"
  start-answer="1"
  end-answer="4"
  summand-answer="k^2 + x"
></pl-sum-notation-input>
```

This renders a sigma-style input with separate fields for the lower limit, upper limit, and summand.

### Integral mode

If `integral="true"`, the element switches to integral notation and appends the differential automatically.

```html
<pl-sum-notation-input
  answers-name="int1"
  index-variable="x"
  variables="a, b"
  start-answer="0"
  end-answer="1"
  summand-answer="x^2 + a"
  integral="true"
></pl-sum-notation-input>
```

## Customizations

Attribute | Type | Default | Description
--- | --- | --- | ---
`answers-name` | string | — | Base answer name used for the combined sum or integral. The element also creates `-start`, `-end`, and `-summand` answer names internally.
`index-variable` | string | — | The summation or integration variable shown in the notation. This symbol is added automatically to the summand field's allowed variables.
`start-answer` | string | — | Correct lower bound expression.
`end-answer` | string | — | Correct upper bound expression.
`summand-answer` | string | — | Correct summand or integrand expression.
`variables` | string | `""` | Comma-delimited list of extra symbols allowed in the bounds and summand. Whitespace around commas is ignored.
`integral` | boolean | `false` | Render integral notation instead of summation notation.
`grading-scheme` | `"strict"`, `"generous"`, `"exact"`, or `"piecewise"` | `"strict"` | Controls how the element awards credit when the submitted sum is not a direct match.
`weight` | integer | `1` | Weight used for the combined answer score when the element is not in `piecewise` mode.
`summand-relative-weight` | integer | `3` | Relative weight assigned to the summand child input when `piecewise` mode is enabled.

## Rendering and badges

In the question panel, the element renders three internal `pl-symbolic-input` fields for the lower bound, upper bound, and summand. When `grading-scheme="piecewise"`, each of those internal inputs receives a weight so PrairieLearn can display per-field score badges.

In the submission panel, non-piecewise grading modes render one combined score badge at the end of the displayed sum or integral. In `piecewise` mode, the child inputs keep their individual badges instead of showing a single combined badge.

## Details

The `start-answer`, `end-answer`, and `summand-answer` attributes are parsed as SymPy expressions. The lower and upper bounds may use only the symbols listed in `variables`, while the summand may use the `index-variable` plus those extra symbols.

When `index-variable` is a Greek LaTeX symbol name, the displayed notation is rendered from the normalized SymPy symbol so the label stays correct while the internal symbolic input still accepts the corresponding typed variable name without requiring the formula editor.

The controller stores the combined graded answer in `data["correct_answers"][answers-name]` and the individual inputs in namespaced answer slots such as `sigma1-start`.

During parsing, the nested child inputs are also written back to `data["submitted_answers"]` in PrairieLearn JSON form.

When `grading-scheme="strict"`, a numerically equivalent final answer receives partial credit. When `grading-scheme="generous"`, that same case receives full credit. When `grading-scheme="exact"`, only a direct sum-to-sum equality match receives credit.

When `grading-scheme="piecewise"`, the grader checks the lower bound, upper bound, and summand independently and awards one third of the total score for each correctly matched subfield.

## Example implementations

* `questions/reviewed/ch5-integration/q5-56/question.html`

## See also

* `pl-symbolic-input` for the internal math-expression inputs used by this element
