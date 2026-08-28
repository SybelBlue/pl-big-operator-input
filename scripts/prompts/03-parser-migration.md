# Prompt: remove direct SymPy parsing

Design a migration that removes every direct call to `sympy.parse*` and replaces as
many `sympy.sympify` calls as practical in project-owned code. Do not edit code yet.
Produce `scripts/prompts/output/parser-migration.md`.

Inventory each parsing/deserialization call and document its input trust boundary,
accepted language, output types, and callers. Prefer:

- `prairielearn.sympy_utils` conversion APIs for mathematical expressions and SymPy
  JSON;
- `re.fullmatch` or similarly explicit lexical validation for identifiers, operator
  wrappers, and direction tokens that are not mathematical expressions;
- direct SymPy constructors for known symbols/constants and already-structured data.

For each current `sympify`, propose a specific replacement or justify why it must
temporarily remain. Pay special attention to canonical SymPy JSON values that
`psu.convert_string_to_sympy` may not round-trip (binder tuples, relations, sets, and
unions/intersections). Include compatibility tests and negative/security tests that
must pass before and after migration. Do not modify the vendored PrairieLearn element;
if its API is insufficient, identify the exact upstream gap rather than bypassing it.
