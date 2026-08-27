# `pl-big-operator-input`

This element collects an indexed big-operator expression in separate limit and body fields while storing one lossless, JSON-safe combined answer.

Its visible component fields are rendered and parsed by a vendored, commit-pinned
copy of PrairieLearn's `pl-symbolic-input`. The wrapper is responsible for the
operator layout, canonical aggregate answer, and grading; the upstream element
owns the MathLive editor and symbolic-input parsing behavior. The source commit
and license are recorded alongside the vendor directory in
`prairielearn-source.json`.

```html
<pl-big-operator-input
  answers-name="total"
  correct-answer="Sum(k**2, (k, 1, n))"
  variables="n"
></pl-big-operator-input>
```

The whole `correct-answer` form is the preferred authoring interface. It lets
the element infer the operator and limits layout while keeping the complete
mathematical expression together. Component correct-answer attributes remain
available as a secondary option when constructing a whole answer is
inconvenient.

## Attributes

| Attribute                                                                                                             | Inferable | Default                  | Meaning                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `answers-name`                                                                                                        |           | required                 | Combined answer namespace.                                                                                                                       |
| `correct-answer`                                                                                                      |           | ---                      | The correct answer, either as a parsable string or canonical form dict, **that sets inference data for the problem**                             |
| `operator`                                                                                                            | ☑️        | required if not inferred | A built-in operator, or `custom` for a custom LaTeX operator. When omitted, a whole string/dictionary correct answer must identify the operator. |
| `limits`                                                                                                              | ☑️        | `auto`                   | `bounds`, `domain`, or `approach`; `auto` uses the table below only when the limits form cannot be inferred from a whole answer.                 |
| `limit-direction`                                                                                                     | ☑️        | `two-sided`              | `two-sided`, `from-left`, or `from-right` for limits.                                                                                            |
| `index-variable`                                                                                                      | ☑️        | required if not inferred | Bound symbol; automatically allowed in the body. When omitted, a whole string/dictionary correct answer must identify it.                        |
| `variables`                                                                                                           |           | empty                    | Comma-separated extra allowed symbols, e.g. `"Gamma,theta,N"`.                                                                                   |
| `operator-latex`                                                                                                      |           | ---                      | Custom operator LaTeX. When supplied without `operator`, it requires `operator="custom"`.                                                        |
| `allowed-blank`                                                                                                       |           | `none`                   | Permit blank `limits`, the `body`, `all` fields, or `none`.                                                                                      |
| `show-help-text`                                                                                                      |           | `true`                   | Show symbolic-entry help beside the body input. Set to `false` to hide it.                                                                       |
| `grading-method`                                                                                                      |           | `equivalent`             | `exact`, `component`, or `equivalent`.                                                                                                           |
| `body-relative-weight`                                                                                                |           | `3`                      | Body weight in component grading; every limit component has weight 1.                                                                            |
| `weight`                                                                                                              |           | `1`                      | PrairieLearn score weight.                                                                                                                       |
| `correct-answer-start`, `correct-answer-end`, `correct-answer-domain`, `correct-answer-target`, `correct-answer-body` | ☑️        | ---                      | Alternative string answers for the visible component fields. Supply every component for the resolved limits form.                                |

## Operators and limits

With `limits="auto"`, the element first tries to infer the limits form from a
whole correct answer. The auto limits in the table below are fallbacks used only
when that inference fails or is unavailable.

| Operator                           | LaTeX                             | Auto limits                  | Explicit limits          |
| ---------------------------------- | --------------------------------- | ---------------------------- | ------------------------ |
| Sum                                | $\sum$                            | bounds                       | bounds, domain           |
| Product                            | $\prod$                           | bounds                       | bounds, domain           |
| Integral                           | $\int$                            | bounds                       | bounds, domain           |
| Limit                              | $\lim$                            | approach                     | approach only            |
| Union, Intersection, DisjointUnion | $\bigcup$, $\bigcap$, $\bigsqcup$ | domain                       | bounds, domain           |
| And, Or                            | $\bigwedge$, $\bigvee$            | domain                       | bounds, domain           |
| Min, Max                           | $\min$, $\max$                    | domain                       | bounds, domain           |
| Custom                             | ---                               | inferred from a whole answer | bounds, domain, approach |

Bounds forms collect a lower bound, an upper bound, and a body. Domain forms
collect a domain and a body, while approach forms collect a target and a body.
The element displays and parses only the inputs required by the selected form.
For a one-sided limit, the target is displayed with a `-` or `+`; the combined
answer records the corresponding descriptive direction.

Custom operators infer their limits form from a parseable whole `Custom(...)`
answer. Without one, they require explicit `limits="bounds"`, `limits="domain"`,
or `limits="approach"`. They are ungraded when no correct answer is supplied.
A custom operator with a correct answer must use
`grading-method="exact"` or `grading-method="component"`; symbolic equivalence
is unavailable because arbitrary LaTeX does not identify a SymPy operation.
For a whole correct answer, use the parseable syntax `Custom(body, limits)`,
where `limits` is `(index, domain)`, `(index, lower, upper)`, or
`(index, target, direction)` and determines the limits form. Approach
directions use the same `"+"`, `"-"`, and `"+-"` values as `Limit`. Supplying
`operator-latex` makes
the separate `operator="custom"` attribute optional.
Component grading uses the same per-field weights as built-in operators. Their
canonical submissions include an additional `"operator_latex"` key so the
stored response remains self-describing:

```html
<pl-big-operator-input
  answers-name="expectation"
  correct-answer="Custom(k**2, (k, {1, 2}))"
  grading-method="component"
  index-variable="k"
  operator-latex="\mathbb{E}"
></pl-big-operator-input>
```

```html
<pl-big-operator-input
  answers-name="evaluation"
  correct-answer="Custom(f(x), (x, 0, '+-'))"
  grading-method="component"
  index-variable="x"
  operator-latex="\operatorname{eval}"
></pl-big-operator-input>
```

For an integral with `limits="domain"`, the domain is rendered as the sole subscript without an `index-variable \in` prefix, for example `\int_\Gamma z\,\mathrm{d}z`. Use `exact` or `component` grading because SymPy has no lossless indexed representation for this notation.

## Correct answers

### Whole `correct-answer` (preferred)

When `operator` is omitted, a whole correct answer supplied as a string or
JSON-safe dictionary identifies the built-in operator. Supported strings begin
with `Sum`, `Product`, `Integral`, `Limit`, `Union`, `Intersection`,
`DisjointUnion`, `And`, `Or`, `Min`, or `Max`. A canonical dictionary uses its
`operator` field, while a PrairieLearn SymPy JSON dictionary can identify the
formatted `Sum`, `Product`, `Integral`, and `Limit` expressions.
In parseable whole answers, `(index, domain)` selects `limits="domain"`,
`(index, lower, upper)` selects `limits="bounds"`, and a `Limit` selects
`limits="approach"`. The formatted variadic syntax described below uses the
same tuple-length rule. An explicit
`limits` attribute remains authoritative and must agree with the answer.

```html
<pl-big-operator-input
  answers-name="total"
  correct-answer="Product(k + 1, (k, 1, 4))"
  index-variable="k"
></pl-big-operator-input>
```

A domain integral can therefore omit both the operator and limits attributes:

```html
<pl-big-operator-input
  answers-name="contour"
  correct-answer="Integral(z**2, (z, Gamma))"
  index-variable="z"
  variables="Gamma"
></pl-big-operator-input>
```

A limit uses the parseable form `Limit(body, (index, target, direction))`.
Valid direction strings are `"+"` (from the right), `"-"` (from the left), and
`"+-"` (two-sided). When `limit-direction` is omitted, it is inferred from this
value; an explicit attribute must agree. For example, the operator, approach
layout, and two-sided direction are all inferred here:

```html
<pl-big-operator-input
  answers-name="sinc-limit"
  correct-answer="Limit(sin(x) / x, (x, 0, '+-'))"
  index-variable="x"
></pl-big-operator-input>
```

Strings and SymPy JSON dictionaries can also be assigned in `server.py`:

```python
k = sympy.symbols("k")
data["correct_answers"]["total"] = str(sympy.Product(k + 1, (k, 1, 4)))
# Alternatively: psu.sympy_to_json(sympy.Product(k + 1, (k, 1, 4)))
```

A canonical structured dictionary, in the format below, is another inferable
answer source because it includes `"operator"` and `"index"`. Whole answer
strings and SymPy JSON also identify their bound symbol, so `index-variable`
can be omitted for these parseable forms. Explicit HTML `operator` and
`index-variable` values always take precedence and are checked against the
answer. Component
`correct-answer-...` attributes and raw SymPy objects do not trigger inference,
so they require an explicit `operator` and `index-variable`. Ungraded,
malformed, or otherwise unrecognized answers likewise require explicit
configuration.

Answers assigned in `server.py` must be JSON-serializable. Do not assign a raw
SymPy object to `data`; convert supported expressions to a string or use
`prairielearn.sympy_utils.sympy_to_json`.

String or `sympy_to_json` representations of single-variable `sympy.Sum`,
`sympy.Product`, and `sympy.Integral`, plus `sympy.Limit`, are accepted as
author conveniences and normalized during `prepare()`. Two-item integral
tuples become domain forms and three-item tuples become bounds forms. Do not
put raw SymPy objects in `data`, because PrairieLearn question data must remain
JSON-serializable. Variadic SymPy `Union`, `Intersection`, `DisjointUnion`,
`And`, `Or`, `Min`, and `Max` do not preserve an indexed whole-answer format and
therefore are never accepted as substitutes for one.

The variadic operators accept a parseable whole-answer syntax that preserves
the index and limits, using `(index, domain)` or `(index, lower, upper)` as the
second argument:

```html
<pl-big-operator-input
  answers-name="sets"
  correct-answer="Union({k}, (k, {1, 2}))"
  grading-method="exact"
  index-variable="k"
></pl-big-operator-input>
```

The same form supports `Intersection`, `DisjointUnion`, `And`, `Or`, `Min`,
and `Max`. These strings normalize to the canonical answer without evaluating
away the index and limits.

### Canonical representation

Every prepared or parsed combined answer is a flat version 1 dictionary. Mathematical leaves use `sympy_to_json(..., allow_sets=True)`:

```python
# canonical JSON repr of \sum_{k=1}^n k^2
{
    "_type": "operator_expression",
    "_version": 1,
    "operator": "sum",
    "limits": "bounds",
    "index": psu.sympy_to_json(k),
    "lower": psu.sympy_to_json(1),
    "upper": psu.sympy_to_json(n),
    "body": psu.sympy_to_json(k**2),
}
```

- Range answers use `lower` and `upper`, as seen above.
- Domain answers replace `lower` and `upper` with `domain`.
- Approach answers use `target`, `direction`, and `body`. The outer `_type` is intentionally distinct from PrairieLearn's reserved `sympy` leaf type.
- Custom submissions use the same form-dependent components and add `"operator_latex"`; built-in answers do not include that key.

### Component attributes (alternative)

Authors may instead provide each visible component as an attribute. This is the
secondary interface; each value is accepted by the same basic parser used for
student input:

```html
<!-- html repr of \sum_{k=1}^n k^2 -->
<pl-big-operator-input
  answers-name="total"
  correct-answer-body="k^2"
  correct-answer-end="n"
  correct-answer-start="1"
  index-variable="k"
  operator="sum"
  variables="n"
></pl-big-operator-input>
```

The required attributes depend on the resolved limits form: bounds use `start`,
`end`, and `body`; domain forms use `domain` and `body`; approach forms use
`target` and `body`. Supplying an irrelevant component, omitting a component, or
combining these attributes with `correct-answer` is an error. The element
supplies the operator, limits form, index, and limit direction and normalizes
the values to the canonical representation during `prepare()`. The index
variable is automatically available when parsing the body; other symbols must
be listed in `variables`.

## Grading

`exact` requires an identical canonical operator, form, direction, index, and exact SymPy components. `component` compares visible components independently. `equivalent` constructs formatted Sum, Product, Integral, or Limit expressions where possible. Domain equivalence expands only a concrete `FiniteSet`; symbolic or infinite domains fail explicitly rather than being expanded eagerly. Bounded variadic expressions cannot be represented faithfully in SymPy and are likewise reported as unsupported for equivalent grading; use `exact` or `component` for those forms.

If no correct answer is supplied through an attribute or
`data["correct_answers"]`, the element is ungraded. It still parses and stores
the combined canonical response, but it does not create a partial score.
Submission panels display the response without a score badge, and answer panels
render nothing. Blank-response validation remains controlled separately by
`allowed-blank`.
