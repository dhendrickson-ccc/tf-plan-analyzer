# Feature Specification: Cleanup and Tech-Debt Reduction

**Feature Branch**: `005-cleanup-and-refactor`  
**Created**: 2026-01-15  
**Status**: Draft  
**Input**: User description: "I want to do a cleanup and tech-debt reduction feature: 1. I feel like there's a lot of of files at the root level, I want to refactor a bit and cleanup the sprawl 2. Look for ways we can clean up the codebase, make things more concise and DRY 3. Make the styling consistent across the report and compare views (there are currently some inconsistencies) 4. Create a style guide so that future UI enhancements will look similar to what we already have. 5. Generate a function glossary that explains what all functions in the libraries do, what their input and output is and where they're at. For reference by other AI agents. (This will be referenced by the constitution later so that future features can see prior work)"

## Clarifications

### Session 2026-01-15

- Q: How should demo HTML files be handled? → A: Delete all existing HTML files; regenerate fresh examples after UI consistency work (US2) is complete to showcase consistent styling
- Q: How detailed should the style guide be? → A: Comprehensive: exact hex codes, font stacks, spacing values (px/rem), complete CSS class examples, copy-paste ready code snippets
- Q: How should the function glossary be generated? → A: Hybrid: Auto-extract function names, locations, signatures; manually add purpose descriptions, usage examples, and notes
- Q: Should tests be reorganized into tests/unit/ and tests/e2e/ subdirectories, or kept flat in tests/? → A: Organize into tests/unit/ and tests/e2e/ subdirectories
- Q: How should the CLI entry point be handled during the transition? → A: Set up proper pip package with entry points (pyproject.toml), install in editable mode during development, enable `tf-plan-analyzer` command immediately

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reorganize Root-Level Files (Priority: P1)

Developers working on the codebase need a cleaner project structure where source files, tests, documentation, and outputs are organized into logical directories, making it easier to find files and understand project organization.

**Why this priority**: Currently there are 40+ files at root level, making it difficult to navigate and find specific files. This creates friction for new contributors and slows down development. This is the foundation for improved maintainability.

**Independent Test**: Can be fully tested by running all existing tests after reorganization to ensure nothing broke, and manually verifying that the CLI still works with the new structure.

**Acceptance Scenarios**:

1. **Given** all Python source files are currently at root, **When** reorganization is complete, **Then** source files are in `src/` directory with subdirectories (lib/, core/, security/) and all existing tests pass
2. **Given** test files are currently at root, **When** reorganization is complete, **Then** test files are in `tests/unit/` and `tests/e2e/` subdirectories
3. **Given** demo/example HTML files are scattered at root, **When** reorganization is complete, **Then** all existing HTML files are deleted and examples/ directory is created for future regenerated samples
4. **Given** the CLI is invoked with `python analyze_plan.py`, **When** files are reorganized, **Then** the package is pip-installable and `tf-plan-analyzer` commands/` or `demos/` directory or removed if obsolete
4. **Given** the CLI is invoked with `python analyze_plan.py`, **When** files are reorganized, **Then** the CLI entry point still works correctly
5. **Given** documentation files (IMPLEMENTATION_SUMMARY.md, etc.) are at root, **When** reorganization is complete, **Then** they are in a `docs/` directory
6. **Given** shared utility functions are scattered across modules, **When** reorganization is complete, **Then** common library functions are extracted to `src/lib/` directory
7. **Given** the project needs pip installation, **When** reorganization is complete, **Then** pyproject.toml exists with proper entry points and `pip install -e .` enables the `tf-plan-analyzer` CLI command

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
 in a dedicated library directory, reducing maintenance burden and eliminating inconsistencies.

**Why this priority**: Code duplication leads to bugs when fixes are applied to only one copy. Consolidating duplicate code now prevents future maintenance issues. A dedicated `src/lib/` directory provides a clear home for reusable functions.

**Independent Test**: Can be tested by running all existing tests after consolidation to ensure behavior is preserved, and code review to verify duplicates were eliminated.

**Acceptance Scenarios**:

1. **Given** HTML style generation is duplicated across 3 files, **When** consolidation is complete, **Then** a single function exists in `src/lib/html_generation.py` and all reports use it
2. **Given** JSON formatting logic may be duplicated, **When** consolidation is complete, **Then** shared formatting utilities in `src/lib/json_utils.py` are used consistently
3. **Given** file I/O patterns are repeated, **When** consolidation is complete, **Then** common file operations use shared utility functions in `src/lib/file_utils.py`
4. **Given** duplicate code existed before consolidation, **When** a bug fix is needed, **Then** it only needs to be fixed in one place in the `src/lib/` directory
5. **Given** all tests pass before consolidation, **When** consolidation is complete, **Then** all tests still pass with identical behavior
6. **Given** the `src/lib/` directory is created, **When** developers search for reusable functions, **Then** they find all shared utilities organized by category (html_generation, json_utils, file_utils, etc.)

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
- **FR-001**: System MUST organize Python source files into a `src/` directory with subdirectories (lib/, core/, security/)
- **FR-002**: System MUST create a `src/lib/` directory for all shared utilities (HTML generation, JSON utils, file I/O, ignore config, etc.)
- **FR-003**: System MUST organize test files into `tests/unit/` and `tests/e2e/` subdirectories
- **FR-004**: System MUST organize documentation into a `docs/` directory
- **FR-005**: System MUST delete all existing HTML demo files; create `examples/` directory for future regenerated samples
- **FR-006**: System MUST create `pyproject.toml` with entry point definition for pip installation
- **FR-007**: CLI MUST work via `tf-plan-analyzer` command after `pip install -e .`
- **FR-008**: All existing tests MUST pass after reorganization
- **FR-009**: Import statements MUST be updated to reflect new module paths

#### Shared HTML Styles (US2)
- **FR-010**: System MUST extract CSS styles to a shared module in `src/lib/html_generation.py`
- **FR-011**: All HTML reports MUST use consistent color values for semantic meanings (success, error, warning)
- **FR-012**: All HTML reports MUST use consistent font families (sans-serif for body, monospace for code)
- **FR-013**: All HTML reports MUST use consistent spacing values (padding, margin, border-radius)
- **FR-014**: Changes to shared styles MUST automatically apply to all report types
- **FR-015**: After CSS consolidation, fresh example HTML reports MUST be generated to examples/ directory showcasing consistent styling

#### UI Style Guide (US3)
- **FR-016**: Style guide MUST document exact color palette with hex values and semantic usage
- **FR-017**: Style guide MUST document complete typography (font families with fallback stacks, sizes in px/rem, weights)
- **FR-018**: Style guide MUST document spacing system with exact values (padding, margin, gap in px/rem)
- **FR-019**: Style guide MUST include complete CSS class examples that are copy-paste ready
- **FR-020**: Style guide MUST include code snippets for common UI components (cards, headers, buttons, tables)
- **FR-021**: Style guide MUST be referenced in `.specify/memory/constitution.md`

#### Function Glossary (US4)
- **FR-022**: Glossary generation MUST use hybrid approach: auto-extract function names, locations, and signatures
- **FR-023**: Glossary entries MUST be manually enhanced with purpose descriptions and usage examples
- **FR-024**: Glossary entries MUST include function location (file path and line number)
- **FR-025**: Glossary entries MUST include parameter types and descriptions
- **FR-026**: Glossary entries MUST include return type and description
- **FR-027**: Glossary MUST be searchable (Markdown with table of contents)
- **FR-028**: Glossary MUST include all public functions in codebase including those in `src/lib/`
- **FR-029**: Glossary MUST be referenced in `.specify/memory/constitution.md`

#### Code Consolidation (US5)
- **FR-030**: Duplicate CSS generation logic MUST be consolidated into `src/lib/html_generation.py`
- **FR-031**: Duplicate JSON formatting logic MUST be extracted to `src/lib/json_utils.py`
- **FR-032**: Common file I/O operations MUST be consolidated into `src/lib/file_utils.py`
- **FR-033**: Diff highlighting logic MUST be extracted to `src/lib/diff_utils.py` if duplicated
- **FR-034**: All library functions in `src/lib/` MUST have comprehensive docstrings
- **FR-035**: All consolidated code MUST maintain backward compatibility
- **FR-036**: All existing tests MUST pass after consolidation
- **FR-037**: The `src/lib/` directory MUST have an `__init__.py` that exports commonly used functions

### Key Entities *(include if feature involves data)*
- **LibraryModule**: Categorized shared utility modules in `src/lib/` (html_generation, json_utils, file_utils, diff_utils)
- **StyleConfig**: CSS configuration including colors, fonts, spacing
- **FunctionMetadata**: Function name, location, parameters, return type, description
- **ProjectStructure**: New directory organization mapping

## Success Criteria *(mandatory)*

### Completeness Criteria

- **SC-001**: All 45+ root files relocated to appropriate new locations (src/, tests/, docs/, examples/)
- **SC-002**: Centralized CSS module in `src/lib/html_generation.py` is single source of truth for all styles
- **SC-003**: All 158 existing tests pass without modification to test logic
- **SC-004**: Function glossary includes 100% of public functions across all modules including `src/lib/`
- **SC-005**: Style guide referenced in constitution with enforcement in planning workflow
- **SC-006**: Code coverage maintained or improved after refactoring
- **SC-007**: No breaking changes to CLI interface (users install with pip and use `tf-plan-analyzer` command)
- **SC-008**: All shared utilities consolidated into `src/lib/` with clear module organization
- **SC-009**: At least 3 library modules created (html_generation, json_utils, file_utils)
- **SC-010**: Package is pip-installable with `pip install -e .` for development
- **SC-011**: After installation, `tf-plan-analyzer --help` command works correctly

### Quality Metrics

- **SC-012**: All HTML reports generated before and after refactoring are visually identical (or improved)
- **SC-013**: Import statements follow Python best practices (absolute imports from src.)
- **SC-014**: No dead code or unused imports remain after cleanup
- **SC-015**: Documentation builds successfully with updated paths
- **SC-016**: Git history preserves file history through moves (using `git mv`)
- **SC-017**: Fresh example HTML files showcase consistent styling after US2 completion

## Technical Constraints

- **TC-001**: Must maintain Python 3.9.6 compatibility
- **TC-002**: Must enable pip installation with proper entry points (`tf-plan-analyzer` command)
- **TC-003**: Must preserve pytest discovery patterns in tests/unit/ and tests/e2e/ structure
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
