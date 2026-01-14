# Feature Specification: Character-Level Diff Highlighting for Multi-Environment Comparison

**Feature Branch**: `002-char-level-diff`  
**Created**: January 13, 2026  
**Status**: Draft  
**Input**: User description: "I want the lines of the diff to be highlighted to show differences at the individual character level instead of at the configuration item level. This works for before and after in the report function, I want to make it work in the compare function"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Character-Level Diff in HTML Comparison Reports (Priority: P1)

When viewing a multi-environment comparison HTML report, users need to see exactly which characters differ between environments' resource configurations, not just that the configurations differ.

**Why this priority**: This is the core value - without character-level highlighting, users must manually compare large JSON blocks to find subtle differences. This is the primary pain point the feature addresses.

**Independent Test**: Generate a multi-environment comparison HTML report with two environments that have resources with subtle configuration differences (e.g., "t2.micro" vs "t2.small"). Verify that only the differing characters are highlighted in the HTML output.

**Acceptance Scenarios**:

1. **Given** two environments with a resource where only a single field value differs, **When** user generates HTML comparison report, **Then** the HTML should show character-level highlighting on the specific field value that differs, not highlight the entire JSON block
2. **Given** two environments with a resource where multiple field values differ, **When** user views the HTML report, **Then** each differing value should have character-level highlighting showing exactly which characters changed
3. **Given** two environments with identical resource configurations, **When** user views the HTML report, **Then** the configuration should display without any highlighting (shown as identical)
4. **Given** three or more environments with a resource where configs differ, **When** user views HTML report, **Then** each environment column should show character-level highlighting relative to the baseline (first environment or common config)

---

### User Story 2 - Side-by-Side Character Comparison for Similar Lines (Priority: P2)

When configuration values are similar but not identical (e.g., "instance_type": "t2.micro" vs "instance_type": "t2.small"), users need to see the changes aligned character-by-character to understand what specifically changed.

**Why this priority**: This enhances the core functionality by making subtle differences even more visible through alignment and character-level diff highlighting, similar to how git diff works.

**Independent Test**: Create a comparison with resources that have similar but different string values. Verify that similar lines use character-level diff highlighting with visual indicators for insertions/deletions.

**Acceptance Scenarios**:

1. **Given** two environments where a string value has characters added in the middle, **When** viewing HTML report, **Then** the added characters should be highlighted with a distinct color (e.g., green background)
2. **Given** two environments where a string value has characters removed, **When** viewing HTML report, **Then** the removed characters should be shown in the "before" context with distinct highlighting (e.g., red background)
3. **Given** two environments with string values that are >50% similar, **When** viewing HTML report, **Then** character-level diff is applied; otherwise fall back to line-level highlighting

---

### Edge Cases

- What happens when comparing configurations with deeply nested JSON structures (3+ levels deep)? **CLARIFIED:** Character-level diff applies to all leaf values at any nesting depth.
- How does the system handle very long string values (>200 characters)? **CLARIFIED:** Apply character-level diff normally and allow HTML to wrap long lines naturally (no truncation or special handling).
- What happens when one environment has a field that doesn't exist in another? **CLARIFIED:** Show field-level addition/deletion (entire line highlighted as added/removed), not character-level diff, since there's no corresponding text to compare.
- How does character-level diff interact with sensitive value masking? Masked values ([SENSITIVE]) should not show character diffs.
- What happens when comparing more than 3 environments? **CLARIFIED:** First environment (leftmost column) serves as the baseline. All other environments show character-level diffs relative to the first environment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply character-level diff highlighting when displaying resource configurations in multi-environment comparison HTML reports
- **FR-002**: System MUST use the same character-level diff algorithm currently used in the `report` subcommand's `highlight_json_diff()` function in `generate_html_report.py`
- **FR-003**: System MUST highlight only the characters that differ between environment configurations, not entire JSON blocks
- **FR-004**: System MUST maintain visual alignment between environment columns when showing character-level diffs
- **FR-004a**: System MUST use the first environment (leftmost column) as the baseline for all comparisons
- **FR-004b**: System MUST display the baseline environment (first column) as plain JSON without highlighting
- **FR-004c**: System MUST display all non-baseline environments (columns 2, 3, 4, etc.) with character-level diff highlighting relative to the baseline
- **FR-005**: System MUST apply character-level diff only to lines that are >50% similar (using `difflib.SequenceMatcher` ratio), falling back to line-level highlighting for completely different lines
- **FR-005a**: System MUST apply character-level diff to leaf values at any nesting depth (no depth restrictions)
- **FR-006**: System MUST display identical configurations without highlighting (preserve current "identical" display behavior)
- **FR-007**: System MUST support character-level diff for all JSON value types (strings, numbers, booleans) when serialized
- **FR-008**: System MUST preserve existing CSS classes for diff highlighting (`.added`, `.removed`, `.unchanged`)
- **FR-009**: System MUST integrate with existing collapsible resource blocks without breaking expand/collapse functionality
- **FR-010**: Character-level diff MUST NOT apply to sensitive values that are masked with `[SENSITIVE]` markers
- **FR-011**: When a field exists in one environment but not another, system MUST highlight the entire field line as added/removed (not character-level diff)
- **FR-012**: System MUST allow long string values (>200 characters) to wrap naturally in HTML without truncation or special handling

### Key Entities *(include if feature involves data)*

- **ResourceComparison**: Existing entity that holds configurations from multiple environments; will need new method to generate character-level diffs for HTML output
- **DiffHighlight**: New concept representing character-level differences between two configuration strings, including spans of identical/added/removed characters
- **EnvironmentConfigPair**: Logical pairing of configurations from two environments for diff generation (may be implicit, not a class)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the exact characters that differ between environment configurations within 5 seconds of viewing a comparison report
- **SC-002**: Character-level diff highlighting is visually consistent with the existing `report` subcommand's diff display (same colors, same highlighting logic)
- **SC-003**: HTML comparison reports load and render without performance degradation for plans containing up to 100 resources across 5 environments
- **SC-004**: 100% of existing multi-environment comparison tests continue to pass (no regression)
- **SC-005**: Character-level diffs correctly identify differences in at least 95% of test cases with subtle configuration changes (measured by test coverage)

## Clarifications

### Session 2026-01-13

- Q: Which environment serves as the baseline for comparison? → A: First environment (leftmost column) is always the baseline
- Q: How should highlighting be displayed across multiple columns? → A: First environment shows plain JSON (no highlighting), all other environments show character-level diffs relative to first environment
- Q: How should missing fields be handled when one environment has a field that another doesn't? → A: Highlight the entire field line as added/removed (field-level highlighting), not character-level diff
- Q: How should very long string values (>200 characters) be handled? → A: Apply character-level diff normally, allow HTML to wrap long lines naturally (no special handling)
- Q: Should character-level diff apply at all nesting depths for deeply nested JSON? → A: Yes, apply character-level diff to all leaf values at any nesting depth

## Assumptions

- The existing `highlight_json_diff()` function in `generate_html_report.py` provides the correct character-level diff logic and can be reused or adapted
- Multi-environment comparisons will continue to use columnar display (not side-by-side "before/after" style)
- Users want character-level diff applied to all differing resources, not as an opt-in feature
- Character-level diff highlighting is primarily valuable in HTML output; text output can remain as-is (config-level display)

## Constraints

- Must not break existing multi-environment comparison functionality
- Must maintain backward compatibility with existing HTML report structure
- CSS and JavaScript changes must work in modern browsers (Chrome, Firefox, Safari, Edge - last 2 versions)
- Performance must remain acceptable (HTML generation <10 seconds for 100 resources across 5 environments)

## Out of Scope

- Character-level diff in text output (verbose mode) - will continue showing full JSON configs
- Interactive diff toggling (switching between character-level and config-level views)
- Custom diff algorithms beyond what's in `difflib.SequenceMatcher`
- Diff highlighting for non-JSON configuration formats
- Real-time diff highlighting (all highlighting done during HTML generation)

## Dependencies

- Existing `generate_html_report.py` - contains reference implementation of `highlight_json_diff()`
- Existing `multi_env_comparator.py` - needs modification to generate character-level diffs
- Python `difflib` library - provides `SequenceMatcher` for similarity detection
- Python `html` module - for proper escaping of highlighted HTML content

## Technical Notes

### Current Implementation Analysis

The `report` subcommand uses `highlight_json_diff()` in `generate_html_report.py` (lines 36-120) which:
1. Converts JSON to formatted strings
2. Uses `difflib.SequenceMatcher` to compare line-by-line
3. Applies character-level highlighting for lines that differ but are similar (>50% match)
4. Returns HTML strings with `<span>` tags for highlighting

The `compare` subcommand currently (in `multi_env_comparator.py` lines 470-476):
1. Displays each environment's config as plain JSON (`json.dumps()`)
2. Shows entire config blocks without any diff highlighting
3. Uses `<pre class="config-json">` tags for display

### Proposed Approach

1. Extract or import the `highlight_json_diff()` logic from `generate_html_report.py`
2. Modify `MultiEnvReport.generate_html()` to apply character-level diff when displaying configs
3. For each resource with differences:
   - Compare each environment's config against a baseline (first environment or pairwise)
   - Apply `highlight_json_diff()` to generate highlighted HTML
   - Replace plain `<pre>` blocks with highlighted versions
4. Ensure CSS classes (`.added`, `.removed`, `.unchanged`) are already defined in the HTML template
5. Add test cases covering character-level diff scenarios

## Questions for Clarification

None - the feature is well-defined based on existing `report` functionality.
