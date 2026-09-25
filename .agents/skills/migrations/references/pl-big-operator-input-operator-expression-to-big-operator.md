# `pl-big-operator-input`: `operator_expression` to `big_operator`

Update legacy uses of this repository's element without changing the mathematical task, accepted answer, grading intent, or score weights. Work from the course root and limit edits to the questions or helpers the user placed in scope.

Read the current element documentation and schema before editing:

- `elements/pl-big-operator-input/README.md`
- `elements/pl-big-operator-input/pl-big-operator-input.schema.json`

Do not treat source edits as a data migration. PrairieLearn persists `correct_answers`, `submitted_answers`, and related dictionaries in existing variants and submissions. If the old element has already served students, identify that constraint before changing the element version: use a compatibility layer, a versioned element, new question IDs, or an explicit data migration according to the user's deployment plan. Do not silently assume old rows will be regenerated.

## Find and classify legacy uses

Search the requested question directories and shared server code for `pl-big-operator-input` plus these legacy markers:

```sh
rg -n 'operator_expression|allow-limit-direction-input|correct-answer-(start|end|domain|target|body)|index-variable=|limits=|limit-direction=|limit-size=|allowed-blank="limits"' questions
```

Also inspect custom `parse()` or `grade()` functions for the aggregate answer name and component keys ending in `-start` or `-end`. Read each affected `question.html`, `server.py`, and test before editing. Classify each answer as bounds, domain, or approaches and record its operator, index, body, and index values.

## Build one complete answer

The current element must infer the operator, index variable, and indexing form from a complete answer supplied by `correct-answer` or `data["correct_answers"][answers-name]`. Preserve `answers-name`.

Use these forms:

| Form              | Complete answer                            |
| ----------------- | ------------------------------------------ |
| Bounds            | `Func(body, (index, lower, upper))`        |
| Domain            | `Func(body, (index, domain))`              |
| Approaches        | `Limit(body, (index, target, direction))`  |
| Custom approaches | `Custom(body, (index, target, direction))` |

`Func` is one of `Sum`, `Product`, `Integral`, `Union`, `Intersection`, `DisjointUnion`, `Min`, `Max`, or `Custom`. Direction is `"+-"` for two-sided, `"-"` for from-left, or `"+"` for from-right.

Convert component attributes as follows:

```html
<!-- legacy -->
<pl-big-operator-input
  answers-name="total"
  correct-answer-body="k^2"
  correct-answer-end="n"
  correct-answer-start="1"
  index-variable="k"
  limits="bounds"
  operator="sum"
  variables="n"
></pl-big-operator-input>

<!-- current -->
<pl-big-operator-input
  answers-name="total"
  correct-answer="Sum(k**2, (k, 1, n))"
  variables="n"
></pl-big-operator-input>
```

For randomized questions, construct the same complete string in `server.py` instead of splitting it across attributes:

```python
data["correct_answers"]["total"] = f"Sum(k**2, (k, 1, {upper}))"
```

SymPy `Sum`, `Product`, `Integral`, and `Limit` answers may instead be stored with `pl.to_json(...)`. Never put a raw SymPy object in question data. Use a current `_type: big_operator` dictionary for other programmatically constructed operators.

Existing complete `Func(body, (index, ...))` answers usually remain valid. Normalize legacy `Limit(body, index, target, dir=...)` strings to the tuple form above. When explicit legacy attributes disagree with the complete answer, stop and report the inconsistency rather than choosing one silently.

An old element with no correct answer is not mechanically migratable. The new element still requires a complete configuring answer when `grading-method="none"`; that answer is shown in the answer panel. Ask the author to choose the intended answer when it cannot be derived from the prompt or existing code.

## Migrate HTML attributes

Apply this map after the complete answer captures the removed configuration:

| Legacy                                        | Current action                                            |
| --------------------------------------------- | --------------------------------------------------------- |
| `operator="sum"`, etc.                        | Remove; infer the operator from the complete answer.      |
| `index-variable="k"`                          | Remove; infer it from the complete answer.                |
| `limits="bounds"` or `"domain"`               | Remove; infer it from tuple length.                       |
| `limits="approach"`                           | Remove; use an approaches-style complete answer.          |
| `limit-direction="two-sided"`                 | Remove; encode `"+-"` in the complete answer.             |
| `limit-direction="from-left"`                 | Remove; encode `"-"` in the complete answer.              |
| `limit-direction="from-right"`                | Remove; encode `"+"` in the complete answer.              |
| `allow-limit-direction-input`                 | Rename to `allow-approach-direction-input`.               |
| `limit-size`                                  | Rename to `index-field-size`.                             |
| `allowed-blank="limits"`                      | Change to `allowed-blank="indices"`.                      |
| `correct-answer-start/end/domain/target/body` | Replace the full applicable set with one complete answer. |

Keep `answers-name`, `variables`, `custom-functions`, `operator-latex`, `grading-method`, weights, sizes, and other still-supported presentation settings unless a migration rule requires a change. Convert multi-value `variables` and `custom-functions` lists to comma-separated form because the current parser splits on commas.

For a custom operator, use `Custom(...)`, retain the required `operator-latex`, and use `grading-method="exact"`, `"component"`, or `"none"`; equivalent grading is unsupported. `operator-latex` may remain as a display override for a built-in operator.

The current schema allows `Min` and `Max` only with domain indexing. Do not mechanically translate a legacy bounded minimum or maximum. Ask the author whether to express the index set as a domain or use a bounded `Custom(...)` operator with `operator-latex="\\min"` or `"\\max"`; the latter cannot preserve equivalent grading.

## Migrate structured answers and custom grading

Translate persisted-shape literals and server-generated dictionaries with this map:

| Legacy field/value                        | Current field/value                           |
| ----------------------------------------- | --------------------------------------------- |
| `_type: "operator_expression"`            | `_type: "big_operator"`                       |
| `_version: 1`                             | unchanged                                     |
| `operator: "sum"`                         | `operator: "Sum"`                             |
| `product`, `integral`, `limit`            | `Product`, `Integral`, `Limit`                |
| `union`, `intersection`, `disjoint-union` | `Union`, `Intersection`, `DisjointUnion`      |
| `min`, `max`, `custom`                    | `Min`, `Max`, `Custom`                        |
| `limits: "bounds"`                        | `indexing: "bounds"`                          |
| `limits: "domain"`                        | `indexing: "domain"`                          |
| `limits: "approach"`                      | `indexing: "approaches"`                      |
| `operator_latex` inside the answer        | Remove; keep `operator-latex` on the element. |

Keep `_version`, `index`, `body`, `lower`, `upper`, `domain`, `target`, and `direction`; mathematical leaves remain PrairieLearn SymPy JSON. A bounds answer now has this shape:

```python
{
    "_type": "big_operator",
    "_version": 1,
    "operator": "Sum",
    "indexing": "bounds",
    "index": pl.to_json(k),
    "lower": pl.to_json(sympy.Integer(1)),
    "upper": pl.to_json(n),
    "body": pl.to_json(k**2),
}
```

Within element code or tests that already import the vendored utilities, prefer `big_operator_to_json(...)` over hand-building these dictionaries. Do not make question `server.py` depend on the element's private vendor directory. In custom grading, branch on `submitted_json.get("indexing")` and decode mathematical leaves with `pl.from_json(...)`. Update exact checks of the old type, operator, or limits values.

The aggregate key remains `data["submitted_answers"][answers-name]`. If custom code reads component fields, rename `<answers-name>-start` to `<answers-name>-lower` and `<answers-name>-end` to `<answers-name>-upper`; `-domain`, `-target`, `-body`, and `-direction` are unchanged.

## Preserve grading behavior

- Preserve `exact`, `component`, and `equivalent` unless the new operator/indexing combination disallows the existing choice.
- Use `grading-method="none"` only to replace an intentionally ungraded legacy element, never as a workaround for a malformed migration.
- Domain integrals, custom operators, and other configurations that cannot build an equivalence baseline need `exact`, `component`, or `none` as documented by the current element.
- Preserve `body-relative-weight` and `weight`.
- Add or update focused tests for custom grading and structured-answer construction. Include the intended answer, a representative wrong answer, blank behavior when relevant, and direction handling for approaches.

## Validate

After editing, repeat the legacy search and explain any intentional remaining matches. Inspect the diff for each migrated element and confirm that the complete answer encodes the same notation as the old attributes.

Run the narrowest relevant checks, then broader repository checks when practical:

```sh
make test-e2e QUESTION_PATHS=questions/<path>
make test-helpers
make typecheck
make check-format
git diff --check
```

`make test-e2e` requires `PRAIRIELEARN_PATH`. If it is unavailable, report that limitation rather than claiming lifecycle validation. In the final response, list migrated questions, non-mechanical decisions, persisted-data risks, and the exact checks run.
