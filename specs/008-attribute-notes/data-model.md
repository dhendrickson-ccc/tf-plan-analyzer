# Data Model: Attribute Change Notes

**Feature**: 008-attribute-notes  
**Created**: January 28, 2026  
**Purpose**: Define data structures for client-side notes storage in browser LocalStorage

---

## Overview

This feature introduces a **client-side only** data model for storing question/answer notes on attribute changes in HTML comparison reports. All data is stored in the user's browser using LocalStorage API. No server-side persistence or database changes are required.

---

## New Entities

### AttributeNote

**Description**: Represents a question/answer pair associated with a specific attribute change in a comparison report.

**Storage**: Browser LocalStorage (JSON-serialized)

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | No | User-entered question text about the attribute change |
| `answer` | string | No | User-entered answer/explanation text |
| `lastModified` | number | Yes | Unix timestamp (milliseconds) of last update |

**LocalStorage Key Pattern**:
```
tf-notes-{reportId}#{resourceAddress}#{attributeName}
```

**Example Keys**:
- `tf-notes-comparison.html#azurerm_storage_account.main#location`
- `tf-notes-stage-prod-2026-01-28.html#aws_instance.web#instance_type`

**Example JSON Value**:
```json
{
  "question": "Why is location different in prod?",
  "answer": "Historical decision - prod was in westus before eastus datacenter opened",
  "lastModified": 1706486400000
}
```

**Lifecycle**:
- **Created**: When user types first character in question or answer field
- **Updated**: Auto-saved after 500ms debounce when user types in either field
- **Read**: On page load via `loadNotes()` JavaScript function
- **Deleted**: Manual browser LocalStorage clearing only (no UI for deletion in v1)

**Relationships**:
- Associated with `AttributeDiff` entity (from existing data model) via resource address + attribute name
- Associated with specific report version via `reportId` (HTML filename)

---

## LocalStorage Schema

### Key Structure

**Pattern**: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`

**Components**:
- `tf-notes-` - Fixed prefix to namespace keys
- `{reportId}` - Report version identifier (HTML filename)
- `#` - Separator character
- `{resourceAddress}` - Terraform resource address (e.g., `azurerm_storage_account.main`)
- `#` - Separator character
- `{attributeName}` - Top-level attribute name (e.g., `location`, `sku`)

**Example**:
```
tf-notes-comparison.html#azurerm_storage_account.main#location
```

### Value Structure

**Format**: JSON string

**Schema**:
```json
{
  "question": "string",
  "answer": "string",
  "lastModified": 1234567890123
}
```

**Field Constraints**:
- `question`: Optional, plaintext only, no length limit (browser LocalStorage quota applies)
- `answer`: Optional, plaintext only, no length limit (browser LocalStorage quota applies)
- `lastModified`: Required, Unix timestamp in milliseconds

### Storage Limits

**Browser Quota**: ~5-10MB per origin (browser-dependent)

**Typical Usage**:
- 50 notes × 500 bytes each = 25KB (well within limits)
- 1000 notes × 1KB each = 1MB (approaching limits)

**Overflow Handling**: JavaScript catches `QuotaExceededError` and logs to console (no user-facing error UI in v1)

---

## Modified Entities

### HTML Report Structure (Client-Side)

**Impact**: New HTML elements added to existing attribute sections

**New HTML Elements**:

```html
<div class="attribute-section">
    <h3 class="attribute-header">...</h3>
    <div class="attribute-values">...</div>
    
    <!-- NEW: Notes container -->
    <div class="notes-container">
        <div>
            <label class="note-label" for="note-q-{resource}-{attribute}">Question:</label>
            <textarea 
                class="note-field" 
                id="note-q-{resource}-{attribute}"
                placeholder="Add a question..."
                oninput="debouncedSaveNote('{resource}', '{attribute}', 'question', this.value)"
                rows="4"></textarea>
        </div>
        <div class="note-answer">
            <label class="note-label" for="note-a-{resource}-{attribute}">Answer:</label>
            <textarea 
                class="note-field" 
                id="note-a-{resource}-{attribute}"
                placeholder="Add an answer..."
                oninput="debouncedSaveNote('{resource}', '{attribute}', 'answer', this.value)"
                rows="4"></textarea>
        </div>
    </div>
</div>
```

**ID Naming Convention**:
- Question field: `note-q-{resource}-{attribute}`
- Answer field: `note-a-{resource}-{attribute}`
- Special characters (`.`, `[`, `]`) replaced with `-` for valid HTML IDs

**Example**:
- Resource: `azurerm_storage_account.main`
- Attribute: `location`
- Question ID: `note-q-azurerm_storage_account-main-location`
- Answer ID: `note-a-azurerm_storage_account-main-location`

---

## Relationship to Existing Data Model

### AttributeDiff (Existing)

**Location**: Defined in `.specify/memory/data_model.md` (from feature 004)

**Attributes** (relevant subset):
- `attribute_name`: string - Top-level attribute key
- `env_values`: dict - Values per environment
- `is_different`: boolean - Whether values differ across environments

**Relationship to AttributeNote**:
- One `AttributeDiff` → Zero or one `AttributeNote`
- `AttributeNote` references `AttributeDiff` via `resourceAddress` + `attributeName`
- No direct object reference (client-side only, no Python representation of AttributeNote)

### ResourceComparison (Existing)

**Location**: Defined in `.specify/memory/data_model.md` (from feature 004)

**Attributes** (relevant subset):
- `resource_address`: string - Terraform resource address
- `attribute_diffs`: List[AttributeDiff] - List of attribute differences

**Relationship to AttributeNote**:
- One `ResourceComparison` → Zero or many `AttributeNote` (one per attribute)
- Notes are associated via `resource_address` from `ResourceComparison`

---

## Data Flow

### Save Flow

1. User types in question or answer textarea
2. `oninput` event fires
3. `debouncedSaveNote(resource, attribute, field, value)` called
4. Debounce delays execution by 500ms
5. If user stops typing, `saveNote()` executes:
   - Constructs LocalStorage key
   - Reads existing note (if any)
   - Updates `question` or `answer` field
   - Sets `lastModified` timestamp
   - Writes JSON to LocalStorage

### Load Flow

1. Page loads, `DOMContentLoaded` event fires
2. `loadNotes()` function executes:
   - Extracts `reportId` from `window.location.pathname`
   - Iterates through all LocalStorage keys
   - Filters keys matching `tf-notes-{reportId}#` prefix
   - For each matching key:
     - Parses JSON value
     - Extracts resource and attribute from key
     - Finds corresponding textarea elements by ID
     - Populates `value` property with saved text

---

## Future Enhancements (Out of Scope for v1)

- **Export/Import**: JSON export of all notes, import from file
- **Search**: Search across all notes by keyword
- **Status Tracking**: Mark notes as "resolved", "pending", "blocked"
- **Timestamps**: Display last modified time in UI
- **Sync**: Cloud storage or file-based sync across devices
- **Content Hash Versioning**: Use report content hash instead of filename for version ID

---

## Validation Rules

### Client-Side (JavaScript)

1. **Key Format Validation**: Ensure LocalStorage keys match pattern `tf-notes-{reportId}#{resource}#{attribute}`
2. **JSON Parsing**: Gracefully handle malformed JSON in LocalStorage (log error, skip entry)
3. **ID Sanitization**: Replace special characters in resource/attribute names with `-` for valid HTML IDs
4. **Quota Handling**: Catch `QuotaExceededError` and log to console

### No Server-Side Validation

This feature is entirely client-side. No Python validation or data processing is required.

---

## Testing Considerations

### Unit Tests

- Verify HTML IDs are correctly sanitized (test with resource names containing `.`, `[`, `]`)
- Verify JavaScript functions are properly embedded in generated HTML

### End-to-End Tests

- Generate HTML report with notes fields
- Manually verify LocalStorage key pattern in browser DevTools
- Verify notes persist across page refresh (simulated by reloading HTML file)
- Verify debouncing works (notes not saved immediately on keystroke)

### Manual Testing

- Open HTML report in browser
- Add question and answer to attribute
- Refresh page → verify notes persist
- Open different report → verify notes don't carry over (isolated by filename)

---

## References

- **Existing AttributeDiff Entity**: `.specify/memory/data_model.md` (feature 004)
- **HTML Generation**: `src/core/multi_env_comparator.py` (MultiEnvReport class)
- **LocalStorage API**: [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
