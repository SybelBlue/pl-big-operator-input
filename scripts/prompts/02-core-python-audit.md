# Prompt: adversarial core Python audit

Perform a read-only, adversarial audit of
`elements/pl-big-operator-input/pl-big-operator-input.py`. Produce
`scripts/prompts/output/core-python-audit.md`, ranked by severity and confidence.

Trace the complete PrairieLearn lifecycle (`prepare`, `render`, `parse`, `grade`) and
all transitions among raw strings, SymPy objects, SymPy JSON, canonical operator
expressions, and rendered TeX. Check especially:

- malformed and partially missing `QuestionData` dictionaries;
- stale submitted answers and format errors across repeated parse calls;
- inference/config mismatches, custom operators, directions, and all limit forms;
- blank handling, set requirements, complex-number policy, variable scoping, and
  custom functions;
- exception boundaries, broad catches, unsafe indexing, ambiguous strings, Unicode,
  nested delimiters, and denial-of-service-shaped inputs;
- exact/component/equivalent grading, score weights, and render-panel isolation.

For every credible issue include a minimal reproducer, expected versus actual
behavior, affected function/lines, and the smallest regression test that proves the
bug. Separate confirmed defects from risks needing product decisions. Run focused
experiments as needed, but do not modify the implementation.
