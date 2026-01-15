# Tasks: Cleanup and Tech-Debt Reduction

**Input**: Design documents from `/specs/005-cleanup-and-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/directory-structure.md, quickstart.md

**Tests**: Tests are NOT explicitly requested in this specification - this is a refactoring feature validated by existing 158 tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and pip-installable package structure

- [ ] T001 Create project metadata file pyproject.toml with entry point `tf-plan-analyzer` mapping to `src.lib.analyze_plan:main`
- [ ] T002 [P] Create pytest configuration in pytest.ini with testpaths=tests
- [ ] T003 [P] Create directory structure: src/, src/lib/, src/core/, src/security/, tests/unit/, tests/e2e/, tests/fixtures/, docs/, examples/, examples/sample_reports/, examples/utilities/
- [ ] T004 [P] Create __init__.py files in all Python package directories (src/, src/lib/, src/core/, src/security/, tests/, tests/unit/, tests/e2e/)
- [ ] T005 [P] Establish baseline code coverage: Run `pytest tests/ --cov=. --cov-report=term --cov-report=json` and save coverage.json as baseline-coverage.json for comparison after refactoring (target: maintain or improve from baseline)
- [ ] T005a Install package in editable mode with `pip install -e .` and verify `tf-plan-analyzer --help` fails gracefully (no main() function yet)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

*(No foundational tasks required for this refactoring feature - existing codebase already has all core infrastructure)*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 2 - Extract Shared HTML Styles (Priority: P2) 🎯 MVP

**Goal**: Consolidate ~400 lines of duplicate CSS into a single shared module, ensuring all HTML reports use consistent styling

**Independent Test**: Generate all three types of reports (single-plan with `analyze_plan.py analyze`, multi-env comparison with `multi_env_comparator.py compare`, and obfuscated report) and visually confirm they use identical color palette, fonts, and spacing

**Implementation Order Rationale**: Starting with US2 instead of US1 because extracting CSS first reduces code before file reorganization, making the move operations cleaner and easier to validate

### Implementation for User Story 2

- [X] T006 [P] [US2] Create src/lib/html_generation.py with function `get_base_css() -> str` that returns complete CSS stylesheet (extract from analyze_plan.py lines 992-1300)
- [X] T007 [P] [US2] Add function `get_diff_highlight_css() -> str` to src/lib/html_generation.py with classes for removed/added/unchanged/char-removed/char-added/known-after-apply
- [X] T008 [P] [US2] Add function `get_summary_card_css() -> str` to src/lib/html_generation.py with classes for summary-card, total/created/updated/removed color values
- [X] T009 [P] [US2] Add function `get_resource_card_css() -> str` to src/lib/html_generation.py with classes for resource-card, diff-header, json-content, resource-name
- [X] T010 [US2] Consolidate font family to Monaco/Menlo/Consolas/monospace (replacing all instances of 'Courier New' based on research.md Section 2.3 findings)
- [X] T011 [US2] Add function `generate_full_styles() -> str` to src/lib/html_generation.py that combines all CSS functions and returns complete <style> block
- [X] T012 [P] [US2] Update analyze_plan.py to import html_generation module (before US1: `import src.lib.html_generation`; imports will be updated to absolute in US1) and replace inline CSS (lines 992-1300) with generate_full_styles() function call
- [X] T013 [P] [US2] Update multi_env_comparator.py to import generate_full_styles from src.lib.html_generation and replace inline CSS (lines 671-720) with function call
- [X] T014 [P] [US2] Delete generate_html_report.py (deprecated file per research.md findings)
- [X] T015 [US2] Run all 158 existing tests with `pytest tests/ -v` to ensure no regressions from CSS extraction
- [X] T016 [US2] Generate sample reports (analyze, compare, obfuscated) and visually validate consistent styling across all reports
- [X] T017 [US2] Delete all existing HTML demo files from root: comparison_report.html, demo-*.html, test_*.html, manual_validation.html, prod-vs-test-comparison.html, etc. (13+ files per research.md Section 1.1)
- [X] T018 [US2] Generate fresh example HTML reports to examples/sample_reports/: single_plan.html, multi_env_comparison.html, obfuscated_report.html using new consistent styles

**Checkpoint**: At this point, all HTML styling is centralized in src/lib/html_generation.py, all reports use consistent CSS, and fresh examples showcase the unified design

---

## Phase 4: User Story 5 - Consolidate Duplicate Code (Priority: P2)

**Goal**: Extract duplicate diff highlighting, JSON formatting, and file I/O logic into shared library functions in src/lib/, reducing ~300-500 lines of duplication

**Independent Test**: Run all existing tests to verify behavior is identical, and manually verify that fixing a bug in one place (e.g., diff highlighting) automatically fixes it everywhere

**Implementation Order Rationale**: Consolidating code while files are still at root makes import updates easier in the next phase (US1)

### Implementation for User Story 5

- [X] T019 [P] [US5] Create src/lib/diff_utils.py and extract `highlight_char_diff(old: str, new: str) -> tuple[str, str]` function (consolidate from analyze_plan.py lines 666-698 and multi_env_comparator.py lines 37-66)
- [X] T020 [P] [US5] Add `highlight_json_diff(before: dict, after: dict, sensitive_paths: list = None) -> str` to src/lib/diff_utils.py (consolidate from analyze_plan.py lines 700-870, multi_env_comparator.py lines 68-167)
- [X] T021 [P] [US5] Create src/lib/json_utils.py with function `load_json_file(file_path: str) -> dict` for common JSON loading pattern (found in 15+ locations per research.md Section 3.3)
- [X] T022 [P] [US5] Add function `format_json_for_display(data: dict, indent: int = 2, sort_keys: bool = True) -> str` to src/lib/json_utils.py
- [X] T023 [P] [US5] Create src/lib/file_utils.py with function `safe_read_file(file_path: str, encoding: str = 'utf-8') -> str` for common file reading pattern
- [X] T024 [P] [US5] Add function `safe_write_file(file_path: str, content: str, encoding: str = 'utf-8') -> None` to src/lib/file_utils.py
- [X] T025 [US5] Update analyze_plan.py to import from src.lib.diff_utils and replace inline implementations with shared functions
- [X] T026 [US5] Update multi_env_comparator.py to import from src.lib.diff_utils and replace inline implementations with shared functions
- [ ] T027 [US5] Update all Python files to use src.lib.json_utils.load_json_file() instead of inline `with open() as f: json.load(f)` patterns (analyze_plan.py, multi_env_comparator.py, ignore_utils.py, test files)
- [X] T028 [US5] Add comprehensive docstrings to all functions in src/lib/ following Google or NumPy style (include parameters, return types, usage examples)
- [X] T029 [US5] Create src/lib/__init__.py with exports: `from .html_generation import generate_full_styles`, `from .diff_utils import highlight_char_diff, highlight_json_diff`, `from .json_utils import load_json_file, format_json_for_display`, `from .file_utils import safe_read_file, safe_write_file`
- [X] T030 [US5] Run all 158 existing tests with `pytest tests/ -v` to ensure code consolidation preserved all behavior
- [X] T031 [US5] Code review: Search codebase for remaining duplicate patterns using `grep -r "with open.*json.load" .` and verify all are either in tests (acceptable) or migrated to shared utilities

**Checkpoint**: All duplicate code eliminated, shared utilities in src/lib/ with comprehensive docstrings, all tests passing

---

## Phase 5: User Story 1 - Reorganize Root-Level Files (Priority: P1)

**Goal**: Move 45+ root-level files into organized directory structure (src/, tests/, docs/, examples/), reducing root directory to <10 files

**Independent Test**: Run all tests after reorganization, verify CLI works with `tf-plan-analyzer` command, check that `git log --follow` preserves file history

**Implementation Order Rationale**: Now that code is consolidated (US2, US5 complete), file reorganization is cleaner and import updates are simpler

### Implementation for User Story 1

- [X] T032 [P] [US1] Use `git mv analyze_plan.py src/cli/analyze_plan.py` to move main CLI file while preserving git history
- [X] T033 [P] [US1] Use `git mv multi_env_comparator.py src/core/multi_env_comparator.py` to preserve git history
- [X] T034 [P] [US1] Use `git mv hcl_value_resolver.py src/core/hcl_value_resolver.py` to preserve git history
- [X] T035 [P] [US1] Use `git mv ignore_utils.py src/lib/ignore_utils.py` to preserve git history (shared utility belongs in lib/)
- [X] T036 [P] [US1] Use `git mv salt_manager.py src/security/salt_manager.py` to preserve git history
- [X] T037 [P] [US1] Use `git mv sensitive_obfuscator.py src/security/sensitive_obfuscator.py` to preserve git history
- [X] T038 [P] [US1] Use `git mv test_change_detection.py tests/unit/test_change_detection.py` to preserve git history
- [X] T039 [P] [US1] Use `git mv test_hcl_reference.py tests/unit/test_hcl_reference.py` to preserve git history
- [X] T040 [P] [US1] Use `git mv test_ignore_utils.py tests/unit/test_ignore_utils.py` to preserve git history
- [X] T041 [P] [US1] Use `git mv test_salt_manager.py tests/unit/test_salt_manager.py` to preserve git history
- [X] T042 [P] [US1] Use `git mv test_sensitive_obfuscator.py tests/unit/test_sensitive_obfuscator.py` to preserve git history
- [X] T043 [P] [US1] Use `git mv test_multi_env_unit.py tests/unit/test_multi_env_unit.py` to preserve git history
- [X] T044 [P] [US1] Use `git mv test_compare_enhancements_unit.py tests/unit/test_compare_enhancements_unit.py` to preserve git history
- [X] T045 [P] [US1] Use `git mv test_e2e_multi_env.py tests/e2e/test_e2e_multi_env.py` to preserve git history
- [X] T046 [P] [US1] Use `git mv test_e2e_obfuscate.py tests/e2e/test_e2e_obfuscate.py` to preserve git history
- [X] T047 [P] [US1] Use `git mv test_e2e_compare_enhancements.py tests/e2e/test_e2e_compare_enhancements.py` to preserve git history
- [X] T048 [P] [US1] Use `git mv test_e2e_sensitive_change.py tests/e2e/test_e2e_sensitive_change.py` to preserve git history
- [X] T049 [P] [US1] Use `git mv test_data/ tests/fixtures/` to move test data directory
- [X] T050 [P] [US1] Use `git mv IMPLEMENTATION_SUMMARY.md docs/IMPLEMENTATION_SUMMARY.md` to organize documentation
- [X] T051 [P] [US1] Use `git mv OBFUSCATION_IMPLEMENTATION_SUMMARY.md docs/OBFUSCATION_IMPLEMENTATION_SUMMARY.md` to organize documentation
- [X] T052 [P] [US1] Use `git mv JSON_REPORT_GUIDE.md docs/JSON_REPORT_GUIDE.md` to organize documentation
- [X] T053 [P] [US1] Use `git mv ignore_config.example.json examples/ignore_config.example.json` to move example config
- [X] T054 [P] [US1] Use `git mv generate_large_test_plan.py examples/demo_data/generate_large_test_plan.py` for utility script
- [X] T055 [US1] Update all import statements in src/cli/analyze_plan.py to use absolute imports: `from src.core.multi_env_comparator import MultiEnvReport`, `from src.lib.ignore_utils import load_ignore_config`, `from src.security.sensitive_obfuscator import SensitiveObfuscator`, `from src.lib.html_generation import generate_full_styles`
- [X] T056 [US1] Update all import statements in src/core/multi_env_comparator.py to use absolute imports from src.lib.ignore_utils and src.lib.html_generation
- [X] T057 [US1] Update all import statements in src/cli/analyze_plan.py to import from new paths: `from src.core.hcl_value_resolver import resolve_references`, `from src.security.salt_manager import SaltManager`
- [X] T058 [US1] Update all import statements in tests/unit/*.py to use absolute imports: `from src.cli.analyze_plan import TerraformPlanAnalyzer`, `from src.core.multi_env_comparator import ResourceComparison`, etc.
- [X] T059 [US1] Update all import statements in tests/e2e/*.py to use absolute imports and update test_data paths to tests/fixtures
- [X] T060 [US1] Update all test files to use `tests/fixtures/` instead of `test_data/` for file path references (grep for "test_data" in tests/)
- [X] T06& Refactor src/lib/analyze_plan.py to wrap existing CLI logic in main() function (if not already present) to serve as entry point for `tf-plan-analyzer` command defined in pyproject.toml - ensure ArgumentParser and all CLI handling is inside main()
- [X] T06& Run `pip install -e .` to reinstall package with new structure and verify `tf-plan-analyzer --help` command works
- [X] T06& Run all 158 tests with `pytest tests/ -v` and ensure 100% pass rate after reorganization
- [X] T06& Verify git history preservation by running `git log --follow src/cli/analyze_plan.py` and confirming full commit history is visible
- [X] T06& Manual validation: Generate single-plan report using `tf-plan-analyzer analyze tests/fixtures/dev-plan.json` and verify output
- [X] T06& Manual validation: Generate multi-env comparison using `tf-plan-analyzer compare tests/fixtures/dev-plan.json tests/fixtures/prod-plan.json` and verify output
- [X] T067 [US1] Update README.md with new usage instructions: Installation (`pip install -e .`), Usage (`tf-plan-analyzer analyze <file>`), Project Structure section showing new directory layout
- [X] T068 [US1] Update .gitignore if needed to ignore Python cache in new locations: `src/__pycache__/`, `src/*/__pycache__/`, `tests/__pycache__/`, `tests/*/__pycache__/`
- [X] T069 [US1] Verify root directory now has <10 files (README.md, .gitignore, pyproject.toml, pytest.ini, and directories only)

**Checkpoint**: All files organized into clean structure, all tests passing, CLI works via pip-installed command, git history preserved

---

## Phase 6: User Story 3 - Create UI Style Guide (Priority: P3)

**Goal**: Create comprehensive style guide documenting exact color palette, typography, spacing, and CSS patterns for consistent future development

**Independent Test**: Have a developer (or AI) implement a simple new HTML card component using only the style guide as reference, without looking at existing code, and verify it matches existing visual patterns

### Implementation for User Story 3

- [ ] T070 [US3] Create docs/style-guide.md with title "Terraform Plan Analyzer - UI Style Guide" and introduction explaining purpose (consistency across all HTML reports)
- [ ] T071 [US3] Add "Color Palette" section to docs/style-guide.md documenting semantic colors with exact hex codes: Primary (#667eea), Success/Added (#51cf66, #d3f9d8), Warning/Updated (#ffa94d, #ffe8cc), Error/Removed (#c92a2a, #ffe0e0), Neutral (#495057, #f5f5f5, #333)
- [ ] T072 [US3] Add "Typography" section to docs/style-guide.md with complete font stacks: Body text (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif), Code/Monospace (Monaco, Menlo, Consolas, 'Courier New', monospace), font sizes (body: 16px/1.6, h1: 2em, h2: 1.5em, code: 14px), font weights (normal: 400, medium: 500, bold: 700)
- [ ] T073 [US3] Add "Spacing System" section to docs/style-guide.md documenting exact spacing values: Padding (card: 24px, section: 16px, inline: 8px 12px), Margin (section: 24px, card: 16px, element: 8px), Border radius (card: 8px, button: 6px, badge: 4px), Gap (grid: 20px, flex: 12px)
- [ ] T074 [US3] Add "CSS Classes Reference" section to docs/style-guide.md with copy-paste ready examples for: .summary-card (with variants .total, .created, .updated, .removed), .resource-card, .diff-header, .json-content, .removed/.added/.unchanged, .char-removed/.char-added, .known-after-apply
- [ ] T075 [US3] Add "Component Patterns" section to docs/style-guide.md with complete HTML+CSS code snippets for: Summary card with icon and number, Resource comparison card with diff, Expandable section with toggle, Badge/tag components, Button styles
- [ ] T076 [US3] Add "Layout Guidelines" section to docs/style-guide.md documenting: Container max-width (1200px), Grid patterns (2-column, 3-column for summary cards), Flexbox patterns for headers, Responsive breakpoints if applicable
- [ ] T077 [US3] Add "Usage Examples" section to docs/style-guide.md showing how to import styles: `from src.lib.html_generation import generate_full_styles`, and how to apply semantic colors to new elements
- [ ] T078 [US3] Add reference to style guide in .specify/memory/constitution.md: Add "Style Guide Reference" section under Principle I stating "Before implementing new UI components, consult docs/style-guide.md for color palette, typography, spacing, and component patterns"
- [ ] T079 [US3] Code review: Verify all color codes, font families, and spacing values in docs/style-guide.md match actual implementation in src/lib/html_generation.py

**Checkpoint**: Comprehensive style guide complete with exact values, copy-paste examples, referenced in constitution for enforcement

---

## Phase 7: User Story 4 - Generate Function Glossary (Priority: P4)

**Goal**: Create comprehensive function reference documenting all 49+ public functions across the codebase, enabling code reuse and preventing duplication

**Independent Test**: Search the glossary for a known function (e.g., `load_ignore_config`) and verify all documented details (location, parameters, return type, purpose) are accurate and complete

### Implementation for User Story 4

- [ ] T080 [US4] Create temporary script examples/utilities/generate_glossary.py that uses ast module to parse all Python files in src/ and extract function definitions (name, file path, line number, parameters, docstring) - this script will be deleted after T092
- [ ] T081 [US4] Run examples/utilities/generate_glossary.py to auto-generate skeleton of docs/function-glossary.md with table of contents organized by module (lib/, core/, security/)
- [ ] T082 [US4] For each function in src/lib/html_generation.py, manually enhance glossary entry with: Purpose description (1-2 sentences), Parameter descriptions with types and examples, Return type with description, Usage example code snippet
- [ ] T083 [US4] For each function in src/lib/diff_utils.py, manually enhance glossary entry with: Purpose, Parameters (old: str, new: str for highlight_char_diff; before: dict, after: dict, sensitive_paths: list for highlight_json_diff), Return type, Usage examples showing both simple and complex diffs
- [ ] T084 [US4] For each function in src/lib/json_utils.py and src/lib/file_utils.py, manually enhance glossary entries with purpose, parameters, return types, and usage examples
- [ ] T085 [US4] For key functions in src/core/multi_env_comparator.py (ResourceComparison class, compare methods), add glossary entries with detailed descriptions
- [ ] T086 [US4] For key functions in src/cli/analyze_plan.py (TerraformPlanAnalyzer class, analyze/compare commands), add glossary entries with CLI usage context
- [ ] T087 [US4] For functions in src/security/ (SaltManager, SensitiveObfuscator), add glossary entries with security considerations and examples
- [ ] T088 [US4] Add "Quick Reference" section at top of docs/function-glossary.md with most commonly used functions: load_ignore_config, highlight_json_diff, generate_full_styles, safe_read_file
- [ ] T089 [US4] Add "Module Organization" section to docs/function-glossary.md explaining the purpose of each src/ subdirectory (lib/: shared utilities, core/: analysis logic, security/: sensitive data handling, cli/: command-line interface)
- [ ] T090 [US4] Add search instructions to docs/function-glossary.md: "Use Cmd+F / Ctrl+F to search by function name, module, or keyword"
- [ ] T091 [US4] Add reference to function glossary in .specify/memory/constitution.md under Principle I (Code Duplication Prohibited): Add "Function Glossary Reference" section stating "Before creating new functions, search docs/function-glossary.md to verify similar functionality does not already exist. All new public functions MUST be added to the glossary with purpose, parameters, and usage examples."
- [ ] T092 [US4] Verify glossary completeness: Use `grep -r "^def " src/` to count all function definitions and compare against glossary entry count (should be 100% coverage of public functions, private functions marked with _ are optional)
- [ ] T092a [US4] Delete temporary script examples/utilities/generate_glossary.py (no longer needed after glossary is complete)

**Checkpoint**: Function glossary complete with 100% coverage of public functions, comprehensive descriptions and examples, referenced in constitution

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation across all user stories

- [ ] T093 [P] Update all docstrings in src/ to follow consistent style (Google or NumPy format) with type hints
- [ ] T094 [P] Run linter/formatter if configured (e.g., `black src/ tests/`, `flake8 src/`) to ensure code quality
- [ ] T095 [P] Search for any remaining TODO comments from refactoring: `grep -r "TODO\|FIXME" src/ tests/` and resolve or document
- [ ] T096 [P] Verify no unused imports remain: Use tool like `autoflake` or manual review with `grep -r "^import\|^from" src/`
- [ ] T097 Run complete validation from specs/005-cleanup-and-refactor/quickstart.md procedures
- [ ] T098 Generate final coverage report: `pytest tests/ --cov=src --cov-report=html` and verify coverage maintained or improved from baseline
- [ ] T099 [P] Update specs/005-cleanup-and-refactor/README.md (if exists) or create summary document listing all deliverables: pyproject.toml, reorganized structure, CSS consolidation, style guide, function glossary
- [ ] T100 Final manual validation: Install in fresh virtual environment with `pip install -e .`, run `tf-plan-analyzer analyze tests/fixtures/dev-plan.json`, verify output matches expectations, confirm `tf-plan-analyzer --help` shows proper usage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - (No tasks in this phase for this refactoring)
- **User Story 2 (Phase 3)**: Can start immediately after Setup - Chosen as MVP starting point
- **User Story 5 (Phase 4)**: Should complete after US2 to leverage consolidated CSS
- **User Story 1 (Phase 5)**: MUST complete after US2 and US5 (cleaner to reorganize after consolidation)
- **User Story 3 (Phase 6)**: Can start after US2 completes (needs actual CSS to document)
- **User Story 4 (Phase 7)**: Can start after US1 completes (needs final file locations)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 2 (P2)**: Independent - can start immediately (MVP)
- **User Story 5 (P2)**: Independent - can start in parallel with US2 (works on different files: diff_utils, json_utils, file_utils vs html_generation)
- **User Story 1 (P1)**: Depends on US2 and US5 completion (reorganize after consolidation)
- **User Story 3 (P3)**: Depends on US2 completion (documents consolidated styles)
- **User Story 4 (P4)**: Depends on US1 completion (needs final file paths)

### Critical Path

```
Setup (Phase 1)
    ↓
    ├─→ US2: CSS Extraction (Phase 3) ← START HERE (MVP)
    │
    └─→ US5: Code Consolidation (Phase 4) [can run in parallel with US2]
         ↓
         (Both US2 and US5 complete)
         ↓
US1: File Reorganization (Phase 5)
    ↓
US3: Style Guide (Phase 6) [can overlap with US4]
    ↓
US4: Function Glossary (Phase 7)
    ↓
Polish (Phase 8)
```

### Recommended Implementation Order

1. **Phase 1** (Setup): T001-T005
2. **Phase 3** (US2) + **Phase 4** (US5) - Can run in parallel:
   - US2: T006-T018 - Consolidate CSS (works on html_generation.py)
   - US5: T019-T031 - Consolidate duplicate code (works on diff_utils.py, json_utils.py, file_utils.py)
   - Both phases work on different files with no conflicts
3. **Phase 5** (US1): T032-T069 - Reorganize files after code is clean
5. **Phase 6** (US3): T070-T079 - Document styles (can overlap with Phase 7)
6. **Phase 7** (US4): T080-T092 - Generate function glossary
7. **Phase 8** (Polish): T093-T100 - Final cleanup and validation

### Parallel Opportunities Within Each Phase

**Phase 1 (Setup)**: T002, T003, T004 can run in parallel

**Phase 3 (US2)**: 
- T006, T007, T008, T009 can run in parallel (different CSS functions)
- T012, T013 can run in parallel (different files)

**Phase 4 (US5)**:
- T019, T020, T021, T022, T023, T024 can all run in parallel (different files)

**Phase 5 (US1)**:
- T032-T054 can all run in parallel (all are `git mv` operations on different files)
- T038-T048 (test file moves) can run in parallel
- T050-T052 (doc moves) can run in parallel

**Phase 6 (US3)**:
- Different sections of style guide can be written in parallel if multiple contributors

**Phase 8 (Polish)**:
- T093, T094, T095, T096, T099 can all run in parallel

### Within Each User Story

**US2 (CSS Extraction)**:
1. Create CSS functions (T006-T010) → Consolidate function (T011) → Update callers (T012-T014) → Test (T015-T016) → Clean up demos (T017-T018)

**US5 (Code Consolidation)**:
1. Create library modules (T019-T024) → Update callers (T025-T027) → Document (T028-T029) → Test and validate (T030-T031)

**US1 (File Reorganization)**:
1. Move all files (T032-T054) → Update imports (T055-T060) → Setup CLI (T061-T062) → Test (T063-T066) → Document (T067-T069)

**US3 (Style Guide)**:
1. Create structure (T070) → Add content sections (T071-T077) → Reference in constitution (T078) → Validate (T079)

**US4 (Function Glossary)**:
1. Auto-generate skeleton (T080-T081) → Manually enhance (T082-T089) → Add metadata (T090-T091) → Validate (T092)

---

## Parallel Example: User Story 2 (CSS Extraction)

```bash
# Terminal 1: Create CSS utility functions
# T006-T009 can run in parallel if using branches

git checkout -b us2-css-base && \
  # Create base CSS function in src/lib/html_generation.py
  
# Terminal 2: Meanwhile, prepare for integration
git checkout -b us2-integration && \
  # Create stubs for integration points
```

**Sequential approach for single developer**:
```bash
# Day 1: Create all CSS functions
# T006 → T007 → T008 → T009 → T010 → T011

# Day 2: Update all callers
# T012 → T013 → T014

# Day 3: Test and clean up
# T015 → T016 → T017 → T018
```

---

## Validation Checkpoints

After each user story phase, verify:

- ✅ All tasks in phase completed
- ✅ All 158 tests pass (`pytest tests/ -v`)
- ✅ No regressions in functionality
- ✅ Git commit created with message referencing user story
- ✅ Independent test criteria from spec.md verified

**Final Success Criteria** (from spec.md):

- ✅ SC-001: All 45+ root files relocated (verify with `ls | wc -l` < 10)
- ✅ SC-002: CSS centralized in src/lib/html_generation.py
- ✅ SC-003: All 158 tests pass
- ✅ SC-004: Function glossary 100% complete
- ✅ SC-005: Style guide referenced in constitution
- ✅ SC-006: Code coverage maintained
- ✅ SC-007: CLI works via `tf-plan-analyzer` command
- ✅ SC-008: All shared utilities in src/lib/
- ✅ SC-009: At least 3 library modules created
- ✅ SC-010: `pip install -e .` works
- ✅ SC-011: `tf-plan-analyzer --help` works
- ✅ SC-012: HTML reports visually identical or improved
- ✅ SC-013: Absolute imports from src.*
- ✅ SC-014: No dead code or unused imports
- ✅ SC-015: Documentation builds successfully
- ✅ SC-016: Git history preserved (verify with `git log --follow`)
- ✅ SC-017: Fresh examples showcase consistent styling

---

## Task Summary

**Total Tasks**: 102

**By Phase**:
- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundational): 0 tasks (no blocking infrastructure needed)
- Phase 3 (US2 - CSS Extraction): 13 tasks
- Phase 4 (US5 - Code Consolidation): 13 tasks
- Phase 5 (US1 - File Reorganization): 38 tasks
- Phase 6 (US3 - Style Guide): 10 tasks
- Phase 7 (US4 - Function Glossary): 14 tasks
- Phase 8 (Polish): 8 tasks

**By User Story**:
- US1 (File Reorganization): 38 tasks
- US2 (CSS Extraction): 13 tasks
- US3 (Style Guide): 10 tasks
- US4 (Function Glossary): 14 tasks
- US5 (Code Consolidation): 13 tasks
- Setup/Polish: 14 tasks

**Parallelizable Tasks**: 47 tasks marked with [P]

**Estimated Timeline** (single developer):
- Phase 1: 0.5 days
- Phase 3 (US2): 2 days
- Phase 4 (US5): 2 days
- Phase 5 (US1): 3 days
- Phase 6 (US3): 1 day
- Phase 7 (US4): 1 day
- Phase 8: 0.5 days

**Total**: ~10 days (matches plan.md estimate of 8-11 days)

**MVP Scope** (User Story 2 only): 13 tasks, ~2 days, delivers immediate value (consistent styling)

**Critical Success Factors**:
1. Use `git mv` for all file moves to preserve history
2. Run tests after each phase
3. Update imports carefully (use absolute imports from src.*)
4. Generate fresh HTML examples to validate styling
5. Reference both guides (style guide, function glossary) in constitution
