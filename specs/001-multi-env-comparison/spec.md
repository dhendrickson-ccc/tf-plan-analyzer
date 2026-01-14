# Feature Specification: Multi-Environment Terraform Plan Comparison

**Feature Branch**: `001-multi-env-comparison`  
**Created**: 2026-01-13  
**Status**: Draft  
**Input**: User description: "I want to create a new function of this tool that will take in multiple terraform plan json files and then do a diff on all resources across all 3. The focus should be the 'before' state. Diffing and Highlighting should be the same. The report should focus on highlighting what is different about the 3 environments so that we can get a baseline across all 3 and easily determine differences at a config level. Data should be shown in columns, 1 per environment instead of 'before' and 'after' columns. I should be able to specify the plans via the CLI"

## Clarifications

### Session 2026-01-13

- Q: When comparing multiple environments, how should the tool handle resources that have been renamed or moved between environments (same configuration but different resource address)? → A: Treat renamed resources as completely separate (one resource missing, one new resource)
- Q: What should the minimum number of environments be for multi-environment comparison mode? The spec mentions 2+ but User Story 4 suggests rejecting single files in comparison mode. → A: Minimum 2 environments (allow comparing just 2 plans when using --compare flag). If no compare mode is passed but multiple plans are provided, fail with error.
- Q: How should the HTML report display deeply nested configuration structures (e.g., complex objects with 10+ levels of nesting) in the columnar layout? Wide nested data could make columns unreadable. → A: Collapse nested structures by default with expand/collapse controls
- Q: When using --tf-dir for HCL resolution in multi-environment mode, should the tool expect a single Terraform directory or separate directories per environment? → A: Single directory - all environments use the same HCL with different .tfvars files (specify via --tfvars-files flag)
- Q: How should the comparison report handle sensitive values across environments? Should it show if the sensitive value differs between environments, or always mask them? → A: Respect existing --show-sensitive flag behavior - mask by default, show actual values if flag is used. Highlighting must still indicate when masked sensitive values differ across environments.
- Q: Should the CLI use flag-based mode switching (--compare) or subcommand-based interface (like AWS CLI)? → A: Subcommand-based interface for isolation. Use `analyze_plan.py report <plan>` for single-plan analysis and `analyze_plan.py compare <plan1> <plan2> ...` for multi-environment comparison. This provides clear separation of concerns and distinct functionality.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Multi-Environment Comparison (Priority: P1) 🎯 MVP

A DevOps engineer has Terraform plan files for dev, staging, and production environments and wants to verify configuration consistency across all three environments to identify drift and ensure parity.

**Why this priority**: This is the core value proposition - being able to compare multiple environments side-by-side is the fundamental capability that doesn't exist in the current tool. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by running the tool with 2-3 plan files and viewing the HTML report showing resources in columns by environment, highlighting differences in configuration values.

**Acceptance Scenarios**:

1. **Given** I have plan files for dev, staging, and prod environments, **When** I run `python analyze_plan.py compare dev.json staging.json prod.json --html`, **Then** I see an HTML report with resource configurations in columns (one per environment) showing the "before" state
2. **Given** I have a single plan file, **When** I run `python analyze_plan.py report dev.json --html`, **Then** the tool operates in standard mode showing before/after columns for that single plan
3. **Given** multiple plan files with the same resource defined differently, **When** I view the comparison report, **Then** configuration differences are highlighted with the same diff styling as the current tool
4. **Given** a resource exists in only 2 of 3 environments, **When** I view the comparison, **Then** the missing environment column shows "N/A" or similar indicator
5. **Given** identical resource configuration across all environments, **When** I view the comparison, **Then** the resource is shown but differences are not highlighted (baseline confirmed)

---

### User Story 2 - Environment Labeling and Ordering (Priority: P2)

A DevOps engineer wants to control how environments are labeled in the report and the order they appear in columns to match their mental model (e.g., dev | staging | prod).

**Why this priority**: Enhances usability and allows the tool to adapt to different naming conventions and organizational standards. Not critical for MVP but significantly improves user experience.

**Independent Test**: Can be tested by providing custom environment names via CLI flags and verifying they appear in the report in the specified order and with the specified labels.

**Acceptance Scenarios**:

1. **Given** I specify `--env-names "Development,Staging,Production"`, **When** I view the report, **Then** columns are labeled "Development", "Staging", "Production" instead of using filenames
2. **Given** I provide plans in order `prod.json dev.json staging.json` but specify `--env-order dev,staging,prod`, **When** I view the report, **Then** columns appear in the order: dev, staging, prod
3. **Given** I don't specify environment names, **When** I view the report, **Then** environment names are derived from plan filenames (e.g., "dev-plan.json" → "dev-plan")

---

### User Story 3 - Filter to Show Only Differences (Priority: P3)

A DevOps engineer working with large infrastructure wants to filter the comparison report to show only resources that differ across environments, hiding resources with identical configuration.

**Why this priority**: Improves signal-to-noise ratio for large infrastructures but not essential for initial value delivery. Users can manually scan for highlighted differences in P1.

**Independent Test**: Can be tested by adding `--diff-only` flag and verifying that resources with identical configuration across all environments are excluded from the report.

**Acceptance Scenarios**:

1. **Given** `--diff-only` flag is provided, **When** I view the report, **Then** only resources with configuration differences are shown
2. **Given** `--diff-only` flag and all resources are identical, **When** I view the report, **Then** a summary message states "No configuration differences found across environments"
3. **Given** no `--diff-only` flag, **When** I view the report, **Then** all resources are shown with identical configs displayed in gray (not highlighted)

---

### User Story 4 - Support Variable Number of Environments (Priority: P2)

A DevOps engineer wants to compare anywhere from 2 to 5+ environments (not just exactly 3) to handle different scenarios like comparing only dev/prod or adding QA, UAT environments.

**Why this priority**: Makes the tool flexible for different organizational structures. Should be relatively straightforward if architecture is designed correctly from P1.

**Independent Test**: Can be tested by providing 2, 3, 4, and 5 plan files and verifying the report adapts column count accordingly.

**Acceptance Scenarios**:

1. **Given** I run `compare` subcommand with 2 plan files, **When** I generate the report, **Then** exactly 2 columns are shown
2. **Given** I run `compare` subcommand with 5 plan files, **When** I generate the report, **Then** all 5 environments are shown in separate columns
3. **Given** I run `compare` subcommand with only 1 plan file, **When** I execute the command, **Then** an error message indicates minimum 2 files required and suggests using `report` subcommand for single-plan analysis

---

### User Story 5 - Text Output for Multi-Environment Comparison (Priority: P3)

A DevOps engineer wants to view multi-environment comparison in the terminal without generating HTML, useful for quick checks in CI/CD pipelines or SSH sessions.

**Why this priority**: Nice to have for terminal-based workflows but HTML is sufficient for MVP. Text rendering of multi-column data is less readable anyway.

**Independent Test**: Can be tested by running comparison without `--html` flag and verifying readable text output showing environment differences.

**Acceptance Scenarios**:

1. **Given** no `--html` flag, **When** I run multi-env comparison, **Then** I see text output with environment names and configuration values grouped by resource
2. **Given** terminal width is narrow, **When** viewing text output, **Then** output wraps gracefully or truncates with indicators
3. **Given** `-v` verbose flag, **When** viewing text output, **Then** full configuration details are shown for all environments

---

### Edge Cases

- What happens when the user invokes `analyze_plan.py` with no subcommand? (Should display usage help showing available subcommands)
- What happens when the `compare` subcommand is given only 1 plan file? (Should error with message requiring minimum 2 files)
- What happens when the `report` subcommand is given multiple plan files? (Should error instructing to use `compare` subcommand instead)
- What happens when plan files have different resource types (some resources don't exist in all environments)?
- How does the system handle when the same resource address exists but refers to completely different resource types across environments (misconfiguration)?
- What if plan files are from different Terraform versions or have incompatible schemas?
- How are deeply nested configuration structures displayed in columns (very wide data)? (Answered: collapse with expand/collapse controls)
- What if one plan file is corrupted or invalid JSON?
- How are sensitive values handled in multi-environment comparison? (Answered: respect --show-sensitive flag, highlight differences even when masked)
- What if environment names conflict or are duplicated?
- How does ignore configuration apply across multiple environments (ignored in one, shown in another)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a subcommand-based CLI architecture with `report` and `compare` subcommands (similar to AWS CLI)
- **FR-002**: The `compare` subcommand MUST accept 2 or more Terraform plan JSON files as positional arguments
- **FR-003**: The `report` subcommand MUST accept a single Terraform plan JSON file and maintain all existing single-plan analysis functionality (backward compatibility)
- **FR-004**: System MUST provide clear error messages and usage help when incorrect number of arguments are provided for each subcommand
- **FR-005**: System MUST extract the "before" state from each plan file for comparison (not the "after" state) in the `compare` subcommand
- **FR-006**: System MUST generate an HTML report with resources organized in a table with one column per environment in `compare` mode
- **FR-007**: System MUST provide expand/collapse controls for deeply nested configuration structures in the HTML report to maintain column readability
- **FR-008**: System MUST highlight configuration differences using the same diff styling as the current single-plan analyzer
- **FR-008a**: System MUST apply diff highlighting to sensitive values even when masked, indicating when sensitive values differ across environments while respecting the --show-sensitive flag for actual value display
- **FR-009**: System MUST handle resources that exist in some environments but not others (show N/A or "Not Present")
- **FR-010**: System MUST group resources by resource address (e.g., `aws_instance.web`) and show each environment's configuration side-by-side; resources with different addresses are treated as separate resources even if configuration is similar
- **FR-011**: System MUST use the same HCL resolution logic as the existing tool to resolve "known after apply" values if `--tf-dir` is provided
- **FR-011a**: When using `--tf-dir` with the `compare` subcommand, system MUST support `--tfvars-files` flag to specify different .tfvars files for each environment (same order as plan files) to resolve environment-specific variable values
- **FR-012**: System MUST support custom environment labels via CLI flag (e.g., `--env-names "Dev,Stage,Prod"`) for the `compare` subcommand
- **FR-013**: System MUST derive default environment names from plan filenames if custom names are not provided
- **FR-014**: System MUST allow users to control column ordering via CLI flag or preserve input file order for the `compare` subcommand
- **FR-015**: System MUST apply ignore configuration (if provided) consistently across all environments
- **FR-016**: System MUST display a summary section showing: number of environments, number of resources compared, number of resources with differences
- **FR-017**: System MUST gracefully handle plan files with different resource counts or types without crashing by continuing comparison with available data, logging warnings for schema incompatibilities, and displaying partial results with clear indicators of which environments failed to load
- **FR-018**: The `report` subcommand MUST support all existing flags from the current implementation (--html, --config, --tf-dir, -v, etc.) for backward compatibility

### Key Entities

- **CLISubcommand**: Represents the command routing layer that distinguishes between `report` (single-plan) and `compare` (multi-environment) modes, with isolated argument parsing and validation for each
- **EnvironmentPlan**: Represents a single environment's Terraform plan, including the plan JSON data, environment label, and extracted "before" state resources
- **ResourceComparison**: Represents a single resource address (e.g., `aws_instance.web`) with its configuration across all environments, including which environments have this resource and which don't
- **MultiEnvReport**: Represents the complete comparison report structure containing all ResourceComparisons, environment metadata, and summary statistics
- **ConfigDifference**: Represents a specific configuration attribute that differs across environments, including the attribute path, values per environment, and diff highlighting metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can compare 3 Terraform plan files and generate an HTML report in under 10 seconds for typical infrastructure (under 100 resources)
- **SC-002**: The HTML report correctly highlights all configuration differences that would be visible in a manual side-by-side diff
- **SC-003**: 100% of resources present in at least one environment are included in the comparison report
- **SC-004**: Users can identify configuration drift across environments within 30 seconds of opening the HTML report (validated by timing 3+ users to locate 3 known differences in a 50-resource report with differences highlighted)
- **SC-005**: The tool handles at least 5 environments simultaneously with processing time within 150% of 3-environment baseline (no exponential degradation)
- **SC-006**: Error rate for parsing valid Terraform plan JSON files is 0% (same as current tool)
- **SC-007**: Users can successfully complete a multi-environment comparison workflow on their first attempt without consulting documentation (CLI follows existing tool patterns)
