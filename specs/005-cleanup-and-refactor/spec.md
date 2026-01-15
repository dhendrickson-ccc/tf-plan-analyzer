# Feature Specification: Cleanup and Tech-Debt Reduction

**Feature Branch**: `005-cleanup-and-refactor`  
**Created**: 2026-01-15  
**Status**: Draft  
**Input**: User description: "I want to do a cleanup and tech-debt reduction feature: 1. I feel like there's a lot of of files at the root level, I want to refactor a bit and cleanup the sprawl 2. Look for ways we can clean up the codebase, make things more concise and DRY 3. Make the styling consistent across the report and compare views (there are currently some inconsistencies) 4. Create a style guide so that future UI enhancements will look similar to what we already have. 5. Generate a function glossary that explains what all functions in the libraries do, what their input and output is and where they're at. For reference by other AI agents. (This will be referenced by the constitution later so that future features can see prior work)"

## Clarifications

### Session 2026-01-15

*(To be filled during planning)*

- Q: Should test files also be reorganized into a separate `tests/` directory, or should they remain at root? → A: NEEDS CLARIFICATION
- Q: For the style guide, should it include specific color values and hex codes, or just general principles? → A: NEEDS CLARIFICATION
- Q: Should the function glossary be auto-generated from docstrings, or manually curated? → A: NEEDS CLARIFICATION
- Q: Are there specific DRY violations that are known pain points, or should these be discovered during implementation? → A: NEEDS CLARIFICATION
- Q: Should demo HTML files be moved to a `demos/` or `examples/` directory, or deleted if no longer needed? → A: NEEDS CLARIFICATION

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reorganize Root-Level Files (Priority: P1)

Developers working on the codebase need a cleaner project structure where source files, tests, documentation, and outputs are organized into logical directories, making it easier to find files and understand project organization.

**Why this priority**: Currently there are 40+ files at root level, making it difficult to navigate and find specific files. This creates friction for new contributors and slows down development. This is the foundation for improved maintainability.

**Independent Test**: Can be fully tested by running all existing tests after reorganization to ensure nothing broke, and manually verifying that the CLI still works with the new structure.

**Acceptance Scenarios**:

1. **Given** all Python source files are currently at root, **When** reorganization is complete, **Then** source files are in `src/` directory and all existing tests pass
2. **Given** test files are currently at root, **When** reorganization is complete, **Then** test files are in `tests/` directory and pytest can still discover and run them
3. **Given** demo/example HTML files are scattered at root, **When** reorganization is complete, **Then** they are in an `examples/` or `demos/` directory or removed if obsolete
4. **Given** the CLI is invoked with `python analyze_plan.py`, **When** files are reorganized, **Then** the CLI entry point still works correctly
5. **Given** documentation files (IMPLEMENTATION_SUMMARY.md, etc.) are at root, **When** reorganization is complete, **Then** they are in a `docs/` directory

---

### User Story 2 - Extract Shared HTML Styles (Priority: P2)

Developers creating HTML reports need a single source of truth for CSS styling, ensuring consistency across all report types (single-plan, multi-environment, comparison) and making style updates easier to maintain.

**Why this priority**: Currently CSS styles are duplicated across `analyze_plan.py`, `generate_html_report.py`, and `multi_env_comparator.py` with inconsistencies (different font families, colors). This makes updates error-prone and creates visual inconsistencies.

**Independent Test**: Can be tested by generating all three types of reports (single-plan, comparison, obfuscated) and visually confirming they use consistent styling, and running existing tests to ensure no regressions.

**Acceptance Scenarios**:

1. **Given** CSS styles are duplicated across 3 files, **When** refactoring is complete, **Then** all HTML generation uses a shared CSS template or module
2. **Given** different reports use different color values for the same concept (e.g., "removed" uses `#ffe0e0` in one place and `#ff9999` in another), **When** refactoring is complete, **Then** all reports use the same color palette from a single source
3. **Given** font families are inconsistent (Monaco/Menlo vs Courier New), **When** refactoring is complete, **Then** all code blocks use the same monospace font stack
4. **Given** a developer wants to change the primary brand color, **When** the shared style module is updated, **Then** all reports reflect the change without modifying multiple files
5. **Given** all three report types are generated, **When** viewed side-by-side, **Then** they have visually consistent headers, cards, buttons, and color schemes

---

### User Story 3 - Create UI Style Guide (Priority: P3)

Future developers and AI agents implementing new features need documented UI/UX guidelines that define the visual language of reports, ensuring new features maintain consistency with existing design patterns.

**Why this priority**: Without documented standards, each new feature risks introducing visual inconsistencies. A style guide prevents this and accelerates development by providing ready-to-use patterns.

**Independent Test**: Can be tested by having a developer (or AI agent) implement a new simple HTML feature using only the style guide as reference, without looking at existing code, and verify it matches existing visual patterns.

**Acceptance Scenarios**:

1. **Given** a developer wants to add a new report section, **When** they consult the style guide, **Then** they find examples of headers, cards, and layouts to use
2. **Given** the style guide documents color usage, **When** a developer needs to show "success", "warning", or "error" states, **Then** they can find the exact hex codes and CSS classes to use
3. **Given** the style guide includes typography guidelines, **When** a developer needs to display code, resource names, or body text, **Then** they know which font families and sizes to use
4. **Given** the style guide includes spacing/layout guidelines, **When** a developer creates a new card or section, **Then** they know the correct padding, margin, and border-radius values
5. **Given** the style guide is referenced in the constitution, **When** future AI agents plan new features, **Then** they can discover and apply existing UI patterns

---

### User Story 4 - Generate Function Glossary (Priority: P4)

AI agents and developers working on new features need comprehensive documentation of all existing functions, their purposes, inputs, outputs, and locations, enabling code reuse and preventing duplication.

**Why this priority**: This directly supports Constitution Principle I (Code Duplication Prohibited) by making existing functions discoverable. Without this, developers waste time recreating functions that already exist.

**Independent Test**: Can be tested by searching the glossary for a known function (e.g., `load_ignore_config`) and verifying all documented details (location, parameters, return type, purpose) are accurate.

**Acceptance Scenarios**:

1. **Given** a developer needs to load a JSON config file, **When** they search the function glossary, **Then** they find `load_ignore_config()` with its file path, parameters, and usage example
2. **Given** the glossary is complete, **When** searching for "HTML", **Then** all HTML generation functions are listed with their purposes and locations
3. **Given** a function accepts complex parameters, **When** viewing its glossary entry, **Then** parameter types and example values are documented
4. **Given** a function returns a complex data structure, **When** viewing its glossary entry, **Then** the return type and structure are documented
5. **Given** the glossary is referenced in `.specify/memory/constitution.md`, **When** AI agents plan new features, **Then** they are required to search the glossary before creating new functions

---

### User Story 5 - Consolidate Duplicate Code (Priority: P2)

Developers maintaining the codebase need a DRY (Don't Repeat Yourself) implementation where common logic is extracted to shared utilities, reducing maintenance burden and eliminating inconsistencies.

**Why this priority**: Code duplication leads to bugs when fixes are applied to only one copy. Consolidating duplicate code now prevents future maintenance issues.

**Independent Test**: Can be tested by running all existing tests after consolidation to ensure behavior is preserved, and code review to verify duplicates were eliminated.

**Acceptance Scenarios**:

1. **Given** HTML style generation is duplicated across 3 files, **When** consolidation is complete, **Then** a single `generate_html_styles()` function exists and all reports use it
2. **Given** JSON formatting logic may be duplicated, **When** consolidation is complete, **Then** shared formatting utilities are used consistently
3. **Given** file I/O patterns are repeated, **When** consolidation is complete, **Then** common file operations use shared utility functions
4. **Given** duplicate code existed before consolidation, **When** a bug fix is needed, **Then** it only needs to be fixed in one place
5. **Given** all tests pass before consolidation, **When** consolidation is complete, **Then** all tests still pass with identical behavior

---

### Edge Cases

- What happens when file paths in tests break after reorganization? → Tests must be updated to use correct paths
- How do imports change when modules move? → Import statements must be updated across all files
- What if the CLI entry point changes? → Documentation and usage examples must be updated
- What if some HTML files are still in use vs obsolete? → Need to audit which HTML files are test artifacts vs examples
- How are relative paths in existing code affected? → Must audit and update all relative path references

## Requirements *(mandatory)*

### Functional Requirements

#### Root-Level Organization (US1)
- **FR-001**: System MUST organize Python source files into a `src/` directory
- **FR-002**: System MUST organize test files into a `tests/` directory
- **FR-003**: System MUST organize documentation into a `docs/` directory
- **FR-004**: System MUST organize examples/demos into an `examples/` directory or remove if obsolete
- **FR-005**: CLI entry point MUST remain functional after reorganization
- **FR-006**: All existing tests MUST pass after reorganization
- **FR-007**: Import statements MUST be updated to reflect new module paths

#### Shared HTML Styles (US2)
- **FR-008**: System MUST extract CSS styles to a shared module or template
- **FR-009**: All HTML reports MUST use consistent color values for semantic meanings (success, error, warning)
- **FR-010**: All HTML reports MUST use consistent font families (sans-serif for body, monospace for code)
- **FR-011**: All HTML reports MUST use consistent spacing values (padding, margin, border-radius)
- **FR-012**: Changes to shared styles MUST automatically apply to all report types

#### UI Style Guide (US3)
- **FR-013**: Style guide MUST document color palette with hex values and semantic usage
- **FR-014**: Style guide MUST document typography (font families, sizes, weights)
- **FR-015**: Style guide MUST document spacing system (padding, margin, gap values)
- **FR-016**: Style guide MUST include code examples for common UI components (cards, headers, buttons)
- **FR-017**: Style guide MUST be referenced in `.specify/memory/constitution.md`

#### Function Glossary (US4)
- **FR-018**: Glossary MUST list all public functions in the codebase
- **FR-019**: Glossary entries MUST include function location (file path and line number)
- **FR-020**: Glossary entries MUST include function purpose/description
- **FR-021**: Glossary entries MUST include parameter types and descriptions
- **FR-022**: Glossary entries MUST include return type and description
- **FR-023**: Glossary MUST be searchable (Markdown with table of contents)
- **FR-024**: Glossary MUST be referenced in `.specify/memory/constitution.md`

#### Code Consolidation (US5)
- **FR-025**: Duplicate CSS generation logic MUST be consolidated into a single function
- **FR-026**: Duplicate JSON formatting logic MUST use shared utilities
- **FR-027**: All consolidated code MUST maintain backward compatibility
- **FR-028**: All existing tests MUST pass after consolidation

### Key Entities *(include if feature involves data)*

- **StyleConfig**: CSS configuration including colors, fonts, spacing
- **FunctionMetadata**: Function name, location, parameters, return type, description
- **ProjectStructure**: New directory organization mapping

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Root-level file count reduced from 40+ to <10 files (excluding .gitignore, README, etc.)
- **SC-002**: CSS code duplication reduced by 100% (single source of truth)
- **SC-003**: All 158 existing tests pass without modification to test logic
- **SC-004**: Function glossary includes 100% of public functions across all modules
- **SC-005**: Style guide referenced in constitution with enforcement in planning workflow
- **SC-006**: Code coverage maintained or improved after refactoring
- **SC-007**: No breaking changes to CLI interface or Python API

### Quality Metrics

- **SC-008**: All HTML reports generated before and after refactoring are visually identical (or improved)
- **SC-009**: Import statements follow Python best practices (relative imports where appropriate)
- **SC-010**: No dead code or unused imports remain after cleanup
- **SC-011**: Documentation builds successfully with updated paths
- **SC-012**: Git history preserves file history through moves (using `git mv`)

## Technical Constraints

- **TC-001**: Must maintain Python 3.9.6 compatibility
- **TC-002**: Must not break existing CLI interface (`python analyze_plan.py [command]`)
- **TC-003**: Must preserve pytest discovery patterns
- **TC-004**: File reorganization must use `git mv` to preserve history
- **TC-005**: All changes must be backward compatible for external users

## Out of Scope

- Changing CLI command structure or arguments
- Rewriting core logic or algorithms
- Adding new features beyond cleanup/organization
- Changing data models or schemas
- Performance optimizations (unless related to DRY)
- External API changes

## Dependencies

- Existing test suite must be comprehensive enough to validate refactoring
- All current features must be stable (no pending PRs with major changes)
- Documentation must be accurate enough to guide reorganization

## Risks

- **Risk 1**: Import path changes may break external tools or scripts → Mitigation: Maintain backward compatibility with deprecation warnings if needed
- **Risk 2**: File moves may break IDE configurations or tooling → Mitigation: Update .vscode, .github, and other config files
- **Risk 3**: Large-scale refactoring may introduce subtle bugs → Mitigation: Comprehensive test coverage and manual validation

## Success Indicators

- All existing tests pass
- CLI commands work identically
- HTML reports are visually consistent
- Code review confirms no duplication
- Function glossary is complete and accurate
- Style guide is comprehensive and usable
