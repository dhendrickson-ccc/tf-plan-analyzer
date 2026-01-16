# Implementation Plan: Multi-Environment Comparison UI Improvements

**Branch**: `006-comparison-ui-improvements` | **Date**: January 15, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-comparison-ui-improvements/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature improves the multi-environment comparison HTML report's visual layout and usability by transforming attribute rows into header-based sections with scrollable value containers, and elegantly displaying resources that exist in only one environment. The changes enhance readability for DevOps engineers comparing 100+ resources across Test, Production, and other environments by providing better spacing, preventing layout breakage from large JSON values, and clearly distinguishing environment-specific resources from configuration drift.

## Technical Context

**Language/Version**: Python 3.9.6  
**Primary Dependencies**: No new dependencies - pure HTML+CSS modifications  
**Storage**: HTML file output (static reports)  
**Testing**: pytest 8.4.2 with existing test suite (158 tests, 36% coverage)  
**Target Platform**: Modern web browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)  
**Project Type**: Single project (CLI tool with HTML report generation)  
**Performance Goals**: <2 seconds to generate comparison report for 200 resources  
**Constraints**: No JavaScript (pure HTML+CSS), HTML file size increase <20%, backward compatible with existing CLI flags  
**Scale/Scope**: 50-500 resources per comparison, 10-1000 line JSON values, 2-5 environments typically compared

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Duplication Prohibited
✅ **PASS** - Will reuse existing functions from `docs/function-glossary.md`:
- `generate_full_styles()` from `html_generation.py` for CSS generation
- `_render_attribute_table()` and `_render_attribute_value()` from `multi_env_comparator.py` (modify, not duplicate)
- Existing diff highlighting utilities preserved

### Principle II: Shared Data Model Is Canonical
✅ **PASS** - Feature uses existing entities from `.specify/memory/data_model.md`:
- `ResourceComparison` - already defined for multi-environment comparison
- `AttributeDiff` - already defined for attribute-level differences
- No new entities introduced, only UI presentation changes

### Principle III: Live Testing Is Mandatory
✅ **PASS** - Live testing plan defined:
- Test with real Terraform plans: `/Users/danielhendrickson/workspace/promega/gsp-infrastructure-tf/2_deployApp/tfplan-test-2.json` vs `tfplan-prod.json`
- Validate 199 real resources with 196 differences
- Verify scrollbar behavior with large JSON objects (100+ lines)
- Test environment-specific resource detection with actual plans
- Validate sticky headers and horizontal spacing in browser

### Principle IV: Commit After Every User Story
✅ **PASS** - Implementation plan structured to commit after each user story:
- Phase 1: Commit after P1 Story 1 (attribute headers) 
- Phase 2: Commit after P1 Story 2 (scrollable containers)
- Phase 3: Commit after P2 Story 3 (environment-specific resources)

### Principle V: User-Facing Features Require End-to-End Testing
✅ **PASS** - End-to-end testing plan:
- Run `tf-plan-analyzer compare --html test-2.json prod.json` with actual CLI
- Verify HTML report generated correctly with all UI improvements
- Test with `--diff-only` flag to validate environment-specific grouping works
- Validate backward compatibility with existing comparison reports

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
├── cli/
│   └── analyze_plan.py          # CLI entry point (no changes needed)
├── core/
│   ├── multi_env_comparator.py  # MODIFY: _render_attribute_table(), _render_attribute_value()
│   └── hcl_value_resolver.py    # No changes
├── lib/
│   ├── html_generation.py       # MODIFY: Add scrollable container CSS, sticky header CSS, env-specific badge CSS
│   ├── diff_utils.py            # No changes (reuse existing highlighting)
│   ├── file_utils.py            # No changes
│   ├── json_utils.py            # No changes
│   └── ignore_utils.py          # No changes
└── security/
    ├── salt_manager.py          # No changes
    └── sensitive_obfuscator.py  # No changes

tests/
├── test_multi_env_unit.py       # ADD: Tests for new HTML structure
├── test_e2e_multi_env.py        # MODIFY: Update assertions for new layout
└── [other test files]           # No changes

docs/
├── style-guide.md               # UPDATE: Document new CSS classes and patterns
└── function-glossary.md         # UPDATE: Document modified functions
```

**Structure Decision**: Single project structure with modifications focused on HTML generation (`lib/html_generation.py`) and multi-environment rendering (`core/multi_env_comparator.py`). No architectural changes needed - purely presentational improvements to existing comparison functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution principles pass.

---

## Phase 0: Research & Discovery

### Research Tasks

Since all technical context is known and no NEEDS CLARIFICATION markers exist in the spec, Phase 0 research is minimal. The following investigations are needed:

1. **CSS Scrollbar Behavior Patterns**
   - Research: Best practices for `overflow: auto` vs `overflow: scroll` for cross-browser compatibility
   - Research: How to prevent scrollbars from appearing when content fits (overflow: auto behavior)
   - Decision needed: Should scrollbars style be customized for better UX or use browser defaults?

2. **CSS Sticky Header Implementation**
   - Research: Best approach for sticky positioning (`position: sticky` vs `position: fixed`)
   - Research: Z-index layering to ensure sticky headers appear above scrollable content
   - Decision needed: Should sticky headers work within resource cards or only at page level?

3. **Collapsible Section Patterns (Pure HTML+CSS)**
   - Research: HTML5 `<details>` and `<summary>` elements for collapsible sections (no JavaScript)
   - Research: CSS-only accordion alternatives if `<details>` doesn't meet accessibility requirements
   - Decision needed: Default state (expanded or collapsed) for environment-specific resource section

### Research Outputs

All research findings will be documented in `research.md` with:
- Decision made
- Rationale for choice
- Alternatives considered and why rejected
- Code examples or references

**Status**: ✅ **COMPLETE** - `research.md` created with 5 key decisions documented.

---

## Phase 1: Design & Contracts

### Data Model

**Status**: ✅ **COMPLETE** - `data-model.md` created

**Summary**: This feature introduces NO new data structures for comparison logic. All comparison entities (`ResourceComparison`, `AttributeDiff`) remain unchanged. The data model document defines 6 UI component entities:

1. **Attribute Section** - Container for attribute comparison with header + values
2. **Value Container** - Scrollable container with overflow constraints
3. **Environment Value Column** - Flex column grouping env label + value
4. **Sticky Environment Header** - Column headers that stick on scroll
5. **Environment-Specific Badge** - Visual indicator for limited-env resources
6. **Environment-Specific Section** - Collapsible group using `<details>` element

All entities are presentational CSS classes - no changes to comparison data structures.

### Contracts

**Status**: ✅ **COMPLETE** - `contracts/html-structure.md` created

**Summary**: Defines the HTML structure contract (v2.0) that `multi_env_comparator.py` MUST generate:

- **Root structure**: Standard HTML5 document with viewport meta tag
- **Summary cards**: Unchanged from v1.0
- **Resource cards**: Migrated from table-based to section-based attribute layout
- **Attribute sections**: New flex layout with H3 headers and value columns
- **Value containers**: Scrollable divs with max-height/max-width constraints
- **Sticky headers**: Environment column headers with `position: sticky`
- **Environment-specific section**: New `<details>` element for collapsible grouping
- **Diff highlighting**: All existing CSS classes preserved (backward compatible)

Contract includes:
- Complete HTML examples
- CSS requirements for each component
- Behavior contracts (scrolling, stickiness, collapsibility)
- Browser compatibility matrix
- Accessibility requirements
- Test validation criteria

### Quickstart Guide

**Status**: ✅ **COMPLETE** - `quickstart.md` created

**Summary**: Step-by-step developer guide for implementing all 3 user stories:

**Story 1: Attribute Headers** (~1.5 hours)
- Add `get_attribute_section_css()` function
- Modify `_render_attribute_table()` to use section-based layout
- Replace table elements with div + flexbox
- Test with real plans and commit

**Story 2: Scrollable Containers** (~2 hours)
- Add `get_scrollable_container_css()` and `get_sticky_header_css()`
- Wrap values in `.value-container` divs
- Add sticky environment headers before attributes
- Test scrollbar behavior and commit

**Story 3: Environment-Specific Grouping** (~2.5 hours)
- Add `get_env_specific_section_css()`
- Detect env-specific resources in `generate_html_report()`
- Separate regular vs env-specific into two lists
- Render collapsible `<details>` section with badges
- Test detection and grouping, then commit

Guide includes:
- Code examples for each modification
- Testing commands with real plan files
- Validation checklists per story
- Common issues and solutions
- End-to-end validation steps

### Re-Check Constitution (Post-Design)

✅ **PASS** - All principles still satisfied after Phase 1 design:

- **Principle I**: No code duplication introduced in design
- **Principle II**: No new data entities (only UI presentation classes)
- **Principle III**: Live testing plan includes real Terraform plans (199 resources)
- **Principle IV**: Each user story has explicit commit checkpoint
- **Principle V**: End-to-end testing with actual CLI command defined

---

## Phase 2: Task Generation

**Status**: ⏳ **PENDING** - Will be created by `/speckit.tasks` command

Phase 2 is NOT executed by `/speckit.plan`. The task breakdown will be generated by the `/speckit.tasks` command, which creates `tasks.md` with:
- Numbered tasks derived from Phase 1 deliverables
- Dependencies between tasks
- Estimated time per task
- Acceptance criteria per task
- Test commands for validation

**What happens after `/speckit.plan`**:
1. Review this plan document for accuracy and completeness
2. Run `/speckit.tasks` to generate `tasks.md`
3. Begin implementation following `quickstart.md` guide
4. Execute tasks in dependency order with commits after each user story

---

## Summary

### Deliverables Created

| Phase | Deliverable | Status | Description |
|-------|-------------|--------|-------------|
| 0 | `research.md` | ✅ Complete | 5 technical decisions documented (scrollbars, sticky headers, collapsible sections, layout strategy, badge design) |
| 1 | `data-model.md` | ✅ Complete | 6 UI component entities defined (all presentational CSS classes) |
| 1 | `contracts/html-structure.md` | ✅ Complete | HTML structure contract v2.0 with examples, CSS requirements, browser compatibility |
| 1 | `quickstart.md` | ✅ Complete | Developer implementation guide with 3 user stories, code examples, testing steps |
| 1 | `.github/agents/copilot-instructions.md` | ✅ Updated | Agent context updated with Python 3.9.6, HTML+CSS tech stack |

### Key Technical Decisions

1. **Scrollbar Behavior**: Use `overflow: auto` (shows scrollbars only when needed)
2. **Sticky Headers**: Use `position: sticky` on environment headers only (user choice: Option A)
3. **Collapsible Section**: Use HTML5 `<details>`/`<summary>` (no JavaScript, default expanded)
4. **Attribute Layout**: Flexbox section-based layout with H3 headers (30px spacing)
5. **Environment-Specific Badges**: Amber/yellow warning color (#ffa94d) distinct from diff colors

### Files Modified (Implementation Phase)

- `src/lib/html_generation.py` - Add 3 new CSS functions
- `src/core/multi_env_comparator.py` - Modify `_render_attribute_table()` and `generate_html_report()`
- `docs/style-guide.md` - Document new CSS classes and patterns
- `docs/function-glossary.md` - Update modified function signatures
- `tests/test_multi_env_unit.py` - Add tests for new HTML structure
- `tests/test_e2e_multi_env.py` - Update assertions for new layout

### Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement User Story 1 (attribute headers) following `quickstart.md`
3. Test with real plans and commit
4. Implement User Story 2 (scrollable containers)
5. Test and commit
6. Implement User Story 3 (environment-specific grouping)
7. Test and commit
8. Run full end-to-end validation with production plans
9. Update documentation and run test suite
10. Push branch and create pull request

### Estimated Total Time

- Phase 0 (Research): 1 hour (complete)
- Phase 1 (Design): 1.5 hours (complete)
- Implementation: 6 hours (1.5 + 2 + 2.5 per quickstart)
- Testing & Documentation: 1.5 hours
- **Total**: ~10 hours for complete feature implementation

---

**Plan Status**: ✅ **COMPLETE AND READY FOR TASK GENERATION**

This plan document can now be used to generate tasks via `/speckit.tasks` command.
