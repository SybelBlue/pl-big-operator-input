# `pl-big-operator-input`

This element collects an indexed big-operator expression in separate limit and body fields while storing one lossless, JSON-safe combined answer.

Its visible component fields are rendered and parsed by a vendored, commit-pinned
copy of PrairieLearn's `pl-symbolic-input`. The wrapper is responsible for the
operator layout, canonical aggregate answer, and grading; the upstream element
owns the MathLive editor and symbolic-input parsing behavior. The source commit
and license are recorded alongside the vendor directory in
`prairielearn-source.json`.

```html
<pl-big-operator-input answers-name="total" operator="sum" index-variable="k" variables="n"></pl-big-operator-input>
```

```python
k, n = sympy.symbols("k n")
data["correct_answers"]["total"] = str(sympy.Sum(k**2, (k, 1, n)))
```

Answers assigned in `server.py` must be JSON-serializable. In particular, do
not assign a raw SymPy object to `data`; convert binder-aware expressions to a
string as above, or serialize them with `prairielearn.sympy_utils.sympy_to_json`.

## Attributes

| Attribute | Default | Meaning |
| --- | --- | --- |
| `answers-name` | required | Combined answer namespace. |
| `index-variable` | required | Bound symbol; automatically allowed in the body. |
| `operator` | inferred | A built-in operator, or `custom` for a custom LaTeX operator. When omitted, a whole string/dictionary correct answer must identify the operator. |
| `operator-latex` | unset | Custom operator LaTeX. When supplied without `operator`, it implies `operator="custom"`; invalid for built-in operators. |
| `limits` | `auto` | `bounds`, `domain`, or `approach`; `auto` uses the table below. |
| `limit-direction` | `two-sided` | `two-sided`, `from-left`, or `from-right` for limits. |
| `variables` | empty | Comma-separated extra allowed symbols. |
| `allow-blank` | `false` | Permit a wholly blank response. |
| `show-help-text` | `true` | Show symbolic-entry help beside the body input. Set to `false` to hide it. |
| `grading-method` | `equivalent` | `exact`, `component`, or `equivalent`. |
| `body-relative-weight` | `3` | Body weight in component grading; every limit component has weight 1. |
| `weight` | `1` | PrairieLearn score weight. |
| `correct-answer` | unset | Optional string form of a losslessly convertible binder-aware SymPy answer. |
| `correct-answer-start`, `correct-answer-end`, `correct-answer-domain`, `correct-answer-target`, `correct-answer-body` | unset | Basic string answers for the visible component fields. Supply every component for the resolved limits form. |

## Operators and limits

| Operator | LaTeX | Auto limits | Explicit limits |
| --- | --- | --- | --- |
| sum | $\sum$ | bounds | bounds, domain |
| product | $\prod$ | bounds | bounds, domain |
| integral | $\int$ | bounds | bounds, domain |
| limit | $\lim$ | approach | approach only |
| union, intersection, disjoint-union | $\bigcup$, $\bigcap$, $\bigsqcup$ | domain | bounds, domain |
| and, or | $\bigwedge$, $\bigvee$ | domain | bounds, domain |
| min, max | $\min$, $\max$ | domain | bounds, domain |
| custom | --- | none | bounds, domain |

Bounds forms collect a lower bound, an upper bound, and a body. Domain forms
collect a domain and a body, while approach forms collect a target and a body.
The element displays and parses only the inputs required by the selected form.
For a one-sided limit, the target is displayed with a `-` or `+`; the combined
answer records the corresponding descriptive direction.

Custom operators require an explicit `limits="bounds"` or `limits="domain"`
because there is no meaningful automatic form. They are ungraded when no correct
answer is supplied. A custom operator with a correct answer must use
`grading-method="exact"` or `grading-method="component"`; symbolic equivalence
is unavailable because arbitrary LaTeX does not identify a SymPy operation.
For a whole correct answer, use the inert syntax `Custom(body, binder)`, where
the binder matches the explicit limits form. Supplying `operator-latex` makes
the separate `operator="custom"` attribute optional.
Component grading uses the same per-field weights as built-in operators. Their
canonical submissions include an additional `"operator_latex"` key so the
stored response remains self-describing:

```html
<pl-big-operator-input
  answers-name="expectation"
  operator="custom"
  operator-latex="\mathbb{E}"
  limits="domain"
  index-variable="k"
></pl-big-operator-input>
```

For an integral with `limits="domain"`, the domain is rendered as the sole subscript without an `index-variable \in` prefix, for example `\int_\Gamma z\,\mathrm{d}z`. Use `exact` or `component` grading because SymPy has no lossless indexed representation for this notation.

## Canonical answer

### Operator inference

When `operator` is omitted, a whole correct answer supplied as a string or
JSON-safe dictionary identifies the built-in operator. Supported strings begin
with `Sum`, `Product`, `Integral`, `Limit`, `Union`, `Intersection`,
`DisjointUnion`, `And`, `Or`, `Min`, or `Max`. A canonical dictionary uses its
`operator` field, while a PrairieLearn SymPy JSON dictionary can identify the
binder-aware `Sum`, `Product`, `Integral`, and `Limit` classes.
For binder-bearing answers, a two-item integral binder `(index, domain)` selects
`limits="domain"`, a three-item binder `(index, lower, upper)` selects
`limits="bounds"`, and a `Limit` selects `limits="approach"`. The inert
variadic syntax described below uses the same binder-arity rule. An explicit
`limits` attribute remains authoritative and must agree with the answer.

```html
<pl-big-operator-input
  answers-name="total"
  index-variable="k"
  correct-answer="Product(k, (k, 1, 4))"
></pl-big-operator-input>
```

A domain integral can therefore omit both the operator and limits attributes:

```html
<pl-big-operator-input
  answers-name="contour"
  correct-answer="Integral(z, (z, Gamma))"
  index-variable="z"
  variables="Gamma"
></pl-big-operator-input>
```

Strings and SymPy JSON dictionaries can also be assigned in `server.py`:

```python
k = sympy.symbols("k")
data["correct_answers"]["total"] = str(sympy.Product(k, (k, 1, 4)))
# Alternatively: psu.sympy_to_json(sympy.Product(k, (k, 1, 4)))
```

A canonical structured dictionary, in the format below, is another inferable
answer source because it includes `"operator"`. An explicit HTML `operator`
always takes precedence and is checked against the answer. Component
`correct-answer-...` attributes and raw SymPy objects do not trigger inference,
so they require an explicit `operator`. Ungraded elements and custom, malformed,
or otherwise unrecognized answers likewise require an explicit `operator`.

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

Authors may instead provide the visible components as attributes. Each value is
accepted by the same basic parser used for student input:

```html
<!-- html repr of \sum_{k=1}^n k^2 -->
<pl-big-operator-input
  answers-name="total"
  operator="sum"
  index-variable="k"
  variables="n"
  correct-answer-start="1"
  correct-answer-end="n"
  correct-answer-body="k^2"
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

String or `sympy_to_json` representations of single-binder `sympy.Sum`,
`sympy.Product`, and `sympy.Integral`, plus `sympy.Limit`, are accepted as
author conveniences and normalized during `prepare()`. Two-item integral
binders become domain forms and three-item binders become bounds forms. Do not
put raw SymPy objects in `data`, because PrairieLearn question data must remain
JSON-serializable. Variadic SymPy `Union`, `Intersection`, `DisjointUnion`,
`And`, `Or`, `Min`, and `Max` lose the indexed binder and therefore are never
accepted as substitutes for it.

The variadic operators also accept an inert function-style author answer that
preserves the binder, using `(index, domain)` or `(index, lower, upper)` as the
second argument. For example:

```html
correct-answer="Union({k}, (k, {1, 2}))"
correct-answer="Min(k**2, (k, {1, 2}))"
correct-answer="Max(k**2, (k, 1, 4))"
```

These strings are normalized to the same canonical answer during `prepare()`;
they are not treated as evaluated variadic SymPy expressions.

## Grading

`exact` requires an identical canonical operator, form, direction, index, and exact SymPy components. `component` compares visible components independently. `equivalent` constructs binder-aware Sum, Product, Integral, or Limit objects where possible. Domain equivalence expands only a concrete `FiniteSet`; symbolic or infinite domains fail explicitly rather than being expanded eagerly. Bounded forms of variadic operators have no faithful SymPy binder and are likewise reported as unsupported for equivalent grading; use `exact` or `component` for those forms.

If no correct answer is supplied through an attribute, `data["correct_answers"]`,
or the prepared-answer cache, the element is ungraded. It still parses and stores
the combined canonical response, but it does not create a partial score. Submission
panels display the response without a score badge, and answer panels render nothing.
Blank-response validation remains controlled separately by `allow-blank`.
