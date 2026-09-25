---
name: migrations
description: Route and perform repository migrations with focused source-to-target guides. Use when converting legacy schemas, APIs, persisted shapes, or content formats, or when adding migration guidance for a new transition.
---

# Migrations

Use this skill as a router. Identify the actual source format and requested target from code, data, schemas, documentation, and version history; do not assume that “old” and “new” always mean the same pair of versions.

Read only the matching migration reference from the catalog. If several migrations apply, determine their dependency order, normally oldest to newest, and validate after each transition. Do not load unrelated references.

## Catalog

| Area                    | Source → target                        | Detect the source by                                                                                         | Guide                                                                                                                                   |
| ----------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| `pl-big-operator-input` | `operator_expression` → `big_operator` | `_type: "operator_expression"`, component `correct-answer-*` attributes, or legacy operator/limit attributes | [pl-big-operator-input-operator-expression-to-big-operator.md](references/pl-big-operator-input-operator-expression-to-big-operator.md) |

If no catalog entry matches, inspect the relevant schema, implementation, documentation, and history before acting. Do not invent a migration map from names alone. A one-off migration may proceed from repository evidence, but add a reusable guide when the user asks to extend this skill.

## Shared migration rules

- Preserve behavior and user data, not merely syntax. Keep identifiers, accepted values, grading or business semantics, weights, and presentation unless the target explicitly changes them.
- Distinguish source-file conversion from persisted-data migration. Determine whether existing stored records, generated artifacts, submissions, caches, or deployed instances retain the old shape.
- Make conversions idempotent where practical: detect source and target markers, skip already-current items, and reject ambiguous hybrid states.
- Stop for a real product or author decision when the old behavior has no equivalent target representation. Report the exact mismatch and supported alternatives.
- Work only in the user’s requested scope. Preserve unrelated changes and use the repository’s narrowest meaningful validation before broader checks.

## Add or revise a migration guide

Read [adding-migration-guides.md](references/adding-migration-guides.md) only when adding or restructuring migration guidance.

Use a descriptive, stable filename in `references/`, normally `<area>-<source>-to-<target>.md`. Use concrete schema names or version labels; avoid names such as `old-to-new`, `latest`, or `migration-v2` that lose meaning as the project evolves.

Add every new guide to the catalog with source markers specific enough to route correctly. When a later target appears, add a new source-to-target guide rather than silently redefining an earlier transition. Update an existing guide in place when clarifying the same transition.
