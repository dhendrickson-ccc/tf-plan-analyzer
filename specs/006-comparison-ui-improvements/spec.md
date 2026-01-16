# Feature Specification: Multi-Environment Comparison UI Improvements

**Feature Branch**: `006-comparison-ui-improvements`  
**Created**: January 15, 2026  
**Status**: Draft  
**Input**: User description: "Improve multi-environment comparison HTML display with better attribute layout, scrollable values, and elegant handling of resources missing from environments"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Attribute Headers with Improved Spacing (Priority: P1)

As a DevOps engineer comparing Terraform configurations across environments, I want each attribute displayed as a prominent header so that I can quickly scan and identify which configuration settings differ, with adequate horizontal spacing to reduce visual clutter and improve readability.

**Why this priority**: This is the foundation for better readability. Without clear attribute headers and spacing, users struggle to parse dense comparison tables, especially when dealing with 100+ resources. This change alone significantly improves usability.

**Independent Test**: Can be fully tested by generating a multi-environment comparison HTML report with 10+ resources having different attributes, then verifying that each attribute appears as a distinct header with sufficient spacing between attribute sections.

**Acceptance Scenarios**:

1. **Given** a multi-environment comparison report with resources having multiple attributes, **When** I view the HTML report, **Then** each attribute name appears as a prominent header (e.g., H3 or similar styling) rather than a table cell
2. **Given** multiple attributes for a single resource, **When** viewing the comparison, **Then** there is clear vertical spacing (minimum 30px margin-bottom) between consecutive attribute sections
3. **Given** long attribute names (e.g., "security_rule_collection"), **When** displayed as headers, **Then** the full name is visible without truncation and does not cause layout issues

---

### User Story 2 - Scrollable Value Containers (Priority: P1)

As a DevOps engineer reviewing complex configuration values (large JSON objects, arrays, or long strings), I want each value displayed in a container with horizontal and vertical scrollbars so that I can view the complete content without it breaking the page layout or requiring excessive scrolling of the entire report.

**Why this priority**: Large JSON objects and arrays currently break page layout or require full-page scrolling. This makes it impossible to compare values side-by-side efficiently. Scrollable containers are critical for usability with real-world Terraform plans.

**Independent Test**: Can be fully tested by comparing plans with large JSON objects (100+ lines) and long strings (500+ characters), then verifying that each value container has independent scrollbars and doesn't affect the overall page layout.

**Acceptance Scenarios**:

1. **Given** an attribute value that is a large JSON object (100+ lines), **When** displayed in the comparison, **Then** the value appears in a fixed-height container (max-height: 400px) with a vertical scrollbar
2. **Given** an attribute value that is a long string (500+ characters), **When** displayed in the comparison, **Then** the value appears in a container with horizontal scrollbar to prevent text wrapping beyond a reasonable width (max-width: 600px)
3. **Given** multiple scrollable value containers on the same page, **When** scrolling within one container, **Then** it does not affect other containers or the main page scroll position
4. **Given** a scrollable container, **When** content is smaller than container size, **Then** scrollbars do not appear (scrollbars only shown when needed)

---

### User Story 3 - Elegant Display of Environment-Specific Resources (Priority: P2)

As a DevOps engineer identifying configuration drift, I want to see resources that exist in only one environment displayed elegantly and distinctly so that I can quickly identify which resources are missing from other environments without cluttering the comparison with empty cells or confusing indicators.

**Why this priority**: Currently, resources missing from environments create visual noise with empty cells or are buried in the report. This makes it hard to spot genuine configuration drift vs. intentional environment-specific resources. Clear visual distinction improves efficiency.

**Independent Test**: Can be fully tested by comparing environments where Test has 5 resources that don't exist in Production, then verifying that these resources are clearly marked with a distinct visual indicator (e.g., badge, color, icon) and grouped separately or with clear labeling.

**Acceptance Scenarios**:

1. **Given** a resource exists in Test but not in Production, **When** viewing the comparison report, **Then** the resource row displays a clear indicator (e.g., badge reading "Test only" with warning color) next to the resource name
2. **Given** multiple resources exist in only one environment, **When** viewing the report, **Then** these resources are optionally grouped in a separate collapsible section labeled "Environment-Specific Resources" at the top or bottom of the report
3. **Given** a resource exists in all environments with no configuration differences, **When** diff-only mode is enabled, **Then** the resource is hidden from the report (not shown)
4. **Given** a resource exists in all environments but only has configuration differences (not missing), **When** viewing the comparison, **Then** the resource appears in the main comparison section without any "environment-specific" indicators
5. **Given** a resource exists in Production but not in Test (reverse scenario), **When** viewing the report, **Then** it displays an equivalent "Production only" indicator with the same visual treatment

---

### Edge Cases

- What happens when an attribute value is exactly at the scroll threshold (e.g., 400px height)? **Answer**: With `overflow: auto`, scrollbars appear only when content strictly exceeds the threshold (>400px), not at exactly 400px. Content at exactly 400px fits without scrollbars.
- How does the system handle attribute names that are very long (50+ characters) when used as headers? Should they wrap or truncate with ellipsis?
- What happens when all resources in a comparison are environment-specific (none exist in multiple environments)? Should the report show a special message?
- How should the system handle attributes that exist in only one environment (not just resources)? Should they be marked similarly?
- What happens with nested JSON objects that have scrollable content inside scrollable content?
- How does the layout behave on mobile devices or narrow browser windows with scrollable containers?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display each attribute name as a prominent header (H3 or equivalent styling) in the multi-environment comparison HTML report
- **FR-002**: System MUST provide minimum 30px vertical spacing between consecutive attribute header sections for improved readability
- **FR-003**: System MUST wrap each attribute value in a container with `overflow: auto` CSS property to enable scrollbars when content exceeds container dimensions
- **FR-004**: Value containers MUST have a maximum height of 400px with vertical scrollbar appearing when content exceeds this height
- **FR-005**: Value containers MUST have a maximum width of 600px (or responsive width based on viewport) with horizontal scrollbar appearing when content exceeds this width
- **FR-006**: System MUST display environment-specific resources (resources existing in only one environment) with a visual indicator such as a colored badge showing which environment(s) contain the resource
- **FR-007**: System MUST group environment-specific resources into a separate collapsible section labeled "Environment-Specific Resources" at the bottom of the report, enabled by default for all comparisons
- **FR-008**: When --diff-only flag is used, system MUST hide resources that exist in all environments but have zero configuration differences
- **FR-009**: Attribute headers MUST display full attribute names without truncation, with text wrapping if names exceed reasonable width (e.g., 300px)
- **FR-010**: Scrollable containers MUST only show scrollbars when content exceeds container size (not pre-emptively displayed)
- **FR-011**: System MUST preserve existing diff highlighting (baseline-removed, baseline-added, char-level diffs) within scrollable value containers
- **FR-012**: System MUST maintain side-by-side environment comparison layout with scrollable containers aligned horizontally
- **FR-013**: Environment column headers (e.g., Test, Production, Staging) MUST be sticky/fixed at the top of the viewport when scrolling vertically through the report to maintain context about which environment is being compared
- **FR-014**: Environment-specific resource indicators MUST use distinct colors from diff highlighting to avoid confusion (e.g., amber/yellow for "environment-specific" vs blue/green for configuration diffs)

### Key Entities *(include if feature involves data)*

- **Attribute Section**: A display section containing an attribute header and corresponding value containers for each environment
  - Attribute name (displayed as header)
  - Environment values (one container per environment)
  - Diff status (whether values differ across environments)

- **Value Container**: A scrollable display container for attribute values
  - Content (HTML-formatted value with diff highlighting)
  - Dimensions (max-width, max-height)
  - Scroll state (horizontal/vertical scroll position)

- **Environment-Specific Indicator**: A visual marker for resources existing in limited environments
  - Badge text (e.g., "Test only", "Production only")
  - Badge color (distinct from diff colors)
  - Affected environments (list of environment names where resource exists)

## Success Criteria *(mandatory)*

- Users can identify attribute differences 40% faster due to improved header visibility and spacing
- Users can view complete JSON values without page layout breaking, regardless of value size
- Users can distinguish environment-specific resources from configuration drift with 95% accuracy based on visual indicators
- HTML report renders correctly on viewports from 1024px to 4K resolution with scrollable containers adapting appropriately
- Comparison report with 200 resources and 50% environment-specific resources loads in under 2 seconds
- Users report improved satisfaction with comparison report readability in usability testing (target: 8/10 or higher)
## Assumptions

- Users are viewing reports on desktop/laptop browsers (minimum 1024px width)
- Users have basic familiarity with scrollable containers and HTML reports
- Terraform plans being compared typically have 50-500 resources
- Attribute values can range from simple strings to complex nested JSON objects (10-1000 lines)
- Users prefer visual clarity over information density for critical comparison tasks
- Current CSS framework (defined in docs/style-guide.md) provides adequate base styling that can be extended

## Out of Scope

- Interactive filtering or sorting of attributes within the report (future enhancement)
- Exporting specific attribute comparisons to separate files
- Customizable scroll container dimensions via user preferences or configuration file
- Search/find functionality within scrollable value containers
- Collapsing/expanding individual attribute sections (beyond environment-specific resource grouping)
- Mobile-optimized responsive layouts (desktop/laptop focus only)
- Dark mode or alternative color schemes
- Printing optimizations for scrollable containers

## Dependencies

- Existing multi-environment comparison logic in `src/core/multi_env_comparator.py`
- Current HTML generation utilities in `src/lib/html_generation.py`
- CSS style guide defined in `docs/style-guide.md`
- Diff highlighting utilities in `src/lib/diff_utils.py`

## Technical Constraints

- Must maintain backward compatibility with existing `tf-plan-analyzer compare` CLI command and flags
- Must work with existing CSS classes (baseline-removed, baseline-added, char-removed, char-added, etc.)
- HTML file size should not increase significantly (max 20% increase for equivalent comparisons)
- Must render correctly in modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Must not introduce JavaScript dependencies (keep reports as pure HTML+CSS)
- Scrollable containers must be accessible via keyboard navigation (tab, arrow keys)

## Related Documentation

- [Multi-Environment Comparator Source](src/core/multi_env_comparator.py) - Current implementation
- [HTML Generation Source](src/lib/html_generation.py) - CSS generation
- [Style Guide](docs/style-guide.md) - UI design system and CSS classes
- [Function Glossary](docs/function-glossary.md) - `_render_attribute_value()` and `_render_attribute_table()` functions