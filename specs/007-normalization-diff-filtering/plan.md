# Implementation Plan: Normalization-Based Difference Filtering

**Branch**: `007-normalization-diff-filtering` | **Date**: 2025-01-15 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from [specs/007-normalization-diff-filtering/spec.md](spec.md)

## Summary

Add normalization-based difference filtering to ignore environment-specific formatting differences (environment naming patterns like -t- vs -p-, subscription IDs, tenant IDs) that are functionally equivalent after normalization. This extends the existing ignore configuration infrastructure to apply regex pattern transformations before comparing attribute values, significantly reducing noise in multi-environment comparisons without losing visibility into actual configuration drift.

**Technical Approach**: Extend the existing `ignore_config.json` schema with an optional `normalization_config_path` field pointing to a `normalizations.json` file containing regex patterns. After diff computation but before filtering differences, apply normalization transformations to both environment values. If normalized values match exactly, mark the attribute difference as ignored_due_to_normalization (tracked separately from config-ignored). Update HTML badge/tooltip to show combined counts.

## Technical Context

**Language/Version**: Python 3.9+ (requires-python = ">=3.9" in pyproject.toml)  
**Primary Dependencies**: Python standard library only (json, re, pathlib) - no external packages needed for normalization  
**Storage**: JSON files (ignore_config.json, normalizations.json) - file-based configuration  
**Testing**: pytest 8.0+ with pytest-cov for coverage (existing test infrastructure)  
**Target Platform**: Cross-platform CLI tool (macOS, Linux, Windows) - runs anywhere Python 3.9+ available
**Project Type**: Single Python project with CLI entry point (tf-plan-analyzer command)  
**Performance Goals**: Normalization overhead ≤10% vs comparison without normalization (measured on same datasets)  
**Constraints**: Backward compatible (must work without normalization config), regex patterns must be validated on load, original values never modified (normalization only for comparison)  
**Scale/Scope**: Typical comparisons: 100-1000 resources, 10-50 normalization patterns, 2-5 environments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Duplication Prohibited
- ✅ **PASS**: Will reuse existing `load_ignore_config()` pattern for loading normalization config
- ✅ **PASS**: Will extend existing `AttributeDiff` and `ResourceComparison` classes rather than creating new ones
- ✅ **PASS**: Will use existing `apply_ignore_config()` pattern for applying normalization transformations
- 📋 **ACTION**: Must check function-glossary.md for regex utilities before implementing pattern matching
- 📋 **ACTION**: Must check style-guide.md for badge/tooltip CSS before adding normalization UI elements

### Principle II: Shared Data Model Is Canonical
- ✅ **PASS**: Will extend canonical AttributeDiff entity with `ignored_due_to_normalization` field
- ✅ **PASS**: Will add NormalizationConfig entity to `.specify/memory/data_model.md`
- ✅ **PASS**: Will extend IgnoreConfig entity definition with `normalization_config_path` field
- 📋 **ACTION**: Must update data_model.md BEFORE implementing new fields

### Principle III: Live Testing Is Mandatory
- 📋 **ACTION**: Must execute live tests with real Terraform plan JSON files containing environment-specific differences
- 📋 **ACTION**: Must validate normalization patterns reduce differences in HTML report
- 📋 **ACTION**: Must test with actual normalizations.json from az-env-compare-config repo patterns
- 📋 **ACTION**: Must verify verbose logging mode outputs before/after values correctly

### Principle IV: Commit After Every User Story
- 📋 **ACTION**: Must commit after US1 (name normalization) is complete with tests passing
- 📋 **ACTION**: Must commit after US2 (resource ID normalization) is complete with tests passing  
- 📋 **ACTION**: Must commit after US3 (combined ignore tracking UI) is complete with tests passing

### Principle V: User-Facing Features Require End-to-End Testing
- 📋 **ACTION**: Must create E2E tests for `--config` flag with normalization_config_path field
- 📋 **ACTION**: Must test CLI with actual normalizations.json file and verify output
- 📋 **ACTION**: Must test error messages when normalization config is invalid (malformed JSON, invalid regex, file not found)
- 📋 **ACTION**: Must test verbose logging flag shows normalization operations in console output

### Principle VI: Python Development Must Use Virtual Environments
- ✅ **PASS**: Development already in virtual environment (venv/ directory exists)
- 📋 **ACTION**: All pytest commands must be run with venv activated
- 📋 **ACTION**: All pip installs (if any new dependencies) must be in venv

### Gate Status: ✅ READY TO PROCEED

All constitution principles align with feature design. No violations detected. Action items will be tracked in tasks.md during implementation.

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
│   └── analyze_plan.py        # CLI entry point (will parse normalization config path)
├── core/
│   └── multi_env_comparator.py # ResourceComparison, AttributeDiff (will add normalization logic)
├── lib/
│   ├── ignore_utils.py        # Ignore config utilities (pattern for normalization loader)
│   ├── normalization_utils.py # NEW: Normalization config loader and pattern applier
│   ├── html_generation.py     # CSS/HTML generation (will update badge tooltip)
│   └── diff_utils.py          # Diff highlighting utilities (existing)
└── security/
    └── obfuscation.py         # Sensitive data handling (existing)

tests/
├── e2e/
│   ├── test_e2e_multi_env.py        # Existing multi-env E2E tests
│   └── test_e2e_normalization.py    # NEW: End-to-end normalization tests
├── unit/
│   ├── test_ignore_utils.py         # Existing ignore config tests (pattern to follow)
│   └── test_normalization_utils.py  # NEW: Unit tests for normalization
└── fixtures/
    └── normalizations_test.json     # NEW: Test normalization config

examples/
├── ignore_config.example.json   # Existing ignore config example
└── normalizations.json          # NEW: Example normalization patterns (pseudo-copy from az-env-compare-config)

docs/
├── function-glossary.md         # Will document new normalization functions
└── style-guide.md               # Will document updated badge/tooltip styles

.specify/
└── memory/
    └── data_model.md            # Will add NormalizationConfig entity
```

**Structure Decision**: Single Python project with CLI (Option 1). This feature extends existing `lib/` utilities and `core/` comparison logic. New file `normalization_utils.py` follows the pattern established by `ignore_utils.py`. HTML generation updates in `html_generation.py`, comparison logic updates in `multi_env_comparator.py`.

## Complexity Tracking

No constitution violations detected. All principles aligned with feature design.

---

## Planning Artifacts Generated

### Phase 0: Research (Complete)
✅ **[research.md](research.md)** - All technical decisions documented:
- Normalization config structure (mirrors ignore_utils.py pattern)
- Regex pattern application strategy (first-match-wins, ordered)
- Integration point (after diff computation, before filtering)
- Type handling rules (string values only)
- Name vs ID normalization (two-phase based on attribute name)
- Tracking approach (extend AttributeDiff with normalization flag)
- Logging strategy (summary stats + optional verbose mode)
- Error handling (fail fast with detailed messages including location)
- Performance optimization (pre-compile patterns, lazy normalization)
- Example patterns (from az-env-compare-config reference)
- Testing strategy (unit + E2E + live testing)

### Phase 1: Design & Contracts (Complete)
✅ **[data-model.md](data-model.md)** - Entities defined:
- **NormalizationConfig**: Store pre-compiled patterns (name_patterns, resource_id_patterns)
- **NormalizationPattern**: Encapsulate compiled regex + replacement
- **AttributeDiff** (extended): Added `ignored_due_to_normalization`, `normalized_values`
- **ResourceComparison** (extended): Added `normalization_config` field
- **IgnoreConfig** (schema extended): Added `normalization_config_path` field
- Data flow documented: Configuration → Comparison → Normalization → Output

✅ **[contracts/normalization-config-schema.md](contracts/normalization-config-schema.md)** - JSON schema specification:
- Root object structure: `name_patterns`, `resource_id_patterns`
- Pattern object fields: `pattern` (regex), `replacement`, `description` (optional)
- Validation rules: Valid JSON, compilable regex, required fields
- Error handling: File not found, malformed JSON, invalid regex, missing fields
- Integration with ignore_config.json via `normalization_config_path`
- Complete examples: Basic, standard, advanced Azure patterns
- Testing requirements and edge cases
- Best practices: pattern ordering, regex testing, documentation

✅ **[quickstart.md](quickstart.md)** - User guide:
- Quick start (3-step setup: create config, reference in ignore config, run comparison)
- Use cases: Environment name normalization, subscription ID normalization, combined ignore+normalization
- CLI usage: Basic comparison, verbose logging, text output
- Configuration examples: Minimal, standard, advanced
- HTML report features: Badge indication, tooltip details, summary statistics
- Troubleshooting: Normalization not applied, invalid regex, file not found, patterns not matching, performance
- Best practices: Start simple, document patterns, test before adding, version control, review periodically
- Integration workflow: Assessment → config creation → testing → iteration
- Complete example: End-to-end workflow with commands

✅ **Canonical Data Model Updated** - `.specify/memory/data_model.md`:
- Added Feature 007 section with NormalizationConfig, NormalizationPattern entities
- Documented extensions to AttributeDiff, ResourceComparison, IgnoreConfig
- Updated last modified date to 2026-01-15

✅ **Agent Context Updated** - `.github/agents/copilot-instructions.md`:
- Added Python 3.9+ language
- Added Python stdlib (json, re, pathlib) framework
- Added JSON files database type
- Feature technology stack now documented for agent awareness

---

## Next Steps

**Planning Complete** ✅

The `/speckit.plan` command has completed Phases 0-1:
- ✅ Phase 0: Research (resolved all technical unknowns)
- ✅ Phase 1: Design & Contracts (data model, schema, quickstart guide)
- ✅ Agent context updated
- ✅ Canonical data model updated

**Ready for Task Generation**:

Run `/speckit.tasks` to generate implementation tasks from this plan and spec.

The tasks will break down the 3 user stories (P1: name normalization, P2: resource ID normalization, P3: combined tracking UI) into concrete, testable implementation steps with:
- File creation/modification tasks
- Unit test tasks
- End-to-end test tasks
- Live testing tasks (Constitution Principle III)
- Documentation update tasks
- Commit points after each user story (Constitution Principle IV)
