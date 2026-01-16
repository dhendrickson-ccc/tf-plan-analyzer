# Feature Specification: Normalization-Based Difference Filtering

**Feature Branch**: `007-normalization-diff-filtering`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Add normalization-based difference filtering to ignore environment-specific formatting differences (like -t- vs -p-, subscription IDs) that are functionally equivalent after normalization"

## Clarifications

### Session 2025-01-15

- Q: Performance baseline clarity - The spec states normalization should degrade performance by "no more than 10%", but the baseline comparison scenario isn't specified. What should the 10% be measured against? → A: 10% measured against same comparison run without normalization config
- Q: Error message detail level - FR-010 requires "clear error messages" for invalid configs, but the expected detail level isn't specified. What information should error messages include? → A: Include problem type, location, and suggestion (e.g., "Invalid regex pattern at name_patterns[2]: unclosed group. Check pattern syntax.")
- Q: Normalization pattern ordering strategy - FR-011 requires resource ID patterns to be applied "in the order specified in the config", but what happens when multiple patterns could match the same text? → A: First-match-wins (stop after first successful replacement per pattern)
- Q: Normalization logging and observability - The spec doesn't specify whether normalization operations should be logged or made observable for debugging. What logging should be provided? → A: Log summary stats always (count of normalizations applied), plus verbose logging with before/after values available optionally for debugging
- Q: Backward compatibility validation approach - The Constraints section states normalization must maintain backward compatibility (comparison works without normalization config), but the validation approach isn't specified. How should backward compatibility be validated? → A: Existing test suite passes with feature disabled (normalization config not provided)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Environment Name Pattern Normalization (Priority: P1)

As a DevOps engineer comparing Terraform plans across environments, I need the tool to ignore environment-specific name suffixes in resource IDs so that resources with the same logical purpose but different environment markers (like `-t-` vs `-p-` or `-test-` vs `-prod-`) don't appear as differences.

**Why this priority**: This is the highest-value normalization pattern. Environment naming conventions create the most noise in multi-environment comparisons, making it hard to spot actual configuration differences. Solving this alone delivers immediate value.

**Independent Test**: Can be fully tested by comparing two environments with resources that have environment suffixes (e.g., `storage-account-t-eastus` vs `storage-account-p-eastus`). After applying name normalization patterns, these should not appear as differences in the comparison report.

**Acceptance Scenarios**:

1. **Given** two environments with resources containing environment suffixes (e.g., `-t-` and `-p-`), **When** normalization patterns are applied to resource names, **Then** differences that only exist due to environment naming are marked as ignored and don't appear in the comparison report
2. **Given** a normalization config file at `examples/normalizations.json` with name patterns, **When** the user references this config via `--config` with a `normalization_config_path` field, **Then** the tool loads and applies the name normalization patterns
3. **Given** resources with both environment-specific names AND actual configuration differences, **When** normalization is applied, **Then** only the name differences are ignored while the configuration differences still appear in the report

---

### User Story 2 - Resource ID Transformation Normalization (Priority: P2)

As a cloud infrastructure engineer, I need the tool to ignore subscription ID, tenant ID, and other Azure-specific identifier differences in resource IDs so that logically identical resources deployed to different Azure subscriptions don't show as differences.

**Why this priority**: After name normalization, subscription/tenant IDs are the next major source of noise. These IDs are environment-specific by nature but don't represent actual configuration drift. This delivers significant value but depends on the normalization infrastructure from P1.

**Independent Test**: Can be fully tested by comparing resources with different subscription IDs in their resource IDs (e.g., `/subscriptions/abc123/.../resource` vs `/subscriptions/xyz789/.../resource`). After applying resource ID normalization, these should not appear as differences.

**Acceptance Scenarios**:

1. **Given** resources with different subscription IDs in their resource IDs, **When** resource ID normalization patterns are applied, **Then** differences that only exist due to subscription ID are marked as ignored
2. **Given** a normalization config with regex patterns for subscription IDs, tenant IDs, and resource group names, **When** these patterns are applied to resource ID attributes, **Then** all matching patterns are replaced with placeholder values before comparison
3. **Given** a deeply nested resource ID with multiple environment-specific components, **When** normalization is applied, **Then** all matching pattern replacements occur in the correct order per the config

---

### User Story 3 - Combined Normalization Ignore Tracking (Priority: P3)

As a user reviewing the comparison report, I want to see a clear indication of how many attributes were ignored due to normalization (separately from config-based ignores) so that I can understand what differences are being filtered and have confidence in the comparison results.

**Why this priority**: This provides visibility and auditability. While the normalization itself is critical (P1/P2), the UI indication is a quality-of-life improvement that helps users trust the tool but isn't required for the core functionality to work.

**Independent Test**: Can be fully tested by comparing environments with both config-ignored and normalization-ignored attributes. The badge should show separate counts (e.g., "5 attributes ignored (3 config, 2 normalized)") and the tooltip should list them separately.

**Acceptance Scenarios**:

1. **Given** a resource with 3 config-ignored attributes and 2 normalization-ignored attributes, **When** the HTML report is generated, **Then** the badge shows "5 attributes ignored (3 config, 2 normalized)"
2. **Given** a resource with only normalization-ignored attributes (no config ignores), **When** hovering over the badge, **Then** the tooltip shows "Normalized:" section with the attribute names
3. **Given** a resource with both types of ignores, **When** hovering over the badge, **Then** the tooltip shows two sections: "Config:" and "Normalized:" with their respective attribute lists

---

### Edge Cases

- What happens when a normalization pattern matches but the resulting normalized values are still different (e.g., pattern normalizes subscription ID but other parts of the resource ID differ)?
  - **Expected**: The difference should still appear in the report since the normalized values don't match
  
- How does the system handle invalid or malformed normalization config files?
  - **Expected**: System should validate the normalization config on load and fail with a clear error message if patterns are invalid regex or config structure is wrong
  
- What happens when normalization_config_path points to a non-existent file?
  - **Expected**: System should fail with a clear error message indicating the file cannot be found
  
- How does the system handle attributes that are both config-ignored AND would be normalization-ignored?
  - **Expected**: Config ignores take precedence (since they're explicit). Count only as config-ignored, not both.
  
- What happens when normalization patterns contain backreferences or complex regex that fails to compile?
  - **Expected**: System should catch regex compilation errors during config load and report them with the pattern index/name

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load normalization patterns from a JSON config file specified via `normalization_config_path` in the ignore config
- **FR-002**: System MUST support name-level normalization patterns (regex find/replace on attribute values)
- **FR-003**: System MUST support resource ID transformation patterns (ordered regex replacements on resource IDs)
- **FR-004**: System MUST apply normalization AFTER diff computation but BEFORE filtering differences
- **FR-005**: System MUST mark attribute differences as ignored if normalized values match exactly
- **FR-006**: System MUST track normalization-ignored attributes separately from config-ignored attributes
- **FR-007**: System MUST display combined ignore counts in the HTML report badge with breakdown by type
- **FR-008**: System MUST provide examples/normalizations.json as a pseudo-copy reference config with path instructions
- **FR-009**: System MUST validate normalization config structure on load (valid JSON, required fields, valid regex patterns)
- **FR-010**: System MUST fail with clear error messages if normalization config is invalid or file not found. Error messages MUST include problem type, location (e.g., field path or pattern index), and suggestion for resolution
- **FR-011**: System MUST apply resource ID transformation patterns in the order specified in the config, using first-match-wins strategy (each pattern attempts replacement once; after first successful replacement for a pattern, proceed to next pattern)
- **FR-012**: System MUST apply normalization to both environment values before comparing (not just one side)
- **FR-013**: Config-ignored attributes MUST take precedence over normalization (if both would apply, count only as config-ignored)
- **FR-014**: System MUST log summary statistics showing total count of normalization-ignored attributes after comparison completes
- **FR-015**: System MUST support optional verbose logging mode that outputs each normalization operation with before/after values for debugging purposes

### Key Entities

- **Normalization Config**: JSON file containing name_patterns and resource_id_patterns arrays
  - `name_patterns`: Array of {pattern: string, replacement: string} for attribute value normalization
  - `resource_id_patterns`: Array of {pattern: string, replacement: string} for resource ID transformation, applied in order with first-match-wins strategy (each pattern replaces once, then moves to next pattern)
  
- **Attribute Difference**: Existing entity, extended with normalization tracking
  - `ignored_due_to_config`: Boolean (existing)
  - `ignored_due_to_normalization`: Boolean (new)
  - `normalized_value`: String (new, optional) - stores normalized value for debugging
  
- **Ignore Config**: Extended to include optional normalization_config_path field
  - `normalization_config_path`: String (new, optional) - path to normalizations.json file

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully load normalization patterns from an external config file and see no errors when patterns are valid
- **SC-002**: Resource differences that only exist due to environment naming patterns (e.g., `-t-` vs `-p-`) completely disappear from the comparison report after normalization
- **SC-003**: Resource ID differences that only exist due to subscription/tenant ID variations completely disappear from the comparison report after normalization
- **SC-004**: The HTML report badge accurately reflects both config-ignored and normalization-ignored counts (e.g., "5 ignored (3 config, 2 normalized)")
- **SC-005**: Users can hover over the ignore badge to see separate lists of config-ignored and normalization-ignored attributes
- **SC-006**: Invalid normalization configs fail immediately with clear error messages indicating the specific problem (missing field, invalid regex, etc.)
- **SC-007**: Comparison performance degrades by no more than 10% when normalization is enabled, measured against the same comparison run without normalization config (baseline: same datasets, environments, and ignore config, only difference is presence/absence of normalization patterns)
- **SC-008**: Summary statistics show total count of normalization-ignored attributes in console output after comparison completes
- **SC-009**: When verbose logging is enabled, users can see individual normalization operations with original and normalized values for troubleshooting pattern effectiveness
- **SC-010**: All existing tests pass when normalization config is not provided, confirming backward compatibility with pre-feature behavior

## Scope

### In Scope

- Loading normalization patterns from external JSON config
- Applying name-level regex normalization to attribute values
- Applying resource ID transformation patterns in specified order
- Tracking normalization-ignored vs config-ignored attributes separately
- Updating HTML report badge and tooltip with normalization ignore counts
- Validating normalization config structure and regex patterns
- Providing examples/normalizations.json as reference implementation
- Extending ignore_config.json schema with normalization_config_path
- Summary statistics logging (count of normalized attributes)
- Optional verbose logging mode for debugging normalization operations

### Out of Scope

- Automatic pattern detection or suggestion (users must provide patterns)
- Normalization of semantic differences beyond string patterns (e.g., equivalent but differently formatted JSON)
- UI for editing normalization patterns (config must be edited manually)
- Normalization pattern testing/validation tools (separate from config validation)
- Performance optimization beyond basic efficiency (advanced caching, parallel normalization)
- Normalization of resource types or module paths (only attribute values and resource IDs)

## Assumptions

- Users have access to the az-env-compare-config repository or similar source for normalization patterns
- Normalization patterns are relatively stable (not changed frequently)
- Regex patterns in normalization config are valid Python regex syntax
- Normalization config file is small enough to load entirely into memory (< 1MB typical)
- Most environments follow consistent naming conventions that can be captured in regex patterns
- Users understand regex syntax well enough to adapt provided patterns to their needs
- The existing ignore config mechanism is understood by users (normalization extends this concept)

## Dependencies

- Existing ignore config infrastructure (IgnoreConfig class, loading mechanism)
- Existing attribute difference tracking (AttributeDiff class)
- Python `re` module for regex pattern compilation and substitution
- Existing HTML badge rendering infrastructure

## Constraints

- Must maintain backward compatibility: comparison works without normalization config (optional feature). Backward compatibility validated by running existing test suite with normalization config not provided - all tests must pass
- Must not modify original attribute values (normalization only for comparison, not stored)
- Must validate regex patterns before use to prevent runtime regex errors
- Must preserve performance: normalization should not significantly slow down large comparisons
- Must follow constitution Principle VI: all Python development in virtual environment
