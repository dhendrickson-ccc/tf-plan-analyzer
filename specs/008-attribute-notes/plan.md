# Implementation Plan: Attribute Change Notes

**Branch**: `008-attribute-notes` | **Date**: January 28, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-attribute-notes/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add interactive question/answer notes to each attribute change in HTML comparison reports. Notes are stored in browser LocalStorage and keyed by report filename + resource address + attribute name. Features auto-save with debouncing, vertically stacked text areas (3-5 rows), and placeholder text. Enables users to document review questions and answers directly on attribute changes for asynchronous collaboration and decision tracking.

## Technical Context

**Language/Version**: Python 3.11 (existing project constraint)
**Primary Dependencies**: None (client-side JavaScript for LocalStorage interaction, no new Python dependencies)
**Storage**: Browser LocalStorage (client-side only, no server-side persistence)
**Testing**: pytest (existing), end-to-end tests with HTML file generation and validation
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge) viewing static HTML files
**Project Type**: Single Python project - generates static HTML reports with embedded JavaScript
**Performance Goals**: Auto-save debouncing at 500ms to prevent excessive LocalStorage writes
**Constraints**: 
- No server-side storage or backend API
- Notes isolated to browser/device (no cross-browser sync)
- LocalStorage quota limits (~5-10MB per origin, browser-dependent)
- Static HTML files must be self-contained (no external JavaScript dependencies)
**Scale/Scope**: 
- Expected usage: 10-50 attribute changes per report with notes
- LocalStorage key pattern: `tf-notes-{filename}#{resource_address}#{attribute_name}`
- Typical note size: 100-500 characters per question/answer pair

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Code Duplication Prohibited**: ✅ PASS
- Will reuse existing `generate_full_styles()` from `src/lib/html_generation.py`
- Will extend `MultiEnvReport._render_attribute_table()` in `src/core/multi_env_comparator.py`
- No new utility functions needed; all logic embedded in HTML/JavaScript

**II. Shared Data Model Is Canonical**: ✅ PASS  
- No new backend data entities (client-side only feature)
- LocalStorage schema will be documented in `data-model.md`
- AttributeNote entity structure will reference existing AttributeDiff from `.specify/memory/data_model.md`

**III. Live Testing Is Mandatory**: ✅ PASS
- End-to-end tests will generate actual HTML files
- Tests will use browser automation or manual validation to verify:
  - Notes fields render correctly
  - LocalStorage save/load works across page refreshes
  - Auto-save debouncing functions properly
- Live test with real comparison report (test-stage-prod HTML)

**IV. Commit After Every User Story**: ✅ PASS
- User Story 1 (Add Question) - will commit after implementation
- User Story 2 (Answer Questions) - will commit after implementation  
- User Story 3 (Review Multiple) - will commit after implementation

**V. User-Facing Features Require End-to-End Testing**: ✅ PASS
- User-facing interface: HTML text fields in generated reports
- E2E tests will:
  - Generate HTML report with `tf-plan-analyzer compare` command
  - Verify HTML contains notes textarea elements with correct IDs
  - Validate JavaScript functions for save/load are embedded
  - Test placeholder text appears correctly
  - Verify LocalStorage keys are generated correctly

**VI. Python Development Must Use Virtual Environments**: ✅ PASS
- All pytest commands will run in activated virtual environment
- Development follows existing project venv usage

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── lib/
│   └── html_generation.py          # Add get_notes_css() and get_notes_javascript()
├── core/
│   └── multi_env_comparator.py     # Modify _render_attribute_value() to add notes fields
├── cli/
│   └── analyze_plan.py             # No changes (feature is client-side only)
└── security/
    └── sensitive_obfuscator.py     # No changes

tests/
├── e2e/
│   └── test_e2e_attribute_notes.py # New: E2E tests for notes functionality
├── unit/
│   └── test_html_generation.py     # Update: Tests for new CSS and JavaScript functions
└── fixtures/
    └── (existing test JSON files)  # Use existing fixtures

docs/
├── function-glossary.md            # Update: Document new functions
└── style-guide.md                  # Update: Document new CSS classes for notes
```

**Structure Decision**: Single Python project (default). All changes are within existing `src/` structure. The feature is implemented entirely client-side (HTML + embedded JavaScript), so no new Python modules are required. JavaScript code will be embedded in HTML via new function `get_notes_javascript()` in `html_generation.py`.

## Complexity Tracking

> **No violations detected** - All constitution principles pass without exceptions needed.

---

## Phase 0: Outline & Research

### Research Questions

1. **How does the current HTML generation structure work for attribute rendering?**
   - **Investigation**: Review `MultiEnvReport._render_attribute_table()` in `src/core/multi_env_comparator.py` (lines 1240-1380)
   - **Goal**: Understand where to inject notes textarea elements within existing attribute section HTML
   - **Output**: Document current HTML structure for attribute sections and identify injection point

2. **What is the LocalStorage API usage pattern and key structure?**
   - **Investigation**: Research JavaScript LocalStorage best practices for auto-save with debouncing
   - **Goal**: Design LocalStorage key naming convention and data structure for notes
   - **Output**: Define key pattern (`tf-notes-{filename}#{resource}#{attribute}`) and JSON structure for stored data

3. **How are existing CSS styles organized and how to extend them?**
   - **Investigation**: Review `src/lib/html_generation.py` functions (`get_base_css()`, `get_attribute_section_css()`, etc.)
   - **Goal**: Determine where to add new CSS for notes textareas and how to integrate with existing styles
   - **Output**: Document CSS organization pattern and plan for `get_notes_css()` function

4. **What JavaScript patterns exist in current HTML reports?**
   - **Investigation**: Search for existing `<script>` tags in generated HTML (e.g., `toggleResource()` function)
   - **Goal**: Understand how to add JavaScript functions for auto-save, load, and debouncing
   - **Output**: Document existing JavaScript patterns and plan for `get_notes_javascript()` function

5. **How to extract report filename for LocalStorage keys from static HTML?**
   - **Investigation**: Research browser APIs for getting current file path from `file://` URLs
   - **Goal**: Determine if `window.location.pathname` provides usable filename or if alternative approach needed
   - **Output**: Define method for extracting report version identifier in browser context

### Research Output Location

All findings will be documented in `specs/008-attribute-notes/research.md` with:
- Code excerpts from existing implementation
- LocalStorage API usage examples
- CSS and JavaScript integration patterns
- Decision rationale for technical choices

---

## Phase 1: Design & Contracts

### Data Model

**Output File**: `specs/008-attribute-notes/data-model.md`

**Entities to Define**:

1. **AttributeNote** (Client-side data structure stored in LocalStorage)
   - `reportId`: string (extracted from HTML filename)
   - `resourceAddress`: string (e.g., "azurerm_storage_account.main")
   - `attributeName`: string (e.g., "location")
   - `question`: string (user-entered question text)
   - `answer`: string (user-entered answer text)
   - `lastModified`: timestamp (for potential future features)

2. **LocalStorage Schema**
   - Key format: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`
   - Value format: JSON string of AttributeNote object
   - Example: `tf-notes-comparison.html#azurerm_storage_account.main#location`

### Contracts

**Output Directory**: `specs/008-attribute-notes/contracts/`

**Contract Files**:

1. **html-structure.md** - HTML structure for notes textarea elements
   - Placement within `.env-value-column` div
   - ID naming convention for textareas
   - CSS classes for styling
   - Accessibility attributes (labels, placeholders, aria-*)

2. **javascript-api.md** - JavaScript function signatures
   - `saveNote(resourceAddress, attributeName, field, value)` - Auto-save to LocalStorage
   - `loadNotes()` - Load all notes on page load
   - `debounce(func, delay)` - Debouncing utility
   - `getReportId()` - Extract report filename from URL

3. **localstorage-schema.md** - LocalStorage key/value specification
   - Key naming pattern with examples
   - JSON value structure
   - Migration strategy (if schema changes in future)
   - Cleanup/garbage collection considerations

### Quickstart Guide

**Output File**: `specs/008-attribute-notes/quickstart.md`

**Contents**:
- Step-by-step implementation sequence
- Code snippets for each modification
- Testing approach for each user story
- Example HTML output with notes fields
- Browser console testing commands for LocalStorage verification

---

## Phase 2: Planning Complete - Tasks Generation Next

**Status**: Implementation plan complete through Phase 1.

**Next Command**: `/speckit.tasks` - Generate actionable task breakdown for implementation

**Branch**: `008-attribute-notes`  
**Plan File**: `specs/008-attribute-notes/plan.md`  
**Artifacts Generated**:
- ✅ `plan.md` (this file)
- ⏳ `research.md` (to be generated)
- ⏳ `data-model.md` (to be generated)
- ⏳ `quickstart.md` (to be generated)
- ⏳ `contracts/` (to be generated)
