# Test inventory and proposed suite design: `pl-big-operator-input`

## Executive summary

Baseline on 2026-08-28 (America/Los_Angeles), from the repository root:

```text
$ pytest -q elements/pl-big-operator-input/tests --durations=20
263 passed in 0.96s
```

Collection contains **263 pytest cases from 129 test functions**: 253 cases in the project-owned large module and 10 README-contract cases. The proposed suite has **103 test functions / 181 collected cases**. That is a design target, not an already-applied count: this task intentionally changes no test or production code.

The strongest coverage is the prepare/parse/grade/render lifecycle and its supported operator matrix. The largest maintenance cost comes from broad Cartesian parameterization, tests that exercise several phases at once, and assertions against literal HTML, LaTeX, CSS source text, or complete dictionaries when only one branch is under test. Line coverage is not used as a retention argument.

No current test is recommended for outright deletion without replacement. Three CSS-source tests are marked “rewrite around an invariant”: deleting their current implementation-coupled form is acceptable only when their observable layout contract has moved to a browser/DOM-level check. The mapping appendix therefore has no silent coverage gaps.

## Ownership boundary

The tests in `elements/pl-big-operator-input/tests/` are project-owned wrapper tests. The directory `elements/pl-big-operator-input/vendor/prairielearn/pl-symbolic-input/` is a vendored PrairieLearn snapshot from commit `14e65830861bee4cfe10c3ef73b000794edd66ed`, documented in `prairielearn-source.json`; its upstream `pl-symbolic-input_test.py` is not collected by the command above and should remain an upstream compatibility snapshot, not be mixed into wrapper unit counts.

Wrapper tests should prove forwarding and integration at the adapter boundary, not duplicate the entire upstream symbolic-input behavior. Keep one contract per delegated attribute (for example width, custom functions, and `allow-complex`) and a small end-to-end adapter smoke. Changes to the vendored snapshot should be checked separately against its pin/license and, if its upstream tests are intentionally enabled, reported as a distinct job.

The README tests are executable public-contract tests. Preserve them in their own file. The “README contains examples” guard and the parameterized validate/prepare/render test prevent an empty extraction from passing and are both meaningful.

## Classification and disposition by test function

“Cases” is the current collected parameter count. A row classifies every case belonging to that function; the appendix expands all 263 old node IDs. “Specific-output only” flags assertions that mainly repeat a sample value or implementation string without independently proving a branch, contract, or known regression.

| Current test function | Cases | Level | Feature area | Disposition | Specific-output only? |
|---|---:|---|---|---|---|
| `test_auto_limits` | 9 | unit | configuration | merge/parameterize | some—table lookup examples |
| `test_operator_attribute_accepts_initial_capital` | 9 | unit | configuration | merge/parameterize | some—table lookup examples |
| `test_custom_operator_attribute_accepts_initial_capital` | 1 | unit | configuration | merge/parameterize | some—table lookup examples |
| `test_operator_attribute_rejects_other_capitalization` | 1 | unit | configuration | keep | no |
| `test_operator_attribute_rejects_boolean_operators` | 4 | unit | configuration | merge/parameterize | no |
| `test_whole_answers_do_not_infer_boolean_operators` | 2 | unit | answer inference | keep | no |
| `test_infers_operator_from_whole_answer_strings` | 9 | smoke | answer inference | keep | no |
| `test_sympy_string_forms_are_parseable` | 9 | unit | parsing | keep | no |
| `test_sympy_limit_string_form_is_parseable` | 1 | unit | parsing | keep | no |
| `test_infers_operator_from_sympy_json` | 4 | unit | answer inference | keep | no |
| `test_infers_operator_from_canonical_dictionary` | 1 | unit | normalization | keep | no |
| `test_omitted_index_requires_inferable_whole_answer` | 1 | unit | answer inference | keep | no |
| `test_omitted_operator_requires_inferable_whole_answer` | 1 | unit | answer inference | keep | no |
| `test_uninferable_string_or_dictionary_requires_operator` | 4 | unit | answer inference | keep | no |
| `test_explicit_operator_remains_authoritative` | 1 | unit | answer inference | keep | no |
| `test_raw_sympy_object_does_not_trigger_inference` | 1 | unit | answer inference | keep | no |
| `test_inferred_operator_validates_explicit_limits` | 1 | unit | answer inference | keep | no |
| `test_inferred_limit_validates_and_preserves_direction` | 1 | unit | answer inference | keep | no |
| `test_limit_infers_index_and_direction_from_whole_answer` | 1 | unit | answer inference | keep | no |
| `test_explicit_limit_direction_still_rejects_mismatch` | 1 | unit | answer inference | keep | no |
| `test_formatted_limit_accepts_documented_directions` | 3 | unit | answer inference | merge/parameterize | no |
| `test_limit_rejects_unknown_direction_in_either_string_form` | 2 | unit | answer inference | merge/parameterize | no |
| `test_infers_domain_integral_from_two_item_binder` | 1 | unit | normalization | keep | no |
| `test_infers_domain_integral_from_sympy_json` | 1 | unit | answer inference | keep | no |
| `test_infers_bounds_from_three_item_variadic_binder` | 1 | unit | normalization | keep | no |
| `test_whole_domain_integral_matches_component_answer` | 1 | unit | configuration | keep | no |
| `test_custom_operator_requires_explicit_supported_limits` | 2 | unit | configuration | keep | no |
| `test_custom_operator_rejects_auto_limits` | 1 | unit | configuration | merge/parameterize | some—table lookup examples |
| `test_custom_operator_requires_nonempty_latex` | 1 | unit | rendering | keep | no |
| `test_builtin_operator_accepts_custom_latex` | 1 | unit | rendering | merge/parameterize | no |
| `test_inferred_builtin_operator_accepts_custom_latex` | 1 | unit | rendering | merge/parameterize | no |
| `test_flexible_operator_limit_forms` | 16 | unit | configuration | merge/parameterize | no |
| `test_invalid_limit_forms` | 4 | unit | configuration | merge/parameterize | no |
| `test_prepare_normalizes_binders` | 3 | unit | normalization | keep | no |
| `test_prepare_does_not_populate_params_with_correct_answer` | 1 | unit | configuration | keep | no |
| `test_prepare_does_not_use_correct_answer_backup_from_params` | 1 | unit | configuration | keep | no |
| `test_prepare_decodes_serialized_binders_without_interval_parsing` | 3 | unit | normalization | keep | no |
| `test_prepare_normalizes_function_domain_binders` | 5 | unit | normalization | keep | no |
| `test_prepare_normalizes_function_bounds_binder` | 1 | unit | normalization | keep | no |
| `test_limit_directions` | 3 | unit | answer inference | merge/parameterize | no |
| `test_limit_direction_input_defaults_true_and_can_be_disabled` | 1 | unit | answer inference | keep | no |
| `test_fixed_two_sided_limit_has_no_target_suffix` | 1 | unit | configuration | keep | no |
| `test_limit_direction_input_schema_values_are_valid` | 2 | unit | schema | merge/parameterize | no |
| `test_limit_direction_input_rejects_invalid_boolean` | 1 | unit | answer inference | keep | no |
| `test_limit_direction_input_rejects_non_approach_form` | 1 | unit | answer inference | keep | no |
| `test_limit_direction_input_preserves_raw_selection` | 1 | regression | answer inference | keep | no |
| `test_limit_direction_input_two_sided_option_has_accessible_text` | 1 | unit | accessibility/layout | keep | no |
| `test_limit_direction_input_is_a_red_single_character_monospace_control` | 1 | unit | answer inference | keep | no |
| `test_limit_direction_input_uses_binary_score_badge` | 2 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_limit_direction_input_parses_into_canonical_answer` | 3 | unit | parsing | keep | no |
| `test_limit_direction_input_rejects_missing_or_invalid_selection` | 2 | unit | answer inference | keep | no |
| `test_limit_direction_input_clears_stale_format_error_after_valid_selection` | 1 | regression | answer inference | keep | no |
| `test_limit_direction_input_honors_allowed_blank_limits` | 1 | unit | parsing | keep | no |
| `test_limit_direction_input_clears_stale_submission_when_blank_is_allowed` | 1 | regression | parsing | keep | no |
| `test_fixed_limit_direction_is_injected_without_raw_field` | 1 | regression | answer inference | keep | no |
| `test_student_limit_direction_participates_in_grading` | 6 | unit | grading | merge/parameterize | no |
| `test_direction_component_feedback_is_rendered` | 1 | unit | rendering | keep | no |
| `test_submission_and_answer_panels_use_their_own_limit_directions` | 1 | regression | rendering | merge/parameterize | no |
| `test_canonical_custom_answer_infers_operator_and_limits` | 1 | unit | normalization | keep | no |
| `test_domain_structured_answer_and_rendering` | 1 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_prepare_parses_basic_component_correct_answer_strings` | 1 | unit | parsing | keep | no |
| `test_prepare_parses_set_component_correct_answer_strings` | 1 | unit | parsing | keep | no |
| `test_prepare_accepts_symbolic_integral_domain` | 1 | unit | configuration | keep | no |
| `test_prepare_component_correct_answer_requires_every_visible_attribute` | 1 | unit | configuration | keep | no |
| `test_prepare_component_correct_answer_enforces_set_fields` | 1 | unit | parsing | keep | no |
| `test_prepare_rejects_irrelevant_component_correct_answer_attribute` | 1 | unit | configuration | keep | no |
| `test_prepare_rejects_combined_whole_and_component_correct_answers` | 1 | unit | configuration | keep | no |
| `test_min_max_correct_answer_rendering` | 2 | unit | rendering | merge/parameterize | yes—exact sample output; rewrite/assert contract |
| `test_min_max_answer_rendering_uses_prepared_answer` | 2 | unit | rendering | merge/parameterize | yes—exact sample output; rewrite/assert contract |
| `test_min_max_answer_panel_never_renders_question_mark_fallback` | 2 | unit | rendering | merge/parameterize | no |
| `test_variadic_operators_require_structured_answers` | 5 | unit | accessibility/layout | keep | no |
| `test_rejects_malformed_structured_answers` | 5 | unit | normalization | merge/parameterize | no |
| `test_parse_only_relevant_fields_and_allows_index_in_body` | 1 | smoke | parsing | keep | no |
| `test_domain_fields_reject_non_sets_at_parse_time` | 5 | unit | parsing | merge/parameterize | no |
| `test_set_combinator_bodies_reject_non_sets_at_parse_time` | 3 | unit | parsing | merge/parameterize | no |
| `test_bare_variables_are_accepted_as_symbolic_sets` | 1 | unit | accessibility/layout | keep | no |
| `test_allow_complex_is_delegated_to_symbolic_inputs` | 1 | unit | parsing | keep | no |
| `test_custom_functions_are_used_to_parse_component_correct_answers` | 1 | unit | parsing | keep | no |
| `test_custom_functions_are_delegated_to_student_body_input` | 1 | unit | parsing | keep | no |
| `test_parse_errors_are_rendered_with_their_fields` | 2 | unit | rendering | keep | no |
| `test_partially_blank_submission_has_a_descriptive_field_error` | 1 | unit | parsing | keep | no |
| `test_wholly_blank_required_submission_marks_every_field_invalid` | 1 | unit | parsing | keep | no |
| `test_initial_latex_is_stored_outside_math_fields` | 1 | unit | rendering | keep | no |
| `test_question_fields_are_rendered_by_vendored_symbolic_input` | 1 | smoke | rendering | keep | no |
| `test_symbolic_input_width_defaults_preserve_existing_layout` | 3 | unit | accessibility/layout | keep | no |
| `test_custom_widths_are_forwarded_to_rendered_symbolic_inputs` | 1 | unit | accessibility/layout | keep | no |
| `test_custom_widths_are_forwarded_when_parsing` | 1 | regression | accessibility/layout | keep | no |
| `test_symbolic_input_width_schema_accepts_integers` | 2 | unit | schema | merge/parameterize | no |
| `test_symbolic_input_width_schema_rejects_non_integers` | 2 | unit | schema | merge/parameterize | no |
| `test_symbolic_input_widths_must_be_positive` | 4 | unit | accessibility/layout | merge/parameterize | no |
| `test_symbolic_input_width_css_uses_wrapper_properties` | 1 | unit | accessibility/layout | rewrite around an invariant | yes—pins CSS text/selectors |
| `test_body_help_text_can_be_disabled` | 1 | unit | configuration | keep | no |
| `test_body_right_edge_is_rounded_only_when_it_has_no_trailing_control` | 1 | regression | accessibility/layout | keep | no |
| `test_parse_does_not_add_render_or_grade_phase_data_keys` | 1 | regression | rendering | keep | no |
| `test_component_grading_weights_body` | 1 | unit | grading | keep | no |
| `test_component_grading_uses_equivalence_for_each_field` | 1 | regression | grading | keep | no |
| `test_component_grading_shows_icon_only_badges_on_symbolic_inputs` | 1 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_exact_and_equivalent_grading` | 2 | smoke | grading | keep | no |
| `test_equivalent_grading_domain_sum` | 1 | unit | grading | keep | no |
| `test_symbolic_domain_named_like_sympy_function_renders_as_a_symbol` | 1 | regression | rendering | keep | no |
| `test_allowed_blank_and_independent_parse_errors` | 1 | unit | parsing | keep | no |
| `test_allowed_blank_submission_is_gradable_as_incorrect` | 1 | unit | grading | keep | no |
| `test_ungraded_submission_is_parsed_but_not_scored` | 1 | unit | grading | keep | no |
| `test_ungraded_submission_panel_shows_response_without_score_badge` | 1 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_ungraded_answer_panel_is_empty` | 1 | unit | rendering | keep | no |
| `test_ungraded_blank_submission_still_requires_allowed_blank` | 1 | unit | grading | keep | no |
| `test_allowed_blank_modes_accept_the_selected_fields` | 8 | unit | parsing | merge/parameterize | no |
| `test_allowed_blank_modes_reject_unselected_fields` | 3 | unit | parsing | merge/parameterize | no |
| `test_invalid_allowed_blank_value_is_rejected` | 1 | unit | parsing | keep | no |
| `test_custom_operator_is_self_describing_ungraded_input` | 2 | unit | grading | keep | no |
| `test_custom_operator_exact_grading` | 1 | unit | grading | keep | no |
| `test_custom_operator_component_grading` | 1 | unit | grading | keep | no |
| `test_operator_latex_implies_custom_operator_for_whole_answer` | 1 | unit | rendering | keep | no |
| `test_custom_operator_accepts_approach_syntax` | 1 | unit | configuration | keep | no |
| `test_schema_accepts_implied_custom_operator` | 1 | unit | schema | merge/parameterize | no |
| `test_schema_rejects_statically_invalid_configurations` | 4 | unit | schema | merge/parameterize | no |
| `test_custom_operator_correct_answer_panel_renders_complete_notation` | 1 | unit | rendering | keep | no |
| `test_custom_operator_correct_answer_rejects_equivalent_grading` | 1 | unit | grading | keep | no |
| `test_custom_operator_correct_answer_data_rejects_equivalent_grading` | 1 | unit | grading | keep | no |
| `test_integral_and_submission_reconstruct_complete_notation` | 1 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_question_view_shows_score_badge` | 3 | unit | rendering | merge/parameterize | yes—exact sample output; rewrite/assert contract |
| `test_set_submission_renders_literal_braces` | 1 | unit | rendering | keep | yes—exact sample output; rewrite/assert contract |
| `test_integral_bounds_use_a_column_between_operator_and_body` | 1 | unit | accessibility/layout | rewrite around an invariant | yes—pins CSS text/selectors |
| `test_bounds_upper_field_restores_left_border_radius` | 1 | regression | accessibility/layout | keep | yes—pins CSS text/selectors |
| `test_domain_integral_renders_only_a_subscript_field_between_operator_and_body` | 1 | unit | rendering | keep | no |
| `test_domain_integral_parses_and_reconstructs_notation` | 1 | regression | rendering | keep | no |
| `test_annotated_operator_stack_has_vertical_offset` | 2 | unit | accessibility/layout | rewrite around an invariant | yes—pins CSS text/selectors |
| `test_readme_contains_markup_examples` | 1 | smoke | documentation contract | keep | no |
| `test_readme_markup_examples_validate_prepare_and_render` | 9 | smoke | documentation contract | keep | no |

## Design principles behind the dispositions

- Keep matrices only where every row represents a supported public member of a finite contract: operator families, three grading modes, three limit directions, and allowed-blank modes. Give rows semantic IDs.
- Collapse duplicate journeys. A prepare test should assert canonical shape/inference; a render test should consume a prepared fixture rather than re-prove normalization. The three min/max render functions become one answer-panel contract matrix.
- Replace concrete-value repetition with invariants: round-trip canonicalization, irrelevant fields never enter aggregate answers, explicit configuration wins or conflicts deterministically, grading is unchanged by equivalent component syntax, and panel rendering uses the panel’s own answer.
- Preserve bug tests as named regressions. Their names should include the issue/commit contract, for example `test_regression_f454a66_missing_direction_select_blocks_save` and `test_regression_6f1c431_component_grading_uses_equivalence`.
- Literal LaTeX is appropriate when notation is the public contract (integral differential, set braces, sided limit). Literal Bootstrap classes, complete badge fragments, exact CSS declarations, and serialized dictionary fields unrelated to the branch are weak.
- Schema tests prove static authoring validation. Runtime `_config` tests prove dynamic/inferred validation. Do not run both for the same purely static row unless they intentionally specify different boundaries.

## Proposed file layout

```text
elements/pl-big-operator-input/tests/
  conftest.py
  test_smoke.py
  test_readme_contract.py
  test_configuration.py
  test_answer_inference.py
  test_normalization.py
  test_parsing.py
  test_grading.py
  test_rendering.py
  test_schema.py
  test_accessibility_layout.py
  test_regressions.py
  vendor/
    test_symbolic_input_adapter_contract.py
```

Use module-level tests and fixtures by default. Classes are justified only for a shared behavioral context that changes the meaning of every test, such as `TestStudentSelectedLimitDirection`, `TestFixedLimitDirection`, and `TestUngradedInput`. They should share setup/contract language, not merely shorten names.

Common fixtures should provide markup construction, PrairieLearn phase-state factories, canonical bounds/domain/approach answers, and a `run_lifecycle` helper. Keep phase-specific tests able to call one phase directly so lifecycle helpers do not hide state-mutation bugs.

## Marker scheme

Register markers in `pyproject.toml` and run pytest with strict markers:

```toml
[tool.pytest.ini_options]
addopts = "--strict-markers"
markers = [
  "smoke: fast publication-critical lifecycle and documentation contracts",
  "regression: named bug or compatibility contract with issue/commit provenance",
  "vendor_contract: project adapter compatibility with the pinned PrairieLearn snapshot",
  "browser: DOM/CSS layout or accessibility behavior requiring a browser",
]
```

Do not mark every unit test `unit`; unmarked tests in these files are the complete unit suite. Feature area is encoded by filename, avoiding a second redundant marker taxonomy. `regression` may overlap `smoke` only when the bug would make the element unusable. `vendor_contract` never means the vendored upstream suite itself.

## Publication gate

1. **Fast smoke** — `pytest -m smoke elements/pl-big-operator-input/tests`. Target 12–18 cases and under one second locally: one bounds lifecycle, one domain/set lifecycle, one approach/direction lifecycle, exact/equivalent/component grading representatives, ungraded behavior, schema-valid representative, adapter render/parse contract, and all README examples.
2. **Complete unit** — `pytest -m "not browser" elements/pl-big-operator-input/tests`. This is the required publication gate and includes smoke, all finite contract matrices, and named regressions. Target: 181 cases, still comfortably fast given the 0.96-second baseline.
3. **Named regressions** — `pytest -m regression -vv elements/pl-big-operator-input/tests`. Require descriptive node IDs and provenance comments for at least: `f454a66` missing direction selector/save, `51a45fb` schema/config compatibility, `3fcddd7` schema const behavior, `6f1c431` component equivalence, `5ed337e` symbolic/domain handling, and `38b1ba6` field-size forwarding/layout.
4. **Browser/accessibility layout** — run separately when browser infrastructure is available. Publication may consume its prior required CI result, but text searches through CSS are not a substitute. Check accessible names, invalid-state association, keyboard-selectable direction input, no overlap, field ordering, and computed border/width behavior.
5. **Vendored snapshot** — report pin integrity and adapter-contract results separately. Do not add upstream snapshot cases to the project-owned 181-case count.

## Count reconciliation

| Measure | Before | Proposed |
|---|---:|---:|
| Test functions | 129 | 103 |
| Collected cases | 263 | 181 |
| Large mixed modules | 1 | 0 |
| README contract cases | 10 | preserved, count follows README examples |
| Explicit named regression cases | 12 identified by behavior/history | at least 12, renamed with provenance |
| Browser-level layout checks | 0 | 3–6 |
| Unreplaced deletions | 0 | 0 |

The 82-case reduction comes from representative equivalence classes and merged journeys, not from dropping supported operator families or README examples. Exact final collection should be asserted in the refactor PR and this appendix updated if parameter IDs change.

## Old node-ID mapping

Every currently collected node follows. A destination without a bracket suffix means that old parameter row contributes to the named destination contract; the destination may use a smaller representative matrix. “Rewrite around an invariant” explicitly replaces, rather than silently retains, a source-string assertion.

| Old node ID | Classification | Disposition | Destination or rationale |
|---|---|---|---|
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[sum-bounds]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[product-bounds]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[integral-bounds]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[limit-approach]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[union-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[intersection-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[disjoint-union-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[min-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_auto_limits[max-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Sum]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Product]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Integral]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Limit]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Intersection]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Disjoint-union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Min]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_accepts_initial_capital[Max]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_attribute_accepts_initial_capital` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_custom_operator_attribute_accepts_initial_capital` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_rejects_other_capitalization` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_rejects_other_capitalization` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_rejects_boolean_operators[and]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_rejects_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_rejects_boolean_operators[or]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_rejects_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_rejects_boolean_operators[And]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_rejects_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_attribute_rejects_boolean_operators[Or]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_operator_attribute_rejects_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_whole_answers_do_not_infer_boolean_operators[And(k, (k, {1, 2}))]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_whole_answers_do_not_infer_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_whole_answers_do_not_infer_boolean_operators[Or(k, (k, {1, 2}))]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_whole_answers_do_not_infer_boolean_operators` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[sum-Sum(k**2, (k, 1, 4))-bounds]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[product-Product(k, (k, 1, 4))-bounds]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[integral-Integral(k, (k, 0, 1))-bounds]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[limit-Limit(sin(k) / k, (k, 0, '+-'))-approach]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[union-Union({k}, (k, {1, 2}))-domain]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[intersection-Intersection({k}, (k, {1, 2}))-domain]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[disjoint-union-DisjointUnion({k}, (k, {1, 2}))-domain]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[min-Min(k**2, (k, {1, 2}))-domain]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_whole_answer_strings[max-Max(k**2, (k, {1, 2}))-domain]` | smoke / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_whole_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[sum-Sum]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[product-Product]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[integral-Integral]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[union-Union]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[intersection-Intersection]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[disjoint-union-DisjointUnion]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[min-Min]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[max-Max]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_string_forms_are_parseable[custom-Custom]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_string_forms_are_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_sympy_limit_string_form_is_parseable` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_sympy_limit_string_form_is_parseable` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_sympy_json[sum-correct0]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_sympy_json` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_sympy_json[product-correct1]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_sympy_json` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_sympy_json[integral-correct2]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_sympy_json` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_sympy_json[limit-correct3]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_operator_from_sympy_json` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_operator_from_canonical_dictionary` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_infers_operator_from_canonical_dictionary` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_omitted_index_requires_inferable_whole_answer` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_omitted_index_requires_inferable_whole_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_omitted_operator_requires_inferable_whole_answer` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_omitted_operator_requires_inferable_whole_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_uninferable_string_or_dictionary_requires_operator[NotAnOperator(k, (k, 1, 4))]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_uninferable_string_or_dictionary_requires_operator` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_uninferable_string_or_dictionary_requires_operator[correct1]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_uninferable_string_or_dictionary_requires_operator` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_uninferable_string_or_dictionary_requires_operator[correct2]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_uninferable_string_or_dictionary_requires_operator` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_uninferable_string_or_dictionary_requires_operator[correct3]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_uninferable_string_or_dictionary_requires_operator` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_explicit_operator_remains_authoritative` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_explicit_operator_remains_authoritative` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_raw_sympy_object_does_not_trigger_inference` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_raw_sympy_object_does_not_trigger_inference` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_inferred_operator_validates_explicit_limits` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_inferred_operator_validates_explicit_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_inferred_limit_validates_and_preserves_direction` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_inferred_limit_validates_and_preserves_direction` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_infers_index_and_direction_from_whole_answer` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_infers_index_and_direction_from_whole_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_explicit_limit_direction_still_rejects_mismatch` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_explicit_limit_direction_still_rejects_mismatch` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_formatted_limit_accepts_documented_directions[+-from-right]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_formatted_limit_accepts_documented_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_formatted_limit_accepts_documented_directions[--from-left]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_formatted_limit_accepts_documented_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_formatted_limit_accepts_documented_directions[+--two-sided]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_formatted_limit_accepts_documented_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_rejects_unknown_direction_in_either_string_form[Limit(k, (k, 0, 'sideways'))]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_rejects_unknown_direction_in_either_string_form` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_rejects_unknown_direction_in_either_string_form[Limit(k, k, 0, dir='sideways')]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_rejects_unknown_direction_in_either_string_form` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_domain_integral_from_two_item_binder` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_infers_domain_integral_from_two_item_binder` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_domain_integral_from_sympy_json` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_infers_domain_integral_from_sympy_json` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_infers_bounds_from_three_item_variadic_binder` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_infers_bounds_from_three_item_variadic_binder` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_whole_domain_integral_matches_component_answer` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_whole_domain_integral_matches_component_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_requires_explicit_supported_limits[bounds]` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_custom_operator_requires_explicit_supported_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_requires_explicit_supported_limits[domain]` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_custom_operator_requires_explicit_supported_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_rejects_auto_limits` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_custom_operator_rejects_auto_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_requires_nonempty_latex` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_custom_operator_requires_nonempty_latex` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_builtin_operator_accepts_custom_latex` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_builtin_operator_latex_override` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_inferred_builtin_operator_accepts_custom_latex` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_builtin_operator_latex_override` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-sum]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-product]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-integral]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-intersection]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-disjoint-union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-min]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[bounds-max]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-sum]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-product]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-integral]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-intersection]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-disjoint-union]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-min]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_flexible_operator_limit_forms[domain-max]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_flexible_operator_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_invalid_limit_forms[integral-approach]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_invalid_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_invalid_limit_forms[limit-bounds]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_invalid_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_invalid_limit_forms[limit-domain]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_invalid_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_invalid_limit_forms[sum-approach]` | unit / configuration | merge/parameterize | `elements/pl-big-operator-input/tests/test_configuration.py::test_invalid_limit_forms` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_binders[sum-correct0]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_binders[product-correct1]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_binders[integral-correct2]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_does_not_populate_params_with_correct_answer` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_does_not_populate_params_with_correct_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_does_not_use_correct_answer_backup_from_params` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_does_not_use_correct_answer_backup_from_params` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_decodes_serialized_binders_without_interval_parsing[sum-correct0]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_decodes_serialized_binders_without_interval_parsing` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_decodes_serialized_binders_without_interval_parsing[product-correct1]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_decodes_serialized_binders_without_interval_parsing` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_decodes_serialized_binders_without_interval_parsing[integral-correct2]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_decodes_serialized_binders_without_interval_parsing` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_domain_binders[union-Union-{k}]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_domain_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_domain_binders[intersection-Intersection-{k}]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_domain_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_domain_binders[disjoint-union-DisjointUnion-{k}]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_domain_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_domain_binders[min-Min-k**2]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_domain_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_domain_binders[max-Max-k**2]` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_domain_binders` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_normalizes_function_bounds_binder` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_prepare_normalizes_function_bounds_binder` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_directions[two-sided-+-]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_directions[from-left--]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_directions[from-right-+]` | unit / answer inference | merge/parameterize | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_defaults_true_and_can_be_disabled` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_defaults_true_and_can_be_disabled` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_fixed_two_sided_limit_has_no_target_suffix` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_fixed_two_sided_limit_has_no_target_suffix` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_schema_values_are_valid[true]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_limit_direction_input_schema_values_are_valid` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_schema_values_are_valid[false]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_limit_direction_input_schema_values_are_valid` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_rejects_invalid_boolean` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_rejects_invalid_boolean` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_rejects_non_approach_form` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_rejects_non_approach_form` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_preserves_raw_selection` | regression / answer inference | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_limit_direction_input_preserves_raw_selection` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_two_sided_option_has_accessible_text` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_limit_direction_input_two_sided_option_has_accessible_text` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_is_a_red_single_character_monospace_control` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_is_a_red_single_character_monospace_control` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_uses_binary_score_badge[from-right-text-bg-success-fa-check-Correct]` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_limit_direction_input_uses_binary_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_uses_binary_score_badge[from-left-text-bg-danger-fa-times-Incorrect]` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_limit_direction_input_uses_binary_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_parses_into_canonical_answer[two-sided]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_limit_direction_input_parses_into_canonical_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_parses_into_canonical_answer[from-left]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_limit_direction_input_parses_into_canonical_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_parses_into_canonical_answer[from-right]` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_limit_direction_input_parses_into_canonical_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_rejects_missing_or_invalid_selection[]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_rejects_missing_or_invalid_selection` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_rejects_missing_or_invalid_selection[sideways]` | unit / answer inference | keep | `elements/pl-big-operator-input/tests/test_answer_inference.py::test_limit_direction_input_rejects_missing_or_invalid_selection` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_clears_stale_format_error_after_valid_selection` | regression / answer inference | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_limit_direction_input_clears_stale_format_error_after_valid_selection` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_honors_allowed_blank_limits` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_limit_direction_input_honors_allowed_blank_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_limit_direction_input_clears_stale_submission_when_blank_is_allowed` | regression / parsing | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_limit_direction_input_clears_stale_submission_when_blank_is_allowed` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_fixed_limit_direction_is_injected_without_raw_field` | regression / answer inference | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_fixed_limit_direction_is_injected_without_raw_field` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[exact-from-right-1.0]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[exact-from-left-0.0]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[component-from-right-1.0]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[component-from-left-0.8]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[equivalent-from-right-1.0]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_student_limit_direction_participates_in_grading[equivalent-from-left-0.0]` | unit / grading | merge/parameterize | `elements/pl-big-operator-input/tests/test_grading.py::test_student_limit_direction_participates_in_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_direction_component_feedback_is_rendered` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_direction_component_feedback_is_rendered` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_submission_and_answer_panels_use_their_own_limit_directions` | regression / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_regressions.py::test_submission_and_answer_panels_use_their_own_limit_directions` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_canonical_custom_answer_infers_operator_and_limits` | unit / normalization | keep | `elements/pl-big-operator-input/tests/test_normalization.py::test_canonical_custom_answer_infers_operator_and_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_structured_answer_and_rendering` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_domain_structured_answer_and_rendering` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_parses_basic_component_correct_answer_strings` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_prepare_parses_basic_component_correct_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_parses_set_component_correct_answer_strings` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_prepare_parses_set_component_correct_answer_strings` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_accepts_symbolic_integral_domain` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_accepts_symbolic_integral_domain` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_component_correct_answer_requires_every_visible_attribute` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_component_correct_answer_requires_every_visible_attribute` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_component_correct_answer_enforces_set_fields` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_prepare_component_correct_answer_enforces_set_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_rejects_irrelevant_component_correct_answer_attribute` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_rejects_irrelevant_component_correct_answer_attribute` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_prepare_rejects_combined_whole_and_component_correct_answers` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_prepare_rejects_combined_whole_and_component_correct_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_correct_answer_rendering[min]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_correct_answer_rendering[max]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_answer_rendering_uses_prepared_answer[min]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_answer_rendering_uses_prepared_answer[max]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_answer_panel_never_renders_question_mark_fallback[min]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_min_max_answer_panel_never_renders_question_mark_fallback[max]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_min_max_answer_panel_contract` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_variadic_operators_require_structured_answers[union]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_variadic_operators_require_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_variadic_operators_require_structured_answers[intersection]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_variadic_operators_require_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_variadic_operators_require_structured_answers[disjoint-union]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_variadic_operators_require_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_variadic_operators_require_structured_answers[min]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_variadic_operators_require_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_variadic_operators_require_structured_answers[max]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_variadic_operators_require_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_rejects_malformed_structured_answers[<lambda>0]` | unit / normalization | merge/parameterize | `elements/pl-big-operator-input/tests/test_normalization.py::test_rejects_malformed_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_rejects_malformed_structured_answers[<lambda>1]` | unit / normalization | merge/parameterize | `elements/pl-big-operator-input/tests/test_normalization.py::test_rejects_malformed_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_rejects_malformed_structured_answers[<lambda>2]` | unit / normalization | merge/parameterize | `elements/pl-big-operator-input/tests/test_normalization.py::test_rejects_malformed_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_rejects_malformed_structured_answers[<lambda>3]` | unit / normalization | merge/parameterize | `elements/pl-big-operator-input/tests/test_normalization.py::test_rejects_malformed_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_rejects_malformed_structured_answers[<lambda>4]` | unit / normalization | merge/parameterize | `elements/pl-big-operator-input/tests/test_normalization.py::test_rejects_malformed_structured_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_parse_only_relevant_fields_and_allows_index_in_body` | smoke / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_parse_only_relevant_fields_and_allows_index_in_body` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_fields_reject_non_sets_at_parse_time[sum]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_domain_fields_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_fields_reject_non_sets_at_parse_time[product]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_domain_fields_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_fields_reject_non_sets_at_parse_time[integral]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_domain_fields_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_fields_reject_non_sets_at_parse_time[union]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_domain_fields_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_fields_reject_non_sets_at_parse_time[min]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_domain_fields_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_set_combinator_bodies_reject_non_sets_at_parse_time[union]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_set_combinator_bodies_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_set_combinator_bodies_reject_non_sets_at_parse_time[intersection]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_set_combinator_bodies_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_set_combinator_bodies_reject_non_sets_at_parse_time[disjoint-union]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_set_combinator_bodies_reject_non_sets_at_parse_time` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_bare_variables_are_accepted_as_symbolic_sets` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_bare_variables_are_accepted_as_symbolic_sets` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allow_complex_is_delegated_to_symbolic_inputs` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_allow_complex_is_delegated_to_symbolic_inputs` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_functions_are_used_to_parse_component_correct_answers` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_custom_functions_are_used_to_parse_component_correct_answers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_functions_are_delegated_to_student_body_input` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_custom_functions_are_delegated_to_student_body_input` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_parse_errors_are_rendered_with_their_fields[op-domain-op-body]` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_parse_errors_are_rendered_with_their_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_parse_errors_are_rendered_with_their_fields[op-body-op-domain]` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_parse_errors_are_rendered_with_their_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_partially_blank_submission_has_a_descriptive_field_error` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_partially_blank_submission_has_a_descriptive_field_error` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_wholly_blank_required_submission_marks_every_field_invalid` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_wholly_blank_required_submission_marks_every_field_invalid` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_initial_latex_is_stored_outside_math_fields` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_initial_latex_is_stored_outside_math_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_question_fields_are_rendered_by_vendored_symbolic_input` | smoke / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_question_fields_are_rendered_by_vendored_symbolic_input` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_defaults_preserve_existing_layout[sum-7]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_width_defaults_preserve_existing_layout` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_defaults_preserve_existing_layout[union-10]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_width_defaults_preserve_existing_layout` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_defaults_preserve_existing_layout[limit-10]` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_width_defaults_preserve_existing_layout` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_widths_are_forwarded_to_rendered_symbolic_inputs` | unit / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_custom_widths_are_forwarded_to_rendered_symbolic_inputs` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_widths_are_forwarded_when_parsing` | regression / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_custom_widths_are_forwarded_when_parsing` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_schema_accepts_integers[body-size]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_symbolic_input_width_schema_accepts_integers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_schema_accepts_integers[limit-size]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_symbolic_input_width_schema_accepts_integers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_schema_rejects_non_integers[body-size]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_symbolic_input_width_schema_rejects_non_integers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_schema_rejects_non_integers[limit-size]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_symbolic_input_width_schema_rejects_non_integers` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_widths_must_be_positive[0-body-size]` | unit / accessibility/layout | merge/parameterize | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_widths_must_be_positive` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_widths_must_be_positive[0-limit-size]` | unit / accessibility/layout | merge/parameterize | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_widths_must_be_positive` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_widths_must_be_positive[-1-body-size]` | unit / accessibility/layout | merge/parameterize | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_widths_must_be_positive` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_widths_must_be_positive[-1-limit-size]` | unit / accessibility/layout | merge/parameterize | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_symbolic_input_widths_must_be_positive` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_input_width_css_uses_wrapper_properties` | unit / accessibility/layout | rewrite around an invariant | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_width_contract_controls_computed_field_minimums` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_body_help_text_can_be_disabled` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_body_help_text_can_be_disabled` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_body_right_edge_is_rounded_only_when_it_has_no_trailing_control` | regression / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_body_right_edge_is_rounded_only_when_it_has_no_trailing_control` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_parse_does_not_add_render_or_grade_phase_data_keys` | regression / rendering | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_parse_does_not_add_render_or_grade_phase_data_keys` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_component_grading_weights_body` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_component_grading_weights_body` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_component_grading_uses_equivalence_for_each_field` | regression / grading | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_component_grading_uses_equivalence_for_each_field` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_component_grading_shows_icon_only_badges_on_symbolic_inputs` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_component_grading_shows_icon_only_badges_on_symbolic_inputs` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_exact_and_equivalent_grading[exact]` | smoke / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_exact_and_equivalent_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_exact_and_equivalent_grading[equivalent]` | smoke / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_exact_and_equivalent_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_equivalent_grading_domain_sum` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_equivalent_grading_domain_sum` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_symbolic_domain_named_like_sympy_function_renders_as_a_symbol` | regression / rendering | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_symbolic_domain_named_like_sympy_function_renders_as_a_symbol` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_and_independent_parse_errors` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_and_independent_parse_errors` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_submission_is_gradable_as_incorrect` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_allowed_blank_submission_is_gradable_as_incorrect` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_ungraded_submission_is_parsed_but_not_scored` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_ungraded_submission_is_parsed_but_not_scored` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_ungraded_submission_panel_shows_response_without_score_badge` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_ungraded_submission_panel_shows_response_without_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_ungraded_answer_panel_is_empty` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_ungraded_answer_panel_is_empty` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_ungraded_blank_submission_still_requires_allowed_blank` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_ungraded_blank_submission_still_requires_allowed_blank` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[limits-raw0-op-end]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[limits-raw1-op-start]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[limits-raw2-op-start]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[body-raw3-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[all-raw4-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[all-raw5-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[all-raw6-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_accept_the_selected_fields[all-raw7-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_accept_the_selected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_reject_unselected_fields[none-raw0-op-start]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_reject_unselected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_reject_unselected_fields[limits-raw1-op-body]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_reject_unselected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_allowed_blank_modes_reject_unselected_fields[body-raw2-op-start]` | unit / parsing | merge/parameterize | `elements/pl-big-operator-input/tests/test_parsing.py::test_allowed_blank_modes_reject_unselected_fields` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_invalid_allowed_blank_value_is_rejected` | unit / parsing | keep | `elements/pl-big-operator-input/tests/test_parsing.py::test_invalid_allowed_blank_value_is_rejected` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_is_self_describing_ungraded_input[bounds-raw0-\\\\mathop{\\\\mathbb{E}}\\\\limits_{k=1}^{4} k^{2}]` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_is_self_describing_ungraded_input` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_is_self_describing_ungraded_input[domain-raw1-\\\\mathop{\\\\mathbb{E}}\\\\limits_{k\\\\in \\\\left\\\\{1, 2\\\\right\\\\}} k^{2}]` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_is_self_describing_ungraded_input` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_exact_grading` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_exact_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_component_grading` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_component_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_operator_latex_implies_custom_operator_for_whole_answer` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_operator_latex_implies_custom_operator_for_whole_answer` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_accepts_approach_syntax` | unit / configuration | keep | `elements/pl-big-operator-input/tests/test_configuration.py::test_custom_operator_accepts_approach_syntax` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_schema_accepts_implied_custom_operator` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_schema_accepts_implied_custom_operator` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_schema_rejects_statically_invalid_configurations[<pl-big-operator-input answers-name="op" index-variable="k" operator="limit" limits="bounds"></pl-big-operator-input>]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_schema_rejects_statically_invalid_configurations` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_schema_rejects_statically_invalid_configurations[<pl-big-operator-input answers-name="op" index-variable="k" operator="custom" limits="bounds"></pl-big-operator-input>]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_schema_rejects_statically_invalid_configurations` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_schema_rejects_statically_invalid_configurations[<pl-big-operator-input answers-name="op" index-variable="k" correct-answer-start="1" correct-answer-end="2" correct-answer-body="k"></pl-big-operator-input>]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_schema_rejects_statically_invalid_configurations` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_schema_rejects_statically_invalid_configurations[<pl-big-operator-input answers-name="op" operator="sum" correct-answer-start="1" correct-answer-end="2" correct-answer-body="k"></pl-big-operator-input>]` | unit / schema | merge/parameterize | `elements/pl-big-operator-input/tests/test_schema.py::test_schema_rejects_statically_invalid_configurations` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_correct_answer_panel_renders_complete_notation` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_custom_operator_correct_answer_panel_renders_complete_notation` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_correct_answer_rejects_equivalent_grading` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_correct_answer_rejects_equivalent_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_custom_operator_correct_answer_data_rejects_equivalent_grading` | unit / grading | keep | `elements/pl-big-operator-input/tests/test_grading.py::test_custom_operator_correct_answer_data_rejects_equivalent_grading` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_integral_and_submission_reconstruct_complete_notation` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_integral_and_submission_reconstruct_complete_notation` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_question_view_shows_score_badge[1-text-bg-success-100%]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_question_view_shows_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_question_view_shows_score_badge[0.4-text-bg-warning-40%]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_question_view_shows_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_question_view_shows_score_badge[0-text-bg-danger-0%]` | unit / rendering | merge/parameterize | `elements/pl-big-operator-input/tests/test_rendering.py::test_question_view_shows_score_badge` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_set_submission_renders_literal_braces` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_set_submission_renders_literal_braces` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_integral_bounds_use_a_column_between_operator_and_body` | unit / accessibility/layout | rewrite around an invariant | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_integral_bounds_have_visual_upper_and_lower_stack` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_bounds_upper_field_restores_left_border_radius` | regression / accessibility/layout | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_bounds_upper_field_restores_left_border_radius` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_integral_renders_only_a_subscript_field_between_operator_and_body` | unit / rendering | keep | `elements/pl-big-operator-input/tests/test_rendering.py::test_domain_integral_renders_only_a_subscript_field_between_operator_and_body` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_domain_integral_parses_and_reconstructs_notation` | regression / rendering | keep | `elements/pl-big-operator-input/tests/test_regressions.py::test_domain_integral_parses_and_reconstructs_notation` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_annotated_operator_stack_has_vertical_offset[union]` | unit / accessibility/layout | rewrite around an invariant | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_annotated_operator_does_not_overlap_limits` |
| `elements/pl-big-operator-input/tests/test_pl_big_operator_input.py::test_annotated_operator_stack_has_vertical_offset[limit]` | unit / accessibility/layout | rewrite around an invariant | `elements/pl-big-operator-input/tests/test_accessibility_layout.py::test_annotated_operator_does_not_overlap_limits` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_contains_markup_examples` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_contains_markup_examples` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="total"\\n  correct-answer="Sum(k**2, (k, 1, n))"\\n  variables="n"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="expectation"\\n  correct-answer="Custom(k**2, (k, {1, 2}))"\\n  operator-latex="\\\\mathbb{E}"\\n  grading-method="component"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="evaluation"\\n  operator="custom"\\n  operator-latex="\\\\operatorname{eval}"\\n  limits="approach"\\n  index-variable="x"\\n  custom-functions="f"\\n  correct-answer-target="0"\\n  limit-direction="two-sided"\\n  correct-answer-body="f(x)"\\n  grading-method="component"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="right-limit"\\n  correct-answer="Limit(1/x, (x, 0, '+'))"\\n  allow-limit-direction-input="false"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="total"\\n  correct-answer="Product(k + 1, (k, 1, 4))"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="contour"\\n  correct-answer="Integral(z**2, (z, Gamma))"\\n  variables="Gamma"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="sinc-limit"\\n  correct-answer="Limit(sin(x) / x, (x, 0, '+-'))"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<pl-big-operator-input\\n  answers-name="sets"\\n  correct-answer="Union({k}, (k, {1, 2}))"\\n  grading-method="exact"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |
| `elements/pl-big-operator-input/tests/test_readme_examples.py::test_readme_markup_examples_validate_prepare_and_render[<!-- component repr of Sum(k ** 2, (k, 1, n)) -->\\n<pl-big-operator-input\\n  answers-name="total"\\n  correct-answer-body="k^2"\\n  correct-answer-end="n"\\n  correct-answer-start="1"\\n  index-variable="k"\\n  operator="sum"\\n  variables="n"\\n></pl-big-operator-input>\\n]` | smoke / documentation contract | keep | `elements/pl-big-operator-input/tests/test_readme_contract.py::test_readme_markup_examples_validate_prepare_and_render` |

