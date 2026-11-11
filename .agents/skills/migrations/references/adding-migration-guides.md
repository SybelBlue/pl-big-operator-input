# Add a migration guide

Create a focused reference for one well-defined source-to-target transition. A guide should be usable without reading other migration references unless it explicitly declares a prerequisite transition.

## Name and route it

- Name the file `<area>-<source>-to-<target>.md` in lowercase kebab case. Prefer schema identifiers or released version labels that will remain meaningful.
- Add a catalog row to `../SKILL.md` with the area, source and target, distinctive source markers, and the reference link.
- If one source can migrate to several targets, create separate guides and make the target-selection rule explicit in the catalog or guide.
- If migrations must be chained, state the prerequisite and link it directly. Do not duplicate the prerequisite’s procedure.

## Include the evidence needed to act

Adapt these sections to the transition; omit sections that genuinely do not apply:

1. **Scope and target definition:** Name the affected files, APIs, or persisted objects and the authoritative target schema or implementation.
2. **Detection:** Give positive source markers, positive target markers, and a way to recognize ambiguous or partially migrated states. Prefer a safe read-only search or inspection command.
3. **Preconditions and data lifetime:** Explain deployment, persistence, compatibility, sequencing, backup, or authorization constraints that change the migration decision.
4. **Migration map:** Map renamed, removed, split, combined, and behavior-changing fields or operations. Include compact before-and-after examples when they remove ambiguity.
5. **Procedure:** Describe the smallest reliable workflow. Preserve room for repository-specific judgment unless ordering is a correctness requirement.
6. **Non-mechanical cases:** Identify source states with no lossless target and say what decision or input is required.
7. **Verification:** Check both structure and observable behavior. Include focused commands, important invariants, and any unavailable validation that must be reported.
8. **Final report:** Require the affected scope, decisions, persisted-data risks, and exact validation results.

Keep generic migration policy in `../SKILL.md` and transition-specific facts in the reference. Do not copy entire external manuals or restate unrelated repository conventions.

## Add automation only when it earns its cost

Put a helper in `../scripts/` when the same deterministic transformation will be repeated, manual editing is error-prone, or the migration spans many files or records. Name it for the same source-to-target transition, support a non-mutating check or dry-run mode when practical, reject ambiguous inputs, and make repeated execution safe. Document how to run and validate it from the migration reference.

Do not add a script for a small guide whose important work is semantic judgment. Do not let automation guess through non-mechanical cases.

## Validate the skill change

After adding or revising a guide:

- Follow every link from `../SKILL.md` and confirm the catalog’s detection markers distinguish it from neighboring migrations.
- Check that source and target names agree across the filename, catalog, guide, examples, and any scripts.
- Run the skill validator and the repository’s Markdown formatter.
- Exercise any added script on a representative source case, an already-current case, and an ambiguous or invalid case.
