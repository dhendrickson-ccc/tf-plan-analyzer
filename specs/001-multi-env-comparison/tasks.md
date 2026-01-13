# Tasks: Multi-Environment Terraform Plan Comparison

**Input**: Design documents from `/specs/001-multi-env-comparison/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: End-to-end tests required per Constitution Principle V - User-Facing Features Require End-to-End Testing

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Repository root (no src/ directory)
- All Python files at top level
- Test files prefixed with `test_`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and code structure preparation

- [X] T001 Review existing codebase structure (analyze_plan.py, generate_html_report.py, hcl_value_resolver.py)
- [X] T002 [P] Create multi_env_comparator.py stub with module docstring and imports
- [X] T003 [P] Create test_multi_env_unit.py stub for unit tests
- [X] T004 [P] Create test_e2e_multi_env.py stub for end-to-end tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement CLI subcommand routing in analyze_plan.py main() function
- [X] T006 [P] Create argparse subparsers for 'report' and 'compare' subcommands
- [X] T007 Add argument validation: report requires 1 file, compare requires 2+ files
- [X] T008 Implement error messages for incorrect argument counts per subcommand
- [X] T009 Route 'report' subcommand to existing TerraformPlanAnalyzer workflow (preserve backward compatibility)
- [X] T010 Create handler stub for 'compare' subcommand that routes to multi_env_comparator
- [X] T011 Add help text for both subcommands showing usage examples
- [X] T012 [P] Write end-to-end test for CLI routing (test both subcommands invoke correct handlers) in test_e2e_multi_env.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Multi-Environment Comparison (Priority: P1) 🎯 MVP

**Goal**: Compare 2-3 environment plan files and generate HTML report with columnar layout showing "before" state differences

**Independent Test**: Run `python analyze_plan.py compare dev.json staging.json prod.json --html` with real plan files and verify HTML report shows resources in columns with differences highlighted

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement EnvironmentPlan class in multi_env_comparator.py (load plan file, extract before_values)
- [X] T014 [P] [US1] Implement ResourceComparison class in multi_env_comparator.py (aggregate configs from multiple environments)
- [X] T015 [US1] Implement MultiEnvReport class in multi_env_comparator.py (orchestrate comparison logic)
- [X] T016 [US1] Add method to extract all unique resource addresses across all environments in MultiEnvReport
- [X] T017 [US1] Add method to build ResourceComparison objects for each unique resource address in MultiEnvReport
- [X] T018 [US1] Implement difference detection logic - compare configs across environments in ResourceComparison
- [X] T019 [US1] Handle missing resources (show "N/A" when resource exists in some but not all environments)
- [X] T020 [US1] Implement summary statistics calculation in MultiEnvReport (total_environments, total_unique_resources, resources_with_differences, etc.)
- [X] T021 [P] [US1] Create multi-column HTML table template in generate_html_report.py
- [X] T022 [P] [US1] Add function generate_multi_env_html_report() in generate_html_report.py
- [X] T023 [US1] Implement resource row generation with one column per environment in HTML report
- [X] T024 [US1] Reuse existing highlight_json_diff() function to highlight differences between environment configs
- [X] T025 [US1] Add CSS styling for multi-column table (responsive, readable columns)
- [X] T026 [US1] Implement summary card showing comparison metrics at top of HTML report
- [X] T027 [US1] Wire compare subcommand to call MultiEnvReport and generate HTML in analyze_plan.py

### Tests for User Story 1

- [X] T028 [P] [US1] Write unit test: EnvironmentPlan loads plan file and extracts before_values correctly in test_multi_env_unit.py
- [X] T029 [P] [US1] Write unit test: ResourceComparison aggregates configs from 3 environments in test_multi_env_unit.py
- [X] T030 [P] [US1] Write unit test: ResourceComparison detects differences correctly in test_multi_env_unit.py
- [X] T031 [P] [US1] Write unit test: MultiEnvReport calculates summary statistics correctly in test_multi_env_unit.py
- [X] T032 [US1] Write end-to-end test: compare 3 plan files with --html flag, verify HTML file created in test_e2e_multi_env.py
- [X] T033 [US1] Write end-to-end test: verify HTML contains correct number of columns (3) in test_e2e_multi_env.py
- [X] T034 [US1] Write end-to-end test: verify differences are highlighted in HTML output in test_e2e_multi_env.py
- [X] T035 [US1] Write end-to-end test: verify missing resources show "N/A" in appropriate columns in test_e2e_multi_env.py
- [X] T036 [US1] Write end-to-end test: verify report subcommand still works (backward compatibility) in test_e2e_multi_env.py
- [X] T037 [US1] Run end-to-end tests with actual Terraform plan files and validate output
- [X] T038 [US1] Fix any bugs discovered during end-to-end testing
- [X] T039 [US1] Verify summary statistics are accurate in generated HTML report

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Core comparison functionality works.

---

## Phase 4: User Story 4 - Support Variable Number of Environments (Priority: P2)

**Goal**: Support comparing anywhere from 2 to 5+ environments (not locked to exactly 3)

**Independent Test**: Run compare with 2, 3, 4, and 5 plan files and verify HTML adapts column count

### Implementation for User Story 4

- [X] T040 [P] [US4] Update MultiEnvReport to handle variable number of environments (no hardcoded assumptions of 3) in multi_env_comparator.py
- [X] T041 [P] [US4] Update HTML table generation to dynamically create N columns based on environment count in generate_html_report.py
- [X] T042 [US4] Add responsive CSS for 2-5+ column layouts in generate_html_report.py
- [X] T043 [US4] Update summary statistics to work with any number of environments in MultiEnvReport

### Tests for User Story 4

- [X] T044 [P] [US4] Write end-to-end test: compare 2 plan files, verify 2 columns in HTML in test_e2e_multi_env.py
- [X] T045 [P] [US4] Write end-to-end test: compare 5 plan files, verify 5 columns in HTML in test_e2e_multi_env.py
- [X] T046 [US4] Write end-to-end test: compare with 1 file triggers error message suggesting 'report' subcommand in test_e2e_multi_env.py
- [X] T047 [US4] Run end-to-end tests with variable environment counts and validate output
- [X] T048 [US4] Fix any layout issues with 5+ column tables

**Checkpoint**: Tool now supports flexible environment counts (2-5+)

---

## Phase 5: User Story 2 - Environment Labeling and Ordering (Priority: P2)

**Goal**: Allow custom environment labels and control column order

**Independent Test**: Use --env-names flag and verify custom labels appear in report

### Implementation for User Story 2

- [X] T049 [P] [US2] Add --env-names flag to compare subcommand argparse in analyze_plan.py
- [X] T050 [US2] Implement environment name parsing (comma-separated list) in compare handler
- [X] T051 [US2] Validate that number of env-names matches number of plan files, show error if mismatch
- [X] T052 [US2] Implement default name derivation from plan filenames when --env-names not provided in EnvironmentPlan
- [X] T053 [US2] Update HTML table headers to use environment labels in generate_html_report.py
- [X] T054 [US2] Preserve input file order for column ordering (plan files provided in desired column order)

### Tests for User Story 2

- [X] T055 [P] [US2] Write end-to-end test: use --env-names flag, verify custom labels in HTML in test_e2e_multi_env.py
- [X] T056 [P] [US2] Write end-to-end test: omit --env-names, verify names derived from filenames in test_e2e_multi_env.py
- [ ] T057 [US2] Write end-to-end test: provide mismatched env-names count, verify error message in test_e2e_multi_env.py
- [ ] T058 [US2] Run end-to-end tests and validate custom labeling works correctly
- [ ] T059 [US2] Fix any naming or ordering issues

**Checkpoint**: Environment labeling and ordering functionality complete

---

## Phase 6: User Story 3 - Filter to Show Only Differences (Priority: P3)

**Goal**: Add --diff-only flag to hide resources with identical configuration across all environments

**Independent Test**: Use --diff-only flag and verify only differing resources shown in report

### Implementation for User Story 3

- [ ] T060 [P] [US3] Add --diff-only flag to compare subcommand argparse in analyze_plan.py
- [ ] T061 [US3] Implement filtering logic in MultiEnvReport to exclude resources where has_differences=False
- [ ] T062 [US3] Update HTML generation to show "No configuration differences found" message when no diffs and --diff-only used
- [ ] T063 [US3] Ensure identical resources still shown in gray when --diff-only NOT used (default behavior)

### Tests for User Story 3

- [ ] T064 [P] [US3] Write end-to-end test: use --diff-only with identical resources, verify message shown in test_e2e_multi_env.py
- [ ] T065 [P] [US3] Write end-to-end test: use --diff-only with some differences, verify only diffs shown in test_e2e_multi_env.py
- [ ] T066 [US3] Write end-to-end test: omit --diff-only, verify all resources shown in test_e2e_multi_env.py
- [ ] T067 [US3] Run end-to-end tests and validate filtering works
- [ ] T068 [US3] Fix any filtering edge cases

**Checkpoint**: Diff-only filtering complete

---

## Phase 7: Advanced Features - HCL Resolution & Sensitive Values

**Goal**: Support HCL resolution with per-environment tfvars and sensitive value handling

**Independent Test**: Use --tf-dir and --tfvars-files to resolve values, verify HCL-resolved values in report

### Implementation

- [ ] T069 [P] Add --tf-dir flag to compare subcommand (reuse existing flag pattern) in analyze_plan.py
- [ ] T070 [P] Add --tfvars-files flag to compare subcommand argparse in analyze_plan.py
- [ ] T071 Implement tfvars file list parsing (comma-separated) in compare handler
- [ ] T072 Validate that number of tfvars files matches number of plan files, show error if mismatch
- [ ] T073 Create HCLValueResolver instance for each environment with corresponding tfvars file in EnvironmentPlan
- [ ] T074 Apply HCL resolution to "known after apply" values in each environment's before_values
- [ ] T075 [P] Implement sensitive value detection across environments in ResourceComparison
- [ ] T076 [P] Add --show-sensitive flag support to compare subcommand in analyze_plan.py
- [ ] T077 Implement masked sensitive value display ("[SENSITIVE]") with difference highlighting in HTML
- [ ] T078 Add visual indicator (⚠️) when masked sensitive values differ across environments

### Tests

- [ ] T079 [P] Write end-to-end test: use --tf-dir and --tfvars-files, verify HCL-resolved values in HTML in test_e2e_multi_env.py
- [ ] T080 [P] Write end-to-end test: verify mismatched tfvars count triggers error in test_e2e_multi_env.py
- [ ] T081 [P] Write end-to-end test: verify sensitive values masked by default in test_e2e_multi_env.py
- [ ] T082 [P] Write end-to-end test: verify --show-sensitive reveals actual values in test_e2e_multi_env.py
- [ ] T083 [P] Write end-to-end test: verify differing masked sensitive values are highlighted in test_e2e_multi_env.py
- [ ] T084 Run HCL resolution tests with real tfvars files
- [ ] T085 Fix any HCL resolution issues

**Checkpoint**: HCL resolution and sensitive value handling complete

---

## Phase 8: Advanced Features - Nested Structures & Ignore Config

**Goal**: Add expand/collapse for nested structures and ignore configuration support

**Independent Test**: Generate report with deeply nested config and verify collapse/expand works

### Implementation

- [ ] T086 [P] Add expand/collapse JavaScript controls for nested JSON structures in HTML template in generate_html_report.py
- [ ] T087 [P] Add CSS styling for collapsible sections (default: collapsed for depth > 2)
- [ ] T088 Add --config flag to compare subcommand (reuse existing ignore config format) in analyze_plan.py
- [ ] T089 Load ignore configuration in compare handler
- [ ] T090 Apply ignore fields consistently across all environments in ResourceComparison
- [ ] T091 Update diff detection to respect ignore configuration

### Tests

- [ ] T092 [P] Write end-to-end test: verify deeply nested structures are collapsed by default in test_e2e_multi_env.py
- [ ] T093 [P] Write end-to-end test: use --config flag, verify ignored fields not shown in diffs in test_e2e_multi_env.py
- [ ] T094 Run tests with complex nested structures and ignore configs
- [ ] T095 Fix any collapsing or ignore configuration issues

**Checkpoint**: Nested structure handling and ignore config support complete

---

## Phase 9: User Story 5 - Text Output (Priority: P3)

**Goal**: Provide terminal-friendly text output for multi-environment comparison (no HTML)

**Independent Test**: Run compare without --html flag and verify readable text output

### Implementation for User Story 5

- [ ] T096 [P] [US5] Implement text output formatter for multi-environment comparison in multi_env_comparator.py
- [ ] T097 [US5] Add resource grouping logic for text display (group by resource address)
- [ ] T098 [US5] Implement column-style text output with environment names
- [ ] T099 [US5] Add -v (verbose) flag support for detailed text output in compare subcommand
- [ ] T100 [US5] Handle terminal width gracefully (wrap or truncate with indicators)

### Tests for User Story 5

- [ ] T101 [P] [US5] Write end-to-end test: omit --html flag, verify text output generated in test_e2e_multi_env.py
- [ ] T102 [P] [US5] Write end-to-end test: use -v flag, verify verbose text output in test_e2e_multi_env.py
- [ ] T103 [US5] Run text output tests and validate readability
- [ ] T104 [US5] Fix any text formatting issues

**Checkpoint**: Text output functionality complete

---

## Phase 10: Polish & Cross-Cutting Concerns

**Goal**: Final polish, error handling, documentation, and validation

### Error Handling & Edge Cases

- [ ] T105 Add error handling for corrupted/invalid JSON plan files
- [ ] T106 Add error handling for plan files from different Terraform versions
- [ ] T107 Add validation for duplicate environment names (error if names conflict)
- [ ] T108 Implement graceful handling of plan files with different resource types
- [ ] T109 Add error handling for missing plan files (clear file not found messages)
- [ ] T110 Test edge case: same resource address but different resource types across environments

### Documentation & Help

- [ ] T111 Update README.md with compare subcommand documentation and examples
- [ ] T112 Add usage examples to --help text for both subcommands
- [ ] T113 Create example plan files for testing/demonstration purposes (must include: 2+ resource types (e.g., aws_instance, aws_s3_bucket), nested configuration depth 3+, at least one sensitive value, one resource missing in one environment)
- [ ] T114 Update existing documentation to reference new subcommand architecture

### Final Validation

- [ ] T115 Run all unit tests and verify 100% pass rate
- [ ] T116 Run all end-to-end tests and verify 100% pass rate
- [ ] T117 Performance test: verify 3 plans with 100 resources each complete in <10 seconds
- [ ] T118 Performance test: verify 5 environments process without degradation
- [ ] T119 Backward compatibility test: verify all existing analyze_plan.py use cases still work with 'report' subcommand
- [ ] T120 Manual test: generate comparison reports with real Terraform plans and validate output quality
- [ ] T121 Manual test: verify HTML reports are readable and visually clear
- [ ] T122 Code review: verify no code duplication (Constitution Principle I)
- [ ] T123 Constitution check: verify all data entities in canonical data model (Principle II)
- [ ] T124 Constitution check: verify end-to-end tests cover all CLI flags (Principle V)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Phase 1-3 delivers MVP**:
- Phase 1: Setup
- Phase 2: Foundational (CLI routing)
- Phase 3: User Story 1 (Basic comparison)

**MVP Capabilities**:
- Compare 2-3 environments
- HTML output with columnar layout
- Basic difference highlighting
- Subcommand-based CLI

**MVP Validation**: Can generate useful comparison report for real Terraform plans

### Incremental Delivery

After MVP (Phase 3), deliver in priority order:
1. Phase 4: Variable environment count (US4 - P2)
2. Phase 5: Custom labeling (US2 - P2)
3. Phase 6: Diff-only filter (US3 - P3)
4. Phase 7: HCL resolution & sensitive values
5. Phase 8: Nested structures & ignore config
6. Phase 9: Text output (US5 - P3)
7. Phase 10: Polish & validation

### Parallel Execution Opportunities

**Within User Story 1** (after foundational complete):
- T013, T014 can run in parallel (different classes)
- T021, T022 can run in parallel with T013-T020 (HTML work vs. comparison logic)
- T028-T031 can all run in parallel (independent unit tests)

**Within User Story 4**:
- T040, T041 can run in parallel (backend vs. frontend)
- T044, T045 can run in parallel (independent test cases)

**Within Advanced Features**:
- T069, T070, T086, T087, T088 can all run in parallel (independent features)
- T079-T083, T092, T093 can all run in parallel (independent test cases)

### Dependencies Summary

**Critical Path**:
1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 Core)
2. Phase 3 complete → Phase 4, 5, 6, 7, 8, 9 can proceed in parallel
3. All phases → Phase 10 (Polish)

**Story Dependencies**:
- US2, US3, US4, US5 all depend on US1 being complete
- US2, US3, US4, US5 are independent of each other
- Advanced features (Phases 7-8) can be implemented in any order after US1

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (US1 - MVP)**: 27 tasks (15 implementation + 12 tests)
- **Phase 4 (US4)**: 9 tasks (4 implementation + 5 tests)
- **Phase 5 (US2)**: 11 tasks (6 implementation + 5 tests)
- **Phase 6 (US3)**: 9 tasks (4 implementation + 5 tests)
- **Phase 7 (Advanced - HCL & Sensitive)**: 17 tasks (10 implementation + 7 tests)
- **Phase 8 (Advanced - Nested & Ignore)**: 10 tasks (6 implementation + 4 tests)
- **Phase 9 (US5 - Text Output)**: 9 tasks (5 implementation + 4 tests)
- **Phase 10 (Polish)**: 20 tasks

**Total**: 124 tasks

**Estimated Effort**:
- MVP (Phases 1-3): ~40% of total effort
- Full Feature (All Phases): 100% effort
- Polish & Validation: ~15% of total effort
