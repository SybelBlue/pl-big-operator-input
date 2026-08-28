# Prompt: test inventory and suite design

Audit the tests for `elements/pl-big-operator-input` without editing production or
test code. The current large test module mixes many concerns and contains extensive
parameterization. Produce `scripts/prompts/output/test-inventory.md` with:

- A classification of every test by test level (`smoke`, `regression`, or `unit`) and
  feature area (`configuration`, `answer inference`, `normalization`, `parsing`,
  `grading`, `rendering`, `schema`, `accessibility/layout`, or another justified area).
- For each test, a disposition: keep, merge/parameterize, rewrite around an invariant,
  or delete. Flag assertions that merely repeat specific output values without proving
  branching logic, contracts, or a known regression.
- A proposed file layout and pytest marker scheme. Prefer file-based feature suites;
  use classes only where they give a real shared behavioral context.
- A small publication gate: fast smoke tests, complete unit tests, and named regression
  tests tied to bugs or compatibility contracts.
- Before/after test counts and a mapping from every old node ID to its destination or
  deletion rationale, so pruning cannot silently lose coverage.

Run the existing tests and record the baseline. Do not treat line coverage alone as a
reason to keep a test. Preserve README contract tests and distinguish project-owned
tests from the vendored PrairieLearn snapshot.
