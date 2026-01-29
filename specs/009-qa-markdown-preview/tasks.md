# Tasks: Q&A Notes Markdown Support with Preview Toggle

**Feature**: 009-qa-markdown-preview  
**Input**: Design documents from `/specs/009-qa-markdown-preview/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and environment verification

- [ ] T001 Verify Python virtual environment is activated
- [ ] T002 Verify existing Q&A notes feature (008) is working and committed
- [ ] T003 Review existing code in src/lib/html_generation.py for get_notes_css() and get_notes_javascript() patterns

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create get_notes_markdown_css() function in src/lib/html_generation.py with complete CSS from contracts/css-styling.md
- [ ] T005 [P] Create get_notes_markdown_javascript() function in src/lib/html_generation.py with complete JavaScript from contracts/javascript-api.md
- [ ] T006 [P] Add unit tests for get_notes_markdown_css() in tests/unit/test_html_generation.py
- [ ] T007 [P] Add unit tests for get_notes_markdown_javascript() in tests/unit/test_html_generation.py
- [ ] T008 Update generate_full_styles() in src/lib/html_generation.py to include get_notes_markdown_css()
- [ ] T009 Update HTML template generation to include get_notes_markdown_javascript() after existing get_notes_javascript()

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Formatted Q&A Notes (Priority: P1) 🎯 MVP

**Goal**: Enable markdown rendering in preview mode for Q&A notes with proper formatting for headings, lists, code blocks, and emphasis

**Independent Test**: Open a comparison report with Q&A notes containing markdown syntax and verify proper rendering with headings, bold, italic, lists, code blocks

### Implementation for User Story 1

- [ ] T010 [P] [US1] Modify _render_attribute_section() in src/core/multi_env_comparator.py to generate <details> container structure with data-resource and data-attribute attributes
- [ ] T011 [P] [US1] Add <summary> header with "Q&A Notes" title in src/core/multi_env_comparator.py
- [ ] T012 [P] [US1] Create question field with note-edit class and note-preview div in src/core/multi_env_comparator.py
- [ ] T013 [P] [US1] Create answer field with note-edit class and note-preview div in src/core/multi_env_comparator.py
- [ ] T014 [US1] Implement renderMarkdown() function in get_notes_markdown_javascript() using marked.parse() and DOMPurify.sanitize()
- [ ] T015 [US1] Configure DOMPurify sanitization rules to strip ALL HTML tags (per spec clarifications)
- [ ] T016 [US1] Add markdown-specific CSS classes (.note-preview h1-h6, code, pre, blockquote, ul, ol, etc.) to get_notes_markdown_css()
- [ ] T017 [US1] Test markdown rendering with headings (# ## ###) generates proper h1-h6 tags
- [ ] T018 [US1] Test markdown rendering with lists (ordered/unordered) generates proper ul/ol/li tags
- [ ] T019 [US1] Test markdown rendering with code blocks (```) generates proper pre/code tags with monospace styling
- [ ] T020 [US1] Test markdown rendering with inline formatting (**bold**, *italic*, links) generates proper strong/em/a tags

**Checkpoint**: At this point, markdown rendering should work when manually setting data-mode="preview"

---

## Phase 4: User Story 2 - Edit Q&A Notes with Markdown Preview Toggle (Priority: P2)

**Goal**: Enable toggling between edit mode (raw markdown) and preview mode (rendered HTML) with save-on-switch

**Independent Test**: Add new Q&A notes or edit existing ones, toggle between edit and preview modes, verify markdown renders correctly

### Implementation for User Story 2

- [ ] T021 [P] [US2] Add toggle-mode button to <summary> header in src/core/multi_env_comparator.py with onclick="toggleNoteMode(event, resource, attribute)"
- [ ] T022 [P] [US2] Add data-mode="preview" attribute to <details> container in src/core/multi_env_comparator.py
- [ ] T023 [US2] Add CSS rules for .notes-container[data-mode="edit"] to show textarea and hide preview in get_notes_markdown_css()
- [ ] T024 [US2] Add CSS rules for .notes-container[data-mode="preview"] to hide textarea and show preview in get_notes_markdown_css()
- [ ] T025 [US2] Implement toggleNoteMode(event, resource, attribute) function in get_notes_markdown_javascript()
- [ ] T026 [US2] Add event.stopPropagation() in toggleNoteMode() to prevent details collapse when clicking toggle button
- [ ] T027 [US2] Call saveNote() before mode switch in toggleNoteMode() to trigger explicit save (per spec clarifications)
- [ ] T028 [US2] Render markdown and update preview div innerHTML when switching to preview mode in toggleNoteMode()
- [ ] T029 [US2] Update toggle button text and aria-pressed attribute based on current mode in toggleNoteMode()
- [ ] T030 [US2] Add onblur="saveNoteWithBlur(resource, attribute, field)" to textareas in src/core/multi_env_comparator.py
- [ ] T031 [US2] Implement saveNoteWithBlur() function to trigger immediate save on blur (per spec clarifications)
- [ ] T032 [US2] Test clicking toggle button switches between edit and preview modes
- [ ] T033 [US2] Test editing markdown in edit mode and switching to preview renders updated content
- [ ] T034 [US2] Test switching modes preserves content without loss
- [ ] T035 [US2] Test blur event triggers save before losing focus

**Checkpoint**: At this point, mode toggling should work with proper save triggers

---

## Phase 5: User Story 3 - Smart Mode Selection for Existing Notes (Priority: P2)

**Goal**: Default to preview mode for notes with content, edit mode for empty notes

**Independent Test**: Open reports with existing Q&A notes (should show preview mode) and empty notes (should show edit mode)

### Implementation for User Story 3

- [X] T036 [P] [US3] Implement initializeNoteMode(reportId, resource, attribute) function in get_notes_markdown_javascript()
- [X] T037 [US3] Add smart default logic: hasContent = (question.trim() || answer.trim()) in initializeNoteMode()
- [X] T038 [US3] Set mode to 'preview' if hasContent is true, 'edit' if false in initializeNoteMode()
- [X] T039 [US3] If defaulting to preview mode, render markdown for both question and answer fields in initializeNoteMode()
- [X] T040 [US3] Call initializeNoteMode() for all .notes-container elements on DOMContentLoaded event
- [X] T041 [US3] Test report with existing markdown content defaults to preview mode on page load
- [X] T042 [US3] Test report with empty Q&A notes defaults to edit mode on page load
- [X] T043 [US3] Test closing and reopening report with content maintains preview mode default (mode NOT persisted per spec)

**Checkpoint**: At this point, smart mode defaults should work correctly based on content presence

---

## Phase 6: User Story 4 - Collapse/Expand Q&A Section (Priority: P3)

**Goal**: Enable collapsing and expanding Q&A section with per-report state persistence

**Independent Test**: Click collapse/expand controls, verify section visibility changes, refresh page to verify collapsed state persists

### Implementation for User Story 4

- [X] T044 [P] [US4] Add 'open' attribute to <details> element in src/core/multi_env_comparator.py (default expanded)
- [X] T045 [P] [US4] Add CSS styling for details.notes-container with collapse/expand states in get_notes_markdown_css()
- [X] T046 [P] [US4] Add CSS for .notes-header::marker with ▼ and ▶ icons in get_notes_markdown_css()
- [X] T047 [US4] Implement saveCollapseState(resource, attribute, isCollapsed) function in get_notes_markdown_javascript()
- [X] T048 [US4] Add 'toggle' event listener to details element that calls saveCollapseState() in get_notes_markdown_javascript()
- [X] T049 [US4] Update existing LocalStorage note data to include isCollapsed property in saveCollapseState()
- [X] T050 [US4] Implement restoreCollapseState(reportId, resource, attribute) function in get_notes_markdown_javascript()
- [X] T051 [US4] Load isCollapsed from LocalStorage and set details.open attribute accordingly in restoreCollapseState()
- [X] T052 [US4] Call restoreCollapseState() for all notes on DOMContentLoaded (before initializeNoteMode)
- [X] T053 [US4] Test clicking summary collapses section and hides content
- [X] T054 [US4] Test clicking summary when collapsed expands section and shows content
- [X] T055 [US4] Test collapsed state preserves mode state (edit or preview) when re-expanded
- [X] T056 [US4] Test collapsed state preserves content when re-expanded
- [X] T057 [US4] Test page refresh maintains collapsed state for specific report (per-report persistence)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Testing, documentation, and refinements that affect multiple user stories

- [ ] T058 [P] Create end-to-end test file tests/e2e/test_e2e_qa_markdown.py
- [ ] T059 [P] Add e2e test: generate HTML comparison report with markdown notes and verify structure in tests/e2e/test_e2e_qa_markdown.py
- [ ] T060 [P] Add e2e test: verify CDN script tags for marked.js and DOMPurify are present in generated HTML
- [ ] T061 [P] Add e2e test: verify HTML contains data-mode, data-resource, data-attribute attributes
- [ ] T062 [P] Add e2e test: verify onclick and onblur event handlers are present in HTML
- [ ] T063 [P] Test XSS prevention: verify <script> tags are stripped in markdown rendering
- [ ] T064 [P] Test XSS prevention: verify onclick/onerror event attributes are stripped
- [ ] T065 [P] Test malformed markdown renders gracefully without breaking interface
- [ ] T065a [P] Add UI feedback for malformed markdown (e.g., warning icon, tooltip, or message in preview mode)
- [ ] T066 [P] Test very long lines wrap appropriately without breaking layout
- [ ] T066a [P] Add UI feedback for long lines/nesting (e.g., horizontal scroll, ellipsis, or wrapping indicator)
- [ ] T067 [P] Test special characters in markdown are escaped correctly
- [ ] T068 [P] Update docs/function-glossary.md with get_notes_markdown_css() documentation
- [ ] T069 [P] Update docs/function-glossary.md with get_notes_markdown_javascript() documentation
- [ ] T070 [P] Update docs/style-guide.md with markdown preview component styling guidelines and visual indicator requirements for edit/preview mode (e.g., icon, color, label)
- [ ] T070a [P] Standardize terminology: use "section visibility state (collapsed/expanded)" throughout all documentation and code comments
- [ ] T070b [P] Review and update all references in code, docs, and UI to use "section visibility state (collapsed/expanded)"
- [ ] T071 [P] Add accessibility verification: ARIA labels present on toggle button and textareas
- [ ] T072 [P] Add accessibility verification: keyboard navigation works (Tab, Enter, Space)
- [ ] T073 [P] Add accessibility verification: focus indicators visible on all interactive elements
- [ ] T074 [P] Test responsive design: mobile viewport (<768px) styling works correctly
- [ ] T075 [P] Test print styles: preview mode shown when printing, edit mode hidden
- [ ] T076 Create test HTML file with various markdown content types (headings, lists, code, links, blockquotes)
- [ ] T077 Manually open test HTML file in browser and verify all markdown renders correctly
- [ ] T078 Manually test mode toggle, collapse/expand, and state persistence in browser
- [ ] T079 Test in Chrome, Firefox, and Safari for cross-browser compatibility
- [ ] T080 Run full test suite: pytest tests/ --cov
- [ ] T081 [P] Update .specify/memory/data_model.md with QANoteData, QANoteViewState, and MarkdownRenderResult entities and ensure all new/modified data structures are documented before implementation
- [ ] T081a [P] Add explicit check that .specify/memory/data_model.md is referenced in all relevant spec, plan, and code comments
- [ ] T082 Verify all acceptance scenarios from spec.md are testable and passing
- [ ] T083 Code review: verify no code duplication, reuse of existing patterns
- [ ] T084 Performance check: verify mode toggle completes in <100ms, markdown rendering in <50ms for typical note
- [ ] T085 Run validation from quickstart.md to ensure implementation matches design

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Depends on US1 (needs markdown rendering to work)
  - User Story 3 (P2): Depends on US1 and US2 (needs both rendering and toggle to work)
  - User Story 4 (P3): Can start after Foundational - Independent of other stories (but typically done last due to P3 priority)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - markdown rendering core
- **User Story 2 (P2)**: Depends on US1 completion (can't toggle to preview without rendering)
- **User Story 3 (P2)**: Depends on US1 and US2 completion (needs both rendering and toggle mechanisms)
- **User Story 4 (P3)**: Foundation only - collapse/expand is independent (can be implemented in parallel with US1-3 technically, but P3 priority suggests last)

### Within Each User Story

- US1: All tasks T010-T020 can proceed in parallel after foundation (marked [P])
- US2: T021-T024 (HTML/CSS) can run in parallel; T025-T031 sequential (JavaScript logic); T032-T035 tests at end
- US3: T036-T039 (implementation) sequential; T040-T043 (tests) after implementation
- US4: T044-T046 (HTML/CSS) in parallel; T047-T052 (JavaScript) sequential; T053-T057 (tests) at end
- Polish: Most tasks marked [P] can run in parallel except those that depend on test results

### Parallel Opportunities Per User Story

**User Story 1** (after Foundation complete):
```bash
# Parallel track 1: HTML structure
T010, T011, T012, T013  # Can all run together

# Parallel track 2: JavaScript rendering
T014, T015  # JavaScript implementation

# Parallel track 3: CSS styling
T016  # CSS classes

# Sequential: Tests after implementation
T017, T018, T019, T020
```

**User Story 2** (after US1 complete):
```bash
# Parallel track 1: HTML updates
T021, T022, T030

# Parallel track 2: CSS mode states
T023, T024

# Sequential: JavaScript implementation
T025 → T026 → T027 → T028 → T029 → T031

# Sequential: Tests
T032 → T033 → T034 → T035
```

**User Story 4** (after Foundation complete, independent of US1-3):
```bash
# Parallel tracks:
T044, T045, T046  # HTML/CSS together

# Sequential: JavaScript
T047 → T048 → T049 → T050 → T051 → T052

# Sequential: Tests
T053 → T054 → T055 → T056 → T057
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Include**: User Story 1 only
- Basic markdown rendering in preview mode
- No toggle functionality (always preview)
- No smart defaults
- No collapse/expand

**Delivers**: Core value - formatted markdown viewing

### Full Feature Scope

**Include**: All user stories (US1, US2, US3, US4)
- Complete markdown rendering (US1)
- Edit/preview toggle (US2)
- Smart mode selection (US3)
- Collapsible sections (US4)

**Delivers**: Complete feature as specified

### Recommended Delivery Sequence

1. **Sprint 1**: Phase 1 (Setup) + Phase 2 (Foundation) + Phase 3 (US1) → Commit
2. **Sprint 2**: Phase 4 (US2) → Commit
3. **Sprint 3**: Phase 5 (US3) + Phase 6 (US4) → Commit
4. **Sprint 4**: Phase 7 (Polish) → Final commit

Each sprint delivers independently testable value.

---

## Task Summary

- **Total Tasks**: 85
- **Setup Tasks**: 3
- **Foundation Tasks**: 6
- **User Story 1 Tasks**: 11
- **User Story 2 Tasks**: 15
- **User Story 3 Tasks**: 8
- **User Story 4 Tasks**: 14
- **Polish Tasks**: 28
- **Parallelizable Tasks**: 45 (marked with [P])

---

## Testing Strategy

**Unit Tests** (Python):
- Test CSS function returns valid styles (T006)
- Test JavaScript function includes all required functions (T007)
- Test HTML generation includes correct structure

**End-to-End Tests** (Browser-based):
- Generate actual HTML files (T059-T062)
- Verify markdown rendering (T076-T077)
- Verify XSS prevention (T063-T064)
- Verify edge cases (T065-T067)
- Manual browser testing (T078-T079)

**Accessibility Tests**:
- ARIA labels (T071)
- Keyboard navigation (T072)
- Focus indicators (T073)

**Cross-Browser Tests**:
- Chrome, Firefox, Safari (T079)

---

## Validation Checklist

Before considering this feature complete:

- [ ] All 4 user stories have passing tests
- [ ] All 13 functional requirements (FR-001 to FR-013) are implemented
- [ ] All 9 success criteria (SC-001 to SC-009) are met
- [ ] All acceptance scenarios from spec.md pass
- [ ] Constitution check: No code duplication (reused existing patterns)
- [ ] Constitution check: Data model updated (.specify/memory/data_model.md)
- [ ] Constitution check: Live testing completed (browser-based)
- [ ] Constitution check: Commits per user story completed
- [ ] Constitution check: End-to-end tests passing
- [ ] Documentation updated (function glossary, style guide)
- [ ] Performance targets met (<1s toggle, <50ms rendering)
- [ ] Security verified (HTML sanitization working)
- [ ] Accessibility verified (keyboard nav, ARIA, focus)

---

**Tasks Status**: Ready for implementation  
**Next Action**: Begin Phase 1 (Setup) tasks
