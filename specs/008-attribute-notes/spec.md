# Feature Specification: Attribute Change Notes

**Feature Branch**: `008-attribute-notes`  
**Created**: January 28, 2026  
**Status**: Draft  
**Input**: User description: "I would like to add a feature where I can add a notes field below each attribute change in the HTML with questions and then have another notes field where I can put answers. I want answers to persist (at least locally)"

## Clarifications

### Session 2026-01-28

- Q: How should the question and answer fields be laid out in the UI? → A: Two vertically stacked text boxes (question above, answer below) with clear labels
- Q: Should there be a visual indicator to distinguish attributes that have questions/answers? → A: No special visual indication
- Q: What should be the visible size of the text fields? → A: Medium-sized text areas (3-5 rows visible) for both question and answer
- Q: How should notes be saved to LocalStorage? → A: Auto-save notes to LocalStorage as the user types (with debouncing)
- Q: What should empty fields display? → A: Show placeholder text in empty fields (e.g., "Add a question..." / "Add an answer...")

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Question to Attribute Change (Priority: P1)

A user reviewing the HTML comparison report notices an attribute change that requires investigation or clarification. They want to document a question directly on that specific attribute change for future reference.

**Why this priority**: This is the core value proposition - capturing questions inline during review prevents forgetting important details and enables asynchronous collaboration.

**Independent Test**: Can be fully tested by opening a report, locating any attribute change, adding a question note, and verifying it appears in the UI and is stored.

**Acceptance Scenarios**:

1. **Given** a user is viewing an HTML comparison report with attribute changes, **When** they locate an attribute change they want to question, **Then** they see a notes interface below that attribute
2. **Given** the notes interface is visible, **When** they enter a question in the question field, **Then** the question text is immediately visible and automatically saved to LocalStorage
3. **Given** a question has been entered, **When** they refresh the page or close/reopen the report, **Then** the question persists and displays exactly as entered

---

### User Story 2 - Answer Questions on Attribute Changes (Priority: P1)

A user reviewing their own questions or questions from others needs to provide answers and context. They want to document answers that persist alongside the questions.

**Why this priority**: Questions without answers have limited value. This completes the core workflow of documenting review findings.

**Independent Test**: Can be tested by adding a question (from Story 1), then adding an answer, and verifying both persist together.

**Acceptance Scenarios**:

1. **Given** a question exists on an attribute change, **When** the user enters text in the answer field, **Then** the answer is visible below the question
2. **Given** an answer has been entered, **When** the user refreshes the page or closes/reopens the report, **Then** the answer persists and displays exactly as entered
3. **Given** an existing answer, **When** the user modifies the answer text, **Then** the updated answer replaces the previous one and persists

---

### User Story 3 - Review Multiple Annotated Changes (Priority: P2)

A user has annotated multiple attribute changes across a large comparison report and needs to review all their questions and answers to prepare a summary or make decisions.

**Why this priority**: Once notes exist, users need to efficiently navigate and review them without manually scrolling through the entire report.

**Independent Test**: Can be tested by adding questions/answers to 3+ different attributes, then using navigation or filtering to find them all.

**Acceptance Scenarios**:

1. **Given** multiple attribute changes have questions/answers, **When** the user views the report, **Then** all annotated attributes display their question/answer content (no special visual indicator beyond the presence of filled-in text fields)
2. **Given** the user is viewing one annotated attribute, **When** they want to find other annotations, **Then** they can scroll through the report to locate attributes with filled-in notes fields
3. **Given** a large report with many changes, **When** the user returns days later, **Then** all their previous notes are still present and associated with the correct attributes

---

### Edge Cases

- What happens when the same report file is opened on different browsers or computers? (Notes are browser-specific via LocalStorage, won't sync across devices)
- What happens when a user generates a new version of the report from updated plan files? (Notes are tied to the specific report version; new report starts with no notes)
- What happens when LocalStorage quota is exceeded? (Standard browser behavior - older data may be evicted or writes may fail)
- What happens when a resource or attribute no longer appears in a new report version? (Notes remain in LocalStorage but are not displayed; they're orphaned)
- What happens if two users annotate the same attribute in their browsers? (Each user's LocalStorage is independent; no conflicts occur)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a question text field below each attribute change in the HTML report
- **FR-002**: System MUST display an answer text field below the question field (vertically stacked layout)
- **FR-003**: Question and answer fields MUST have clear labels to distinguish their purpose
- **FR-004**: Question and answer text areas MUST display 3-5 rows of text by default (with scrolling for longer content)
- **FR-005**: Empty question and answer fields MUST display placeholder text to indicate their purpose (e.g., "Add a question..." / "Add an answer...")
- **FR-006**: System MUST store all question and answer text in the browser's LocalStorage
- **FR-007**: System MUST automatically save notes to LocalStorage as the user types (with debouncing to prevent excessive writes)
- **FR-008**: System MUST use a composite key of resource address + attribute name to identify notes in storage
- **FR-009**: System MUST tie notes to a specific report version using the HTML file name as the version identifier
- **FR-010**: System MUST retrieve and populate previously saved notes when a user reopens the same report version
- **FR-011**: System MUST allow users to edit existing answers with the new content replacing the old
- **FR-012**: System MUST render question and answer fields using plaintext (no special formatting or character limits)
- **FR-013**: System MUST preserve question and answer text exactly as entered (including whitespace and line breaks)
- **FR-014**: Notes fields MUST be visible for every attribute change without requiring a click or toggle to reveal them

### Key Entities

- **AttributeNote**: Represents a question/answer pair for a specific attribute change
  - Associated with: resource address (e.g., `aws_instance.example`)
  - Associated with: attribute name (e.g., `instance_type`)
  - Contains: question text (free-form string)
  - Contains: answer text (free-form string)
  - Contains: report version identifier
  - Stored in: Browser LocalStorage

- **ReportVersion**: Identifies a unique version of a comparison report
  - Used to: Isolate notes to specific plan runs
  - Prevents: Notes from one analysis appearing in another analysis

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a question to any attribute change in under 10 seconds
- **SC-002**: Notes persist across browser sessions with 100% reliability for the same report version
- **SC-003**: Users can locate and review their annotated changes without viewing every change in the report
- **SC-004**: The notes interface does not obscure or interfere with viewing the attribute change details themselves

## Assumptions

- Users are comfortable with browser-based LocalStorage (notes won't sync across devices or browsers)
- The HTML report is viewed in a modern browser with LocalStorage support
- Users understand that clearing browser data will delete their notes
- Notes are for individual use or sharing via screenshot/screen-sharing, not collaborative editing
- Report files are uniquely identifiable (file name or content can serve as version ID)
- Question fields have a 1:1 relationship with answer fields (one answer per question)

## Out of Scope

The following are explicitly excluded from this feature:

- Multi-user collaboration or real-time syncing of notes
- Server-side storage or database persistence
- Export/import of notes to external formats (CSV, JSON, etc.)
- Rich text formatting (bold, italics, links, Markdown)
- Character limits or validation on note content
- Search or filtering functionality for notes
- Status tracking (resolved, pending, etc.) on questions
- Timestamps or user attribution on notes
- Bulk operations (delete all notes, export all, etc.)
- Edit history or version control for answers
- Notifications when notes exist

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
