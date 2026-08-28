# Adversarial audit: `pl-big-operator-input.py`

## Executive summary

The lifecycle is generally coherent on its intended, well-formed path, and the existing controller suite passes (253 tests). The audit nevertheless confirmed five defects. The most serious are persistent state from an earlier attempt, which can show an obsolete parse error or retain a previously earned score, and inconsistent validation of correct-answer encodings, which permits canonical/whole answers that students are forbidden to enter. Component score badges can also contradict the score actually awarded.

Ranked findings:

| Rank | Severity | Confidence | Finding |
|---:|---|---|---|
| 1 | High | High | A valid repeated parse does not clear a stale component format error |
| 2 | High | High | An invalid later attempt can retain the previous attempt's score |
| 3 | High | High | Canonical and whole correct answers bypass student set, complex-number, and symbol-policy checks |
| 4 | Medium | High | Component badges use structural equality although grading uses symbolic equivalence |
| 5 | Low | High | Malformed nested `QuestionData` values and partial canonical submissions raise uncaught exceptions |

Two additional risks require product/security decisions: unbounded SymPy work on student-shaped input, and use of `sympy.sympify` on trusted author data. No implementation files were modified.

## Lifecycle and representation trace

1. `prepare()` calls `_config()` and `_correct()` (lines 779–783). Correct answers may begin as an element string, component strings, a SymPy object/JSON leaf, or a canonical operator dictionary. `_formatted_answer()`, `_binder()`, `_component_values()`, or `_structured()` turn these into the version-1 canonical dictionary. Each mathematical leaf is PrairieLearn SymPy JSON.
2. `render(question)` delegates each visible field to the vendored symbolic input and displays raw field strings. `render(answer)` decodes canonical leaves to SymPy, converts them to TeX, and renders the correct expression. Every other panel is treated as a submission panel; it prefers the canonical submitted answer but falls back to raw strings (lines 994–1018).
3. `parse()` delegates each component string to symbolic input, receives SymPy JSON in per-field `submitted_answers`, decodes it back to SymPy for wrapper validation, and re-encodes all fields into one canonical operator expression (lines 1059–1154). Direction remains a public enum string, not SymPy JSON. Allowed whole blanks are represented by `""`; invalid/incomplete answers by `None`.
4. `grade()` decodes submitted and correct canonical leaves. Exact grading compares canonical dictionaries; component grading uses symbolic equivalence per component and weights the body; equivalent grading constructs a SymPy binder/operator and evaluates/simplifies the two expressions (lines 1240–1285). It stores an element partial score and invokes PrairieLearn weighted-score aggregation.

This round trip is not validation-equivalent across entry routes: student strings receive the strongest checks, component correct-answer strings receive most wrapper checks, and canonical/whole author forms receive fewer policy checks. Findings 1–4 arise at these transition boundaries.

## Confirmed defects

### 1. High: successful reparses retain stale component format errors

**Confidence:** High (directly reproduced)

**Affected code:** `_parse_values()`, especially lines 1092–1110; `parse()`, lines 1132–1136. The direction field explicitly removes its prior error at line 1151, but mathematical fields never do so after successful delegated parsing.

**Minimal reproducer:**

```python
markup = html(operator="sum")
state = data(raw={"op-start": "bad@", "op-end": "2", "op-body": "k"})
mod.parse(markup, state)
assert "op-start" in state["format_errors"]

state["raw_submitted_answers"]["op-start"] = "1"
mod.parse(markup, state)
assert state["submitted_answers"]["op"]["lower"]["_value"] == "1"
assert "op-start" not in state["format_errors"]  # fails
```

**Expected:** Once `op-start` parses successfully, its old error is removed; the valid canonical answer renders as valid.

**Actual:** The canonical answer is successfully built, but `format_errors["op-start"]` still contains the old syntax error. Question rendering continues to mark that field invalid. If a later parse enters the early blank path, lines 1132–1136 can also use that stale error to store the whole answer as `None`.

**Smallest regression test:** Add the reproducer as `test_component_parse_clears_stale_format_error_after_valid_reparse`, checking both absence of the key and a non-`None` canonical answer. This complements the existing direction-only stale-error test.

### 2. High: an invalid later attempt can retain an earlier score

**Confidence:** High (directly reproduced)

**Affected code:** `grade()`, lines 1248–1250. The early return for missing/non-dictionary submitted answers does not clear or replace `partial_scores[answer]`, then does not rerun weighted aggregation.

**Minimal reproducer:**

```python
markup = html(operator="sum", **{"correct-answer": "Sum(k,(k,1,2))"})
state = data(raw={"op-start": "1", "op-end": "2", "op-body": "k"})
mod.prepare(markup, state)
mod.parse(markup, state)
mod.grade(markup, state)
assert state["partial_scores"]["op"]["score"] == 1

state["raw_submitted_answers"]["op-body"] = "bad@"
mod.parse(markup, state)
mod.grade(markup, state)
assert state["submitted_answers"]["op"] is None
assert state["partial_scores"]["op"]["score"] != 1  # fails: still 1
```

**Expected:** The invalid current attempt must not report or contribute the old perfect score. Depending on PrairieLearn convention, grading should delete the element partial score or replace it with zero while preserving format-error behavior.

**Actual:** The old `{score: 1.0, weight: 1}` remains. Submission/question rendering can display the obsolete score, and aggregate score data remains stale when the same dictionary is reused.

**Smallest regression test:** `test_invalid_reparse_clears_previous_partial_score`, performing exactly two parse/grade cycles on one state and asserting the agreed invalid-attempt score semantics plus refreshed weighted-score data.

### 3. High: correct-answer routes bypass policies enforced on students

**Confidence:** High (set and complex cases directly reproduced; symbol-scoping follows the same code path)

**Affected code:** `_structured()`, lines 581–620; `_formatted_answer()`, lines 693–742; `_decode()`, lines 520–554. Compare `_component_values()` lines 646–647 and student `_parse_values()` lines 1105–1107. Structured leaves are only required to decode to `sympy.Basic`; whole formatted answers do not call `_requires_set`; `_decode` does not apply `allow_complex` or an allowed-symbol check.

**Minimal set reproducer:**

```python
markup = html(**{"correct-answer": "Union(k, (k, 1))"})
state = data()
mod.prepare(markup, state)  # accepted; domain is scalar 1, body is scalar k

student = data(raw={"op-domain": "1", "op-body": "k"})
mod.parse(markup, student)
assert student["format_errors"]["op-domain"] == "This field must be a set."
assert student["format_errors"]["op-body"] == "This field must be a set."
```

**Minimal complex reproducer:** create a canonical sum answer whose body leaf is `_json(sympy.I)` while `allow-complex` is false, place it in `correct_answers["op"]`, and call `prepare()`. It is accepted. Parsing student body `i` (or `I`) is rejected as an invalid/disallowed symbol, so the configured correct value cannot be submitted.

A canonical leaf containing an undeclared symbol is likewise accepted by `sympy.sympify`, while the student parser restricts symbols to `variables` plus the body index.

**Expected:** Every correct-answer representation should obey the same semantic contract as the corresponding student field: set-valued domain/set-combinator body, complex policy, variable scope, and custom-function policy. Invalid author configuration should fail in `prepare()`.

**Actual:** Encoding choice changes validation. Some accepted questions are impossible to answer; others make grading behavior depend on an undeclared symbol or function unavailable in the UI/parser.

**Smallest regression tests:**

- Parameterize `Union(k, (k, 1))` and `Union({k}, (k, 1))`, asserting `prepare()` rejects the non-set domain/body respectively.
- Mutate a known-good canonical answer with a scalar set field and assert `_structured()` rejects it.
- Mutate a canonical leaf to `I` with `allow-complex="false"` and to an undeclared symbol, asserting `prepare()` rejects both.

### 4. Medium: component badges contradict component grading

**Confidence:** High (directly reproduced)

**Affected code:** `_component_scores()`, lines 822–841, versus `grade()`, lines 1257–1271. The former uses Python/SymPy structural `==`; the latter calls `_expressions_equivalent()`.

**Minimal reproducer:**

```python
markup = html(operator="sum", **{
    "grading-method": "component",
    "correct-answer-start": "1",
    "correct-answer-end": "2",
    "correct-answer-body": "(k+1)^2",
})
state = data(raw={"op-start": "1", "op-end": "2", "op-body": "k^2+2*k+1"})
mod.prepare(markup, state)
mod.parse(markup, state)
mod.grade(markup, state)
assert state["partial_scores"]["op"]["score"] == 1
assert mod._component_scores(mod._config(markup, state), state)["body"] == 1  # fails: 0
```

**Expected:** The body badge is correct because the exact equivalence predicate that awarded its points returns true.

**Actual:** The total badge reports 100%, but the body field reports incorrect.

**Smallest regression test:** The reproducer above, ideally also asserting rendered question HTML contains a correct rather than incorrect body badge.

### 5. Low: malformed nested state raises uncaught exceptions

**Confidence:** High (directly reproduced)

**Affected code:** `_raw_correct_answer()` line 157 assumes `correct_answers` is a mapping; `_values()` lines 1157–1169 indexes every canonical component; `_component_scores()`, `_submitted_tex()`, and `grade()` trust any dictionary tagged by location as complete canonical data.

**Minimal reproducer:**

```python
state = {
    "params": {}, "panel": "submission", "raw_submitted_answers": {},
    "correct_answers": {"op": valid_canonical},
    "submitted_answers": {"op": {}},
}
mod.render(html(operator="sum"), state)  # KeyError: 'lower'

state["panel"] = "question"
mod.grade(html(operator="sum"), state)   # KeyError: 'lower'
```

Also, `{"correct_answers": None}` raises `AttributeError` in `_raw_correct_answer`, and analogous non-mapping values fail at other nested `.get()` calls.

**Expected:** For corrupted/partially restored student state, rendering should fall back to raw/placeholder TeX, and grading should decline to grade or record a controlled format error. Author-side malformed correct state should raise a descriptive `ValueError`, not an incidental `KeyError`/`AttributeError`.

**Actual:** Submission rendering or grading aborts the element request with an implementation exception.

**Smallest regression test:** Parameterize missing canonical keys in submission and correct dictionaries across `render(submission)`, `render(answer)`, and `grade()`, asserting controlled behavior and a descriptive author error for malformed correct answers.

## Risks requiring product or security decisions

### A. High risk, high confidence: unbounded symbolic parsing/evaluation can consume request resources

Student-controlled components flow into SymPy parsing and, for equivalent grading, `_construct()`, `.doit()`, `expand()`, `simplify()`, and `.equals()` (lines 1172–1237) with no input-size, AST-size, operation-count, domain-cardinality, or time budget. Concrete domain forms eagerly allocate one substituted term per `FiniteSet` member at line 1202. Large bounds, deeply nested expressions, expensive limits/integrals, or very large finite sets are denial-of-service-shaped inputs. Exception catches do not address CPU/memory exhaustion, `RecursionError`, or all SymPy failure modes.

**Decision needed:** Define platform-level versus element-level resource limits. If PrairieLearn already isolates grading with a hard deadline/memory limit, document and test that boundary; otherwise add conservative source/AST/domain limits or a cancellable grading budget.

**Minimal protective test:** Run an intentionally expensive but syntactically valid equivalent comparison under the chosen deadline and assert a controlled incorrect/format result, not a worker timeout. Avoid a deterministic giant expression in the ordinary unit suite; mark it as a resource-limit integration test.

### B. Medium risk, high confidence: author-data decoding uses unrestricted `sympy.sympify`

`_decode()` calls `sympy.sympify` directly on correct-answer strings and most SymPy JSON `_value` strings (lines 528–547). SymPy documents `sympify` as using evaluation and unsuitable for unsanitized input. The comments call these leaves trusted author answers, so exploitability depends entirely on the course-author/server-data trust boundary.

**Decision needed:** Explicitly classify `correct_answers` and element attributes as executable/trusted author input. If they can be influenced by less-trusted question generators, imports, or stored data, replace direct sympification with a restricted decoder/allowlist and validate canonical leaves.

**Minimal security test:** Once the trust policy is selected, test that a benign forbidden constructor/payload is rejected without side effects, or document that author code already has equivalent execution authority.

### C. Low risk, high confidence: global `weight` accepts surprising values

`weight` is read as `int(get_integer(...) or 1)` at line 512: zero silently becomes one, while negative values remain negative. The schema declares only `type: integer`, unlike the explicit positive validation for body-relative weight. This may corrupt or unexpectedly alter aggregate scoring, but the intended PrairieLearn semantics are not stated here.

**Decision needed:** Decide whether weight must be positive, nonnegative, or may be negative. Validate consistently in controller and schema. A regression test should cover `0` and `-1` under the chosen policy.

## Additional observations

- Exact grading compares full canonical JSON dictionaries. Because both normal student and correct paths are re-canonicalized, this is internally consistent, but it intentionally makes direction and representation part of equality.
- Direction parsing is better isolated than mathematical components: invalid selections clear the whole submitted answer, and a later valid selection removes the stale direction error. Finding 1 is specifically the missing analogous cleanup for delegated fields.
- All unknown render panels fall into the submission branch (line 1009). If PrairieLearn guarantees the three panel values this is harmless; otherwise an explicit panel check would make malformed state easier to diagnose.
- `_split_top_level()` tracks nesting and simple quotes but accepts negative/unbalanced depth and treats any quote preceded by a backslash as escaped without backslash-parity handling. This affects trusted correct-answer inference rather than student parsing and usually degrades to a configuration error; no separate user-impacting defect was demonstrated.
- Submission fallback TeX interpolates raw strings (lines 945–968). Mustache HTML escaping prevents direct HTML injection, but MathJax macro/security and maximum-input behavior should be covered by platform policy, particularly for malformed submissions.

## Verification performed

- Read the complete controller and vendored symbolic-input adapter/parser paths used by it.
- Ran `python -m pytest -q elements/pl-big-operator-input/tests/test_pl_big_operator_input.py`: **253 passed**.
- Ran focused two-attempt lifecycle experiments for stale field errors and stale scores.
- Ran focused correct-answer experiments for scalar union domains/bodies and canonical complex leaves.
- Ran an equivalently graded expanded-polynomial component experiment and compared awarded versus displayed component scores.
- Exercised partial canonical submission dictionaries through submission rendering and grading; both raised `KeyError` as described.

