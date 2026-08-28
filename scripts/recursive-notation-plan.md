# Recursive Expanded-Body Operator UI

## Summary

Implement fixed, author-defined recursive operator notation. A nested whole correct
answer such as `Sum(Product(f(i, j), (j, 1, i)), (i, 1, n))` replaces the outer
body field with a complete nested operator UI. Explicit nesting determines operator
order; multi-binder shorthand is not added.

## Implementation Changes

- Parse nested whole answers into an internal operator tree during `prepare()`.
  Permit recognized built-in operators only, allow up to eight operator nodes, and
  reject custom or malformed nested nodes with a path-specific author error.
- Preserve existing version 1 canonical answers for nonrecursive expressions. Add a
  version 2 recursive canonical representation in which each operator node contains
  its operator, limit form, index, limit components, direction when applicable, and
  a `body` containing either another version 2 node or a terminal SymPy JSON value.
- Infer every nested node from the correct-answer tree; students edit fields but
  cannot add, remove, reorder, or change operators. Continue supporting all existing
  built-in bounds/domain/approach restrictions at each node.
- Render recursively server-side. Replace a node's body field with the child UI,
  carry outer indices into inner bounds/domains and bodies, and make each child index
  available within its subtree. Use hierarchical raw answer names such as
  `op-start`, `op-body-start`, and `op-body-body`.
- Parse visible fields recursively and assemble one version 2 submission under the
  outer `answers-name`. Apply the outer `allowed-blank` globally: `limits` covers
  every operator-limit field, `body` covers only the terminal symbolic body, and
  `all` covers both.
- Construct built-in SymPy expressions from the leaf upward for equivalent grading.
  Preserve the existing finite-domain and unsupported domain-integral behavior at
  every level. Exact grading compares the complete tree; equivalent grading rejects
  trees containing unsupported nodes.
- For component grading, compare every visible limit/direction field independently
  and compare the terminal body independently. Give every limit/direction field
  weight 1 and apply `body-relative-weight` only to the terminal body.
- Render submission and answer panels by recursively producing one complete TeX
  expression, including differentials in the nesting order established by the
  explicit tree.
- Update the element schema and README to document nested whole-answer inference,
  built-ins-only recursion, version 2 answers, lexical index scope, the depth limit,
  field naming, blank behavior, grading, and unsupported cases.

## Test Plan

- Nested bounds, domain, and approach combinations, including dependent inner bounds
  referencing outer indices.
- Recursive rendering, hierarchical answer names, TeX nesting, integral differential
  order, and answer/submission panels.
- Version 2 prepare/parse round trips and unchanged version 1 behavior for all
  existing nonrecursive questions.
- Exact, equivalent, and per-visible-field component grading, including incorrect
  inner limits, terminal bodies, and directions.
- Lexical scope tests: outer indices available below, inner indices unavailable
  above, shadowed or duplicate active index names rejected.
- Global blank-policy behavior at outer and inner levels.
- Rejection of custom nested operators, unsupported equivalence cases, malformed
  nested answers, multi-binder shorthand, and trees deeper than eight nodes.
- Run the focused element test suite and schema checks, then the repository's
  standard formatting/type checks without changing unrelated behavior.

## Assumptions

- Recursive UI topology is inferred only from an explicitly nested whole correct
  answer.
- Students cannot dynamically alter the operator tree.
- Component correct-answer attributes remain flat-only; recursive questions require
  a whole correct answer.
- Existing nonrecursive author markup, raw field names, and version 1 canonical
  answers remain backward compatible.
