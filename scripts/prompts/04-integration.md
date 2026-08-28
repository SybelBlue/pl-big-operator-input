# Prompt: integrate publication-readiness work

Read the three audit reports in `scripts/prompts/output/` and implement the agreed
publication-readiness changes. Resolve contradictory recommendations explicitly in
the integration summary.

Work in this order:

1. Add regression tests for every confirmed core defect, observe each test fail for
   the intended reason, then fix the implementation.
2. Add characterization tests around parsing compatibility and migrate direct SymPy
   parsing one call site at a time to PrairieLearn `sympy_utils`, regular expressions,
   or direct constructors. Keep each change independently reviewable.
3. Reorganize tests into feature-specific files and mark them as smoke, regression,
   or unit. Rewrite value-enumeration tests around invariants and branch boundaries;
   delete only tests whose old node IDs have a recorded disposition.
4. Add Makefile/pytest entry points for smoke, regression, unit, and full publication
   gates. Keep the default test target comprehensive.
5. Run pytest, pyright, Ruff formatting checks, PrairieLearn schema validation, and
   `git diff --check`. Report final counts by marker and feature file.

Do not edit the vendored `pl-symbolic-input` snapshot. Do not weaken assertions merely
to make tests pass. Any remaining `sympy.sympify` call requires an inline rationale and
a tracked follow-up; no direct `sympy.parse*` calls may remain in project-owned code.
