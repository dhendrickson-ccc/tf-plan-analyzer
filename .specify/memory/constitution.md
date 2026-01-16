<!--
SYNC IMPACT REPORT
==================
Version: 1.4.0 → 1.5.0 (MINOR: Added Principle VI - Python Development Must Use Virtual Environments)
Modified Principles: N/A
Added Sections:
  - Principle VI: Python Development Must Use Virtual Environments
Removed Sections: N/A
Templates Status:
  ✅ plan-template.md - Constitution Check will include Principle VI gate
  ✅ tasks-template.md - Setup phase already includes environment preparation tasks
  ✅ spec-template.md - Technical constraints already cover dependency management
Follow-up TODOs:
  - Agents must verify virtual environment activation before executing Python commands
  - Task definitions for Python projects should include explicit venv setup/activation steps
  - CI/CD pipelines should validate virtual environment usage in automated workflows
Amendment Rationale:
  - Virtual environments isolate project dependencies from system Python packages
  - Prevents version conflicts between different projects on the same machine
  - Ensures reproducible builds with locked dependency versions
  - Avoids polluting system Python installation with project-specific packages
  - Enables testing across different Python versions without system-level changes
  - Critical for maintaining clean development environments and preventing "works on my machine" issues

Previous Amendments:
  v1.3.0 → 1.4.0 (2026-01-13): Added Principle V - User-Facing Features Require End-to-End Testing
  v1.2.0 → 1.3.0 (2026-01-07): Materially expanded Principle III - Agent Must Execute Live Tests
  v1.1.0 → 1.2.0 (2026-01-06): Added Principle IV - Commit After Every User Story
  v1.0.0 → 1.1.0 (2026-01-06): Added Principle III - Live Testing Is Mandatory
-->

# Constitution

## Core Principles

### I. Code Duplication Prohibited

Code reuse is mandatory to ensure maintainability, consistency, and reduced technical debt.

**Rules**:
- You MUST search for existing functions before creating a new one
- If there are no functions to be reused, then a new one MAY be introduced
- Duplicate implementations of the same logic are strictly prohibited
- Shared utilities MUST be extracted to common modules

**Rationale**: Duplicated code leads to inconsistent behavior, increased maintenance burden, and bugs when fixes are applied to only one copy. This principle ensures a single source of truth for each piece of functionality.

#### Function Glossary Reference

Before creating new functions, consult `docs/function-glossary.md` to:
- Search for existing functions that solve the same problem
- Understand parameter signatures and return types of available utilities
- Review usage examples for proper integration patterns
- Identify which module (lib, core, security, cli) should house new functionality

The glossary documents all 23+ public functions across src/ with:
- Detailed descriptions and parameter documentation
- Comprehensive usage examples with actual code
- Performance notes and security considerations
- Related functions and cross-references

**Quick Reference - Commonly Reused Functions**:
- `generate_full_styles()` - Complete CSS for HTML reports
- `highlight_json_diff()` - Character-level diff highlighting with sensitive field marking
- `load_ignore_config()` - Load and validate ignore configuration
- `safe_read_file()` / `safe_write_file()` - Safe file I/O with error handling
- `load_json_file()` - Load and parse JSON files
- `filter_ignored_fields()` - Recursively remove ignored fields from nested dicts

#### Style Guide Reference

Before implementing new UI components for HTML reports, consult `docs/style-guide.md` for:
- Color palette with exact hex codes for semantic colors (primary, success, warning, error)
- Typography specifications (font families, sizes, weights, line heights)
- Spacing system (padding, margin, border radius, gap values)
- CSS class reference with copy-paste ready examples
- Component patterns for common UI elements (cards, badges, buttons, expandable sections)
- Layout guidelines (grid patterns, flexbox, responsive breakpoints)

**Purpose**: The style guide ensures visual consistency across all HTML reports (single-plan analysis, multi-environment comparison, sensitive data obfuscation) and prevents developers from creating divergent or conflicting styles. All UI-related values MUST reference the style guide to maintain a cohesive design system.

### II. Shared Data Model Is Canonical

The shared data model serves as the single source of truth for all data structures in the project.

**Rules**:
- The shared data model MUST be maintained at `.specify/memory/data_model.md`
- Before introducing, modifying, or duplicating any data structure, you MUST review the existing data model
- If the required data already exists in the data model, it MUST be reused
- If the required data does not exist, it MUST be added to `data_model.md` before being used elsewhere
- All feature specifications MUST reference the canonical data model for entity definitions

**Rationale**: A canonical data model prevents schema drift, ensures consistency across modules, and provides a single reference point for understanding data relationships. This principle eliminates ambiguity about data structures and prevents duplicated or conflicting definitions.

### III. Live Testing Is Mandatory

All features MUST be validated against real production-like environments, not just unit tests or synthetic data. The implementing agent MUST execute live tests and validate results.

**Rules**:
- Every feature specification MUST define Independent Test scenarios that use real external systems (APIs, databases, cloud resources, etc.)
- Implementation plans MUST include a dedicated Live Testing/Validation phase
- The agent MUST execute live tests against actual external systems with real data or representative test data
- The agent MUST validate live test results and document evidence (output files, logs, screenshots, metrics)
- Live test execution tasks MUST be included in the tasks.md file with explicit commands and expected outcomes
- The agent MUST analyze live test results for correctness, errors, and edge cases
- Bugs discovered during live testing MUST be fixed before the feature is considered complete
- The agent MUST NOT proceed to subsequent user stories until live tests for the current story pass validation
- Features that cannot be live tested MUST justify the exception in writing and document alternative validation approaches

**Rationale**: Unit tests and mocked environments miss real-world edge cases, API behavior differences, and integration issues. Live testing with actual external systems reveals bugs that synthetic tests cannot detect. The drift detection feature (001) demonstrates this principle: live Azure testing with 217 real resources uncovered a critical case-sensitivity bug that unit tests missed. Without live validation, this bug would have shipped to production. Requiring the agent to execute and validate tests (not just define them) ensures validation actually occurs and is not deferred or skipped.

### IV. Commit After Every User Story

Each user story must be committed to a git branch when it is complete.

**Rules**:
- A user story is not considered complete until it is committed to a git branch
- Work on a new user story MUST NOT begin until the previous story is committed
- Commits MUST NOT span multiple user stories
- Completed work MUST NOT remain uncommitted across story boundaries

**Rationale**: Requiring a commit after each user story enforces clear completion boundaries, preserves a clean and traceable history, and prevents unrelated changes from being mixed together. This practice improves reviewability, supports reliable rollback and debugging, and keeps development aligned with incremental delivery.

### V. User-Facing Features Require End-to-End Testing

Features that provide user-facing interfaces (CLI flags, configuration files, API endpoints, environment variables) MUST include end-to-end tests that exercise the complete path from user input to system behavior.

**Rules**:
- Features introducing or modifying CLI flags MUST include tests that invoke the CLI with those flags and validate the resulting behavior
- Features introducing or modifying configuration files MUST include tests that load actual config files and verify they control system behavior correctly
- Features introducing or modifying API endpoints MUST include contract tests that call the endpoint with various inputs and validate responses
- End-to-end tests MUST use the actual user-facing interface (not just call internal functions directly)
- End-to-end tests MUST validate both success cases and error cases (invalid inputs, missing config, malformed data)
- End-to-end tests MUST verify that changes to internal implementation don't break the external contract
- Tests MUST cover at least: default behavior, common use cases, and critical edge cases
- For tools with multiple user-facing options, tests MUST include representative combinations of those options

**Rationale**: Internal unit tests validate logic but don't catch integration bugs between internal components and user-facing interfaces. End-to-end tests ensure the complete user journey works correctly. For example, a CLI tool might have perfect internal logic but fail if argument parsing, flag validation, or output formatting is broken. Configuration files might have schema errors or default value bugs that unit tests miss. This principle is particularly critical for tools like tf-plan-analyzer with multiple CLI flags (--html, --config, --tf-dir, -v) where combinations of flags must work correctly together. End-to-end tests serve as living documentation of how users interact with the system and prevent regressions in the user contract.

### VI. Python Development Must Use Virtual Environments

All Python development MUST occur within isolated virtual environments to ensure dependency isolation, reproducibility, and clean system state.

**Rules**:
- Agents MUST activate a Python virtual environment before executing any Python commands (pip, pytest, python scripts, etc.)
- The virtual environment MUST be created using venv, virtualenv, or equivalent tools
- Virtual environment activation MUST be verified before running tests, installing packages, or executing application code
- System Python MUST NOT be used directly for project development
- Virtual environment setup MUST be documented in project README or setup instructions
- Agents MUST use commands like `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows) before Python operations
- When running terminal commands that invoke Python, agents MUST ensure the virtual environment is activated first
- Project dependencies MUST be installed within the virtual environment, not system-wide

**Rationale**: Virtual environments prevent dependency conflicts between projects sharing the same machine, ensure reproducible builds by isolating package versions, and avoid polluting the system Python installation with project-specific dependencies. This is critical for maintaining clean development environments and preventing "works on my machine" issues caused by conflicting package versions or missing dependencies. Using virtual environments is a Python best practice that ensures consistency across development, testing, and production environments.


## Development Workflow

### Feature Development Process

All features MUST follow the speckit workflow:

1. **Specification** (`/speckit.specify`): Create feature spec with user stories and requirements
2. **Planning** (`/speckit.plan`): Generate implementation plan with technical decisions
3. **Data Modeling**: Define or reference entities in `.specify/memory/data_model.md`
4. **Task Generation** (`/speckit.tasks`): Create actionable, dependency-ordered task list
5. **Implementation** (`/speckit.implement`): Execute tasks in phases
6. **Analysis** (`/speckit.analyze`): Validate consistency and alignment

### Documentation Standards

- Each feature MUST maintain documentation in `specs/[###-feature-name]/`
- Plans MUST include a Constitution Check section verifying alignment with these principles
- Data entities MUST be documented in the canonical data model before implementation
- All code MUST include clear comments explaining non-obvious logic

### Quality Gates

- Code duplication checks MUST pass before merge
- Data structures MUST be validated against the canonical data model
- Constitution compliance MUST be verified during code review
- All principles are enforceable through automated checks where possible

## Governance

This constitution supersedes all other development practices and guidelines.

**Amendment Process**:
- Amendments require explicit documentation in this file
- Version MUST be incremented according to semantic versioning:
  - MAJOR: Backward-incompatible governance or principle removals/redefinitions
  - MINOR: New principles or materially expanded guidance
  - PATCH: Clarifications, wording, or non-semantic refinements
- All amendments MUST include rationale and effective date
- Dependent templates and scripts MUST be updated to reflect amendments

**Compliance**:
- All feature plans MUST include a Constitution Check gate
- Code reviews MUST verify adherence to these principles
- Violations MUST be justified in the Complexity Tracking section of plan.md
- Unjustified violations MUST be corrected before merge

**Living Document**:
- This constitution evolves with the project
- Regular reviews SHOULD be conducted as the project matures
- Feedback from development experience SHOULD inform amendments

**Version**: 1.5.0 | **Ratified**: 2026-01-05 | **Last Amended**: 2026-01-15