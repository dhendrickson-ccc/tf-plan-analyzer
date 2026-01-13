<!--
SYNC IMPACT REPORT
==================
Version: 1.3.0 → 1.4.0 (MINOR: Added Principle V - User-Facing Features Require End-to-End Testing)
Modified Principles: N/A
Added Sections:
  - Principle V: User-Facing Features Require End-to-End Testing
Removed Sections: N/A
Templates Status:
  ✅ plan-template.md - Constitution Check will include Principle V gate
  ✅ tasks-template.md - Already structured to support end-to-end test tasks per user story
  ✅ spec-template.md - Independent Test scenarios already cover this pattern
Follow-up TODOs:
  - Future features with CLI flags or config files must include end-to-end test tasks
  - Test examples should demonstrate CLI invocation patterns with different flag combinations
  - Config file testing should validate schema, defaults, and edge cases
Amendment Rationale:
  - Unit tests alone don't validate user-facing contract points (CLI flags, config files, API parameters)
  - Integration gaps between internal logic and user-facing interfaces cause production bugs
  - End-to-end tests exercise the complete path from user input to system behavior
  - Ensures CLI flags, config files, and other user interfaces work as documented
  - Validates that internal changes don't break external contracts
  - Particularly critical for tools like tf-plan-analyzer with multiple CLI flags (--html, --config, --tf-dir, -v)

Previous Amendments:
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

**Version**: 1.4.0 | **Ratified**: 2026-01-05 | **Last Amended**: 2026-01-13