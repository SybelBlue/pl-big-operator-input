# Parser migration: remove direct SymPy parsing

## Goal and scope

Remove direct parsing from project-owned code, route mathematical text and SymPy JSON through `prairielearn.sympy_utils` (PSU), and treat the non-mathematical pieces of the legacy whole-answer syntax as a small, explicitly validated grammar. The vendored `pl-symbolic-input` directory must remain byte-for-byte unchanged.

The repository currently contains no call to `sympy.parse_expr`, `parse_latex`, `parse_mathematica`, `parse_maxima`, or another `sympy.parse*` API. It contains four production `sympy.sympify` calls and one test-only call. The production calls are all in `elements/pl-big-operator-input/pl-big-operator-input.py`.

“Trusted author input” below means question HTML attributes, `correct_answers` populated by question `server.py`, or their persisted PrairieLearn representation. It is not student input, but malformed or hostile course content must still fail closed. “Untrusted student input” means `raw_submitted_answers` and any submitted JSON derived from it.

## Inventory

| Site | Input and trust boundary | Accepted language today | Output | Direct callers / consumers | Migration |
|---|---|---|---|---|---|
| `_infer_spec`, formatted index (`sympify(formatted[1][0])`, currently near line 253) | Index token extracted from a trusted author whole-answer string | Full `sympify` language, although only a `Symbol` result is used | `Symbol` or any SymPy/Python value, then `_symbol_name` narrows it to `str | None` | `_config`; operator/limit/index inference during `prepare`, `render`, `parse`, and grading | Replace with an identifier helper using `re.fullmatch` and `sympy.Symbol`. Do not parse mathematical syntax here. Invalid tokens produce no inferred index. |
| `_decode`, `_type: sympy` fast path (`sympify(source, locals=...)`, near line 539) | Canonical/legacy SymPy JSON from trusted author or normalized answer data | SymPy/Python textual form emitted in `_value`; locals contain declared symbols plus `_Exp1` and `_ImaginaryUnit` | Arbitrary result from `sympify`; downstream normally requires `Basic` or a known binder | `_infer_spec`, `_infer_direction`, `_structured`, `_component_values`, `_correct`, `_values`; indirectly all lifecycle functions | Use `psu.json_to_sympy(..., allow_sets=True)` for values it supports. Temporarily retain one narrowly named legacy JSON fallback only for exact upstream round-trip gaps described below; validate the decoded result against the expected context/type immediately. Preserve the full JSON metadata rather than rebuilding locals where PSU works. |
| `_decode`, bare string (`sympify(value, locals=...)`, near line 545) | Trusted author correct answer, either an attribute/component or old whole-answer string | Unrestricted SymPy textual language | Arbitrary Python/SymPy value; later paths require `Basic`/matching binder | `_infer_spec` fallback and `_correct`; `_component_values` normally chooses `_parse` for strings and does not use this branch | Remove. Component mathematical strings go to `_parse`/`psu.convert_string_to_sympy`. Whole answers go to the explicit wrapper grammar and direct constructors. Raw `sympy.Basic` objects remain already-structured data and are returned unchanged. Unknown strings fail with the existing author-facing `ValueError`. |
| `_formatted_answer`, formatted index (`sympify(limits[0])`, near line 710) | Index field in a trusted author `Sum(...)`, `Limit(...)`, etc. wrapper | Full `sympify` language, followed by equality with `Symbol(config.index)` | Arbitrary result, used only as an index identity check | `_correct` for string whole answers; `_infer_spec` has a parallel inference path | Replace with the same identifier helper, compare the resulting name to `config.index`, and construct `sympy.Symbol(config.index)` only after validation. |
| Test assertion (`sympify(body)`, test file near line 563) | Fixed parametrized test literal (`{k}` or `k**2`) | Full `sympify` language | SymPy expression/set | `test_prepare_normalizes_function_domain_binders` only | Replace expected values with direct constructors (`FiniteSet(Symbol("k"))`, `Symbol("k") ** 2`) or use `_parse` when the parser itself is the subject of the assertion. Project tests should not normalize use of the forbidden API. |
| `_parse` / `psu.convert_string_to_sympy` | Trusted author component text and fragments extracted from a whole-answer wrapper | PrairieLearn mathematical expression language: declared variables/custom functions, hidden constants, sets, trig; plus the local compatibility rewrites `infinity -> infty` and spaced trig names | `sympy.Basic` (annotated by PSU as `Expr`) | `_component_values`, `_formatted_answer` | Keep as the sole mathematical-text entry point. Pass the precise component variable set and custom functions. Add an explicit `isinstance(result, sympy.Basic)` check because sets are valid although PSU's annotation says `Expr`. |
| `_decode` / `psu.json_to_sympy` special branch | `_type: sympy` JSON from trusted author or canonical answer storage; selected today by a source-string heuristic for `{`, `[`, ` ∪ `, or ` ∩ ` | PSU SymPy JSON, internally reparsed using the restricted PrairieLearn expression language | `sympy.Expr`/`sympy.Set` | All `_decode` callers listed above | Remove source-string dispatch. Attempt the public JSON decoder first for every SymPy JSON value, without mutating or discarding `_variables`, `_assumptions`, or `_custom_functions`. Handle only classified upstream failures in the temporary legacy seam. |
| `_parse_values` / `psu.json_to_sympy` | JSON produced by the vendored symbolic-input parser from untrusted student text | PSU SymPy JSON with sets and the configured complex-number policy | `sympy.Basic`, then constrained to a set where required | Public `parse`; later canonicalization and grading | Keep. This is the correct untrusted boundary. Continue passing `allow_sets=True` and `allow_complex=config.allow_complex`, enforcing component type after decoding, and turning every decoder exception into a field format error. No fallback is permitted for student data. |
| `symbolic_input_adapter.parse` -> vendored `CONTROLLER.parse` | Untrusted `raw_submitted_answers` | Pinned upstream `pl-symbolic-input` language configured by generated markup | Submitted PSU JSON or a format error | `_parse_values` | Keep delegation. Do not edit or bypass the vendored element. The adapter is the integration boundary. |
| `_json` / `psu.sympy_to_json` | Already-structured, project-constructed SymPy values | No text input; serializer supports sets when enabled | Canonical PSU JSON dictionary | `_canonical`, hence correct/submitted structured answers | Keep. Add round-trip coverage because its documented counterpart is not currently a total inverse. |

The hand-written `_formatted_call`, `_split_top_level`, and `_formatted_direction` functions are also parsers, though they do not call SymPy. They currently accept a broad wrapper shape, track delimiters and quotes incompletely, and return raw strings. They should become an explicit compatibility grammar rather than a precursor to general evaluation.

## Target design

### 1. Separate lexical and mathematical parsing

Introduce one helper for symbol names, used by both inference and normalization. Its grammar should be explicit and shared with configuration validation, for example `re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", token.strip())`. Before implementation, reconcile this grammar with PSU's accepted variable-name rules; if PrairieLearn permits a required Unicode identifier, encode that rule explicitly rather than falling back to SymPy. The helper returns the name (or `None`/raises according to its caller), and callers create known symbols with `sympy.Symbol(name)`.

Likewise, validate rather than parse:

- wrapper names against the fixed `OPERATOR_SNAKECASE` reverse map;
- direction literals against exactly the quoted tokens `"+"`, `"-"`, and `"+-"`;
- `operator`, `limits`, and public direction names against their existing finite maps;
- delimiter balance, quote closure, argument count, and absence of trailing text with `re.fullmatch` plus a small scanner.

Only body, lower, upper, domain, and target fragments are mathematical expressions. Send those fragments to `_parse`. Build binders with `sympy.Sum`, `Product`, `Integral`, `Limit`, `Union`, `Intersection`, `DisjointUnion`, `Min`, or `Max` after the wrapper has been validated. No constructor name should come from an evaluated string.

Support the two documented legacy `Limit` spellings explicitly if compatibility requires them:

- `Limit(body, (index, target, 'direction'))`;
- `Limit(body, index, target, dir='direction')`.

The latter needs a dedicated exact grammar for the keyword, not Python keyword-argument evaluation. Any other keyword, extra argument, attribute access, indexing, comprehension, lambda, or statement is rejected. If repository documentation does not promise that second spelling, deprecate it first and remove it after a release rather than retaining general `sympify` for it.

### 2. Make `_decode` type-directed

Replace the overloaded behavior with distinct operations:

1. `decode_sympy_json(value, *, expected, allow_complex)` accepts only a dictionary with the exact PSU SymPy JSON envelope and calls `psu.json_to_sympy` first.
2. `parse_math_text(source, variables, custom_functions)` wraps `_parse` and is used only for trusted author mathematical fields/fragments.
3. Already-structured `sympy.Basic` values are accepted without parsing where the public correct-answer contract permits them.
4. Operator-expression dictionaries are decoded field by field and checked for exact keys, version, operator, limits, direction, and expected component types.

Do not let a bare string reach JSON deserialization. Do not let submitted JSON reach a legacy fallback. Validate decoded outputs as `sympy.Basic`, then more narrowly as `Symbol`, `Set`, or the expected binder class where applicable.

### 3. Canonical SymPy JSON compatibility and the upstream gap

At pinned PrairieLearn revision `14e65830861bee4cfe10c3ef73b000794edd66ed`, `sympy_to_json` serializes using a SymPy-oriented printer, but `json_to_sympy` calls `convert_string_to_sympy`, whose allowlist is the student-expression language. Therefore the two public APIs are not inverses for all values they advertise/emit. Confirmed examples include:

- binder tuples: `Sum(k, (k, 1, 4))` fails because the tuple is interpreted/rejected by the expression parser; domain binders such as `Integral(z, (z, Gamma))` also fail;
- relations: `Eq(x, 1)` is an invalid function and `x < 2` is an invalid expression;
- set forms vary: finite sets, intervals, and ordinary printed `Union(...)` can round-trip at this pin, but this is not sufficient assurance for unevaluated unions/intersections, nested set operations, relational set members, or printer forms containing union/intersection glyphs. They need a matrix test rather than a source-prefix heuristic.

The exact upstream gap is: **`prairielearn.sympy_utils.json_to_sympy` lacks a safe, lossless deserializer for every canonical value produced by `sympy_to_json`, notably binder tuples and Boolean/relational nodes, with complete set union/intersection coverage.** The desired upstream API is either a safe AST/constructor-based canonical deserializer or a `json_to_sympy` canonical mode whose accepted node set matches `sympy_to_json` and does not expand the student-input grammar.

Until that API exists, retain at most one direct `sympy.sympify` call in a clearly named `decode_trusted_legacy_sympy_json` compatibility function. This is justified only for trusted canonical author JSON, never student input or arbitrary strings. It must:

- require an exact `_type == "sympy"` envelope and bounded string input;
- construct locals only from validated `_variables`/expected configuration variables and known constants/functions;
- reject names not represented in the JSON metadata or an explicit constructor allowlist;
- validate the result immediately against an expected class/shape (known binder, relation, or set);
- catch a narrow set of known PSU round-trip failures, not all exceptions;
- carry an inline rationale and an upstream issue/reference, and be removed when the pinned PSU API closes the gap.

If a safe constructor-based compatibility decoder can be implemented entirely from already-structured metadata and an explicit AST node allowlist, prefer it and eliminate this last `sympify`. Do not copy or modify the vendored element and do not route canonical JSON through its student parser by hand.

### 4. Migration order

1. Add characterization tests for all current accepted formats and security failures.
2. Add identifier/direction/wrapper lexical helpers and validate `index-variable`, `variables`, and `custom-functions` consistently.
3. Route every mathematical fragment through `_parse`; build whole answers with direct constructors; remove the three non-JSON production `sympify` calls and the test call.
4. Make PSU JSON decoding unconditional-first and type-directed. Add the narrow trusted compatibility seam for only proven upstream failures.
5. Switch internal version-1 `operator_expression` data fully to component PSU JSON. Treat whole-binder `_type: sympy` as legacy input, emit only version-1 component data, and document a future removal version.
6. Run the full Python suite, lint, and type checking; verify that `rg` finds no `sympy.parse*` and either no `sympy.sympify`, or exactly the documented legacy JSON seam plus its inline rationale.

## Required compatibility tests

All existing element and README tests must pass before and after each step. Add focused tests for:

- component strings for arithmetic, hidden constants (`infty`, `E`, `I` according to configuration), spaced trig compatibility, declared variables, custom functions, sets, and complex-number policy;
- every operator and limits form, including two- and three-item binders, all three limit directions, explicit versus inferred operator/index/limits, and both supported `Limit` spellings;
- direct already-structured `sympy.Basic` correct answers, with no parsing of those objects;
- exact version-1 `operator_expression` round trips through `_canonical`, `_structured`, `_values`, rendering, and grading;
- `sympy_to_json` -> decoder equality for `Symbol`, constants, arithmetic, custom functions and assumptions, `FiniteSet`, open/closed `Interval`, nested `Union`, unevaluated/nested `Intersection`, `Complement` if emitted/supported, `Eq`, `Ne`, strict/non-strict inequalities, `Sum`, `Product`, bounded and domain `Integral`, and `Limit` in each direction;
- binder tuple fidelity: `(k, domain)` must not become an interval, and `(k, lower, upper)` must retain order and arity;
- PSU metadata fidelity for `_variables`, `_assumptions`, and `_custom_functions`;
- student submissions still flow only through vendored symbolic input plus `json_to_sympy`, preserve per-field errors, set requirements, blank behavior, partial grading, and complex-number restrictions;
- persisted legacy `_type: sympy` correct answers remain readable only for the explicitly supported compatibility window, while newly normalized answers are emitted as version-1 component dictionaries.

Where SymPy eagerly simplifies a set expression (for example an intersection becoming an interval), assert semantic equality and type/shape only where the shape is part of the contract. Use `evaluate=False` or symbolic set operands where available to exercise actual union/intersection nodes.

## Required negative and security tests

Apply these at both trusted-author and untrusted-student boundaries, asserting a controlled `ValueError`/format error and no side effect:

- Python execution payloads: `__import__('os').system(...)`, `open(...)`, `eval(...)`, `exec(...)`, lambdas, comprehensions, f-strings, and dunder/attribute traversal;
- constructor/attribute payloads in wrappers: `Symbol.__new__(...)`, `foo.bar(...)`, indexing, unknown wrapper names, unknown keywords, duplicate `dir`, trailing expressions, and text after the closing parenthesis;
- malformed structure: unbalanced/mismatched delimiters, unterminated/escaped quotes, empty required arguments, extra commas/arguments, deeply nested input, and oversized source strings;
- invalid identifiers: expressions in the index slot (`k+1`), numeric names, whitespace-separated names, dotted/dunder names, quoted names, commas, and names conflicting with PSU constants/functions;
- direction near-misses: unquoted `+`, empty strings, `++`, `sideways`, case variants, escaped/trailing characters, and public direction names placed in the SymPy direction slot;
- forged JSON: missing/extra keys where exact envelopes are required, wrong `_type`, non-string `_value`, non-list variables, hostile variable/custom-function names, inconsistent assumptions, unknown constructor names, and nested operator-expression dictionaries where PSU JSON is required;
- canonical JSON category confusion: a relational or binder supplied where a scalar component is expected, a scalar where a set is required, a binder with multiple limits, the wrong bound index, and a `Limit` with a mismatched direction;
- demonstrate that a payload submitted through `raw_submitted_answers` can never reach the trusted legacy JSON fallback, including a forged `_type: sympy` value placed in submitted-answer state;
- monkeypatch the compatibility fallback in a student parse test to raise if invoked, proving separation of the trust boundaries.

Also add a repository guard test (or CI check) that scans project-owned Python excluding `vendor/` and fails on `sympy.parse*`. It should fail on `sympy.sympify` as well once the upstream gap is closed; during the compatibility window, allow only the single named legacy decoder location.

## Exit criteria

- No project-owned mathematical string is evaluated by direct SymPy parsing.
- Identifiers, wrapper names, and directions use explicit finite/lexical validation.
- Student input uses only the pinned vendored symbolic-input flow and public PSU conversion APIs.
- Canonical component JSON uses public PSU serialization/deserialization with type checks.
- Any remaining `sympify` is the single documented, tested, trusted legacy JSON compatibility seam; its upstream removal condition is recorded.
- The vendored PrairieLearn element is unchanged.
- Compatibility, negative/security, full test, lint, and type-check suites pass.
