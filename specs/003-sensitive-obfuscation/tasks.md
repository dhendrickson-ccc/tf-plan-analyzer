---
description: "Implementation tasks for Sensitive Data Obfuscation feature"
---

# Tasks: Sensitive Data Obfuscation

**Input**: Design documents from `/specs/003-sensitive-obfuscation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md

**Note**: This feature does NOT require explicit test tasks per the specification. Tests will be created as part of implementation tasks to verify functionality, but the specification does not mandate TDD approach.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [ ] T001 Install cryptography>=41.0.0 dependency for Fernet salt encryption
- [ ] T002 [P] Create test fixture directory structure in test_data/obfuscate/
- [ ] T003 [P] Verify analyze_plan.py has subcommand infrastructure for adding obfuscate command

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core modules that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create salt_manager.py with get_encryption_key() function that reads TF_ANALYZER_SALT_KEY environment variable
- [ ] T005 [P] Create sensitive_obfuscator.py with obfuscate_value() function signature for hashing with salt
- [ ] T006 Implement salt generation in salt_manager.py using secrets.token_bytes(32) for 32-byte salt
- [ ] T007 Implement position seed generation in salt_manager.py using secrets.token_bytes(32)
- [ ] T008 Implement get_salt_position() function in sensitive_obfuscator.py using PRNG with position_seed
- [ ] T009 Implement store_salt() function in salt_manager.py with binary format [salt_length(2) + position_seed(32) + encrypted_salt]
- [ ] T010 Implement load_salt() function in salt_manager.py with Fernet decryption and error handling
- [ ] T011 Create test fixtures in test_data/obfuscate/: basic.json (simple resource with sensitive values)
- [ ] T012 [P] Create test fixtures in test_data/obfuscate/: nested.json (5+ levels deep), multiple-resources.json (overlapping sensitive values)
- [ ] T013 [P] Create test fixtures in test_data/obfuscate/: empty-sensitive.json, null-sensitive.json, malformed-sensitive.json, no-sensitive-marker.json

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Obfuscate Sensitive Values in Single File (Priority: P1) 🎯 MVP

**Goal**: DevOps engineers can obfuscate a single Terraform plan file with all sensitive values replaced by deterministic hashes, enabling safe sharing while preserving the plan structure.

**Independent Test**: Provide a tfplan.json with sensitive_values markers, run obfuscate command, verify output has all sensitive values replaced with "obf_" prefixed hashes and non-sensitive values unchanged.

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement obfuscate_value() core hashing logic in sensitive_obfuscator.py: convert value to bytes, insert salt at position, SHA-256 hash, format as "obf_" + hexdigest
- [X] T015 [P] [US1] Implement traverse_and_obfuscate() function in sensitive_obfuscator.py to recursively traverse JSON and find sensitive_values markers
- [X] T016 [US1] Implement value replacement logic in sensitive_obfuscator.py: for each field marked true in sensitive_values, replace corresponding value in resource data with obfuscated hash
- [X] T017 [US1] Add obfuscate subcommand to analyze_plan.py with argument parser for positional plan_file argument
- [X] T018 [US1] Implement --output/-o flag in analyze_plan.py obfuscate subcommand with default value <input_stem>-obfuscated.json
- [X] T019 [US1] Implement input file validation in analyze_plan.py: check file exists, parse JSON, validate Terraform plan structure (has resource_changes field)
- [X] T020 [US1] Implement output file check in analyze_plan.py: exit with error code 4 if output file already exists
- [X] T021 [US1] Implement main obfuscation workflow in analyze_plan.py: load plan → generate salt → traverse resources → obfuscate sensitive values → write output
- [X] T022 [US1] Implement salt file auto-creation in analyze_plan.py: save generated salt to <output>.salt using store_salt() from salt_manager.py
- [X] T023 [US1] Implement error handling in analyze_plan.py: catch and report errors with detailed messages to stderr, appropriate exit codes (1-8)
- [X] T024 [US1] Add type handling in sensitive_obfuscator.py obfuscate_value(): support string, number, boolean, null (convert all to JSON bytes for hashing)
- [X] T025 [US1] Create test_e2e_obfuscate.py with test_basic_obfuscation() using test_data/obfuscate/basic.json
- [X] T026 [P] [US1] Create tests in test_e2e_obfuscate.py: test_nested_obfuscation(), test_multiple_resources(), test_empty_sensitive_value(), test_null_sensitive_value()
- [X] T027 [P] [US1] Create tests in test_e2e_obfuscate.py: test_no_sensitive_marker(), test_invalid_json(), test_malformed_sensitive_values()
- [X] T027b [US1] Create test_e2e_obfuscate.py test_error_behavior(): verify FR-018 (detailed error messages to stderr with resource/field) and FR-019 (no output file created on any error)
- [X] T028 [US1] Verify all FR requirements for US1: FR-001 through FR-008, FR-010 through FR-014, FR-017 through FR-019, FR-022
- [X] T029 [US1] Test with real Terraform plan files from test_data/: dev-sensitive.json and prod-sensitive.json
- [X] T030 [US1] Validate quickstart.md Step 1-3 instructions work end-to-end

**Checkpoint**: User Story 1 complete - single file obfuscation works, safe sharing enabled

---

## Phase 4: User Story 2 - Deterministic Obfuscation for Drift Detection (Priority: P2)

**Goal**: DevOps engineers can compare two obfuscated Terraform plan files and detect drift, knowing that identical sensitive values produce identical hashes when using the same salt.

**Independent Test**: Obfuscate the same tfplan.json twice, verify identical output. Obfuscate two different files with overlapping sensitive values using same salt, confirm matching values produce matching hashes.

### Implementation for User Story 2

- [X] T031 [US2] Verify determinism in obfuscate_value() function: same input + same salt + same position_seed → identical hash every time
- [X] T032 [US2] Create test_e2e_obfuscate.py test_deterministic_same_file(): obfuscate same file twice with same salt, assert outputs are byte-identical
- [X] T033 [US2] Create test_e2e_obfuscate.py test_deterministic_cross_file(): create two different plans with same sensitive value, obfuscate with same salt, assert matching values have matching hashes
- [X] T034 [US2] Create test_e2e_obfuscate.py test_drift_detection(): create two plans with some matching and some different sensitive values, obfuscate both, verify differences are visible as different hashes
- [X] T035 [US2] Validate with existing compare functionality: obfuscate dev-sensitive.json and prod-sensitive.json with same salt, run analyze_plan.py compare, verify comparison works correctly
- [X] T036 [US2] Validate SC-002 success criteria: same file + same salt = 100% identical output
- [X] T037 [US2] Validate SC-003 success criteria: different files + same sensitive value + same salt = matching hashes
- [X] T038 [US2] Validate SC-004 success criteria: users can compare obfuscated files and identify actual drift

**Checkpoint**: User Story 2 complete - drift detection validated across environments

---

## Phase 5: User Story 3 - Configurable Salt Randomization (Priority: P3)

**Goal**: Security-conscious engineers can use different salts for unrelated obfuscation sessions (preventing rainbow table attacks) or reuse saved salts for related comparisons (maintaining determinism).

**Independent Test**: Run obfuscation with different salt configurations, verify same input produces different outputs with different salts but identical outputs with same salt.

### Implementation for User Story 3

- [X] T039 [P] [US3] Implement --salt-file/-s flag in analyze_plan.py obfuscate subcommand to accept path to existing salt file
- [X] T040 [US3] Implement salt file loading logic in analyze_plan.py: when --salt-file provided, load salt using load_salt() instead of generating new one
- [X] T041 [US3] Implement salt file validation in analyze_plan.py: exit with error code 5 if salt file not found, code 6 if corrupted/invalid
- [X] T042 [US3] Update obfuscation workflow in analyze_plan.py: skip salt file creation when --salt-file was provided (salt already exists)
- [X] T043 [US3] Create test_e2e_obfuscate.py test_salt_reuse(): generate salt, obfuscate file1, reuse salt for file2, verify matching sensitive values have matching hashes
- [X] T044 [US3] Create test_e2e_obfuscate.py test_different_salts(): obfuscate same file with two different salts, verify outputs differ
- [X] T045 [US3] Create test_e2e_obfuscate.py test_salt_file_not_found(): verify exit code 5 when --salt-file points to non-existent file
- [X] T046 [US3] Create test_e2e_obfuscate.py test_corrupted_salt_file(): create invalid salt file, verify exit code 6 and helpful error message
- [X] T047 [US3] Test environment variable encryption: verify TF_ANALYZER_SALT_KEY enables salt decryption across different machines/CI nodes
- [X] T048 [US3] Validate FR-009, FR-015, FR-016, FR-020, FR-021: salt generation, reuse, encryption, naming, file specification
- [ ] T049 [US3] Validate quickstart.md "Drift Detection Across Environments" workflow end-to-end

**Checkpoint**: User Story 3 complete - salt management fully functional, security enhanced

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories and final validation

- [ ] T050 [P] Implement --force/-f flag in analyze_plan.py to allow output file overwriting (exit code 4 → success with warning)
- [ ] T051 [P] Implement --show-stats flag in analyze_plan.py to display resources processed, values obfuscated, execution time
- [ ] T052 Add performance optimization to traverse_and_obfuscate() if needed: ensure 10MB files process in under 5 seconds (SC-001)
- [ ] T053 Test large file handling: validate SC-007 with 1000+ resource plan file (no memory issues, no degradation)
- [ ] T054 [P] Add comprehensive error messages for all exit codes (1-8) per contracts/cli-interface.md
- [ ] T055 [P] Add CLI help text and examples to analyze_plan.py obfuscate subcommand
- [ ] T056 Create test_obfuscation_unit.py with unit tests for obfuscate_value(), get_salt_position(), traverse_and_obfuscate()
- [ ] T057 [P] Create test_salt_manager.py with unit tests for generate, store, load, encrypt, decrypt functions
- [ ] T058 Validate all success criteria SC-001 through SC-007
- [ ] T059 Run full quickstart.md validation: all examples and workflows execute successfully
- [ ] T060 [P] Update main README.md with obfuscate subcommand documentation and examples
- [ ] T061 Security review: verify no sensitive values leak in error messages, logs, or temporary files
- [ ] T062 Code review: verify Constitution Principle I (no duplication), Principle II (canonical data model references)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) completion - relies on basic obfuscation working
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) completion - can run parallel with US2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: FOUNDATIONAL - Must complete first. Provides core obfuscation functionality.
- **User Story 2 (P2)**: DEPENDS on US1 - Cannot test determinism without basic obfuscation working
- **User Story 3 (P3)**: DEPENDS on US1 - Can start after US1 complete, can run parallel with US2

### Within Each User Story

**User Story 1**:
- T014-T016 (core obfuscation logic) can run in parallel
- T017-T024 (CLI integration) sequential, depend on T014-T016
- T025-T027 (tests) can run in parallel after T014-T024 complete
- T028-T030 (validation) sequential, depend on all tests passing

**User Story 2**:
- T031 (verify determinism) depends on US1 complete
- T032-T034 (tests) can run in parallel after T031
- T035-T038 (validation) sequential after tests

**User Story 3**:
- T039-T042 (salt file flag) sequential
- T043-T046 (tests) can run in parallel after T039-T042
- T047-T049 (validation) sequential after tests

### Parallel Opportunities

- **Setup Phase**: T002 and T003 can run in parallel
- **Foundational Phase**: T004 and T005 can run in parallel, T011 and T012 and T013 can run in parallel
- **User Story 1**: T014 and T015 can run in parallel, T025 and T026 and T027 can run in parallel
- **User Story 3**: T039 can run in parallel with T050-T051 from Polish phase
- **Polish Phase**: T050, T051, T054, T055, T057, T060 can all run in parallel
- **User Stories 2 and 3**: Can be worked on in parallel by different developers after US1 complete

---

## Parallel Example: User Story 1

```bash
# Launch core obfuscation modules in parallel:
# Developer A: "Implement obfuscate_value() core hashing logic in sensitive_obfuscator.py"
# Developer B: "Implement traverse_and_obfuscate() function in sensitive_obfuscator.py"

# After core modules complete, CLI integration:
# Single developer or sequential: T016 → T017 → T018 → ... → T024

# Launch all tests in parallel after CLI complete:
# Developer A: "test_basic_obfuscation(), test_nested_obfuscation()"
# Developer B: "test_multiple_resources(), test_empty_sensitive_value()"
# Developer C: "test_no_sensitive_marker(), test_invalid_json()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (10 tasks) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 (17 tasks)
4. **STOP and VALIDATE**: Run all US1 tests, verify quickstart.md workflows
5. **COMMIT**: Constitution Principle IV - commit after User Story 1
6. Deploy/demo MVP - single file obfuscation ready for use

### Incremental Delivery

1. **Foundation** (Setup + Foundational) → Checkpoint: Core modules ready
2. **MVP Release** (+ User Story 1) → Checkpoint: Safe sharing enabled → COMMIT
3. **Drift Detection** (+ User Story 2) → Checkpoint: Comparison workflows work → COMMIT
4. **Enhanced Security** (+ User Story 3) → Checkpoint: Salt management complete → COMMIT
5. **Production Ready** (+ Polish) → Final validation and release

### Parallel Team Strategy

With 2-3 developers:

1. **Together**: Complete Setup + Foundational (Phases 1-2)
2. **Once Foundational done**:
   - Developer A: User Story 1 (critical path)
   - Developer B: Create all test fixtures (T011-T013) and unit tests (T056-T057)
3. **After US1 complete**:
   - Developer A: User Story 2
   - Developer B: User Story 3
   - Developer C: Polish tasks (T050-T055, T060-T062)
4. **Final**: All developers: Validation (T058-T059)

---

## Task Summary

- **Total Tasks**: 63
- **Setup**: 3 tasks
- **Foundational (BLOCKING)**: 10 tasks
- **User Story 1 (P1 - MVP)**: 18 tasks
- **User Story 2 (P2)**: 8 tasks
- **User Story 3 (P3)**: 11 tasks
- **Polish**: 13 tasks

**Parallel Opportunities**: 19 tasks marked [P] can run in parallel with other tasks in same phase

**Suggested MVP Scope**: Phases 1-3 (User Story 1 only) = 31 tasks = core obfuscation functionality

**Full Feature Scope**: All 63 tasks = complete obfuscation with drift detection and salt management

---

## Notes

- Tests are integrated into implementation tasks (not separate TDD phase) per specification guidance
- Each user story is independently testable and deployable
- Constitution Principle IV: Commit after completing T030 (US1), T038 (US2), T049 (US3)
- Constitution Principle V: End-to-end tests in test_e2e_obfuscate.py cover complete user journeys
- All file paths are absolute from repository root (single-project Python CLI structure)
- Exit codes 1-8 per contracts/cli-interface.md must be tested and validated
