# Implementation Plan: Cleanup and Tech-Debt Reduction

**Branch**: `005-cleanup-and-refactor` | **Date**: January 15, 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-cleanup-and-refactor/spec.md`

**Note**: This plan addresses technical debt through file reorganization, CSS consolidation, and documentation improvements without changing functionality.

## Summary

Refactor the tf-plan-analyzer project to reduce technical debt by: (1) reorganizing 45+ root-level files into logical directories (src/, tests/, docs/, examples/), (2) consolidating ~400 lines of duplicate CSS across 3 files into a shared styling module, (3) creating a UI style guide for consistent future development, (4) generating a function glossary to support code reuse, and (5) eliminating code duplication through shared utilities. This cleanup improves maintainability while preserving 100% backward compatibility.

**Research Findings**: Analysis identified 13+ HTML demo files, 11 test files, and 8 source files in root directory; ~400 lines of duplicate CSS with font family inconsistencies (Courier New vs Monaco/Menlo); and opportunities for DRY improvements in HTML generation, JSON formatting, and file I/O patterns. See [research.md](./research.md) for details.

## Technical Context

**Language/Version**: Python 3.9.6  
**Primary Dependencies**: pytest 8.4.2 (testing only, no runtime dependencies)  
**Storage**: File system (JSON plan files, HTML reports)  
**Testing**: pytest with 158 existing tests (unit + e2e)  
**Target Platform**: macOS/Linux CLI tool
**Project Type**: Single project (CLI application with report generation)  
**Performance Goals**: Maintain current performance (<1s for 100+ resources)  
**Constraints**: 100% backward compatibility required, no CLI breaking changes  
**Scale/Scope**: ~3,000 LOC across 8 source files, 11 test files, 158 tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Code Duplication Prohibited
**Status**: COMPLIANT (by design)
- This feature explicitly eliminates duplicate CSS (~400 lines)
- Consolidates duplicate HTML generation patterns
- Creates function glossary to prevent future duplication
- Extract shared utilities for JSON formatting and file I/O

### ✅ Principle II: Shared Data Model Is Canonical
**Status**: COMPLIANT  
- No new data models introduced (refactoring only)
- Preserves existing data structures without modification
- Updates will be reflected in canonical data model if needed

### ✅ Principle III: Live Testing Is Mandatory
**Status**: COMPLIANT
- All 158 existing tests serve as live validation
- Will manually test all CLI commands after reorganization
- Will generate and visually validate all HTML report types
- Will verify imports work correctly after file moves

### ✅ Principle IV: Commit After Every User Story
**Status**: COMPLIANT
- US1 (file reorganization) → Commit after tests pass
- US2 (CSS extraction) → Commit after validation
- US3 (style guide) → Commit after creation
- US4 (function glossary) → Commit after generation
- US5 (code consolidation) → Commit after tests pass

### ✅ Principle V: User-Facing Features Require End-to-End Testing
**Status**: COMPLIANT
- No new user-facing features (refactoring only)
- Existing e2e tests validate CLI interface remains unchanged
- Manual validation of HTML output ensures visual consistency

**Gate Result**: ✅ PASS - All principles aligned or explicitly addressed

## Project Structure

### Documentation (this feature)

```text
specs/005-cleanup-and-refactor/
├── spec.md              # Feature specification with user stories
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - project analysis (COMPLETE)
├── data-model.md        # Phase 1 output - N/A for refactoring
├── quickstart.md        # Phase 1 output - refactoring guide
├── style-guide.md       # US3 deliverable - UI/UX style guide
├── function-glossary.md # US4 deliverable - function reference
└── contracts/           # Phase 1 output
    └── directory-structure.md  # New project layout contract
```

### Source Code (current state → proposed)

**Current (problematic):**
```text
/
├── analyze_plan.py                    # 2,200 LOC
├── generate_html_report.py            # 700 LOC (deprecated)
├── multi_env_comparator.py            # 800 LOC
├── hcl_value_resolver.py              # 300 LOC
├── ignore_utils.py                    # 300 LOC
├── salt_manager.py                    # 200 LOC
├── sensitive_obfuscator.py            # 400 LOC
├── generate_large_test_plan.py        # 100 LOC (test utility)
├── test_*.py (11 files)               # 3,000+ LOC of tests
├── *.html (13+ files)                 # Demo/test HTML files
├── IMPLEMENTATION_SUMMARY.md (4 files)
└── specs/
```

**Proposed (organized):**
```text
/
├── README.md
├── .gitignore
├── pyproject.toml (new - project metadata)
│
├── src/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── analyze_plan.py          # Main CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── multi_env_comparator.py
│   │   └── hcl_value_resolver.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── salt_manager.py
│   │   └── sensitive_obfuscator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── ignore_utils.py
│   └── templates/
│       ├── __init__.py
│       ├── html_styles.py           # NEW: Shared CSS
│       └── report_template.py       # NEW: Shared HTML structure
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_change_detection.py
│   │   ├── test_hcl_reference.py
│   │   ├── test_ignore_utils.py
│   │   ├── test_salt_manager.py
│   │   ├── test_sensitive_obfuscator.py
│   │   ├── test_multi_env_unit.py
│   │   └── test_compare_enhancements_unit.py
│   ├── e2e/
│   │   ├── test_e2e_multi_env.py
│   │   ├── test_e2e_obfuscate.py
│   │   ├── test_e2e_compare_enhancements.py
│   │   └── test_e2e_sensitive_change.py
│   └── fixtures/
│       └── (move from test_data/)
│
├── docs/
│   ├── README.md (project overview)
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── OBFUSCATION_IMPLEMENTATION_SUMMARY.md
│   ├── JSON_REPORT_GUIDE.md
│   └── style-guide.md (new)
│
├── examples/
│   ├── ignore_config.example.json
│   ├── sample_reports/
│   │   ├── single_plan.html
│   │   ├── multi_env.html
│   │   └── obfuscated.html
│   └── demo_data/
│       └── generate_large_test_plan.py
│
└── specs/  (unchanged)
```

**Structure Decision**: Adopted single-project structure (Option 1 from template) organized into functional modules (cli/, core/, security/, utils/, templates/). Test files separated into unit/ and e2e/ directories. Documentation and examples moved to dedicated directories. This aligns with Python best practices and improves discoverability while maintaining backward compatibility through proper import paths.

## Complexity Tracking

> No violations - this feature reduces complexity rather than increasing it.

---

## Phase 0: Research & Analysis

**Status**: ✅ COMPLETE

**Deliverable**: [research.md](./research.md) - Comprehensive analysis of current state

**Key Findings**:
- 45+ files in root directory (should be <10)
- ~400 lines of duplicate CSS across 3 files
- Font family inconsistencies (Courier New vs Monaco/Menlo)
- 49 public functions cataloged across 19 files
- Opportunities for DRY improvements in HTML generation

---

## Phase 1: Design & Contracts

### Data Model

**Status**: N/A for this feature (no new data structures)

This is a refactoring feature that preserves existing data models:
- TerraformPlanAnalyzer class structure unchanged
- MultiEnvReport class structure unchanged  
- ResourceComparison data structures unchanged
- JSON schemas unchanged

Changes only affect code organization and presentation layer (CSS).

### Contracts

**Deliverable**: `contracts/directory-structure.md` - New project layout specification

**Content**:
- Mapping of old file paths to new file paths
- Import path changes required
- Backward compatibility strategy
- Migration guide for external tools

### Quickstart Guide

**Deliverable**: `quickstart.md` - Guide for implementing refactoring

**Content**:
- Step-by-step reorganization procedure
- Testing strategy at each step
- Rollback procedures
- Common pitfalls and solutions

---

## Phase 2: Implementation

*Note: Implementation tasks will be generated by `/speckit.tasks` command*

### High-Level Implementation Strategy

1. **US2 First (CSS Extraction)**: Lowest risk, highest immediate impact
   - Extract shared CSS to `src/templates/html_styles.py`
   - Update all HTML generators to use shared styles
   - Validate visual consistency
   - Commit

2. **US5 (Code Consolidation)**: Build on CSS work
   - Extract HTML generation boilerplate
   - Consolidate JSON formatting utilities
   - Commit

3. **US1 (File Reorganization)**: After code is DRY
   - Create new directory structure
   - Move files using `git mv`
   - Update imports across codebase
   - Run all tests
   - Commit

4. **US3 (Style Guide)**: Document decisions
   - Create comprehensive style guide
   - Update constitution to reference it
   - Commit

5. **US4 (Function Glossary)**: Final documentation
   - Generate function catalog
   - Update constitution to reference it
   - Commit

### Testing Strategy

**At Each Step**:
- Run full test suite: `pytest tests/ -v`
- Manual CLI validation: `python -m src.cli.analyze_plan --help`
- Generate sample reports and visually compare
- Check import statements work correctly

**Validation Criteria**:
- All 158 tests must pass
- CLI commands work identically
- HTML reports visually identical or improved
- No new warnings or errors

---

## Phase 3: Validation & Deployment

### Validation Checklist

- [ ] All tests pass (158/158)
- [ ] CLI interface unchanged
- [ ] HTML reports visually validated
- [ ] Import paths work correctly
- [ ] Documentation updated
- [ ] Style guide complete
- [ ] Function glossary complete
- [ ] Constitution updated with references

### Success Metrics

- Root-level files: <10 (currently 45+)
- CSS duplication: 0% (currently ~400 lines)
- Test pass rate: 100% (maintain)
- Code coverage: Maintained or improved
- Function glossary: 100% coverage of public functions

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Import paths break external tools | Medium | High | Provide backward-compatible imports with deprecation warnings |
| File moves lose git history | Low | Medium | Use `git mv` exclusively, never delete+recreate |
| Visual regressions in HTML | Low | Medium | Side-by-side visual comparison before/after |
| Test discovery breaks | Low | High | Test after each move, update pytest.ini if needed |
| Merge conflicts with in-flight PRs | Medium | Medium | Coordinate timing, provide migration guide |

---

## Dependencies

- No external dependencies required
- Relies on existing test suite for validation
- Requires git 2.0+ for proper file move tracking

---

## Timeline Estimate

Based on 5 user stories with phased approach:

- **US2 (CSS Extraction)**: 1-2 days
- **US5 (Code Consolidation)**: 2-3 days  
- **US1 (File Reorganization)**: 2-3 days
- **US3 (Style Guide)**: 1 day
- **US4 (Function Glossary)**: 1 day
- **Testing & Validation**: 1 day

**Total**: 8-11 days (with buffer for unexpected issues)
