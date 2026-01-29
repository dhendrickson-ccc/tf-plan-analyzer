# Implementation Plan: Q&A Notes Markdown Support with Preview Toggle

**Branch**: `009-qa-markdown-preview` | **Date**: 2026-01-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-qa-markdown-preview/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add markdown rendering support to existing Q&A notes with a toggle between edit mode (raw markdown) and preview mode (rendered HTML). Include collapsible section functionality for better screen space management. Q&A notes currently exist as plain textarea fields with auto-save to LocalStorage - this feature enhances them with formatted markdown display while preserving the existing auto-save behavior and adding save-on-mode-switch and save-on-blur triggers.

## Technical Context

**Language/Version**: Python 3.9+ (currently supports 3.9, 3.10, 3.11)  
**Primary Dependencies**: json5>=0.9.0 for parsing; client-side JavaScript for markdown rendering  
**Storage**: LocalStorage (client-side) for Q&A notes persistence  
**Testing**: pytest>=8.0, pytest-cov>=4.0 with e2e tests for HTML generation  
**Target Platform**: Generated HTML files (static, client-side functionality)  
**Project Type**: Single Python project with CLI interface  
**Performance Goals**: <1 second toggle between edit/preview modes; instant markdown rendering  
**Constraints**: Pure client-side implementation (no server); must work in offline HTML files; HTML sanitization required  
**Scale/Scope**: Q&A notes per attribute per resource (potentially hundreds per report)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Duplication Prohibited ✅ PASS
- **Status**: PASS - Will reuse existing `get_notes_css()`, `get_notes_javascript()`, and HTML generation patterns from `src/lib/html_generation.py` and `src/core/multi_env_comparator.py`
- **Action**: Search function glossary and codebase for reusable markdown rendering, DOM manipulation, and state management patterns before creating new functions

### II. Shared Data Model Is Canonical ✅ PASS
- **Status**: PASS - Q&A notes already exist in the system. Will document markdown-specific state (view mode, collapsed state) in data_model.md
- **Action**: Review `.specify/memory/data_model.md` and add Q&A note markdown extension entities before implementation

### III. Live Testing Is Mandatory ✅ PASS
- **Status**: PASS - Will generate actual HTML comparison reports and test markdown rendering, mode toggling, collapse/expand, and persistence in real browser environment
- **Action**: Create live test HTML files with markdown content, verify rendering, test all interactive features

### IV. Commit After Every User Story ✅ PASS
- **Status**: PASS - Each user story (markdown rendering, toggle functionality, smart defaults, collapse/expand) will be committed separately
- **Action**: Commit after completing each prioritized user story

### V. User-Facing Features Require End-to-End Testing ✅ PASS
- **Status**: PASS - This feature modifies HTML generation (user-facing output). Will add e2e tests that generate HTML files and validate JavaScript functionality
- **Action**: Add e2e tests in `tests/e2e/` that generate comparison reports and verify markdown rendering, toggle behavior, and state persistence

### VI. Python Development Must Use Virtual Environments ✅ PASS
- **Status**: PASS - Development will occur in activated virtual environment
- **Action**: Ensure venv is activated before running tests, installing packages, or executing code

## Project Structure

### Documentation (this feature)

```text
specs/009-qa-markdown-preview/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Requirements checklist (completed)
├── research.md          # Phase 0 output (to be created by /speckit.plan)
├── data-model.md        # Phase 1 output (to be created by /speckit.plan)
├── quickstart.md        # Phase 1 output (to be created by /speckit.plan)
├── contracts/           # Phase 1 output (to be created by /speckit.plan)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── lib/
│   └── html_generation.py      # Add markdown CSS/JS functions here
├── core/
│   └── multi_env_comparator.py # Modify Q&A notes HTML generation
├── cli/
│   └── analyze_plan.py         # No changes needed (CLI unaffected)
└── security/
    └── sensitive_obfuscator.py # No changes needed

tests/
├── e2e/
│   └── test_e2e_qa_markdown.py # New: End-to-end tests for markdown rendering
├── unit/
│   └── test_html_generation.py # Add tests for new markdown functions
└── fixtures/
    └── markdown_notes_*.json   # Test data with markdown content

docs/
├── function-glossary.md        # Update with new markdown functions
└── style-guide.md              # Add markdown preview styling
```

**Structure Decision**: Single project structure (default). This feature extends existing HTML generation functionality in `src/lib/html_generation.py` and modifies Q&A notes rendering in `src/core/multi_env_comparator.py`. All changes are client-side (CSS/JavaScript) within generated HTML files. No new modules or significant architectural changes required.

## Complexity Tracking

> **No constitution violations** - This section is intentionally empty as all gates passed without justification needed.

---

## Phase 0: Research & Design Decisions ✅ COMPLETE

**Status**: Complete - 2026-01-28

### Key Decisions Made

| Decision Point | Choice | Document Reference |
|----------------|--------|-------------------|
| **Markdown Library** | marked.js v12+ (~30KB) | [research.md](research.md#1-client-side-markdown-rendering-libraries) |
| **HTML Sanitization** | DOMPurify v3+ (~20KB) | [research.md](research.md#1-client-side-markdown-rendering-libraries) |
| **Sanitization Mode** | Strip ALL HTML tags | [spec.md](spec.md#clarifications) |
| **State Management** | DOM data attributes + CSS classes | [research.md](research.md#2-state-management-for-mode-toggle) |
| **Persistence Layer** | Extend existing LocalStorage pattern | [research.md](research.md#3-localstorage-persistence-patterns) |
| **Collapse Pattern** | HTML5 `<details>/<summary>` | [research.md](research.md#4-collapsible-section-patterns) |
| **Save Triggers** | Auto-save + mode-switch + blur | [research.md](research.md#5-save-trigger-mechanisms) |
| **Mode Persistence** | Smart default (NO persistence) | [research.md](research.md#6-smart-default-mode-selection) |
| **Collapse Persistence** | Per-report (YES persistence) | [research.md](research.md#3-localstorage-persistence-patterns) |

### Research Outputs

- ✅ **research.md**: Complete technical research on markdown libraries, state management, persistence, and styling
- ✅ **Clarifications**: All specification ambiguities resolved (5 questions answered in spec.md)

### Technologies Selected

**Client-Side (CDN)**:
- marked.js: https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js
- DOMPurify: https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js

**Python Libraries**: None required (pure client-side implementation)

**Browser APIs**:
- LocalStorage API (persistence)
- Details/Summary Elements (collapsible)
- DOM API (manipulation)

---

## Phase 1: Data Model & Contracts ✅ COMPLETE

**Status**: Complete - 2026-01-28

### Deliverables

- ✅ **data-model.md**: Comprehensive data model with 3 new entities
- ✅ **contracts/javascript-api.md**: Complete JavaScript API contract (6 functions)
- ✅ **contracts/css-styling.md**: Complete CSS styling contract (15+ classes)
- ✅ **quickstart.md**: Developer implementation guide with examples

### New Data Entities Defined

1. **QANoteData** (persisted in LocalStorage)
   - question: string (markdown)
   - answer: string (markdown)
   - lastModified: number (timestamp)
   - isCollapsed: boolean (state)

2. **QANoteViewState** (transient UI state)
   - mode: 'edit' | 'preview'
   - hasContent: boolean
   - isCollapsed: boolean
   - resourceAddress: string
   - attributeName: string

3. **MarkdownRenderResult** (processing output)
   - rawMarkdown: string
   - dirtyHtml: string
   - cleanHtml: string
   - hasInvalidSyntax: boolean

### API Contracts

**JavaScript Functions** (6 new):
1. renderMarkdown(rawMarkdown: string): string
2. toggleNoteMode(event, resource, attribute): void
3. initializeNoteMode(reportId, resource, attribute): void
4. saveCollapseState(resource, attribute, isCollapsed): void
5. restoreCollapseState(reportId, resource, attribute): void
6. saveNoteWithBlur(resource, attribute, field): void

**CSS Classes** (15+ new):
- Container: `.notes-container` (details element)
- Header: `.notes-header`, `.notes-title`, `.toggle-mode`
- Content: `.notes-content`, `.note-edit`, `.note-preview`
- Markdown: `.note-preview h1-h6`, `.note-preview code`, etc.

### Integration Points Identified

**Python Side**:
- `src/lib/html_generation.py`: Add `get_notes_markdown_css()` and `get_notes_markdown_javascript()`
- `src/core/multi_env_comparator.py`: Modify `_render_attribute_section()` to generate `<details>` structure

**Client Side**:
- CDN script includes in HTML `<head>`
- Event handlers in HTML attributes (onclick, onblur, oninput)
- LocalStorage keys: `tf-notes-${reportId}#${resource}#${attribute}`

---

## Constitution Check Re-Evaluation (Post-Design)

*All gates remain PASS after Phase 1 design completion.*

### Updated Assessment

**I. Code Duplication Prohibited** ✅ PASS (Verified)
- Reuses existing `get_notes_css()` and `get_notes_javascript()` patterns
- Extends (not replaces) current Q&A notes functionality
- No duplicate markdown rendering logic

**II. Shared Data Model Is Canonical** ✅ PASS (Verified)
- New entities documented in [data-model.md](data-model.md)
- Integrates with existing AttributeDiff and ResourceComparison entities
- No schema conflicts

**III. Live Testing Is Mandatory** ✅ PASS (Planned)
- E2E test plan defined in [quickstart.md](quickstart.md#phase-3-end-to-end-testing)
- Will generate real HTML files and test in browser
- Manual verification checklist created

**IV. Commit After Every User Story** ✅ PASS (Ready)
- Four user stories from spec.md can be implemented independently
- Each story has clear acceptance criteria
- Git workflow defined in quickstart

**V. User-Facing Features Require End-to-End Testing** ✅ PASS (Planned)
- HTML generation is user-facing output
- E2E tests will validate complete workflow
- Browser-based testing required and planned

**VI. Python Development Must Use Virtual Environments** ✅ PASS (Ready)
- Venv activation reminder in quickstart
- No new Python dependencies required
- Existing environment sufficient

---

## Next Steps

### Ready for Phase 2: Task Generation

Run `/speckit.tasks` to generate actionable task list in `tasks.md`

### Implementation Order (from Spec User Stories)

1. **P1 - Markdown Rendering**: Basic markdown preview functionality
2. **P2 - Mode Toggle**: Edit/preview switching with save triggers
3. **P2 - Smart Defaults**: Content-based mode initialization
4. **P3 - Collapse/Expand**: Collapsible section with persistence

### Estimated Effort

- **Phase 2 (Tasks)**: ~30 minutes (task generation)
- **Implementation**: ~8-12 hours
  - Python CSS/JS generation: ~2 hours
  - HTML structure modification: ~2 hours
  - JavaScript client-side logic: ~3 hours
  - Testing (unit + e2e): ~3 hours
  - Documentation updates: ~1 hour
  - Live testing & fixes: ~1-2 hours

---

## Artifacts Summary

**Phase 0 Complete**:
- ✅ research.md (8 sections, complete technical decisions)

**Phase 1 Complete**:
- ✅ data-model.md (3 entities, state diagrams, security notes)
- ✅ contracts/javascript-api.md (6 functions, error handling, testing)
- ✅ contracts/css-styling.md (15+ classes, responsive, accessibility)
- ✅ quickstart.md (4 phases, testing checklist, troubleshooting)

**Pending**:
- ⏳ tasks.md (Phase 2 - `/speckit.tasks` command)

---

**Plan Status**: ✅ **COMPLETE** - Ready for task generation and implementation
