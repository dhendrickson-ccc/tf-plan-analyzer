# Feature Specification: Q&A Notes Markdown Support with Preview Toggle

**Feature Branch**: `009-qa-markdown-preview`  
**Created**: January 28, 2026  
**Status**: Draft  
**Input**: User description: "I want a feature that will add markdown support along with a preview & edit toggle to the Q&A notes. If something is already present, I want the toggle to be set to non-edit mode displaying rendered markdown. Also, make it so that I can collapse the Q&A section if I want to"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Formatted Q&A Notes (Priority: P1)

As a user reviewing comparison results, I want to see Q&A notes with formatted markdown rendering so that I can easily read structured documentation with headings, lists, code blocks, and emphasis without needing to parse raw markdown syntax.

**Why this priority**: This is the core value proposition - users can immediately benefit from richer note formatting for better comprehension. Without this, the other features have no purpose.

**Independent Test**: Can be fully tested by opening a comparison report with existing Q&A notes containing markdown syntax and verifying the notes display with proper formatting (headings, bold, italic, lists, code blocks).

**Acceptance Scenarios**:

1. **Given** a comparison report with Q&A notes containing markdown syntax, **When** the user opens the report, **Then** the Q&A notes display with rendered markdown formatting
2. **Given** Q&A notes contain headings (# ## ###), **When** displayed in preview mode, **Then** headings appear with appropriate size and styling
3. **Given** Q&A notes contain lists (ordered/unordered), **When** displayed in preview mode, **Then** lists render with proper bullets or numbering
4. **Given** Q&A notes contain code blocks (```), **When** displayed in preview mode, **Then** code blocks appear with monospace font and appropriate background
5. **Given** Q&A notes contain inline formatting (bold, italic, links), **When** displayed in preview mode, **Then** formatting is properly applied

---

### User Story 2 - Edit Q&A Notes with Markdown Preview Toggle (Priority: P2)

As a user documenting comparison findings, I want to toggle between editing raw markdown and previewing rendered output so that I can write markdown syntax while verifying how it will appear to readers.

**Why this priority**: Provides essential editing capability with immediate feedback. This is the second most critical feature as users need to create and edit notes with confidence.

**Independent Test**: Can be fully tested by adding new Q&A notes or editing existing ones, toggling between edit and preview modes, and verifying the markdown renders correctly in preview mode.

**Acceptance Scenarios**:

1. **Given** the Q&A section is visible, **When** the user clicks the edit/preview toggle button, **Then** the view switches between raw markdown text (editable) and rendered markdown (read-only)
2. **Given** the user is in edit mode, **When** markdown syntax is entered, **Then** the raw markdown text displays in an editable text area
3. **Given** the user is in preview mode, **When** viewing the notes, **Then** the markdown is rendered with proper formatting
4. **Given** the user toggles to preview mode, **When** returning to edit mode, **Then** the previous content is preserved
5. **Given** the user makes edits in edit mode, **When** switching to preview mode, **Then** the updated content is rendered

---

### User Story 3 - Smart Mode Selection for Existing Notes (Priority: P2)

As a user opening a comparison report with existing Q&A notes, I want the view to default to preview mode (non-editable) so that I can immediately see formatted content without needing to manually switch modes.

**Why this priority**: Improves user experience by making the common case (viewing existing notes) the default. Users shouldn't need extra clicks to see formatted notes.

**Independent Test**: Can be fully tested by opening comparison reports with existing Q&A notes and verifying they display in preview mode, while empty Q&A sections default to edit mode.

**Acceptance Scenarios**:

1. **Given** a comparison report with existing Q&A notes content, **When** the report is opened, **Then** the Q&A notes display in preview mode (non-editable, rendered markdown)
2. **Given** a comparison report with empty Q&A notes, **When** the report is opened, **Then** the Q&A section defaults to edit mode
3. **Given** the user closes and reopens a report, **When** Q&A notes contain content, **Then** preview mode is selected by default each time

---

### User Story 4 - Collapse/Expand Q&A Section (Priority: P3)

As a user viewing comparison reports, I want to collapse and expand the Q&A section so that I can focus on the comparison data when needed or hide lengthy notes to reduce scrolling.

**Why this priority**: Nice-to-have feature that improves navigation and screen space management but doesn't block core note-taking functionality.

**Independent Test**: Can be fully tested by clicking collapse/expand controls on the Q&A section and verifying the section visibility changes while preserving content and mode state.

**Acceptance Scenarios**:

1. **Given** the Q&A section is visible, **When** the user clicks the collapse control, **Then** the Q&A content is hidden and only a header/title bar remains visible
2. **Given** the Q&A section is collapsed, **When** the user clicks the expand control, **Then** the Q&A content becomes visible again
3. **Given** the Q&A section is in a specific mode (edit or preview), **When** collapsed and then expanded, **Then** the section returns to the same mode
4. **Given** the user has entered content in edit mode, **When** the section is collapsed and expanded, **Then** the entered content is preserved
5. **Given** the Q&A section is collapsed for a specific report, **When** the page is refreshed, **Then** the collapsed state persists for that report only

---

### Edge Cases

- What happens when Q&A notes contain invalid or malformed markdown syntax?
  - System should gracefully render what it can and display invalid syntax as-is
- What happens when markdown contains very long lines or deeply nested structures?
  - Content should wrap appropriately and not break the layout
- What happens if the user switches modes rapidly while content is being entered?
  - Mode transitions should be smooth without content loss
- What happens when Q&A notes contain HTML or script tags within markdown?
  - All HTML tags should be stripped and converted to plain text for security
- What happens when the user collapses the Q&A section while in edit mode with unsaved changes?
  - Changes should be preserved; collapse/expand should not trigger save or discard
- What happens when markdown contains special characters that need escaping?
  - Markdown processor should handle escaping correctly per markdown specification

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render markdown syntax in Q&A notes when in preview mode
- **FR-002**: System MUST support standard markdown formatting including headings, bold, italic, lists, code blocks, links, and blockquotes
- **FR-003**: System MUST provide a toggle control to switch between edit mode (raw markdown) and preview mode (rendered markdown)
- **FR-004**: System MUST display Q&A notes in preview mode by default when existing content is present (mode does not persist across page loads)
- **FR-005**: System MUST display Q&A notes in edit mode by default when no content exists (mode does not persist across page loads)
- **FR-006**: System MUST preserve Q&A note content and trigger an explicit save when switching between edit and preview modes, and whenever focus leaves the edit area (on blur), in addition to existing auto-save behavior
- **FR-007**: System MUST provide a collapse/expand control for the Q&A section
- **FR-008**: System MUST preserve Q&A section visibility state (collapsed/expanded, edit/preview mode) when toggling visibility
- **FR-008a**: System MUST persist the section visibility state (collapsed/expanded) per-report across page refreshes
- **FR-009**: System MUST sanitize markdown content by stripping all HTML tags and converting them to plain text to prevent XSS attacks
- **FR-010**: System MUST handle malformed or invalid markdown gracefully without breaking the interface, and provide clear UI feedback (e.g., warning icon, tooltip, or message in preview mode)
- **FR-011**: System MUST wrap long lines and handle deeply nested markdown structures without breaking layout, and provide UI feedback if content is truncated or requires scrolling
- **FR-012**: System MUST maintain the Q&A section's mode state (edit/preview) independently from its section visibility state (collapsed/expanded)
- **FR-013**: System MUST clearly indicate which mode (edit/preview) is currently active through visual indicators (e.g., icon, color, label)

### Key Entities *(include if feature involves data)*

- **Q&A Note**: Represents user-generated documentation content stored as markdown text, associated with a specific comparison report or resource
- **View Mode State**: Represents whether Q&A notes are displayed in edit mode (raw markdown) or preview mode (rendered HTML)
- **Section Visibility State**: Represents whether the Q&A section is expanded (visible) or collapsed (hidden)

## Clarifications

### Session 2026-01-28

- Q: When users edit Q&A notes in edit mode, should changes be saved automatically or require an explicit save action? → A: Existing auto-save function continues to work, plus trigger an explicit save when switching to preview mode
- Q: Should the collapsed/expanded state of the Q&A section persist across page refreshes or reset to a default state each time? → A: Persist per-report (remember state for each specific comparison report)
- Q: When markdown content is sanitized for XSS prevention, which level of HTML support should be allowed? → A: Strip all HTML completely (only pure markdown syntax, convert all HTML to plain text)
- Q: When the user is in edit mode and switches away from the page (navigates to another page, closes the tab, or refreshes), what should happen to unsaved changes? → A: Force save on blur (auto-save whenever focus leaves the edit area)
- Q: Should the edit/preview mode state persist (like the collapsed state), or should it always reset based on content presence? → A: Smart default only (always use content-based rule: existing→preview, empty→edit)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can read formatted Q&A notes with proper markdown rendering without requiring any additional actions
- **SC-002**: Users can switch between edit and preview modes in under 1 second with a single click
- **SC-003**: 100% of standard markdown syntax (headings, lists, code blocks, bold, italic, links) renders correctly in preview mode
- **SC-004**: Users can collapse and expand the Q&A section in under 1 second with visual feedback
- **SC-005**: Q&A notes with existing content default to preview mode 100% of the time on initial load
- **SC-006**: Empty Q&A sections default to edit mode 100% of the time on initial load
- **SC-007**: Zero content loss occurs when switching between modes or toggling section visibility
- **SC-008**: Malformed markdown degrades gracefully without breaking the interface in 100% of cases
- **SC-009**: Users can identify current mode (edit/preview) instantly through clear visual indicators
