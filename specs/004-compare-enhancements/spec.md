# Feature Specification: Compare Subcommand Enhancements

**Feature Branch**: `004-compare-enhancements`  
**Created**: 2026-01-14  
**Status**: Draft  
**Input**: User description: "I want to do a new feature, but I want it to consist of multiple smaller features from the report function. If these exist already, please let me know and we can adjust: 1. The ability to Ignore any change that I specify in an ignore file so that it doesn't show up in the diff when I run the compare subcommand. This is done in the report subcommand. 2. Modify the compare subcommand so that the diff only displays changes on a attribute by attribute level such that I only see the attributes that are changing. This will require a change to the UI where the resource is at the top level, then a list of the attributes underneath that. From those attributes, I shouldn't see any attributes where there isn't a change so that we can reduce noise and clutter in the report."

## Clarifications

### Session 2026-01-14

- Q: When a resource has changes in both ignored and non-ignored attributes, how should the resource appear in the summary statistics? → A: Count resource as "different" only if it has non-ignored changes; count as "identical" if all changes are ignored
- Q: For nested attribute changes (e.g., `identity.type` or `settings.config.enabled`), what display format should be used in the attribute-level diff view? → A: Only break down to top-level attributes; nested content below the top level can be displayed as a block (same as current JSON display)
- Q: When displaying a top-level attribute that differs across environments, should the HTML report show values from each environment side-by-side (columns) or in another format? → A: Side-by-side columns (one column per environment, matching current multi-environment comparison design)
- Q: When a user applies ignore rules that filter out some (but not all) attributes from a resource, should the HTML report indicate which attributes were ignored? → A: Show a subtle indicator (e.g., small badge or tooltip) showing "N attributes ignored" at the resource level
- Q: When the `--diff-only` flag is combined with ignore rules and all resources become identical after filtering, what should the exit code be? → A: Exit code 0 with a special summary message distinguishing "no differences" from "differences but all filtered"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ignore File Support for Compare (Priority: P1)

DevOps engineers need to filter out noise from multi-environment comparisons by ignoring known acceptable differences (like environment-specific tags, descriptions, or dynamic block conversions) using the same ignore configuration format already available in the single-plan report subcommand.

**Why this priority**: This is the foundation for cleaner reports. Without ignore functionality, users see hundreds of irrelevant differences that obscure real configuration drift. This delivers immediate value by making existing reports actionable.

**Independent Test**: Can be fully tested by running `compare` with an ignore config file and verifying that specified attributes are excluded from difference detection and HTML output, delivering cleaner, focused reports.

**Acceptance Scenarios**:

1. **Given** a comparison of dev and prod plans where both have different `tags` attributes, **When** I run `compare` with `--config ignore_config.json` containing `global_ignores: {"tags": "reason"}`, **Then** the tags differences are not shown in the output and resources are marked as identical if tags are the only difference.

2. **Given** a comparison with resource-specific ignore rules (e.g., ignore `description` for `azurerm_monitor_metric_alert`), **When** I run compare with the config file, **Then** only the specified attributes for those resource types are ignored.

3. **Given** a comparison with both global and resource-specific ignore rules, **When** I run compare, **Then** both types of rules are applied correctly and the summary statistics reflect the filtered view.

4. **Given** a resource with 3 attributes changed where 2 are ignored, **When** I view the HTML report, **Then** I see an indicator on that resource showing "2 attributes ignored" and only the 1 non-ignored attribute is displayed in the diff.

5. **Given** an ignore config file that doesn't exist, **When** I run compare with `--config nonexistent.json`, **Then** the tool exits with an error message indicating the file was not found.

6. **Given** an ignore config file that doesn't exist, **When** I run compare with `--config nonexistent.json`, **Then** the tool exits with an error message indicating the file was not found.

5. **Given** a valid ignore config file with malformed JSON, **When** I run compare with that config, **Then** the tool exits with an error message indicating JSON parsing failed.

---

### User Story 2 - Attribute-Level Diff View (Priority: P2)

Infrastructure teams reviewing multi-environment comparisons need to see only the specific attributes that differ between environments, rather than entire resource configurations, to quickly identify and remediate configuration drift.

**Why this priority**: While ignore functionality reduces noise, users still see full JSON configurations for resources with differences. Attribute-level view drastically improves readability by showing only what changed, making it easier to spot critical differences.

**Independent Test**: Can be fully tested by running compare on plans with partial differences and verifying that the HTML report shows a structured view with resources as top-level items, expandable attribute lists underneath, and only changed attributes visible.

**Acceptance Scenarios**:

1. **Given** a resource that differs only in the `location` attribute between dev and prod, **When** I view the HTML comparison report, **Then** I see the resource name at the top level, an expandable list of attributes below it, and only the `location` attribute is shown with dev and prod values in side-by-side columns.

2. **Given** a resource with multiple changed attributes (e.g., `sku`, `capacity`, `enabled`), **When** I view the HTML report, **Then** I see each changed attribute listed separately under the resource, with values from each environment displayed in columns.
the entire `identity` object changed), **When** I view the HTML report, **Then** I see "identity" as the top-level changed attribute with the full identity object (before/after) displayed as a block below it.

4. **Given** a resource with deeply nested changes (e.g., changes within `settings.config.advanced`), **When** I view the attribute-level diff, **Then** I see "settings" as the top-level attribute with the full settings object displayed, showing the nested changes within the block.

5. **Given** a resource with list/array changes (e.g., `tags` object added or modified), **When** I view the attribute-level diff, **Then** I see "tags" as the changed attribute with the full tags object displayed showing the difference
5. **Given** a resource with list/array changes (e.g., `tags` added or removed), **When** I view the attribute-level diff, **Then** I see the list items that changed clearly highlighted with added/removed indicators.

6. **Given** a resource that is identical across environments, **When** I expand it in the HTML report, **Then** I see a message indicating "No differences detected" rather than showing all attributes.

---

### User Story 3 - Combined Ignore and Attribute-Level View (Priority: P3)

Power users need to combine ignore rules with attribute-level diff view to create the cleanest possible comparison reports, showing only actionable configuration differences without noise from known acceptable variations.

**Why this priority**: This represents the optimal user experience by combining both features, but each feature independently delivers value. This is the "polish" layer that makes the tool exceptionally powerful.

**Independent Test**: Can be fully tested by running compare with both `--config` ignore rules and verifying that the attribute-level diff view excludes ignored attributes entirely and shows only non-ignored changed attributes.

**Acceptance Scenarios**:

1. **Given** a comparison with ignore rules for `tags` and `description`, **When** I view the attribute-level diff for a resource that has changes in `tags`, `description`, and `location`, **Then** I only see `location` in the changed attributes list (tags and description are filtered out).

2. **Given** a resource where all changed attributes are covered by ignore rules, **When** I view the comparison report, **Then** the resource is marked as identical and does not appear in the diff (if `--diff-only` is used) or shows "No actionable differences" when expanded.

3. **Given** ignore rules that filter out nested attributes (e.g., `identity.user_assigned_identity_ids`), **When** I view the attribute-level diff, **Then** the nested attribute does not appear in the diff even if it has changed.

---

### Edge Cases

- What happens when an ignore rule specifies a non-existent attribute (e.g., typo in attribute name)? → Ignore rule has no effect, no error thrown (fail silently to avoid breaking reports).
- What happens when all attributes of a resource are ignored? → Resource should be marked as identical in summary statistics.
- What happens when a resource exists in only one environment? → Attribute-level diff shows all attributes as "added" or "removed" depending on presence.
- What happens when an attribute value changes from a complex object to null or vice versa? → Show the attribute with clear "before: {object}" and "after: null" representation.
- What happens when comparing 3+ environments with different attribute values across all environments? → Show all environment values side-by-side for each changed attribute.
- What happens when an attribute has a very long value (e.g., 1000+ character connection string)? → Truncate with "show more" functionality or apply wrapping/scrolling in UI.
- What happens when combining `--diff-only` with ignore rules that make all resources identical? → Exit code 0 with message "No actionable differences found (N attributes filtered by ignore rules)" to distinguish from truly identical environments.
- What happens when a top-level attribute changes from a primitive to a complex object? → Show the attribute name with before (primitive value) and after (JSON block) clearly separated.
- What happens when only a deeply nested value within a top-level attribute changes? → The entire top-level attribute is shown as changed, with the full before/after blocks displayed (user can see the nested change within the block).

## Requirements *(mandatory)*

### Functional Requirements

**Ignore File Support (US1):**

- **FR-001**: System MUST accept a `--config` parameter on the compare subcommand that points to an ignore configuration JSON file
- **FR-002**: System MUST support the same ignore configuration format as the report subcommand (global_ignores and resource_ignores)
- **FR-003**: System MUST apply global ignore rules to all resources during difference detection
- **FR-004**: System MUST apply resource-specific ignore rules only to matching resource types
- **FR-005**: System MUST remove ignored attributes from configuration comparison BEFORE detecting differences
- **FR-006**: System MUST recalculate summary statistics (resources_with_differences, resources_consistent) based on filtered configurations, counting resources as "identical" if all their changes are covered by ignore rules and as "different" only if they have non-ignored changes
- **FR-007**: System MUST exit with error code 1 if the config file path is invalid or file does not exist
- **FR-008**: System MUST exit with error code 2 if the config file contains malformed JSON
- **FR-009**: System MUST support ignore rules for nested attributes using dot notation (e.g., "identity.type")
- **FR-010**: System MUST support ignore rules for top-level attributes
- **FR-011**: System MUST display a badge indicator at the resource level showing how many attributes were ignored when ignore rules are applied to that resource (format: "N attributes ignored" where N is the count)
- **FR-012**: System MUST display a special summary message when all resources are identical after filtering: "No differences found (N attributes filtered by ignore rules)" to distinguish from truly identical environments with message "No differences found"

**Attribute-Level Diff View (US2):**

- **FR-013**: System MUST restructure HTML report to show resources as top-level collapsible sections
- **FR-014**: System MUST display only changed top-level attributes under each resource (not full JSON)
- **FR-015**: System MUST show top-level attribute names clearly; nested content within an attribute can be displayed as a block (preserving current JSON display format for nested structures)
- **FR-016**: System MUST display values for each changed top-level attribute in side-by-side columns, with one column per environment (matching current multi-environment comparison layout)
- **FR-017**: System MUST support displaying changes for primitive types (string, number, boolean, null)
- **FR-018**: System MUST support displaying changes for complex types (objects, arrays) with clear visual representation
- **FR-019**: System MUST indicate when a resource has no differences with a clear message (when expanded)
- **FR-020**: System MUST maintain the existing baseline comparison logic (first environment is baseline)
- **FR-021**: System MUST show sensitive value indicators for changed attributes that are marked sensitive
- **FR-022**: System MUST preserve the expand/collapse functionality for resource sections
- **FR-023**: System MUST maintain color-coding for different change types (added, removed, modified)
- **FR-024**: System MUST apply character-level diff highlighting within top-level attribute blocks when the attribute value is a string or simple type
- **FR-025**: System MUST display complex nested structures (objects, arrays) within a top-level attribute using the current JSON block display format

**Combined Functionality (US3):**

- **FR-026**: System MUST exclude ignored attributes from the attribute-level diff view
- **FR-027**: System MUST mark resources as identical in summary statistics if all changed attributes are covered by ignore rules (applying the filtered-view counting approach from FR-006)
- **FR-028**: System MUST work correctly when both `--config` and `--diff-only` flags are used together
- **FR-029**: System MUST exit with code 0 when `--diff-only` is used with ignore rules that make all resources identical

**Backward Compatibility:**

- **FR-030**: System MUST maintain existing compare subcommand functionality when no `--config` flag is provided
- **FR-031**: System MUST maintain existing report subcommand functionality (no changes to report command)
- **FR-032**: System MUST maintain existing text output format (attribute-level view only applies to HTML output)

### Key Entities

- **Ignore Configuration**: JSON file containing global_ignores (attribute name → reason) and resource_ignores (resource type → attributes map), same format as report subcommand
- **Resource Comparison**: Represents a single resource across multiple environments, now with filtered configurations and attribute-level diff detection
- **Attribute Diff**: Represents a single changed attribute with its path, before/after values across environments, and change type
- **Environment Configuration**: Resource configuration for a specific environment, filtered by ignore rules before comparison

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can reduce visible differences in comparison reports by 50%+ using ignore rules on typical infrastructure with environment-specific tags
- **SC-002**: Users can identify the specific changed attributes in a resource in under 5 seconds (vs 30+ seconds scanning full JSON)
- **SC-003**: Attribute-level diff view displays correctly for resources with up to 10 changed attributes without UI performance degradation
- **SC-004**: Ignore file configuration applies correctly to 100% of test cases covering global rules, resource-specific rules, and nested attributes
- **SC-005**: Existing compare functionality remains unchanged when no `--config` flag is used (100% backward compatibility)
- **SC-006**: Combined ignore + attribute-level view correctly filters and displays resources with mixed ignored/non-ignored changes in all test scenarios
- **SC-007**: HTML report loads and renders in under 3 seconds for comparisons with 100+ resources with differences

## Assumptions

- Ignore configuration format from report subcommand is well-documented and stable (based on code review, this is true - see ignore_config.example.json)
- Users understand JSON structure and dot notation for nested attributes (industry standard for DevOps/infrastructure teams)
- HTML report is the primary output format for detailed comparison (text output remains summary-focused)
- Performance target is reports with up to 500 resources (based on existing multi-env comparison feature scope)
- Character-level diff highlighting from 002-char-level-diff feature remains unchanged and works with attribute-level view
- Sensitive value masking from existing compare logic continues to work with attribute-level view

## Dependencies

- Depends on existing `multi_env_comparator.py` ResourceComparison class for difference detection
- Depends on existing ignore configuration parsing logic from report subcommand (`handle_report_subcommand`)
- Depends on existing HTML generation framework in `MultiEnvReport.generate_html()`
- Depends on character-level diff highlighting from feature 002-char-level-diff
- No external library dependencies required (uses existing Python stdlib: json, pathlib, difflib)

## Out of Scope

- Adding ignore functionality to report subcommand (already exists)
- CLI argument parsing for ignore rules (only file-based config supported, matching report subcommand)
- Attribute-level diff view in text output (only HTML output gets this enhancement)
- Interactive filtering/sorting of attributes in HTML report (static HTML only)
- Export of attribute-level diff to JSON format (HTML only)
- Custom diff algorithms beyond existing line/character-level diff
- Ignore rules based on attribute values (only attribute names/paths supported)
- Regex-based ignore patterns (exact attribute name matching only)
- UI redesign beyond attribute-level changes (overall HTML structure remains similar)

## Notes

**Existing Implementation Analysis**:

1. **Ignore Config in Report**: Lines 1833-1865 in analyze_plan.py show ignore config loading and application. This logic can be reused for compare subcommand.

2. **Compare Config Flag**: Line 2503 shows `--config` flag already exists for compare subcommand but is currently not fully implemented (only passed to MultiEnvReport constructor, not applied during difference detection).

3. **Current HTML Structure**: Lines 696-775 in multi_env_comparator.py show HTML generation displays full JSON for each environment. This needs restructuring for attribute-level view.

4. **ResourceComparison Class**: This class in multi_env_comparator.py handles difference detection using `env_configs` and `env_configs_raw`. The `_apply_ignore_config` method exists but only applies to report subcommand.

**Implementation Strategy**:

1. **US1** can be implemented by:
   - Refactoring `_apply_ignore_config()` from report subcommand into a shared utility function
   - Applying ignore rules in `MultiEnvReport.build_comparisons()` before calling `detect_differences()`
   - Updating summary calculation to reflect filtered results

2. **US2** requires:
   - New method to compute attribute-level diffs from `env_configs_raw` 
   - HTML generation refactor to iterate over changed attributes instead of showing full JSON
   - Nested path rendering logic for multi-level attribute changes

3. **US3** naturally emerges from implementing US1 and US2 together with integration testing

**User Clarification Questions**:

None - requirements are clear and can be implemented with reasonable defaults for edge cases.
