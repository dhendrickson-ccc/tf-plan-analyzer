# Implementation Plan: Compare Subcommand Enhancements

**Branch**: `004-compare-enhancements` | **Date**: 2026-01-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-compare-enhancements/spec.md`

## Clarifications

### Session 2026-01-14

- Q: Where should refactored ignore configuration logic be placed? → A: Create new ignore_utils.py module
- Q: What testing strategy should be used for HTML attribute-level rendering? → A: Hybrid approach (unit tests for data structures + e2e tests parsing HTML + manual visual review when needed)
- Q: How should the attribute-level diff feature integrate with existing HTML generation? → A: Replace JSON display with attribute table when differences exist (conditional rendering)
- Q: When should ignore configuration filtering be applied in the comparison pipeline? → A: Filter during comparison (before has_differences calculation)
- Q: Should the implementation preserve backward compatibility by making attribute-level view opt-in? → A: Attribute-level view always enabled (replaces full JSON display by default)

## Summary

Add ignore file support and attribute-level diff view to the `compare` subcommand to reduce noise and improve readability of multi-environment comparison reports. Users can filter out known acceptable differences (tags, environment-specific descriptions) using the same ignore configuration format as the `report` subcommand. The HTML report will be restructured to show only changed top-level attributes for each resource in side-by-side columns, rather than displaying full JSON configurations.

## Technical Context

**Language/Version**: Python 3.9.6  
**Primary Dependencies**: Python stdlib (json, pathlib, difflib, html), pytest 8.4.2 (testing)  
**Storage**: Filesystem (JSON plan files, HTML output files)  
**Testing**: pytest (existing test_e2e_multi_env.py, test_multi_env_unit.py patterns)  
**Target Platform**: macOS/Linux CLI tool  
**Project Type**: Single project (flat file structure, no src/ directory)  
**Performance Goals**: <3 seconds HTML rendering for 100+ resources with differences (SC-007)  
**Constraints**: Backward compatibility required - existing `compare` functionality must remain unchanged when `--config` flag is not used (FR-030)  
**Scale/Scope**: Up to 500 resources across 2-5 environments (based on feature 001 scope)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Duplication Prohibited ✅ PASS
- **Status**: No violations detected
- **Rationale**: Feature reuses existing ignore configuration parsing logic from `report` subcommand (lines 1833-1865 in analyze_plan.py). Will refactor ignore configuration parsing and application logic into new `ignore_utils.py` module with functions usable by both `report` and `compare` subcommands. No new duplicate code will be introduced.

### Principle II: Shared Data Model Is Canonical ✅ PASS
- **Status**: No new data structures required
- **Rationale**: Feature uses existing entities (EnvironmentPlan, ResourceComparison, MultiEnvReport) from multi_env_comparator.py. Ignore configuration format already documented in ignore_config.example.json. No changes to canonical data model needed.

### Principle III: Live Testing Is Mandatory ✅ PASS
- **Status**: Live testing requirements met
- **Rationale**: Feature will be validated with real Terraform plan JSON files from test_data/ directory (dev-plan.json, staging-plan.json, prod-plan.json). End-to-end tests will invoke CLI with actual plan files and verify HTML output, ignore rule application, and summary statistics. Live testing phase included in Phase 4-6 for each user story.

### Principle IV: Commit After Every User Story ✅ PASS
- **Status**: Commit boundaries defined
- **Rationale**: Implementation plan includes 3 user stories (US1: Ignore File Support, US2: Attribute-Level Diff View, US3: Combined Functionality). Each user story will be committed separately after completion and testing, following the pattern from feature 001 and 003.

### Principle V: User-Facing Features Require End-to-End Testing ✅ PASS
- **Status**: End-to-end tests planned for CLI flags and config files
- **Rationale**: Feature introduces `--config` CLI flag (reusing existing flag but making it functional for compare). End-to-end tests will:
  - Test `--config` flag with valid ignore configuration files
  - Test `--config` with nonexistent file (error handling)
  - Test `--config` with malformed JSON (error handling)
  - Test `--config` combined with `--diff-only` flag
  - Test attribute-level HTML output structure by parsing generated HTML for key elements (attribute tables, ignore badges, side-by-side columns)
  - Validate summary statistics reflect filtered results
  - Testing strategy: Hybrid approach with unit tests for AttributeDiff data structures and e2e tests that parse HTML output; manual visual review requested when needed for UX validation

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
# Single project structure (existing layout)
.
├── analyze_plan.py                    # MODIFIED: Update handle_compare_subcommand() to use ignore_utils
├── multi_env_comparator.py            # MODIFIED: Add attribute-level diff methods, use ignore_utils for filtering
├── ignore_utils.py                    # NEW: Shared ignore config parsing and application logic
├── ignore_config.example.json         # NO CHANGES: Existing config format reused
├── test_e2e_compare_enhancements.py   # NEW: End-to-end tests for ignore + attribute-level features
├── test_compare_enhancements_unit.py  # NEW: Unit tests for new comparison logic
├── test_ignore_utils.py               # NEW: Unit tests for ignore_utils module
├── test_e2e_multi_env.py              # NO CHANGES: Existing compare tests preserved
├── test_multi_env_unit.py             # NO CHANGES: Existing unit tests preserved
└── test_data/
    ├── dev-plan.json                  # REUSED: Existing test data
    ├── staging-plan.json              # REUSED: Existing test data
    ├── prod-plan.json                 # REUSED: Existing test data
    └── ignore_config.json             # REUSED: Existing test config file
```

**Structure Decision**: 
This is a single-project Python CLI tool with flat file structure (no src/ directory). The implementation will follow the existing pattern:
- Create new ignore_utils.py module to extract ignore configuration parsing and application logic from analyze_plan.py (refactoring for reuse)
- Modify analyze_plan.py handle_compare_subcommand() to use ignore_utils and fully implement --config flag support (currently stub)
- Modify multi_env_comparator.py to:
  - Add attribute-level diff computation (extract changed top-level keys from env_configs)
  - Use ignore_utils for filtering during comparison (before has_differences calculation)
  - Replace full JSON display with attribute-level tables in HTML generation (always enabled, no opt-in flag required)
- Create new test files following existing naming convention (test_e2e_*, test_*_unit.py, test_ignore_utils.py)
- Reuse existing test data from test_data/ directory
- All changes maintain backward compatibility: existing compare functionality unchanged when --config flag not used; attribute-level view improves UX without breaking existing workflows

## Complexity Tracking

**No violations** - This feature adheres to all constitution principles and requires no complexity justification.

---

## Phase 0: Outline & Research

**Goal**: Resolve all "NEEDS CLARIFICATION" items from Technical Context and document technology choices.

### Research Tasks

1. **Existing ignore configuration implementation analysis**
   - **Question**: How does the report subcommand parse and apply ignore configuration?
   - **Method**: Code review of analyze_plan.py lines 1833-1865, trace `_apply_ignore_config()` usage
   - **Output**: Document ignore config structure (global_ignores, resource_ignores), both dict and list formats supported

2. **HTML generation architecture review**
   - **Question**: How does multi_env_comparator.py generate HTML currently?
   - **Method**: Code review of MultiEnvReport.generate_html() in multi_env_comparator.py lines 696-775
   - **Output**: Document current HTML structure (CSS Grid columnar layout, full JSON display per environment). Note: Feature 004 will conditionally replace full JSON with attribute-only tables when differences exist (reduces visual noise)

3. **Diff detection mechanism analysis**
   - **Question**: How does ResourceComparison detect differences between environments?
   - **Method**: Code review of ResourceComparison class, detect_differences() method. Note: Ignore filtering will be applied during comparison (before has_differences calculation) to ensure statistics and --diff-only flag reflect filtered results
   - **Output**: Document difference detection logic (config comparison, env_configs vs env_configs_raw)

4. **Best practices for attribute-level diff computation**
   - **Question**: How to efficiently compute top-level attribute diffs from nested JSON?
   - **Method**: Review Python dict/JSON traversal patterns, analyze performance implications
   - **Output**: Document approach for extracting changed top-level keys from nested structures

### Output: research.md

Document all findings in `specs/004-compare-enhancements/research.md` with sections:
- **Ignore Configuration Format**: JSON schema, global vs resource-specific rules, dot notation for nested attributes
- **Current HTML Structure**: Table layout, columnar design, diff highlighting integration
- **Diff Detection Flow**: When differences are calculated, how env_configs are compared
- **Attribute-Level Diff Strategy**: Algorithm for identifying changed top-level attributes, handling nested structures
- **Integration Points**: Where to inject ignore logic and attribute-level computation in existing flow

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete

### Design Artifacts

1. **Data Model** (`data-model.md`)
   - **AttributeDiff**: Represents a single changed top-level attribute
     - `attribute_name`: string (top-level key, e.g., "location", "identity", "tags")
     - `env_values`: Dict[str, Any] (environment name → attribute value)
     - `is_different`: bool (whether values differ across environments)
   - **FilteredResourceComparison**: Extension of ResourceComparison with ignore tracking
     - `ignored_attributes`: Set[str] (attributes filtered out by ignore rules)
     - `attribute_diffs`: List[AttributeDiff] (top-level attributes that changed)
   - **IgnoreStatistics**: New tracking entity
     - `total_ignored_attributes`: int (count of attributes filtered)
     - `resources_with_ignores`: int (resources with at least 1 ignored attribute)
     - `all_changes_ignored`: int (resources with all changes ignored)

2. **API Contracts** (`contracts/`)
   - **CLI Contract** (`cli-interface.md`):
     ```bash
     # Existing (unchanged)
     python analyze_plan.py compare dev.json prod.json --html
     
     # New: with ignore config
     python analyze_plan.py compare dev.json prod.json --config ignore.json --html
     
     # New: combined with diff-only
     python analyze_plan.py compare dev.json prod.json --config ignore.json --diff-only --html
     ```
     - Exit codes: 0 (success), 1 (file not found), 2 (invalid JSON)
     - HTML output structure: resources → changed attributes → side-by-side values
   
   - **Ignore Config Schema** (`ignore-config-schema.md`):
     ```json
     {
       "global_ignores": {
         "<attribute_name>": "<reason_string>"
       },
       "resource_ignores": {
         "<resource_type>": {
           "<attribute_name>": "<reason_string>"
         }
       }
     }
     ```
     - Supports nested attributes with dot notation: "identity.type"
     - Supports both top-level and nested attribute filtering

3. **Quickstart Guide** (`quickstart.md`)
   - Installation: No new dependencies
   - Usage example 1: Filter tags from comparison
   - Usage example 2: Resource-specific ignore rules
   - Usage example 3: Attribute-level diff view benefits
   - Troubleshooting: Config file not found, malformed JSON

### Agent Context Update

```bash
.specify/scripts/bash/update-agent-context.sh copilot
```

**Technologies to add**:
- Python stdlib only (no new dependencies)
- Existing pytest framework
- HTML template string manipulation

**Context preservation**: Maintain existing project description, keep manual additions between markers

### Re-evaluate Constitution Check

After design complete, verify:
- ✅ No duplicate code introduced (ignore logic refactored into shared utility)
- ✅ Data model updated with new entities (AttributeDiff, FilteredResourceComparison)
- ✅ CLI contract documented for end-to-end testing
- ✅ Backward compatibility maintained

---

## Phase 2: Stop and Report

**Command completion point** - `/speckit.plan` ends here.

### Generated Artifacts

- ✅ `plan.md` - This implementation plan
- ✅ `research.md` - Technology research and decisions (Phase 0 output)
- ✅ `data-model.md` - Entity definitions (Phase 1 output)
- ✅ `contracts/cli-interface.md` - CLI contract specification
- ✅ `contracts/ignore-config-schema.md` - Config file schema
- ✅ `quickstart.md` - User-facing usage guide
- ⏳ `tasks.md` - Created by `/speckit.tasks` command (not part of `/speckit.plan`)

### Branch Status

- **Branch**: `004-compare-enhancements`
- **Spec**: [specs/004-compare-enhancements/spec.md](spec.md)
- **Plan**: [specs/004-compare-enhancements/plan.md](plan.md)
- **Next Command**: `/speckit.tasks` to generate task breakdown for implementation

### Summary

This plan establishes the foundation for adding ignore file support and attribute-level diff view to the compare subcommand. Research phase will analyze existing ignore configuration logic and HTML generation patterns. Design phase will define new data entities for tracking attribute-level diffs and ignored attributes, create CLI contract documentation, and provide a quickstart guide for users. Implementation details will be broken down into specific tasks by `/speckit.tasks` command.

**Key Design Decisions**:
1. **Reuse over reinvent**: Refactor existing `_apply_ignore_config()` from report subcommand into shared utility
2. **Top-level only**: Attribute-level diff displays only top-level changed attributes; nested content shown as blocks
3. **Side-by-side layout**: Maintain existing columnar design, add attribute granularity within each resource
4. **Backward compatible**: No changes to compare behavior when `--config` flag is not used
5. **Transparent filtering**: Show "N attributes ignored" indicator to inform users about applied filters
