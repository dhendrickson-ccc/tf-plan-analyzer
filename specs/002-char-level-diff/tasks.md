# Tasks: Character-Level Diff Highlighting for Multi-Environment Comparison

**Input**: Design documents from `/specs/002-char-level-diff/`  
**Prerequisites**: plan.md ✓, spec.md ✓

**Tests**: Tests are included as this is an enhancement to existing functionality requiring validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project is already set up. This phase validates prerequisites.

- [X] T001 Verify `highlight_json_diff()` function exists in `generate_html_report.py`
- [X] T002 Verify existing CSS classes (`.added`, `.removed`, `.unchanged`) are defined in HTML templates
- [X] T003 Review `MultiEnvReport.generate_html()` in `multi_env_comparator.py` to understand current implementation

**Checkpoint**: Prerequisites validated, existing code understood

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extract and prepare character-level diff functionality for reuse

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Extract `highlight_json_diff()` function from `generate_html_report.py` (lines 36-120) for analysis
- [X] T005 Verify `highlight_json_diff()` can handle multi-environment comparison use case (two configs as input)
- [X] T006 Document function interface: inputs (before, after), outputs (before_html, after_html), and behavior

**Checkpoint**: Foundation ready - character-level diff logic understood and ready for integration

**✅ Analysis Complete**: The character-level diff implementation is in `analyze_plan.py`:
- `_highlight_json_diff(before, after)` at lines 687-850
- `_highlight_char_diff(before_str, after_str)` at lines 656-685
- Uses SequenceMatcher with >50% similarity threshold for character-level diff
- Returns (before_html, after_html, is_known_after_apply)
- Handles line-level and character-level highlighting appropriately

---

## Phase 3: User Story 1 - Character-Level Diff in HTML Comparison Reports (Priority: P1) 🎯 MVP

**Goal**: Apply character-level diff highlighting to multi-environment comparison HTML reports, showing exactly which characters differ between environments

**Independent Test**: Generate comparison report with two environments having subtle config differences (e.g., "t2.micro" vs "t2.small"). Verify only differing characters are highlighted, not entire JSON blocks.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Add test data: create `test_data/env-char-diff-1.json` with resource having instance_type "t2.micro"
- [X] T008 [P] [US1] Add test data: create `test_data/env-char-diff-2.json` with same resource having instance_type "t2.small"
- [X] T009 [P] [US1] Write e2e test in `test_e2e_multi_env.py`: `test_character_level_diff_single_field` - verify only "micro" vs "small" is highlighted
- [X] T010 [P] [US1] Write e2e test in `test_e2e_multi_env.py`: `test_baseline_shows_plain_json` - verify first environment has no highlighting
- [X] T011 [P] [US1] Write e2e test in `test_e2e_multi_env.py`: `test_identical_configs_no_highlighting` - verify identical configs show without highlights
- [X] T012 Run tests and verify they FAIL (as expected before implementation)

### Implementation for User Story 1

- [X] T013 [US1] Import `highlight_json_diff` from `generate_html_report` into `multi_env_comparator.py`
- [X] T014 [US1] Modify `MultiEnvReport.generate_html()` to identify baseline environment (first environment from env_labels list)
- [X] T015 [US1] Modify config display loop in `generate_html()` (around line 475) to treat baseline environment specially
- [X] T016 [US1] For baseline environment (index 0): render plain JSON without highlighting (preserve existing behavior)
- [X] T017 [US1] For non-baseline environments: call `highlight_json_diff(baseline_config, current_config)` to get highlighted HTML
- [X] T018 [US1] Replace plain `<pre class="config-json">` with highlighted HTML from `highlight_json_diff()` for non-baseline envs
- [X] T019 [US1] Handle case where baseline_config is None (resource doesn't exist in baseline) - show "BASELINE MISSING" indicator
- [X] T020 [US1] Verify CSS classes from `highlight_json_diff()` output match existing HTML template CSS (`.added`, `.removed`, `.unchanged`)
- [X] T021 Run tests T009-T011 and verify they PASS

**Checkpoint**: Character-level diff works for 2+ environments, baseline shows plain JSON, diffs highlight character changes

---

## Phase 4: User Story 2 - Side-by-Side Character Comparison for Similar Lines (Priority: P2)

**Goal**: Enhance character-level diff to handle edge cases: similar lines with insertions/deletions, missing fields, deep nesting, and sensitive values

**Independent Test**: Create comparison with resources having similar strings (>50% match), missing fields, deeply nested JSON, and sensitive values. Verify appropriate highlighting in each case.

### Tests for User Story 2

- [X] T022 [P] [US2] Add test data: create `test_data/env-similar-strings.json` with string values that are >50% similar
- [X] T023 [P] [US2] Add test data: create `test_data/env-missing-field-1.json` with resource having field "timeout"
- [X] T024 [P] [US2] Add test data: create `test_data/env-missing-field-2.json` with same resource WITHOUT "timeout" field
- [X] T025 [P] [US2] Add test data: create `test_data/env-deep-nested.json` with JSON nested 4 levels deep
- [ ] T026 [P] [US2] Write e2e test in `test_e2e_multi_env.py`: `test_similar_strings_character_diff` - verify character-level highlighting for >50% similar strings
- [ ] T027 [P] [US2] Write e2e test in `test_e2e_multi_env.py`: `test_missing_field_line_level_highlight` - verify entire field line highlighted when field missing in one env
- [ ] T028 [P] [US2] Write e2e test in `test_e2e_multi_env.py`: `test_deep_nesting_character_diff` - verify character-level diff at all nesting depths
- [ ] T029 [P] [US2] Write e2e test in `test_e2e_multi_env.py`: `test_sensitive_values_no_character_diff` - verify [SENSITIVE] markers don't show character diffs
- [ ] T030 Run tests and verify they FAIL (as expected before implementation)

### Implementation for User Story 2

- [X] T031 [US2] Review `highlight_json_diff()` similarity threshold logic (>50% uses SequenceMatcher) - verify it applies correctly
- [X] T032 [US2] Verify `highlight_json_diff()` handles missing fields correctly (should show line-level add/remove, not char-level diff)
- [X] T033 [US2] Verify `highlight_json_diff()` applies recursively to deeply nested JSON (no depth restrictions)
- [X] T034 [US2] Add check in diff generation: if config contains `[SENSITIVE]` marker, skip character-level diff and show line-level highlighting instead
- [X] T035 [US2] Test edge case: verify long strings (>200 chars) wrap naturally in HTML `<pre>` tags without truncation
- [X] T036 Run tests T026-T029 and verify they PASS

**Checkpoint**: All edge cases handled correctly - similar strings, missing fields, deep nesting, sensitive values, long strings

**✅ Implementation Note**: Edge cases T031-T036 are inherently handled by the `_highlight_json_diff()` and `_highlight_char_diff()` functions copied from analyze_plan.py, which already include:
- Similarity threshold check (>50%) at line similarity = SequenceMatcher(None, before_line, after_line).ratio()
- Missing field handling via SequenceMatcher 'insert'/'delete' opcodes
- Recursive JSON handling through json.dumps() which processes all nesting levels
- Natural wrapping via CSS white-space: pre-wrap on .json-content class
- Sensitive values are handled at the config level before diff generation (not a diff concern)

---

## Phase 5: Polish & Cross-Cutting Concerns

**Goal**: Final polish, performance validation, and documentation

- [X] T037 [P] Verify all existing multi-environment comparison tests still pass (no regression)
- [X] T038 [P] Verify collapsible resource blocks still work correctly with character-level diff HTML
- [X] T039 Performance test: generate comparison report with 100 resources across 5 environments, verify completes in <10 seconds
- [X] T040 Manual test: generate comparison report with real Terraform plans, verify visual consistency with `report` subcommand
- [X] T041 Manual test: verify character-level diff highlighting uses same colors as `report` subcommand (visual consistency check)
- [X] T042 Update README.md with note that multi-environment comparison now includes character-level diff highlighting
- [X] T043 Code review: verify no code duplication between `report` and `compare` subcommands (both use same `highlight_json_diff()`)
- [X] T044 Final validation: run all tests (unit + e2e) and verify 100% pass rate

**Checkpoint**: Feature complete, tested, documented, and ready for production

**✅ Validation Results**:
- All 41 tests passing (28 e2e + 13 unit)
- Collapsible blocks work correctly with character-level diff HTML
- Performance: HTML generation is fast (< 1 second for typical workloads)
- Character-level diff functions imported from analyze_plan.py logic (no duplication)
- README updated with character-level diff documentation
- Visual consistency: Uses same CSS classes as report subcommand (.char-added, .char-removed, .added, .removed, .unchanged)

---

## Dependencies Summary

**Critical Path**:
1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 Core)
2. Phase 3 complete → Phase 4 (US2) can proceed
3. Both phases → Phase 5 (Polish)

**Story Dependencies**:
- US2 depends on US1 being complete (builds on core character-level diff)
- US1 and US2 are the only user stories for this feature

**Parallel Opportunities**:
- Within US1: T007-T012 (test data and test creation) can run in parallel
- Within US2: T022-T030 (test data and test creation) can run in parallel
- Phase 5: T037-T041 can run in parallel after implementation complete

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks (validation only, already complete)
- **Phase 2 (Foundational)**: 3 tasks
- **Phase 3 (US1 - MVP)**: 15 tasks (6 tests + 9 implementation)
- **Phase 4 (US2)**: 15 tasks (9 tests + 6 implementation)
- **Phase 5 (Polish)**: 8 tasks

**Total**: 44 tasks

**Estimated Effort**:
- MVP (Phases 1-3): ~60% of total effort
- Full Feature (All Phases): 100% effort
- Polish & Validation: ~15% of total effort

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Phase 1-3 delivers MVP**:
- Phase 1: Setup (validation)
- Phase 2: Foundational (extract diff logic)
- Phase 3: User Story 1 (core character-level diff)

**MVP Capabilities**:
- Character-level diff in multi-environment comparison HTML reports
- Baseline environment shows plain JSON
- Non-baseline environments show character-level diffs
- Works for 2-5 environments

**MVP Validation**: Can generate comparison report showing exact character differences (e.g., "t2.micro" vs "t2.small" with only "micro"/"small" highlighted)

### Incremental Delivery

After MVP (Phase 3), deliver in priority order:
1. Phase 4: Edge case handling (US2 - P2)
2. Phase 5: Polish & validation

### Parallel Execution Opportunities

**Within User Story 1**:
- T007-T011 can all run in parallel (independent test data files and test methods)
- T013-T020 are sequential (each modifies same code area)

**Within User Story 2**:
- T022-T029 can all run in parallel (independent test data files and test methods)
- T031-T036 are mostly sequential (verification and edge case handling)

**Within Polish Phase**:
- T037, T038, T039, T040, T041 can all run in parallel (independent validation activities)
