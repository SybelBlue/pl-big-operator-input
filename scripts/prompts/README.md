# Publication-readiness agent prompts

These prompts split the publication work into independent discovery tracks before a
single integration pass. Run the first three prompts in parallel. They are read-only
audits whose reports become inputs to the integration prompt, so agents do not race
over the implementation or test tree.

Suggested order:

1. `01-test-inventory.md`, `02-core-python-audit.md`, and
   `03-parser-migration.md` in parallel.
2. Review and reconcile their reports.
3. Run `04-integration.md` to implement the agreed changes in small, verified commits.

All agents should preserve the vendored `pl-symbolic-input` snapshot unless the task
explicitly includes updating the pinned PrairieLearn revision.
