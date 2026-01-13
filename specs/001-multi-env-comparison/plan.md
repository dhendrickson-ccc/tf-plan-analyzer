# Implementation Plan: Multi-Environment Terraform Plan Comparison

**Branch**: `001-multi-env-comparison` | **Date**: 2026-01-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-multi-env-comparison/spec.md`

## Summary

This feature adds multi-environment comparison capability to the Terraform Plan Analyzer tool. Users will be able to compare the "before" state configuration across 2+ environments (dev, staging, prod) in a side-by-side columnar HTML report. The implementation introduces a subcommand-based CLI architecture (`report` for single-plan analysis, `compare` for multi-environment comparison) providing clear separation of concerns while maintaining backward compatibility.

**Core Value**: Enable DevOps engineers to quickly identify configuration drift and ensure parity across multiple environments by highlighting differences in resource configurations side-by-side.

## Technical Context

**Language/Version**: Python 3.8+ (matching existing codebase)
**Primary Dependencies**: 
- argparse (stdlib, for subcommand CLI)
- json (stdlib)
- pathlib (stdlib)
- typing (stdlib)
- Existing: hcl_value_resolver (optional, for HCL resolution)
- Existing: difflib (for diff highlighting)

**Storage**: N/A (file-based input/output only)
**Testing**: pytest (for unit and end-to-end tests)
**Target Platform**: Cross-platform CLI tool (macOS, Linux, Windows)
**Project Type**: Single-project Python CLI tool
**Performance Goals**: 
- Compare 3 plans with <100 resources each in <10 seconds
- Support up to 5 environments without significant degradation
- HTML report generation <5 seconds for typical use cases

**Constraints**:
- Must maintain 100% backward compatibility with existing `analyze_plan.py` behavior
- Must reuse existing diff highlighting logic from generate_html_report.py
- Must work with existing HCL resolution infrastructure
- No external service dependencies (fully offline capable)

**Scale/Scope**:
- Target: 2-5 environments per comparison
- Typical use: 50-200 resources per environment
- HTML report must remain readable with wide tables (columnar layout)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Duplication Prohibited
✅ **PASS** - Plan requires reusing existing TerraformPlanAnalyzer logic, diff highlighting from generate_html_report.py, and HCL resolution from hcl_value_resolver.py. New code will be isolated to subcommand routing and multi-environment comparison orchestration.

### Principle II: Shared Data Model Is Canonical
✅ **PASS** - Will create data-model.md during Phase 1 defining EnvironmentPlan, ResourceComparison, MultiEnvReport, and ConfigDifference entities. These will be added to canonical data model before implementation.

### Principle III: Live Testing Is Mandatory
✅ **PASS** - Spec defines Independent Test scenarios for each user story. Plan includes Phase 3: Live Testing/Validation with actual Terraform plan files across multiple mock environments. Agent will execute tests and validate HTML output.

### Principle IV: Commit After Every User Story
✅ **PASS** - Implementation will be structured by user story with commits after each story completion as defined in tasks.md (Phase 2 output).

### Principle V: User-Facing Features Require End-to-End Testing
✅ **PASS** - Feature introduces CLI subcommands (report/compare). End-to-end tests will invoke actual CLI commands with real plan files, validate HTML output, and test various flag combinations (--html, --env-names, --tfvars-files, etc.).

**Result**: All constitution principles satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-env-comparison/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-interface.md # CLI subcommand contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single project structure (current layout)
.
├── analyze_plan.py           # MODIFIED: Add subcommand routing, refactor main()
├── multi_env_comparator.py   # NEW: Multi-environment comparison logic
├── generate_html_report.py   # MODIFIED: Add multi-env HTML template support
├── hcl_value_resolver.py     # NO CHANGES: Reused as-is
├── test_e2e_multi_env.py     # NEW: End-to-end tests for compare subcommand
├── test_multi_env_unit.py    # NEW: Unit tests for multi-env comparison logic
├── test_change_detection.py  # NO CHANGES: Existing tests preserved
├── test_e2e_sensitive_change.py  # NO CHANGES: Existing tests preserved
├── test_hcl_reference.py     # NO CHANGES: Existing tests preserved
└── ignore_config.example.json # NO CHANGES: Existing config format reused
```

**Structure Decision**: 
This is a single-project Python CLI tool with flat file structure (no src/ directory currently). The implementation will follow the existing pattern:
- Core logic in top-level .py files
- Test files prefixed with `test_`
- New multi-environment functionality isolated in `multi_env_comparator.py` to avoid modifying core `TerraformPlanAnalyzer` class
- Subcommand routing added to existing `analyze_plan.py` main()
- HTML generation extended in `generate_html_report.py` to support columnar layout

## Complexity Tracking

> No constitution violations - this section intentionally left empty.

---

## Phase Execution Summary

### Phase 0: Research & Technical Decisions ✅ COMPLETE

**Output**: [research.md](research.md)

**Key Decisions**:
1. **CLI Architecture**: argparse subparsers (report/compare) for clean separation
2. **HTML Layout**: Responsive table with collapsible nested structures
3. **Diff Highlighting**: Reuse existing highlight_json_diff() function
4. **HCL Resolution**: Single --tf-dir + --tfvars-files matching common workflow
5. **Resource Matching**: Strict address matching, no fuzzy logic
6. **Sensitive Values**: Respect --show-sensitive flag, highlight masked differences

**Status**: All clarifications obtained, no open questions remain

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**:
- [data-model.md](data-model.md) - Data entities defined
- [contracts/cli-interface.md](contracts/cli-interface.md) - CLI contract specification
- [quickstart.md](quickstart.md) - User-facing quick start guide
- [.specify/memory/data_model.md](../../.specify/memory/data_model.md) - Canonical data model updated

**Entities Defined**:
1. CLISubcommand - Command routing
2. EnvironmentPlan - Single environment plan data
3. ResourceComparison - Multi-env resource aggregation
4. ConfigDifference - Granular difference tracking
5. MultiEnvReport - Report orchestration

**Status**: Design complete, ready for task generation

---

### Constitution Re-Check (Post-Design)

*Re-evaluating constitution compliance after Phase 1 design*

### Principle I: Code Duplication Prohibited
✅ **PASS** - Design confirms reuse strategy:
- TerraformPlanAnalyzer class reused for report subcommand
- generate_html_report.py diff logic reused for multi-env highlighting
- HCLValueResolver reused as-is
- Existing ignore config format reused
- No duplication identified in design

### Principle II: Shared Data Model Is Canonical
✅ **PASS** - All entities documented in:
- specs/001-multi-env-comparison/data-model.md
- .specify/memory/data_model.md (canonical)
- Entities defined before implementation per constitution

### Principle III: Live Testing Is Mandatory
✅ **PASS** - Design includes:
- test_e2e_multi_env.py for end-to-end CLI testing
- Real Terraform plan files for validation
- HTML output validation
- Multi-environment scenarios (2, 3, 5 environments)

### Principle IV: Commit After Every User Story
✅ **PASS** - Will be enforced during Phase 3 (Implementation)
- tasks.md will structure work by user story
- Each story committed independently

### Principle V: User-Facing Features Require End-to-End Testing
✅ **PASS** - Design includes comprehensive CLI testing:
- Both subcommands (report, compare) tested end-to-end
- Flag combinations validated (--html, --env-names, --tfvars-files, etc.)
- Error cases tested (wrong file count, mismatched arguments)
- Contract tests verify CLI interface behavior

**Result**: All constitution principles remain satisfied post-design. No issues identified.

---

## Next Steps

### Phase 2: Task Generation (Not part of /speckit.plan)

Run `/speckit.tasks` to generate:
- Actionable task list structured by user story
- Tasks ordered by dependencies
- Test-first approach for each user story
- Clear acceptance criteria per task

### Phase 3: Implementation (Not part of /speckit.plan)

Run `/speckit.implement` to:
- Execute tasks in dependency order
- Implement user stories incrementally
- Run live tests after each story
- Commit after each story completion

---

## Implementation Notes

### Backward Compatibility Strategy

The subcommand architecture maintains full backward compatibility:

1. **Current behavior preserved**: All existing `analyze_plan.py` functionality moves to `report` subcommand
2. **No breaking changes**: Old scripts can be updated by adding `report` subcommand
3. **Deprecation path**: Direct plan file argument (without subcommand) can show deprecation warning in future

### Code Organization

**New file: multi_env_comparator.py**
- Contains all multi-environment comparison logic
- Isolated from existing TerraformPlanAnalyzer class
- Prevents coupling and maintains single responsibility

**Modified file: analyze_plan.py**
- Add subcommand routing in main()
- Preserve existing TerraformPlanAnalyzer class unchanged
- Route to multi_env_comparator for compare subcommand

**Modified file: generate_html_report.py**
- Add multi-column HTML template generation
- Reuse existing diff highlighting CSS/JS
- Keep single-plan HTML generation unchanged

### Testing Strategy

**Unit Tests** (test_multi_env_unit.py):
- EnvironmentPlan loading and parsing
- ResourceComparison aggregation logic
- ConfigDifference detection
- MultiEnvReport summary statistics

**End-to-End Tests** (test_e2e_multi_env.py):
- CLI invocation with subprocess
- Actual plan file parsing
- HTML report generation and validation
- Flag combination testing
- Error case validation

**Integration Tests**:
- HCL resolution with multiple tfvars
- Ignore config application across environments
- Sensitive value masking and highlighting

---

## Artifacts Generated

✅ research.md - Technical decisions and alternatives  
✅ data-model.md - Entity definitions  
✅ contracts/cli-interface.md - CLI specification  
✅ quickstart.md - User guide  
✅ .specify/memory/data_model.md - Canonical data model updated  
✅ .github/agents/copilot-instructions.md - Agent context updated  

**Planning Phase Complete** - Ready for `/speckit.tasks`
