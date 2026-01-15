---
description: "Task list for Compare Subcommand Enhancements feature"
---

# Tasks: Compare Subcommand Enhancements

**Input**: Design documents from `/specs/004-compare-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per constitution requirement for user-facing features

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Verify Python 3.9.6 environment and pytest 8.4.2 installation
- [X] T002 Review existing codebase structure (analyze_plan.py, multi_env_comparator.py, test patterns)
- [X] T003 Review ignore_config.example.json schema and analyze_plan.py lines 1833-1865 for existing ignore logic

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared utilities that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create ignore_utils.py with load_ignore_config(file_path: Path) -> Dict function (parse JSON, validate schema, raise FileNotFoundError or JSONDecodeError)
- [X] T005 Create ignore_utils.py apply_ignore_config(resource_config: Dict, ignore_rules: Dict, resource_type: str) -> Dict function (accepts resource dict, ignore rules, returns filtered dict)
- [X] T006 Create ignore_utils.py get_ignored_attributes(resource_config: Dict, ignore_rules: Dict, resource_type: str) -> Set[str] function (returns set of ignored attribute names that were actually present)
- [X] T007 Create ignore_utils.py supports_dot_notation(attribute_path: str, config: Dict) -> bool function (handle nested attributes like "identity.type", return True if attribute exists at path)
- [X] T008 [P] Create test_ignore_utils.py with unit tests for load_ignore_config (valid JSON, malformed JSON, file not found)
- [X] T009 [P] Create test_ignore_utils.py with unit tests for apply_ignore_config (global rules, resource-specific rules, nested attributes)
- [X] T010 Run tests for ignore_utils to validate foundational logic

**Checkpoint**: Foundation ready - ignore utilities tested and working

---

## Phase 3: User Story 1 - Ignore File Support for Compare (Priority: P1) 🎯 MVP

**Goal**: Enable users to filter out known acceptable differences using ignore configuration files

**Independent Test**: Run `compare` with --config flag and verify ignored attributes excluded from diff detection and HTML output

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Create test_e2e_compare_enhancements.py with test_ignore_global_rules() (tags ignored across all resources)
- [X] T012 [P] [US1] Create test_e2e_compare_enhancements.py with test_ignore_resource_specific() (description ignored for specific resource type)
- [X] T013 [P] [US1] Create test_e2e_compare_enhancements.py with test_ignore_nested_attributes() (identity.type ignored using dot notation)
- [X] T014 [P] [US1] Create test_e2e_compare_enhancements.py with test_ignore_config_file_not_found() (exit code 1, error message)
- [X] T015 [P] [US1] Create test_e2e_compare_enhancements.py with test_ignore_config_malformed_json() (exit code 2, error message)
- [X] T016 [P] [US1] Create test_data/ignore_test_config.json with global and resource-specific rules for testing

### Implementation for User Story 1

- [X] T017 [US1] Modify analyze_plan.py handle_compare_subcommand() to import ignore_utils and load config file when --config provided
- [X] T018 [US1] Modify analyze_plan.py handle_compare_subcommand() to handle file not found (exit code 1) and JSON parse errors (exit code 2)
- [X] T019 [US1] Modify analyze_plan.py handle_compare_subcommand() to pass ignore_config to MultiEnvReport constructor
- [X] T020 [US1] Modify multi_env_comparator.py MultiEnvReport.__init__() to accept ignore_config parameter (optional)
- [X] T021 [US1] Modify multi_env_comparator.py MultiEnvReport.build_comparisons() to apply ignore filtering before detect_differences()
- [X] T022 [US1] Modify multi_env_comparator.py MultiEnvReport.build_comparisons() to track ignored_attributes per ResourceComparison
- [X] T023 [US1] Modify multi_env_comparator.py MultiEnvReport.build_comparisons() to calculate IgnoreStatistics (total_ignored_attributes, resources_with_ignores)
- [X] T024 [US1] Modify multi_env_comparator.py ResourceComparison.detect_differences() to recalculate has_differences after ignore filtering
- [X] T025 [US1] Update summary statistics calculation to count resources as "identical" if all changes ignored, "different" only if non-ignored changes exist
- [X] T026 [US1] Add IgnoreStatistics display to HTML report header (total ignored, breakdown by attribute name)
- [X] T027 [US1] Add "N attributes ignored" indicator per resource in HTML (visible when ignored_attributes > 0)
- [X] T028 [US1] Run test_e2e_compare_enhancements.py tests for US1 and verify all pass
- [X] T029 [US1] Test manually with dev-plan.json, staging-plan.json, prod-plan.json and ignore_config.json from test_data/

**Checkpoint**: User Story 1 complete - ignore rules working for compare subcommand, independently testable

---

## Phase 4: User Story 2 - Attribute-Level Diff View (Priority: P2)

**Goal**: Show only changed top-level attributes instead of full JSON configs in HTML reports

**Independent Test**: Run compare without --config and verify HTML shows only changed attributes with side-by-side values

### Tests for User Story 2 ⚠️

- [X] T030 [P] [US2] Add test_e2e_compare_enhancements.py with test_attribute_level_single_change() (only location differs, verify HTML shows location row only, verify char-level diff highlighting)
- [X] T031 [P] [US2] Add test_e2e_compare_enhancements.py with test_attribute_level_multiple_changes() (sku, capacity, enabled differ, verify all shown separately)
- [X] T032 [P] [US2] Add test_e2e_compare_enhancements.py with test_attribute_level_nested_object() (identity changed, verify top-level "identity" shown with nested block)
- [X] T033 [P] [US2] Add test_e2e_compare_enhancements.py with test_attribute_level_identical_resource() (verify "No differences" message when expanded)
- [X] T067 [P] [US2] Add test_e2e_compare_enhancements.py with test_attribute_level_sensitive_values() (verify sensitive attributes show 🔒 SENSITIVE badge in attribute view)
- [X] T034 [P] [US2] Create test_compare_enhancements_unit.py with test_compute_attribute_diffs() (unit test for attribute extraction logic)

### Implementation for User Story 2

- [X] T035 [P] [US2] Add compute_attribute_diffs() method to multi_env_comparator.py ResourceComparison (extract top-level keys that differ)
- [X] T036 [US2] Add compute_attribute_diffs() to build AttributeDiff objects (attribute_name, env_values, is_different, attribute_type)
- [X] T037 [US2] Modify multi_env_comparator.py ResourceComparison to store attribute_diffs list after detect_differences()
- [X] T038 [US2] Modify multi_env_comparator.py MultiEnvReport.generate_html() to replace full JSON display with attribute table rendering
- [X] T039 [US2] Implement render_attribute_table() in multi_env_comparator.py (iterate attribute_diffs, create HTML rows)
- [X] T040 [US2] Implement render_attribute_value() in multi_env_comparator.py (handle primitives vs objects vs arrays, apply existing char-level diff highlighting from feature 002-char-level-diff for primitive values)
- [X] T041 [US2] Add side-by-side column layout for environment values (one column per environment, matching existing structure)
- [X] T042 [US2] Add "No differences detected" message rendering when attribute_diffs is empty but resource present
- [X] T043 [US2] Preserve expand/collapse functionality for resource sections with new attribute table structure
- [X] T044 [US2] Preserve sensitive value indicators (🔒 SENSITIVE badge) for attributes marked sensitive in attribute view
- [X] T045 [US2] Run test_e2e_compare_enhancements.py tests for US2 and verify all pass (including char-level diff highlighting and sensitive value preservation)
- [X] T046 [US2] Test manually with comparison_report.html to verify attribute-level view renders correctly

**Checkpoint**: User Story 2 complete - attribute-level view working, independently testable

---

## Phase 5: User Story 3 - Combined Ignore and Attribute-Level View (Priority: P3)

**Goal**: Combine ignore rules with attribute-level diff view for cleanest possible reports

**Independent Test**: Run compare with --config and verify attribute-level view excludes ignored attributes, shows only actionable differences

### Tests for User Story 3 ⚠️

- [ ] T047 [P] [US3] Add test_e2e_compare_enhancements.py with test_combined_ignore_and_attribute_view() (tags ignored, only location shown in attribute table)
- [ ] T048 [P] [US3] Add test_e2e_compare_enhancements.py with test_combined_all_attributes_ignored() (all changes ignored, verify "No actionable differences" message)
- [ ] T049 [P] [US3] Add test_e2e_compare_enhancements.py with test_combined_with_diff_only_flag() (test --config + --diff-only + --html combination, all filtered, verify exit code 0 and special message)
- [ ] T050 [P] [US3] Add test_e2e_compare_enhancements.py with test_combined_nested_ignore() (identity.type ignored, verify nested attribute excluded from diff)
- [ ] T065 [P] [US3] Add test_e2e_compare_enhancements.py with test_config_with_html_flag() (test --config + --html combination, verify HTML output has attribute view + ignore filtering)
- [ ] T066 [P] [US3] Add test_e2e_compare_enhancements.py with test_config_with_diff_only_text() (test --config + --diff-only without --html, verify text output format unchanged)

### Implementation for User Story 3

- [ ] T051 [US3] Modify compute_attribute_diffs() to skip attributes in ignored_attributes set (integrate US1 and US2)
- [ ] T052 [US3] Update "No actionable differences" detection (attribute_diffs empty due to ignore filtering)
- [ ] T053 [US3] Implement special message for --diff-only + ignore rules scenario (exit code 0, "N attributes filtered" message)
- [ ] T054 [US3] Update HTML IgnoreStatistics display to show per-resource and global ignored counts in combined view
- [ ] T055 [US3] Run test_e2e_compare_enhancements.py tests for US3 and verify all pass
- [ ] T056 [US3] Run full test suite (test_e2e_multi_env.py, test_multi_env_unit.py) to verify backward compatibility

**Checkpoint**: All user stories complete - combined functionality working perfectly

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T057 [P] Update quickstart.md with actual CLI examples and screenshots (if needed)
- [ ] T058 [P] Verify backward compatibility: run existing compare tests without --config flag
- [ ] T059 [P] Verify backward compatibility: test text output format unchanged (attribute view only affects HTML)
- [ ] T060 Performance test: generate HTML for comparison with 100+ resources, verify <3 seconds (SC-007)
- [ ] T061 [P] Code cleanup: remove debug logging, ensure consistent error messages
- [ ] T062 [P] Code review: verify ignore_utils.py follows existing code patterns in analyze_plan.py
- [ ] T063 Update PR_DESCRIPTION.md with feature summary, testing results, screenshots
- [ ] T064 Run quickstart.md validation scenarios manually (filter tags, resource-specific ignores, combined diff-only)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - Can proceed in priority order: US1 (P1) → US2 (P2) → US3 (P3)
  - US3 builds on US1+US2 integration
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US1, can run in parallel
- **User Story 3 (P3)**: Depends on US1 and US2 being complete (integration story)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation tasks run sequentially (dependencies on ResourceComparison modifications)
- Manual testing after automated tests pass
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: All 3 tasks can run in sequence (review/learning phase)
- **Phase 2 (Foundational)**: T008-T009 (test creation) can run in parallel after T004-T007 complete
- **Phase 3 (US1)**: T011-T016 (all tests) can be written in parallel
- **Phase 4 (US2)**: T030-T034 (all tests) can be written in parallel, T035-T036 (compute logic) can run in parallel
- **Phase 5 (US3)**: T047-T050 (all tests) can be written in parallel
- **Phase 6 (Polish)**: T057-T059, T061-T062 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test creation for User Story 1 together:
Task T011: "Create test_e2e_compare_enhancements.py with test_ignore_global_rules()"
Task T012: "Create test_e2e_compare_enhancements.py with test_ignore_resource_specific()"
Task T013: "Create test_e2e_compare_enhancements.py with test_ignore_nested_attributes()"
Task T014: "Create test_e2e_compare_enhancements.py with test_ignore_config_file_not_found()"
Task T015: "Create test_e2e_compare_enhancements.py with test_ignore_config_malformed_json()"
Task T016: "Create test_data/ignore_test_config.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (review and learning)
2. Complete Phase 2: Foundational (ignore_utils.py + tests) - CRITICAL
3. Complete Phase 3: User Story 1 (ignore file support)
4. **STOP and VALIDATE**: Test User Story 1 independently with real plan files
5. Commit and consider deploying MVP (ignore support alone delivers value)

### Incremental Delivery

1. Complete Setup + Foundational → Ignore utilities ready
2. Add User Story 1 → Test independently → **Commit** (MVP: ignore support working!)
3. Add User Story 2 → Test independently → **Commit** (attribute-level view working!)
4. Add User Story 3 → Test independently → **Commit** (combined functionality!)
5. Polish → Final validation → **Commit**

Each commit represents a working, testable increment.

### Sequential Implementation (Recommended)

Given US3 depends on US1+US2 integration:

1. Complete Foundational (Phase 2)
2. Implement US1 completely (ignore support) → Commit
3. Implement US2 completely (attribute view) → Commit  
4. Implement US3 (integration) → Commit
5. Polish and finalize

---

## Notes

- **[P] tasks** = different files or independent operations, no dependencies
- **[Story] label** maps task to specific user story for traceability
- Each user story should be independently testable (US1, US2 work alone; US3 integrates them)
- Verify tests fail before implementing
- **Commit boundaries**: After US1 complete, after US2 complete, after US3 complete, after Polish
- Constitution compliance: End-to-end tests for all user stories (CLI behavior), commit after each story
- Backward compatibility: Existing compare functionality unchanged when --config not used
- Performance target: <3 seconds for 100+ resources (SC-007)
- **Updated after analysis**: Added T065-T067 for combinatorial flag testing, char-level diff validation, and sensitive value testing

---

## Task Count Summary

**Total Tasks**: 67 (after /speckit.analyze remediation)
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 7 tasks
- Phase 3 (US1): 19 tasks
- Phase 4 (US2): 18 tasks (added T067)
- Phase 5 (US3): 12 tasks (added T065-T066)
- Phase 6 (Polish): 8 tasks

---

## Suggested MVP Scope

**Minimum Viable Product** = Phase 1 + Phase 2 + Phase 3 (User Story 1 only)

This delivers ignore file support for compare subcommand, which immediately reduces noise in reports and delivers significant value. User Stories 2 and 3 can follow as enhancements.
