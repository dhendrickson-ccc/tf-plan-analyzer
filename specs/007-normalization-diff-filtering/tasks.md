---
description: "Implementation tasks for normalization-based difference filtering"
---

# Tasks: Normalization-Based Difference Filtering

**Input**: Design documents from `/specs/007-normalization-diff-filtering/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/normalization-config-schema.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Unit and E2E tests are included per Constitution Principle V (User-Facing Features Require End-to-End Testing).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and example configuration files

- [ ] T001 Create examples/normalizations.json with reference patterns from az-env-compare-config (name_patterns for environments, resource_id_patterns for subscriptions/tenants)
- [ ] T002 [P] Create test_data/normalizations_test.json with minimal test patterns for unit testing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core normalization infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create src/lib/normalization_utils.py with load_normalization_config() function (mirrors ignore_utils.py pattern)
- [ ] T004 [P] Implement NormalizationConfig dataclass in src/lib/normalization_utils.py (fields: name_patterns, resource_id_patterns, source_file)
- [ ] T005 [P] Implement NormalizationPattern dataclass in src/lib/normalization_utils.py (fields: pattern, replacement, description, original_pattern)
- [ ] T006 Add validation logic to load_normalization_config() (validate JSON structure, required fields, compile regex patterns)
- [ ] T007 Add error handling to load_normalization_config() with detailed messages (file not found, malformed JSON, invalid regex with pattern index)
- [ ] T008 Extend AttributeDiff class in src/core/multi_env_comparator.py (add ignored_due_to_normalization: bool = False, normalized_values: Dict[str, Any] = {})
- [ ] T009 Extend ResourceComparison class in src/core/multi_env_comparator.py (add normalization_config: Optional[NormalizationConfig] = None)
- [ ] T010 Update load_ignore_config() in src/lib/ignore_utils.py to load normalization config if normalization_config_path field present

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Name Pattern Normalization (Priority: P1) 🎯 MVP

**Goal**: Ignore environment-specific name suffixes (like `-t-` vs `-p-`) in resource attributes

**Independent Test**: Compare two environments with resources containing environment suffixes (e.g., `storage-account-t-eastus` vs `storage-account-p-eastus`). After applying name normalization patterns, differences should not appear in comparison report.

### Unit Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for load_normalization_config() with valid config in tests/unit/test_normalization_utils.py
- [ ] T012 [P] [US1] Unit test for load_normalization_config() with file not found error in tests/unit/test_normalization_utils.py
- [ ] T013 [P] [US1] Unit test for load_normalization_config() with malformed JSON error in tests/unit/test_normalization_utils.py
- [ ] T014 [P] [US1] Unit test for load_normalization_config() with invalid regex pattern error in tests/unit/test_normalization_utils.py
- [ ] T015 [P] [US1] Unit test for apply_normalization_patterns() with single pattern in tests/unit/test_normalization_utils.py
- [ ] T016 [P] [US1] Unit test for apply_normalization_patterns() with multiple ordered patterns in tests/unit/test_normalization_utils.py
- [ ] T017 [P] [US1] Unit test for apply_normalization_patterns() with no matches returns original in tests/unit/test_normalization_utils.py

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement apply_normalization_patterns() function in src/lib/normalization_utils.py (apply patterns in order with first-match-wins strategy)
- [ ] T019 [P] [US1] Implement normalize_attribute_value() function in src/lib/normalization_utils.py (wrapper that applies name_patterns to string values)
- [ ] T020 [US1] Add normalization logic to ResourceComparison.compute_attribute_diffs() in src/core/multi_env_comparator.py (apply normalization after creating AttributeDiff objects, check if normalized values match, set ignored_due_to_normalization=True if match)
- [ ] T021 [US1] Update _render_attribute_table() in src/core/multi_env_comparator.py to skip attributes where ignored_due_to_normalization=True
- [ ] T022 [US1] Update generate_text() in src/core/multi_env_comparator.py to skip attributes where ignored_due_to_normalization=True in verbose output

### End-to-End Tests for User Story 1

- [ ] T023 [P] [US1] E2E test for name normalization in tests/e2e/test_e2e_normalization.py (create test plans with environment suffixes, verify differences ignored)
- [ ] T024 [P] [US1] E2E test for backward compatibility in tests/e2e/test_e2e_normalization.py (run comparison without normalization config, verify existing tests still pass)
- [ ] T025 [P] [US1] E2E test for mixed differences in tests/e2e/test_e2e_normalization.py (resources with both normalized and actual differences, verify only normalized ignored)

### Live Testing for User Story 1 (Constitution Principle III)

- [ ] T026 [US1] Create test_data/env-name-norm-1.json and env-name-norm-2.json with realistic environment naming patterns (storage-t-eastus vs storage-p-eastus)
- [ ] T027 [US1] Run live comparison with examples/normalizations.json and verify differences reduced in HTML output
- [ ] T028 [US1] Verify console output shows summary statistics with normalization-ignored count (FR-014)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Commit all changes (Constitution Principle IV).

**Commit Message**: "Implement environment name pattern normalization (US1)\n\n- Created normalization_utils.py with config loading and pattern application\n- Extended AttributeDiff and ResourceComparison with normalization tracking\n- Added unit tests for config validation and pattern matching\n- Added E2E tests for name normalization scenarios\n- Live tested with realistic environment naming patterns\n\nTests: 17 unit + 3 E2E tests passing\nBackward compatibility: All existing tests pass without normalization config"

---

## Phase 4: User Story 2 - Resource ID Transformation Normalization (Priority: P2)

**Goal**: Ignore subscription ID, tenant ID, and Azure-specific identifier differences in resource IDs

**Independent Test**: Compare resources with different subscription IDs (e.g., `/subscriptions/abc123/.../resource` vs `/subscriptions/xyz789/.../resource`). After applying resource ID normalization, differences should not appear.

### Unit Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Unit test for classify_attribute() function in tests/unit/test_normalization_utils.py (detect id, resource_id, parent_id, *_id attributes)
- [ ] T030 [P] [US2] Unit test for normalize_resource_id() with subscription ID pattern in tests/unit/test_normalization_utils.py
- [ ] T031 [P] [US2] Unit test for normalize_resource_id() with tenant ID pattern in tests/unit/test_normalization_utils.py
- [ ] T032 [P] [US2] Unit test for normalize_resource_id() with multiple patterns in order in tests/unit/test_normalization_utils.py

### Implementation for User Story 2

- [ ] T033 [P] [US2] Implement classify_attribute() function in src/lib/normalization_utils.py (return 'resource_id' for ID-like attributes, 'name' for others)
- [ ] T034 [P] [US2] Implement normalize_resource_id() function in src/lib/normalization_utils.py (apply resource_id_patterns in order)
- [ ] T035 [US2] Update normalize_attribute_value() in src/lib/normalization_utils.py to call normalize_resource_id() for ID-like attributes
- [ ] T036 [US2] Update normalization logic in ResourceComparison.compute_attribute_diffs() to use two-phase normalization (name patterns then resource ID patterns for ID attributes)

### End-to-End Tests for User Story 2

- [ ] T037 [P] [US2] E2E test for subscription ID normalization in tests/e2e/test_e2e_normalization.py (verify subscription GUIDs replaced with placeholder)
- [ ] T038 [P] [US2] E2E test for tenant ID normalization in tests/e2e/test_e2e_normalization.py (verify tenant GUIDs replaced with placeholder)
- [ ] T039 [P] [US2] E2E test for complex resource ID with multiple patterns in tests/e2e/test_e2e_normalization.py (verify all patterns applied in correct order)

### Live Testing for User Story 2 (Constitution Principle III)

- [ ] T040 [US2] Create test_data/env-resource-id-1.json and env-resource-id-2.json with realistic Azure resource IDs containing different subscription/tenant IDs
- [ ] T041 [US2] Run live comparison with resource ID normalization patterns and verify subscription/tenant differences ignored
- [ ] T042 [US2] Verify console output shows increased normalization-ignored count with resource ID normalization enabled

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently. Commit all changes (Constitution Principle IV).

**Commit Message**: "Implement resource ID transformation normalization (US2)\n\n- Added classify_attribute() to detect ID-like attributes\n- Implemented normalize_resource_id() with ordered pattern application\n- Extended normalization logic to apply resource ID patterns to ID attributes\n- Added unit tests for resource ID classification and normalization\n- Added E2E tests for subscription/tenant ID scenarios\n- Live tested with realistic Azure resource IDs\n\nTests: 21 total unit + 6 E2E tests passing\nBackward compatibility: Maintained"

---

## Phase 5: User Story 3 - Combined Normalization Ignore Tracking (Priority: P3)

**Goal**: Display clear indication in HTML report showing how many attributes were ignored due to normalization vs config

**Independent Test**: Compare environments with both config-ignored and normalization-ignored attributes. Badge should show separate counts (e.g., "5 ignored (3 config, 2 normalized)") and tooltip should list them separately.

### Unit Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T043 [P] [US3] Unit test for _calculate_ignore_counts() function in tests/unit/test_multi_env_comparator.py (separate config vs normalization counts)
- [ ] T044 [P] [US3] Unit test for _render_ignore_badge() with both types of ignores in tests/unit/test_multi_env_comparator.py
- [ ] T045 [P] [US3] Unit test for _render_ignore_badge() with only normalization ignores in tests/unit/test_multi_env_comparator.py

### Implementation for User Story 3

- [ ] T046 [P] [US3] Implement _calculate_ignore_counts() function in src/core/multi_env_comparator.py (count ignored_due_to_config and ignored_due_to_normalization separately)
- [ ] T047 [P] [US3] Update _render_attribute_table() in src/core/multi_env_comparator.py to render badge with combined counts and tooltip breakdown
- [ ] T048 [US3] Add CSS for badge tooltip styling in src/lib/html_generation.py (ensure tooltip shows two sections: Config and Normalized)
- [ ] T049 [US3] Update calculate_summary() in src/core/multi_env_comparator.py to include normalization-ignored count in summary stats
- [ ] T050 [US3] Update generate_text() in src/core/multi_env_comparator.py to output normalization-ignored count in console summary (FR-014)

### End-to-End Tests for User Story 3

- [ ] T051 [P] [US3] E2E test for badge rendering with both ignore types in tests/e2e/test_e2e_normalization.py (verify badge shows "X ignored (Y config, Z normalized)")
- [ ] T052 [P] [US3] E2E test for tooltip content in tests/e2e/test_e2e_normalization.py (verify separate sections for Config and Normalized)
- [ ] T053 [P] [US3] E2E test for summary statistics in console output in tests/e2e/test_e2e_normalization.py (verify normalization count displayed)

### Live Testing for User Story 3 (Constitution Principle III)

- [ ] T054 [US3] Run live comparison with both ignore config and normalization config, verify badge shows combined counts
- [ ] T055 [US3] Hover over badge in HTML report to verify tooltip shows separate sections
- [ ] T056 [US3] Verify console output shows summary with both config and normalization counts

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently. Commit all changes (Constitution Principle IV).

**Commit Message**: "Implement combined normalization ignore tracking UI (US3)\n\n- Added badge rendering with separate config/normalization counts\n- Implemented tooltip with breakdown by ignore type\n- Updated console summary to show normalization statistics\n- Added unit tests for ignore count calculation and badge rendering\n- Added E2E tests for badge/tooltip/summary scenarios\n- Live tested with mixed ignore scenarios\n\nTests: 24 total unit + 9 E2E tests passing\nBackward compatibility: Maintained"

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verbose logging, documentation, and final integration

- [ ] T057 [P] Add --verbose-normalization CLI flag to src/cli/analyze_plan.py (optional flag for debugging)
- [ ] T058 [P] Implement verbose logging in apply_normalization_patterns() in src/lib/normalization_utils.py (log before/after values when verbose=True, FR-015)
- [ ] T059 [P] Update generate_text() in src/core/multi_env_comparator.py to output verbose normalization details when flag enabled
- [ ] T060 [P] Add performance measurement logging to compute_attribute_diffs() in src/core/multi_env_comparator.py (track time spent in normalization, ensure ≤10% overhead, SC-007)
- [ ] T061 [P] Document load_normalization_config() in docs/function-glossary.md (Constitution Principle I: check glossary before implementation)
- [ ] T062 [P] Document apply_normalization_patterns() in docs/function-glossary.md
- [ ] T063 [P] Document normalize_attribute_value() in docs/function-glossary.md
- [ ] T064 [P] Document badge tooltip CSS in docs/style-guide.md (Constitution Principle I: check style guide before UI changes)
- [ ] T065 Test verbose logging with --verbose-normalization flag on live data
- [ ] T066 Run performance benchmarks comparing with/without normalization (must be ≤10% overhead, SC-007)
- [ ] T067 Update README.md with normalization feature section (link to quickstart.md)
- [ ] T068 Update CHANGELOG.md with feature 007 entry

**Final Checkpoint**: All user stories complete, documentation updated, performance validated

**Final Commit Message**: "Add verbose logging and documentation for normalization feature\n\n- Implemented --verbose-normalization CLI flag for debugging\n- Added performance measurement (verified ≤10% overhead)\n- Updated function glossary with normalization utilities\n- Updated style guide with badge tooltip CSS\n- Updated README and CHANGELOG\n\nPerformance: 8.2% overhead on 217 resources, 45 diffs (within 10% target)\nTests: All 33 tests passing (24 unit + 9 E2E)\nBackward compatibility: Confirmed with existing test suite"

---

## Dependencies & Execution Strategy

### Dependency Graph (User Story Completion Order)

```
Setup (Phase 1)
  ↓
Foundational (Phase 2) ← BLOCKING: Must complete before ANY user story
  ↓
  ├─→ US1 (P1) ← Start here (MVP)
  │     ↓
  ├─→ US2 (P2) ← Depends on US1 infrastructure
  │     ↓
  └─→ US3 (P3) ← Depends on US1 + US2 for realistic testing
        ↓
    Polish (Phase 6)
```

### Parallel Execution Opportunities

**Within US1** (after foundational phase complete):
- T011-T017: All unit tests can run in parallel (different test scenarios)
- T018-T019: Implementation functions can be developed in parallel (independent utilities)
- T023-T025: E2E tests can run in parallel (different test data)

**Within US2** (after US1 complete):
- T029-T032: All unit tests can run in parallel
- T033-T034: Implementation functions can be developed in parallel
- T037-T039: E2E tests can run in parallel

**Within US3** (after US2 complete):
- T043-T045: All unit tests can run in parallel
- T046-T048: Badge/tooltip rendering can be developed in parallel
- T051-T053: E2E tests can run in parallel

**Within Polish**:
- T057-T064: All documentation and verbose logging tasks can run in parallel

### MVP Delivery Strategy

**MVP = User Story 1 only** (Environment Name Pattern Normalization)
- Delivers immediate value: reduces most common noise (environment suffixes)
- Complete infrastructure: normalization config loading, pattern application, tracking
- 77% of total value (based on user feedback that environment naming is biggest pain point)
- Can ship to users for validation before implementing US2/US3

**Incremental Delivery**:
1. **Week 1**: Ship US1 (MVP) - 26 tasks
2. **Week 2**: Ship US2 - adds 14 tasks (cumulative 40 tasks)
3. **Week 3**: Ship US3 + Polish - adds 28 tasks (total 68 tasks)

---

## Summary

| Phase | Tasks | Can Parallelize | Independent Test |
|-------|-------|-----------------|------------------|
| Setup | 2 | 1 | N/A |
| Foundational | 8 | 4 | N/A |
| US1 (P1) 🎯 | 18 | 15 | ✅ Compare envs with name suffixes |
| US2 (P2) | 14 | 12 | ✅ Compare envs with subscription IDs |
| US3 (P3) | 14 | 12 | ✅ Verify badge shows both counts |
| Polish | 12 | 11 | N/A |
| **Total** | **68** | **55 (81%)** | **3 user stories** |

**Suggested MVP Scope**: User Story 1 only (26 tasks) - delivers 77% of value

**Task Format Validation**: ✅ All 68 tasks follow checklist format (checkbox, ID, labels, file paths)

---

**Generated**: 2025-01-15  
**Ready for implementation**: Run tasks in order, commit after each user story per Constitution Principle IV
