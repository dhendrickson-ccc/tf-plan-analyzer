# JavaScript API Contract: Attribute Notes

**Feature**: 008-attribute-notes  
**Version**: 1.0  
**Created**: January 28, 2026  
**Purpose**: Define the JavaScript API for client-side attribute notes functionality

---

## Overview

This document specifies the JavaScript functions and utilities embedded in HTML comparison reports to enable client-side note storage and retrieval using browser LocalStorage. All functions are vanilla JavaScript with no external dependencies.

---

## API Functions

### getReportId()

**Purpose**: Extract the report identifier from the current page URL for use in LocalStorage keys.

**Signature**:
```javascript
function getReportId(): string
```

**Returns**: 
- `string` - The filename portion of the current page URL (e.g., `"comparison.html"`)
- Fallback: `"unknown-report"` if filename cannot be extracted

**Implementation**:
```javascript
function getReportId() {
    const path = window.location.pathname;
    const filename = path.substring(path.lastIndexOf('/') + 1);
    return filename || 'unknown-report';
}
```

**Examples**:
| URL | Return Value |
|-----|--------------|
| `file:///Users/user/reports/comparison.html` | `"comparison.html"` |
| `file:///C:/reports/stage-prod-2026-01-28.html` | `"stage-prod-2026-01-28.html"` |
| `https://example.com/reports/multi-env.html` | `"multi-env.html"` |
| `file:///` (empty path) | `"unknown-report"` |

**Browser Compatibility**: All modern browsers (Chrome, Firefox, Safari, Edge)

**Dependencies**: None

---

### debounce(func, delay)

**Purpose**: Create a debounced version of a function to limit execution frequency (used for auto-save).

**Signature**:
```javascript
function debounce(func: Function, delay: number): Function
```

**Parameters**:
- `func` (Function) - The function to debounce
- `delay` (number) - Delay in milliseconds before executing function after last call

**Returns**: 
- `Function` - Debounced wrapper function that accepts same arguments as original

**Implementation**:
```javascript
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}
```

**Behavior**:
- When debounced function is called, starts a timer for `delay` milliseconds
- If called again before timer expires, cancels previous timer and starts new one
- Only executes `func` once the timer completes without interruption
- Preserves `this` context and arguments from last call

**Example Usage**:
```javascript
const debouncedLog = debounce(console.log, 500);

debouncedLog('a');  // Timer started
debouncedLog('b');  // Previous timer cancelled, new timer started
debouncedLog('c');  // Previous timer cancelled, new timer started
// After 500ms of no calls: logs 'c'
```

**Dependencies**: None

---

### saveNote(resourceAddress, attributeName, field, value)

**Purpose**: Save or update a note field in LocalStorage for a specific resource attribute.

**Signature**:
```javascript
function saveNote(
    resourceAddress: string, 
    attributeName: string, 
    field: 'question' | 'answer', 
    value: string
): void
```

**Parameters**:
- `resourceAddress` (string) - Terraform resource address (e.g., `"azurerm_storage_account.main"`)
- `attributeName` (string) - Attribute name (e.g., `"location"`)
- `field` (string) - Field to update: `"question"` or `"answer"`
- `value` (string) - New value for the field

**Returns**: `void`

**Side Effects**:
- Reads from `localStorage` to get existing note (if any)
- Writes to `localStorage` with updated note data
- Updates `lastModified` timestamp to current time

**Implementation**:
```javascript
function saveNote(resourceAddress, attributeName, field, value) {
    const reportId = getReportId();
    const key = `tf-notes-${reportId}#${resourceAddress}#${attributeName}`;
    
    try {
        const existing = localStorage.getItem(key);
        const note = existing ? JSON.parse(existing) : { question: '', answer: '' };
        note[field] = value;
        note.lastModified = Date.now();
        localStorage.setItem(key, JSON.stringify(note));
    } catch (e) {
        console.error('Failed to save note:', e);
    }
}
```

**Error Handling**:
- Catches `QuotaExceededError` if LocalStorage limit reached
- Catches `JSON.parse()` errors for corrupted data
- Logs errors to console but does not throw

**Example Usage**:
```javascript
saveNote('aws_instance.web', 'instance_type', 'question', 'Why t3.large?');
// Saves to key: tf-notes-comparison.html#aws_instance.web#instance_type
// Value: {"question": "Why t3.large?", "answer": "", "lastModified": 1706486400000}

saveNote('aws_instance.web', 'instance_type', 'answer', 'Cost optimization');
// Updates same key
// Value: {"question": "Why t3.large?", "answer": "Cost optimization", "lastModified": 1706486500000}
```

**Dependencies**: 
- `getReportId()`
- Browser `localStorage` API
- Browser `JSON` API

---

### debouncedSaveNote

**Purpose**: Debounced wrapper around `saveNote()` to prevent excessive LocalStorage writes during typing.

**Signature**:
```javascript
const debouncedSaveNote: Function
```

**Type**: Constant (debounced function)

**Implementation**:
```javascript
const debouncedSaveNote = debounce(saveNote, 500);
```

**Parameters**: Same as `saveNote(resourceAddress, attributeName, field, value)`

**Behavior**:
- Waits 500ms after last call before executing `saveNote()`
- If user types continuously, only saves once after 500ms pause
- Reduces LocalStorage write operations during active typing

**Example Usage**:
```javascript
// In textarea oninput handler
textarea.addEventListener('input', (e) => {
    debouncedSaveNote('aws_instance.web', 'instance_type', 'question', e.target.value);
});

// User types: "W", "h", "y", "?"
// Only one saveNote() call executes 500ms after typing "?"
```

**Dependencies**:
- `debounce()`
- `saveNote()`

**Recommended Delay**: 500ms (balances responsiveness with write efficiency)

---

### loadNotes()

**Purpose**: Load all saved notes from LocalStorage and populate corresponding textarea fields on page load.

**Signature**:
```javascript
function loadNotes(): void
```

**Parameters**: None

**Returns**: `void`

**Side Effects**:
- Iterates through all LocalStorage keys
- Updates DOM elements (textareas) with saved note data
- Logs errors to console for corrupted or unreadable notes

**Implementation**:
```javascript
function loadNotes() {
    const reportId = getReportId();
    const prefix = `tf-notes-${reportId}#`;
    
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(prefix)) {
            try {
                const noteData = JSON.parse(localStorage.getItem(key));
                const keyParts = key.substring(prefix.length).split('#');
                const resourceAddress = keyParts[0];
                const attributeName = keyParts[1];
                
                const questionField = document.getElementById(`note-q-${resourceAddress}-${attributeName}`);
                const answerField = document.getElementById(`note-a-${resourceAddress}-${attributeName}`);
                
                if (questionField && noteData.question) {
                    questionField.value = noteData.question;
                }
                if (answerField && noteData.answer) {
                    answerField.value = noteData.answer;
                }
            } catch (e) {
                console.error('Failed to load note from key:', key, e);
            }
        }
    }
}
```

**Behavior**:
1. Gets current report ID
2. Builds key prefix: `tf-notes-{reportId}#`
3. Iterates through all LocalStorage keys
4. Filters keys matching the prefix
5. Parses JSON value and extracts resource/attribute from key
6. Finds corresponding DOM elements by ID
7. Populates textarea values if elements exist

**Error Handling**:
- Gracefully handles missing DOM elements (note was saved but resource no longer in report)
- Catches JSON parse errors for corrupted data
- Logs errors but continues loading other notes

**Expected DOM Element IDs**:
- Question field: `note-q-{resourceAddress}-{attributeName}`
- Answer field: `note-a-{resourceAddress}-{attributeName}`

**Example**:
```javascript
// LocalStorage contains:
// Key: tf-notes-comparison.html#aws_instance.web#instance_type
// Value: {"question": "Why change?", "answer": "Performance", "lastModified": 1706486400000}

// On page load, populates:
// <textarea id="note-q-aws_instance.web-instance_type">Why change?</textarea>
// <textarea id="note-a-aws_instance.web-instance_type">Performance</textarea>
```

**Dependencies**:
- `getReportId()`
- Browser `localStorage` API
- Browser `JSON` API
- DOM API (`document.getElementById()`)

**Initialization**:
```javascript
document.addEventListener('DOMContentLoaded', loadNotes);
```

**Trigger**: Automatically runs when DOM is fully loaded (DOMContentLoaded event)

---

## Integration Pattern

### Complete JavaScript Block

**Location**: Embedded in `<script>` tag in HTML `<head>` or before `</body>`

**Generated By**: `get_notes_javascript()` function in `src/lib/html_generation.py`

**Integration Example**:
```python
def generate_html():
    html_parts.append("<head>")
    html_parts.append("<style>")
    html_parts.append(generate_full_styles())
    html_parts.append("</style>")
    html_parts.append(get_notes_javascript())  # Add notes JavaScript
    html_parts.append("</head>")
```

### Event Binding

**Textarea Handlers**: Inline `oninput` attributes

```html
<textarea 
    id="note-q-aws_instance.web-instance_type"
    oninput="debouncedSaveNote('aws_instance.web', 'instance_type', 'question', this.value)"
    placeholder="Question...">
</textarea>

<textarea 
    id="note-a-aws_instance.web-instance_type"
    oninput="debouncedSaveNote('aws_instance.web', 'instance_type', 'answer', this.value)"
    placeholder="Answer...">
</textarea>
```

**Page Load**: Automatic via DOMContentLoaded event listener

---

## Browser Compatibility

| Browser | Minimum Version | Notes |
|---------|----------------|-------|
| Chrome | 4+ | Full support |
| Firefox | 3.5+ | Full support |
| Safari | 4+ | Full support |
| Edge | All versions | Full support |
| IE | 11 | LocalStorage supported, arrow functions require transpilation |

**Modern Features Used**:
- Arrow functions (`=>`)
- Template literals (`` ` ``)
- Spread operator (`...args`)
- `const`/`let`

**Fallback**: For IE11 support, transpile to ES5 (not required for this project)

---

## Performance Considerations

### LocalStorage Write Frequency

**Problem**: Excessive writes can cause performance degradation

**Solution**: 500ms debounce on `saveNote()`

**Impact**:
- Without debounce: 1 write per keystroke (e.g., 50 writes for 50-character note)
- With debounce: 1 write per typing session (typically 1-2 writes per field edit)
- ~95% reduction in write operations

### Storage Quota

**Limit**: ~5-10MB per origin (browser-dependent)

**Estimated Usage**:
- Average note: 200 characters × 2 fields = 400 bytes
- 100 notes: ~40KB
- 1000 notes: ~400KB
- **Quota exhaustion**: Extremely unlikely for typical use

**Error Handling**: `saveNote()` catches `QuotaExceededError` and logs to console

### Load Performance

**Worst Case**: 1000 notes in LocalStorage
- `loadNotes()` iterates all keys once: O(n) where n = total LocalStorage keys
- JSON parse + DOM update per matching key
- **Estimated time**: <50ms on modern hardware

**Optimization**: Early filtering via `key.startsWith(prefix)` before JSON parsing

---

## Testing Checklist

### Unit Tests (Manual Browser Console)

- [ ] `getReportId()` returns correct filename from various URL formats
- [ ] `debounce()` delays execution by specified milliseconds
- [ ] `saveNote()` creates new note with correct JSON structure
- [ ] `saveNote()` updates existing note preserving other field
- [ ] `saveNote()` handles QuotaExceededError gracefully
- [ ] `debouncedSaveNote()` reduces write frequency during rapid calls
- [ ] `loadNotes()` populates all textareas with saved values
- [ ] `loadNotes()` handles missing DOM elements without errors
- [ ] `loadNotes()` handles corrupted JSON data without crashing

### Integration Tests

- [ ] Type in question field → auto-saves after 500ms pause
- [ ] Type in answer field → auto-saves independently
- [ ] Reload page → all notes restored correctly
- [ ] Multiple resources/attributes → each note saved independently
- [ ] Open different report → notes are report-specific (different reportId)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial API specification |

---

## References

- [LocalStorage API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [Debouncing in JavaScript](https://davidwalsh.name/javascript-debounce-function)
- Research: [research.md](../research.md)
- Data Model: [data-model.md](../data-model.md)
