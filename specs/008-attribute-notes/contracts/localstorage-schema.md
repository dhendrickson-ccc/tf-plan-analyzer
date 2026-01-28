# LocalStorage Schema Contract: Attribute Notes

**Feature**: 008-attribute-notes  
**Version**: 1.0  
**Created**: January 28, 2026  
**Purpose**: Define the LocalStorage data structure and access patterns for attribute notes

---

## Overview

This document specifies the LocalStorage schema for storing question/answer notes on resource attribute changes in HTML comparison reports. All data is client-side only and persists in the user's browser across sessions.

---

## Key Naming Convention

### Pattern

```
tf-notes-{reportId}#{resourceAddress}#{attributeName}
```

### Components

| Component | Description | Example | Rules |
|-----------|-------------|---------|-------|
| `tf-notes-` | Fixed prefix | `tf-notes-` | Required, prevents namespace collisions |
| `{reportId}` | HTML report filename | `comparison.html` | Extracted from URL via `getReportId()` |
| `#` | Separator | `#` | Fixed delimiter between components |
| `{resourceAddress}` | Terraform resource address | `azurerm_storage_account.main` | Full resource path including type and name |
| `#` | Separator | `#` | Fixed delimiter between components |
| `{attributeName}` | Top-level attribute name | `location` | Attribute key from Terraform plan |

### Key Examples

```
tf-notes-comparison.html#azurerm_storage_account.main#location
tf-notes-stage-prod-2026-01-28.html#aws_instance.web#instance_type
tf-notes-dev-test.html#google_compute_instance.server#machine_type
tf-notes-multi-env.html#azurerm_kubernetes_cluster.aks#sku.0.tier
```

### Special Cases

| Scenario | reportId | Example Key |
|----------|----------|-------------|
| Standard file path | `comparison.html` | `tf-notes-comparison.html#aws_instance.web#ami` |
| Timestamped report | `stage-prod-2026-01-28.html` | `tf-notes-stage-prod-2026-01-28.html#aws_instance.web#ami` |
| URL encoding | `my%20report.html` | `tf-notes-my%20report.html#aws_instance.web#ami` |
| No filename detected | `unknown-report` | `tf-notes-unknown-report#aws_instance.web#ami` |

### Key Parsing

**Extraction Algorithm**:
```javascript
const prefix = `tf-notes-${reportId}#`;
const keyParts = key.substring(prefix.length).split('#');
const resourceAddress = keyParts[0];
const attributeName = keyParts[1];
```

**Example**:
```javascript
// Key: tf-notes-comparison.html#aws_instance.web#instance_type
// reportId: comparison.html
// prefix: tf-notes-comparison.html#

key.substring(prefix.length)  // "aws_instance.web#instance_type"
.split('#')                   // ["aws_instance.web", "instance_type"]

// Result:
// resourceAddress = "aws_instance.web"
// attributeName = "instance_type"
```

---

## Value Structure

### JSON Schema

**Format**: Stringified JSON object

**Schema Definition**:
```json
{
  "question": "string",
  "answer": "string", 
  "lastModified": 1234567890123
}
```

### Field Specifications

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `question` | string | No | Plaintext, no length limit | User-entered question about the attribute change |
| `answer` | string | No | Plaintext, no length limit | User-entered answer/explanation |
| `lastModified` | number | Yes | Unix timestamp (milliseconds) | Last modification time in milliseconds since epoch |

### Value Examples

**New Note** (question only):
```json
{
  "question": "Why is location different in prod?",
  "answer": "",
  "lastModified": 1706486400000
}
```

**Complete Note** (question + answer):
```json
{
  "question": "Why is location different in prod?",
  "answer": "Historical decision - prod was in westus before eastus datacenter opened",
  "lastModified": 1706486450000
}
```

**Answer Only** (no question):
```json
{
  "question": "",
  "answer": "Per security team requirement, all prod resources must use standard SKU",
  "lastModified": 1706486500000
}
```

**Empty Note** (initialized but no content):
```json
{
  "question": "",
  "answer": "",
  "lastModified": 1706486300000
}
```

### Timestamp Format

**Type**: Unix timestamp in milliseconds

**Generation**:
```javascript
const timestamp = Date.now();  // e.g., 1706486400000
```

**Conversion**:
```javascript
// Timestamp to Date object
const date = new Date(1706486400000);

// Date to human-readable string
const readable = date.toLocaleString();
// "1/28/2026, 3:00:00 PM"
```

**Purpose**: Track last edit time for potential future features (e.g., sync, version history)

---

## Storage Access Patterns

### Write Operation

**Function**: `saveNote(resourceAddress, attributeName, field, value)`

**Algorithm**:
1. Construct key: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`
2. Read existing value from LocalStorage (if any)
3. Parse JSON or initialize empty note object
4. Update specified field (`question` or `answer`)
5. Set `lastModified` to current timestamp
6. Stringify JSON and write back to LocalStorage

**Code Example**:
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

**Write Flow**:
```
User types in textarea
  → oninput event fires
  → debouncedSaveNote() queued
  → [500ms delay]
  → saveNote() executes
  → localStorage.getItem(key)
  → JSON.parse(existing) or create new object
  → Update field + timestamp
  → JSON.stringify(note)
  → localStorage.setItem(key, value)
```

### Read Operation

**Function**: `loadNotes()`

**Algorithm**:
1. Get current report ID
2. Build key prefix: `tf-notes-{reportId}#`
3. Iterate through all LocalStorage keys
4. Filter keys starting with prefix
5. Parse JSON value
6. Extract resource/attribute from key
7. Find corresponding DOM elements
8. Populate textarea values

**Code Example**:
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

**Read Flow**:
```
Page loads
  → DOMContentLoaded event fires
  → loadNotes() executes
  → Iterate localStorage keys
  → Filter by prefix (tf-notes-{reportId}#)
  → For each matching key:
      → localStorage.getItem(key)
      → JSON.parse(value)
      → Extract resource/attribute from key
      → document.getElementById(textareaId)
      → Populate textarea.value
```

### Delete Operation

**Method**: Manual browser action (no UI in v1)

**Browser Instructions**:

**Chrome/Edge**:
1. Open DevTools (F12)
2. Go to Application tab
3. Select Local Storage → file://
4. Find key (e.g., `tf-notes-comparison.html#aws_instance.web#instance_type`)
5. Right-click → Delete

**Firefox**:
1. Open DevTools (F12)
2. Go to Storage tab
3. Expand Local Storage
4. Find and delete key

**Safari**:
1. Open Web Inspector
2. Go to Storage tab
3. Select Local Storage
4. Delete key

**Programmatic Delete** (future feature):
```javascript
function deleteNote(resourceAddress, attributeName) {
    const reportId = getReportId();
    const key = `tf-notes-${reportId}#${resourceAddress}#${attributeName}`;
    localStorage.removeItem(key);
}
```

---

## Storage Limits and Quota

### Browser Quota

| Browser | Default Quota | Notes |
|---------|--------------|-------|
| Chrome | ~10 MB | Per origin |
| Firefox | ~10 MB | Per origin |
| Safari | ~5 MB | Per origin |
| Edge | ~10 MB | Per origin |

**Origin**: For `file://` protocol, origin is typically `file://` (all local files share quota)

### Estimated Usage

**Per Note**:
- Question: ~100-500 characters = 100-500 bytes
- Answer: ~100-500 characters = 100-500 bytes
- JSON overhead: ~100 bytes (keys, lastModified, formatting)
- **Total**: ~300-1100 bytes (average: 700 bytes)

**Scaling**:
| Notes | Storage | % of 5MB Quota |
|-------|---------|----------------|
| 10 | ~7 KB | 0.14% |
| 100 | ~70 KB | 1.4% |
| 500 | ~350 KB | 7% |
| 1000 | ~700 KB | 14% |
| 5000 | ~3.5 MB | 70% |

**Conclusion**: Quota exhaustion extremely unlikely for typical use cases

### Quota Exceeded Handling

**Error**: `DOMException: QuotaExceededError`

**Handling in `saveNote()`**:
```javascript
try {
    localStorage.setItem(key, JSON.stringify(note));
} catch (e) {
    if (e.name === 'QuotaExceededError') {
        console.error('LocalStorage quota exceeded. Please clear old notes.');
        // Future: Show user-facing alert
    } else {
        console.error('Failed to save note:', e);
    }
}
```

**Future Enhancement**: Implement storage cleanup (e.g., delete notes older than 6 months)

---

## Data Lifecycle

### Create

**Trigger**: User types first character in question or answer field

**Process**:
1. `oninput` event fires on textarea
2. `debouncedSaveNote()` called with field value
3. After 500ms delay, `saveNote()` executes
4. New note object created: `{ question: '', answer: '', lastModified: Date.now() }`
5. Specified field updated with typed value
6. JSON stringified and written to LocalStorage

**Example**:
```javascript
// User types "Why?" in question field
// After 500ms:
saveNote('aws_instance.web', 'instance_type', 'question', 'Why?');

// LocalStorage now contains:
// Key: tf-notes-comparison.html#aws_instance.web#instance_type
// Value: {"question":"Why?","answer":"","lastModified":1706486400000}
```

### Update

**Trigger**: User edits existing text in question or answer field

**Process**:
1. `oninput` event fires on textarea
2. `debouncedSaveNote()` called with new field value
3. After 500ms delay, `saveNote()` executes
4. Existing note retrieved from LocalStorage
5. JSON parsed to object
6. Specified field updated with new value
7. `lastModified` timestamp updated
8. JSON re-stringified and written back

**Example**:
```javascript
// Existing: {"question":"Why?","answer":"","lastModified":1706486400000}
// User changes question to "Why change instance type?"

saveNote('aws_instance.web', 'instance_type', 'question', 'Why change instance type?');

// LocalStorage updated:
// Value: {"question":"Why change instance type?","answer":"","lastModified":1706486450000}
```

### Read

**Trigger**: Page load (DOMContentLoaded event)

**Process**:
1. `loadNotes()` executes automatically
2. All LocalStorage keys iterated
3. Keys matching `tf-notes-{reportId}#` prefix filtered
4. Each matching note parsed from JSON
5. Resource/attribute extracted from key
6. Corresponding textareas found by ID
7. Textarea values populated with note data

**Example**:
```javascript
// LocalStorage contains:
// tf-notes-comparison.html#aws_instance.web#instance_type
// → {"question":"Why?","answer":"Performance","lastModified":1706486400000}

// On page load:
// <textarea id="note-q-aws_instance.web-instance_type"> ← populated with "Why?"
// <textarea id="note-a-aws_instance.web-instance_type"> ← populated with "Performance"
```

### Persist

**Scope**: Data persists indefinitely until:
- User manually clears browser data
- User deletes LocalStorage key via DevTools
- Browser storage is wiped due to disk space issues (rare)

**Cross-Session**: Notes survive browser restarts and system reboots

**Cross-Report**: Notes are **report-specific** (isolated by `reportId` in key)

### Delete

**v1 Implementation**: No UI-based deletion (manual DevTools only)

**Future v2**: Potential delete button in notes UI

---

## Cross-Report Isolation

### Isolation Mechanism

**Key Component**: `reportId` in key prefix

**Behavior**:
- Each HTML report has unique filename (reportId)
- Keys prefixed with `tf-notes-{reportId}#`
- `loadNotes()` only reads keys matching current report's prefix

**Example**:
```
Report A: comparison.html
  → Keys: tf-notes-comparison.html#...
  → Only loads notes with prefix "tf-notes-comparison.html#"

Report B: stage-prod.html
  → Keys: tf-notes-stage-prod.html#...
  → Only loads notes with prefix "tf-notes-stage-prod.html#"
```

**Result**: Notes for same resource/attribute in different reports are stored separately

### Shared Resource Example

**Scenario**: Same resource appears in two reports

**Report 1**: `comparison.html`
```
Key: tf-notes-comparison.html#aws_instance.web#instance_type
Value: {"question":"Why t3.large?","answer":"Old decision","lastModified":1706486400000}
```

**Report 2**: `stage-prod.html`
```
Key: tf-notes-stage-prod.html#aws_instance.web#instance_type
Value: {"question":"Why different in stage?","answer":"Testing new size","lastModified":1706486500000}
```

**Isolation**: Different `reportId` → completely separate notes

---

## Error Handling

### Invalid JSON

**Scenario**: LocalStorage value is corrupted or not valid JSON

**Handling**:
```javascript
try {
    const noteData = JSON.parse(localStorage.getItem(key));
} catch (e) {
    console.error('Failed to load note from key:', key, e);
    // Skip this note and continue loading others
}
```

**Behavior**: Logs error to console, continues processing remaining notes

### Missing Fields

**Scenario**: Saved note missing `question`, `answer`, or `lastModified`

**Handling**:
```javascript
if (questionField && noteData.question) {
    questionField.value = noteData.question;
}
```

**Behavior**: Only populates field if data exists, gracefully handles missing fields

### Key Collision

**Scenario**: Two different resources/attributes hash to same key (theoretically impossible with current schema)

**Prevention**: Key includes full resource address + attribute name → guaranteed unique per resource-attribute pair

### Quota Exceeded

**Scenario**: LocalStorage quota limit reached

**Error**: `QuotaExceededError`

**Handling**: Caught in `saveNote()` try-catch, logged to console

**User Impact**: Notes will not save until storage is cleared

---

## Migration and Versioning

### Schema Version

**Current**: v1.0 (no version field in JSON)

**Future**: Add optional `schemaVersion` field for breaking changes

**Backward Compatibility**:
```javascript
const note = existing ? JSON.parse(existing) : { question: '', answer: '' };
// Handles v1.0 notes without schemaVersion field
```

### Key Format Changes

**Current Key**: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`

**Future Enhancement**: If key format changes, implement migration function:
```javascript
function migrateKeysV1toV2() {
    // Iterate old keys, convert to new format, delete old
}
```

---

## Security Considerations

### Data Exposure

**Risk**: LocalStorage is readable by any JavaScript on same origin

**Mitigation**: 
- Notes are not sensitive by design (Terraform attribute explanations)
- No passwords, tokens, or PII should be stored
- User education: Don't enter sensitive data in notes

### XSS Protection

**Risk**: Malicious script could read/modify notes

**Mitigation**:
- HTML reports are static files (no server-side execution)
- No user-generated JavaScript injection points
- Notes displayed as plaintext in textarea (no HTML rendering)

### Storage Tampering

**Risk**: User or malicious script could modify LocalStorage directly

**Impact**: 
- Only affects user's own notes
- No server-side consequences (notes are client-side only)
- User can clear/reset via DevTools

**Mitigation**: None needed (user owns their own data)

---

## Testing Scenarios

### Manual Testing Checklist

#### Write Operations
- [ ] Create new note with question only
- [ ] Create new note with answer only
- [ ] Create new note with both fields
- [ ] Update existing question
- [ ] Update existing answer
- [ ] Verify debouncing (rapid typing → single write)

#### Read Operations
- [ ] Load page with existing notes → all fields populated
- [ ] Load page with no notes → all textareas empty
- [ ] Load page with partial notes (some resources have notes, others don't)
- [ ] Load different report → different notes loaded

#### Error Scenarios
- [ ] Corrupt JSON in LocalStorage → no crash, error logged
- [ ] Missing `lastModified` field → gracefully handled
- [ ] LocalStorage quota exceeded → error caught and logged
- [ ] DOM element missing (note saved but resource removed from report) → no crash

#### Cross-Report Isolation
- [ ] Add note in Report A → reload Report B → note not visible
- [ ] Add note in Report B with same resource → reload Report A → different note visible
- [ ] Delete note in Report A → Report B note unaffected

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial schema specification |

---

## References

- [LocalStorage API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [Storage Quotas and Eviction Criteria](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)
- JavaScript API: [javascript-api.md](./javascript-api.md)
- Data Model: [../data-model.md](../data-model.md)
- Research: [../research.md](../research.md)
