# Implement `pl-big-operator-input`

Generalize the existing `pl-big-operator-input` PrairieLearn element into
`pl-big-operator-input`. Treat
`elements/pl-big-operator-input/pl-big-operator-input.schema.json` as the
authoritative API specification at the start of this task, including any edits
made after this prompt was written.

This is an intentional breaking change. Do not retain compatibility aliases for
the old element name or its removed attributes.

## Rename the element

Rename the element directory and every element-owned file from
`pl-big-operator-input` to `pl-big-operator-input`. Update the controller,
schema, Mustache templates and partials, JavaScript, CSS, tests, documentation,
`info.json`, HTML tags, DOM IDs, CSS classes, Python identifiers, test helpers,
and repository references accordingly.

Use operation-neutral terminology throughout:

- `summand` becomes `body`.
- `sigma` becomes `operator` or `operator-stack`, as appropriate.
- `piecewise` grading becomes `component` grading.
- Internal answer suffix `-summand` becomes `-body`.
- Avoid names tied specifically to sums or integrals unless the code path is
  genuinely specific to that operator.

Do not rename mathematical `sympy.Sum` concepts when the code is specifically
handling a SymPy sum.

## Implement the schema API

Support the exact attributes and enum values declared by the edited schema.
In particular, implement these operators:

| `operator` | LaTeX | SymPy operation |
| --- | --- | --- |
| `sum` | `\\sum` | `sympy.Sum` |
| `product` | `\\prod` | `sympy.Product` |
| `integral` | `\\int` | `sympy.Integral` |
| `limit` | `\\lim` | `sympy.Limit` |
| `union` | `\\bigcup` | `sympy.Union` |
| `intersection` | `\\bigcap` | `sympy.Intersection` |
| `disjoint-union` | `\\bigsqcup` | `sympy.sets.DisjointUnion` |
| `and` | `\\bigwedge` | `sympy.And` |
| `or` | `\\bigvee` | `sympy.Or` |
| `min` | `\\min` | `sympy.Min` |
| `max` | `\\max` | `sympy.Max` |

Resolve `limits="auto"` as follows:

- `bounds`: `sum`, `product`, and `integral`.
- `approach`: `limit`.
- `domain`: `union`, `intersection`, `disjoint-union`, `and`, `or`, `min`, and
  `max`.

Validate explicit operator/limits combinations. Permit:

- `bounds` or `domain` for `sum`, `product`, `union`, `intersection`,
  `disjoint-union`, `and`, `or`, `min`, and `max`.
- only `bounds` for `integral`.
- only `approach` for `limit`.

Reject invalid combinations during `prepare()` with an actionable error.

Render the three limit forms as follows:

- `bounds`: lower bound, upper bound, and body inputs. For non-integrals, show
  `index-variable =` before the lower bound. For integrals, show bare bounds and
  append the differential using `index-variable`.
- `domain`: domain and body inputs, displayed as
  `index-variable \\in <domain>` beneath the operator.
- `approach`: target and body inputs, displayed as
  `index-variable \\to <target>` beneath `\\lim`. Render
  `limit-direction="from-left"` with a minus superscript,
  `limit-direction="from-right"` with a plus superscript, and `two-sided`
  without a directional superscript.

Use namespaced child answer names:

- bounds: `<answers-name>-start`, `<answers-name>-end`, and
  `<answers-name>-body`;
- domain: `<answers-name>-domain` and `<answers-name>-body`;
- approach: `<answers-name>-target` and `<answers-name>-body`.

Only create and parse fields relevant to the resolved limits form.

## Canonical answer representation

Use one flat, versioned dictionary as the canonical combined answer for every
operator. Serialize each mathematical component with PrairieLearn's SymPy JSON
utilities so the complete value remains JSON-safe. Its logical shape is:

```python
{
    "_type": "operator_expression",
    "_version": 1,
    "operator": "sum",
    "limits": "bounds",
    "index": <SymPy expression>,
    "lower": <SymPy expression>,
    "upper": <SymPy expression>,
    "body": <SymPy expression>,
}
```

The keys after `index` depend on `limits`:

- `bounds`: `lower`, `upper`, `body`;
- `domain`: `domain`, `body`;
- `approach`: `target`, `direction`, `body`.

Use the public direction values `two-sided`, `from-left`, and `from-right` in
the dictionary. Do not expose SymPy's `+`, `-`, or `+-` direction encoding in
the public representation.

Keep the structural dictionary canonical even where a corresponding SymPy
operation exists. SymPy `Union`, `Intersection`, `DisjointUnion`, `And`, `Or`,
`Min`, and `Max` are variadic operations and do not preserve an indexed binder.
Do not invent fake SymPy binder classes or pretend those variadic objects can be
losslessly converted back into an index, domain, and body.

Accept binder-aware SymPy objects as author conveniences where conversion is
lossless:

- `sympy.Sum` with bounds;
- `sympy.Product` with bounds;
- `sympy.Integral` with bounds;
- `sympy.Limit` with an approach target and direction.

Normalize those objects into the canonical dictionary during `prepare()`. For
domain forms and variadic operators, require the canonical structured answer.
If the existing PrairieLearn correct-answer pipeline cannot safely store the
outer dictionary using `_type`, choose a non-conflicting discriminator name and
document the adjustment; do not discard the structured representation.

## Parsing and grading

Parse each visible field independently with the existing PrairieLearn/SymPy
parser and allowed-variable rules. Automatically allow `index-variable` in the
body. Preserve useful parsing errors and `allowed-blank` behavior.

Implement the schema's grading methods:

- `exact`: require the same operator, limits form, direction where applicable,
  and exact SymPy equality for every mathematical component.
- `component`: grade the visible limit components and body independently. Give
  each limit component weight 1 and the body `body-relative-weight`.
- `equivalent`: require the same operator and compatible limits structure, then
  use operator-aware symbolic equivalence. Preserve the existing sum and
  integral equivalence behavior where mathematically valid, extend it to
  `Product` and `Limit` only where supported reliably, and use the corresponding
  SymPy variadic operation for a concrete finite expansion when that conversion
  is well-defined. Never claim equivalence merely because two displays share a
  glyph or because a binder was discarded.

Fail explicitly for an unsupported equivalence case rather than silently using
an incorrect transformation. Keep grading deterministic and avoid eager
expansion of symbolic or infinite domains.

## Rendering and accessibility

Refactor the Mustache and CSS layout around generic operator, limits, and body
components. Preserve the current compact visual alignment for sums and
integrals, and add suitable layouts for domain annotations and approach
annotations. Submission and correct-answer panels must reconstruct the complete
notation for every operator and limits form.

Give the overall control and each field operator-neutral, descriptive accessible
labels. Do not leave sigma- or summand-specific labels in generated HTML.

## Documentation, examples, and tests

Rewrite the element README around the new API and structured answer format.
Document the operator/limits compatibility matrix, automatic limits resolution,
direction semantics, child answer names, grading behavior, and the distinction
between binder-aware and variadic SymPy objects.

Update all in-repository example questions to the new element name and API.
Add representative examples for at least:

- a bounded sum;
- a bounded product;
- an integral;
- a one-sided limit;
- a domain-indexed union;
- a domain-indexed conjunction.

Expand the tests to cover every operator, every valid limits form, every invalid
operator/limits combination, all automatic limits defaults, all limit
directions, structured-answer serialization, rendering, parsing, each grading
method, accessibility labels, and rejection of malformed correct answers.

Run the focused element tests and the repository's relevant format, lint, and
type checks. Finish with `git diff --check`. Report any behavior that could not
be represented faithfully in SymPy rather than weakening the data model.
