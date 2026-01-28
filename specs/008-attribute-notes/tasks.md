# Tasks: Attribute Change Notes

**Input**: Design documents from `/specs/008-attribute-notes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: E2E tests included to verify HTML generation and notes functionality

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization - no new infrastructure needed (client-side only feature)

- [X] T001 Review existing HTML generation patterns in src/lib/html_generation.py
- [X] T002 Review existing attribute rendering in src/core/multi_env_comparator.py _render_attribute_table()
- [X] T003 [P] Review LocalStorage API and JavaScript patterns from research.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CSS and JavaScript infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create get_notes_css() function in src/lib/html_generation.py with styles for .notes-container, .note-field, .note-label
- [X] T005 Create get_notes_javascript() function in src/lib/html_generation.py with getReportId(), debounce(), saveNote(), debouncedSaveNote, loadNotes()
- [X] T006 Update generate_full_styles() in src/lib/html_generation.py to include get_notes_css()
- [X] T007 Modify MultiEnvReport.generate_html() in src/core/multi_env_comparator.py to include get_notes_javascript() before closing head tag
- [X] T008 Add import for get_notes_javascript in src/core/multi_env_comparator.py
- [X] T009 Create _sanitize_for_html_id() helper method in MultiEnvReport class in src/core/multi_env_comparator.py

**Checkpoint**: Foundation ready - CSS and JavaScript infrastructure complete, can now add notes HTML

---

## Phase 3: User Story 1 - Add Question to Attribute Change (Priority: P1) 🎯 MVP

**Goal**: Add question textarea below each attribute change with auto-save to LocalStorage

**Independent Test**: Generate HTML report, add question to any attribute, refresh page, verify question persists

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Add test_get_notes_css() in tests/unit/test_html_generation.py to verify CSS contains .notes-container, .note-field, .note-label
- [ ] T011 [P] [US1] Add test_get_notes_javascript() in tests/unit/test_html_generation.py to verify JS contains all 5 functions
- [ ] T012 [P] [US1] Add test_generate_full_styles_includes_notes_css() in tests/unit/test_html_generation.py
- [ ] T013 [US1] Create tests/e2e/test_e2e_attribute_notes.py with TestUS1AddQuestionField class
- [ ] T014 [US1] Add test_question_field_renders_in_html() E2E test in tests/e2e/test_e2e_attribute_notes.py to verify question textarea exists

### Implementation for User Story 1

- [ ] T015 [US1] Modify _render_attribute_table() in src/core/multi_env_comparator.py to inject notes HTML after attribute-values div closes
- [ ] T016 [US1] Add question textarea with id="note-q-{sanitized_resource}-{sanitized_attribute}" in notes container
- [ ] T017 [US1] Add question label with for attribute matching textarea id in notes container
- [ ] T018 [US1] Add oninput event handler calling debouncedSaveNote() with question field parameter
- [ ] T019 [US1] Add placeholder="Add a question..." to question textarea
- [ ] T020 [US1] Set rows="4" on question textarea for 3-5 visible rows

**Checkpoint**: User Story 1 complete - question field renders, auto-saves, and persists across page refreshes

**Commit Point**: `git commit -m "feat(008): Add question field to attribute changes (US1)"`

---

## Phase 4: User Story 2 - Answer Questions on Attribute Changes (Priority: P1)

**Goal**: Add answer textarea below question field with same persistence behavior

**Independent Test**: Generate HTML report, add both question and answer to an attribute, refresh page, verify both persist

### Tests for User Story 2 ⚠️

- [ ] T021 [US2] Create TestUS2AnswerField class in tests/e2e/test_e2e_attribute_notes.py
- [ ] T022 [US2] Add test_answer_field_renders_in_html() E2E test to verify answer textarea exists with correct attributes
- [ ] T023 [US2] Add test_question_and_answer_persist_together() manual test guide in tests/e2e/test_e2e_attribute_notes.py

### Implementation for User Story 2

- [ ] T024 [US2] Add answer textarea wrapper div with class="note-answer" in _render_attribute_table() in src/core/multi_env_comparator.py
- [ ] T025 [US2] Add answer label with for="note-a-{sanitized_resource}-{sanitized_attribute}" in notes container
- [ ] T026 [US2] Add answer textarea with id="note-a-{sanitized_resource}-{sanitized_attribute}"
- [ ] T027 [US2] Add oninput event handler calling debouncedSaveNote() with answer field parameter
- [ ] T028 [US2] Add placeholder="Add an answer..." to answer textarea
- [ ] T029 [US2] Set rows="4" on answer textarea

**Checkpoint**: User Stories 1 AND 2 complete - both question and answer fields work independently and together

**Commit Point**: `git commit -m "feat(008): Add answer field below question (US2)"`

---

## Phase 5: User Story 3 - Review Multiple Annotated Changes (Priority: P2)

**Goal**: Ensure users can add notes to multiple attributes and review them by scrolling

**Independent Test**: Generate HTML report with 3+ changed attributes, add questions/answers to each, refresh, verify all persist

### Tests for User Story 3 ⚠️

- [ ] T030 [US3] Create TestUS3ReviewMultipleNotes class in tests/e2e/test_e2e_attribute_notes.py
- [ ] T031 [US3] Add test_multiple_attributes_have_independent_notes() E2E test to verify each attribute has unique note fields
- [ ] T032 [US3] Add manual acceptance test instructions for testing with real multi-environment comparison

### Verification for User Story 3

- [ ] T033 [US3] Verify unique IDs are generated for each attribute's question and answer fields
- [ ] T034 [US3] Verify LocalStorage keys are unique per attribute using composite key pattern
- [ ] T035 [US3] Verify loadNotes() correctly populates all notes fields on page load
- [ ] T036 [US3] Manual test with Livetest-temp data: generate 3-env comparison, add notes to 5+ attributes, refresh, verify persistence

**Checkpoint**: All user stories complete - multiple notes work independently and persist correctly

**Commit Point**: `git commit -m "feat(008): Verify multiple notes functionality (US3)"`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final testing, and polish

- [ ] T037 [P] Update docs/function-glossary.md to document get_notes_css() and get_notes_javascript() functions
- [ ] T038 [P] Update docs/style-guide.md to document .notes-container, .note-field, .note-label CSS classes
- [ ] T039 Run full E2E test suite: pytest tests/e2e/test_e2e_attribute_notes.py -v
- [ ] T040 Run full unit test suite: pytest tests/unit/test_html_generation.py -v
- [ ] T041 Generate live HTML comparison report with notes for demo/validation
- [ ] T042 Manual browser testing: verify notes work in Chrome, Firefox, Safari
- [ ] T043 Manual testing: verify special characters in resource names are sanitized correctly (test with resource containing . [ ] : /)
- [ ] T044 Manual testing: verify LocalStorage quota handling (add very long notes, check console for errors)

**Final Checkpoint**: All tests pass, documentation complete, feature ready for PR

---

## Dependency Graph

### User Story Completion Order

```
Setup Phase (T001-T003)
    ↓
Foundational Phase (T004-T009) ← BLOCKING
    ↓
    ├─→ User Story 1 (T010-T020) [P1] ← MVP
    │   └─→ Commit
    ↓
    ├─→ User Story 2 (T021-T029) [P1]
    │   └─→ Commit
    ↓
    └─→ User Story 3 (T030-T036) [P2]
        └─→ Commit
            ↓
        Polish Phase (T037-T044)
            ↓
        Ready for PR
```

### Parallel Execution Opportunities

**Within Setup Phase**:
- T001, T002, T003 can all run in parallel (different review activities)

**Within Foundational Phase**:
- T004 and T005 can run in parallel (different functions in same file)
- T006-T009 must be sequential (dependencies)

**Within User Story 1 Tests**:
- T010, T011, T012 can run in parallel (different test functions)
- T013, T014 must be sequential (T014 needs file from T013)

**Within User Story 1 Implementation**:
- All T015-T020 modify same method, must be sequential

**Within Polish Phase**:
- T037, T038 can run in parallel (different documentation files)
- T039-T044 should run sequentially (testing phases)

---

## Implementation Strategy

### MVP Scope (Suggested)

**Minimum Viable Product includes**:
- User Story 1 only (question field with persistence)
- Demonstrates core value: ability to annotate and persist notes
- ~2-3 hours of work

**Rationale**: User Story 1 alone provides value - users can document questions during review. Answer field (US2) and multiple notes (US3) are incremental enhancements.

### Incremental Delivery Plan

1. **Sprint 1** (2-3 hours):
   - Complete Foundational Phase (T004-T009)
   - Complete User Story 1 (T010-T020)
   - **Deliverable**: Question field with auto-save working
   - **Commit and deploy**

2. **Sprint 2** (1-2 hours):
   - Complete User Story 2 (T021-T029)
   - **Deliverable**: Answer field added, Q&A pairs work together
   - **Commit and deploy**

3. **Sprint 3** (1 hour):
   - Complete User Story 3 (T030-T036)
   - **Deliverable**: Multiple notes verified working
   - **Commit and deploy**

4. **Sprint 4** (1 hour):
   - Complete Polish Phase (T037-T044)
   - **Deliverable**: Documentation and final testing complete
   - **Ready for PR**

**Total Estimated Time**: 5-7 hours across 4 sprints

---

## Task Counts

- **Total Tasks**: 44
- **Setup**: 3 tasks
- **Foundational (Blocking)**: 6 tasks
- **User Story 1 (P1)**: 11 tasks (6 tests + 5 implementation)
- **User Story 2 (P1)**: 9 tasks (3 tests + 6 implementation)
- **User Story 3 (P2)**: 7 tasks (3 tests + 4 verification)
- **Polish**: 8 tasks

---

## Validation Checklist

### Format Validation

- ✅ ALL tasks follow checklist format: `- [ ] [TaskID] [P?] [Story?] Description`
- ✅ Task IDs are sequential (T001-T044)
- ✅ [P] marker only on truly parallelizable tasks
- ✅ [Story] labels (US1, US2, US3) applied correctly
- ✅ File paths included in all implementation tasks

### Completeness Validation

- ✅ Each user story has independent test criteria
- ✅ Setup phase included
- ✅ Foundational phase clearly marked as blocking
- ✅ User stories ordered by priority (P1, P1, P2)
- ✅ Polish phase included
- ✅ Dependency graph shows story completion order
- ✅ Parallel execution opportunities identified

### User Story Independence

- ✅ User Story 1 can be implemented and tested independently
- ✅ User Story 2 can be implemented independently (extends US1 but doesn't break it)
- ✅ User Story 3 is pure verification (no new implementation)
- ✅ Each story has commit point marked

---

## Notes

**Client-Side Only**: This feature is entirely client-side (HTML + JavaScript). No Python logic changes beyond HTML generation.

**No Breaking Changes**: Notes are additive - existing HTML reports continue to work. Notes simply add new fields below attributes.

**Browser Requirement**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) with LocalStorage support.

**Testing Strategy**: E2E tests verify HTML structure and JavaScript embedding. Manual browser testing required for full LocalStorage validation.
