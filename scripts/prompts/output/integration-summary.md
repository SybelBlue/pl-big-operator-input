# Publication-readiness integration summary

## Integrated changes

- Added failing-first regressions for stale field errors, stale scores, correct-answer policy bypasses, component badge equivalence, and malformed persisted state. The regressions failed for the audited reasons before the controller fixes were applied.
- Component reparses now clear obsolete errors; invalid attempts replace prior scores with zero and refresh weighted scoring; component badges use the same equivalence predicate as grading.
- Whole, component, and canonical correct answers now share set, complex-number, and declared-symbol validation. Malformed submitted state falls back during rendering and grades as zero; malformed author state raises a descriptive error.
- Mathematical fragments use PrairieLearn parsing. Wrapper indices use lexical validation, and both supported `Limit` spellings use an explicit grammar. The only remaining `sympy.sympify` is the documented trusted canonical-JSON compatibility seam for the pinned PrairieLearn round-trip gap, with its removal condition tracked inline and in `parser-migration.md`. No direct `sympy.parse*` call remains in project-owned code.
- Added parser compatibility/security characterization in `test_parser_compatibility.py`, strict pytest marker registration, automatic unit classification, and smoke/regression/unit/publication Makefile entry points. The default `test` target remains comprehensive.

## Resolved recommendation conflicts

- The core audit's example treated a bare symbol in a set-valued field as scalar. Existing documented behavior and tests intentionally allow a bare symbol to represent an abstract set. That contract is preserved; concrete scalar expressions such as `1` and `k + 1` are rejected consistently for author and student routes.
- The inventory proposed leaving unit tests unmarked, while the integration prompt explicitly required smoke, regression, or unit marking. The integration prompt wins: collection assigns `unit` to otherwise-unclassified tests.
- The inventory proposed deleting CSS-source assertions after browser replacements. No browser harness exists in this repository, so those tests were retained rather than creating an unrecorded coverage gap. They remain candidates for replacement once the separately recommended browser gate exists.
- The parser audit permits one narrow `sympify` compatibility seam until PrairieLearn provides a lossless canonical decoder; the integration prompt permits remaining calls only with rationale and follow-up. The retained call satisfies both constraints and is never reachable from student parsing.

## Final verification and counts

- Full Python suite: **287 passed** (282 element cases plus 5 script cases).
- Element markers: **13 smoke**, **15 regression**, **254 unit**. Markers may overlap where a publication-critical test is also a focused unit contract.
- Feature files: `test_parser_compatibility.py` **12**, `test_pl_big_operator_input.py` **260**, `test_readme_examples.py` **10**.
- Pyright: **0 errors, 0 warnings** using the project Python 3.13 interpreter.
- Ruff format check: **21 files already formatted**.
- PrairieLearn schema validation: passed against the pinned upstream schemas.
- `git diff --check`: passed.
