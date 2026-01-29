# JavaScript API Contract: Q&A Notes Markdown Functions

**Feature**: 009-qa-markdown-preview  
**Type**: Client-Side JavaScript API  
**Date**: 2026-01-28

## Overview

This contract defines the JavaScript functions that will be added to generated HTML files to support markdown rendering, mode toggling, and collapse state management for Q&A notes.

---

## 1. renderMarkdown()

**Purpose**: Convert raw markdown text to sanitized HTML

**Signature**:
```javascript
function renderMarkdown(rawMarkdown: string): string
```

**Parameters**:
- `rawMarkdown` (string, required): User-entered markdown text

**Returns**:
- `string`: Sanitized HTML safe for innerHTML injection

**Behavior**:
1. Parse markdown using marked.parse()
2. Sanitize HTML using DOMPurify.sanitize()
3. Strip all user-provided HTML tags
4. Return clean HTML string

**Example**:
```javascript
const markdown = "# Hello\n\n**World**";
const html = renderMarkdown(markdown);
// Returns: "<h1>Hello</h1>\n<p><strong>World</strong></p>"

const malicious = "<script>alert('xss')</script>";
const safe = renderMarkdown(malicious);
// Returns: "" (script tag stripped)
```

**Error Handling**:
- If `rawMarkdown` is null/undefined, return empty string
- If markdown parsing fails, return escaped original text
- Never throw exceptions

**Dependencies**:
- External: marked.js (via CDN)
- External: DOMPurify (via CDN)

---

## 2. toggleNoteMode()

**Purpose**: Switch between edit and preview modes for a Q&A note

**Signature**:
```javascript
function toggleNoteMode(
  event: Event,
  resourceAddress: string, 
  attributeName: string
): void
```

**Parameters**:
- `event` (Event, required): Click event from toggle button
- `resourceAddress` (string, required): Terraform resource address
- `attributeName` (string, required): Terraform attribute name

**Returns**: void

**Behavior**:
1. Prevent event propagation (don't trigger details collapse)
2. Find note container by resource/attribute
3. Get current mode from `data-mode` attribute
4. Save current textarea content to LocalStorage
5. If switching to preview:
   - Get textarea content
   - Render markdown to HTML
   - Update preview div innerHTML
6. Toggle `data-mode` attribute
7. Update button text and aria-pressed

**Example**:
```html
<button onclick="toggleNoteMode(event, 'aws_instance.web', 'instance_type')">
  Edit
</button>
```

**Side Effects**:
- Modifies DOM (data-mode attribute, innerHTML, button text)
- Writes to LocalStorage (via saveNote)
- Updates ARIA attributes for accessibility

**Error Handling**:
- If container not found, log error and return early
- If markdown rendering fails, display error message in preview

---

## 3. initializeNoteMode()

**Purpose**: Set initial mode (edit/preview) based on content presence

**Signature**:
```javascript
function initializeNoteMode(
  reportId: string,
  resourceAddress: string,
  attributeName: string
): void
```

**Parameters**:
- `reportId` (string, required): Report filename from URL
- `resourceAddress` (string, required): Terraform resource address
- `attributeName` (string, required): Terraform attribute name

**Returns**: void

**Behavior**:
1. Load note data from LocalStorage
2. Check if question or answer has content (non-whitespace)
3. Set mode to 'preview' if content exists, 'edit' if empty
4. If preview mode, render markdown for both fields
5. Set `data-mode` attribute on container
6. Update UI elements (button text, visibility)

**Example**:
```javascript
// On page load
document.addEventListener('DOMContentLoaded', () => {
  const reportId = getReportId();
  document.querySelectorAll('.notes-container').forEach(container => {
    const resource = container.dataset.resource;
    const attribute = container.dataset.attribute;
    initializeNoteMode(reportId, resource, attribute);
  });
});
```

**Smart Default Logic**:
```javascript
const hasContent = (data.question?.trim().length > 0) || 
                   (data.answer?.trim().length > 0);
const defaultMode = hasContent ? 'preview' : 'edit';
```

---

## 4. saveCollapseState()

**Purpose**: Persist collapse/expand state to LocalStorage

**Signature**:
```javascript
function saveCollapseState(
  resourceAddress: string,
  attributeName: string,
  isCollapsed: boolean
): void
```

**Parameters**:
- `resourceAddress` (string, required): Terraform resource address
- `attributeName` (string, required): Terraform attribute name
- `isCollapsed` (boolean, required): true if collapsed, false if expanded

**Returns**: void

**Behavior**:
1. Get reportId from URL
2. Construct LocalStorage key
3. Load existing note data (or create empty object)
4. Update `isCollapsed` property
5. Update `lastModified` timestamp
6. Save back to LocalStorage

**Example**:
```javascript
// In details toggle event handler
details.addEventListener('toggle', (event) => {
  const isCollapsed = !event.target.open;  // Invert because 'open' means expanded
  saveCollapseState(
    details.dataset.resource,
    details.dataset.attribute,
    isCollapsed
  );
});
```

**Storage Format**:
```javascript
{
  "question": "...",
  "answer": "...",
  "isCollapsed": true,
  "lastModified": 1706483256789
}
```

---

## 5. restoreCollapseState()

**Purpose**: Restore collapse/expand state from LocalStorage on page load

**Signature**:
```javascript
function restoreCollapseState(
  reportId: string,
  resourceAddress: string,
  attributeName: string
): void
```

**Parameters**:
- `reportId` (string, required): Report filename from URL
- `resourceAddress` (string, required): Terraform resource address
- `attributeName` (string, required): Terraform attribute name

**Returns**: void

**Behavior**:
1. Construct LocalStorage key
2. Load note data
3. Get `isCollapsed` property (default to false)
4. Find details element by resource/attribute
5. Set `open` attribute (inverse of isCollapsed)

**Example**:
```javascript
// On page load
document.addEventListener('DOMContentLoaded', () => {
  const reportId = getReportId();
  document.querySelectorAll('.notes-container').forEach(container => {
    restoreCollapseState(
      reportId,
      container.dataset.resource,
      container.dataset.attribute
    );
  });
});
```

**State Mapping**:
- `isCollapsed: true` → `<details open=false>` (collapsed)
- `isCollapsed: false` → `<details open=true>` (expanded)
- Missing property → Default to expanded (false)

---

## 6. saveNoteWithBlur()

**Purpose**: Save note content when textarea loses focus (NEW trigger)

**Signature**:
```javascript
function saveNoteWithBlur(
  resourceAddress: string,
  attributeName: string,
  field: 'question' | 'answer'
): void
```

**Parameters**:
- `resourceAddress` (string, required): Terraform resource address
- `attributeName` (string, required): Terraform attribute name
- `field` (string, required): Either 'question' or 'answer'

**Returns**: void

**Behavior**:
1. Get textarea element by field
2. Get current value
3. Call saveNote() immediately (no debounce)

**Example**:
```html
<textarea 
  id="note-q-aws_instance_web-instance_type"
  oninput="debouncedSaveNote('aws_instance.web', 'instance_type', 'question', this.value)"
  onblur="saveNoteWithBlur('aws_instance.web', 'instance_type', 'question')">
</textarea>
```

**Difference from Auto-Save**:
- Auto-save: Debounced (500ms), triggered on every keystroke
- Blur save: Immediate, triggered only when focus leaves textarea
- Both call same underlying saveNote() function

---

## Existing Functions (Modified)

### saveNote()

**Changes**: No signature changes, but now called from additional contexts

**New Call Sites**:
1. toggleNoteMode() - Before switching modes
2. saveNoteWithBlur() - On textarea blur event
3. debouncedSaveNote() - Existing auto-save (unchanged)

**Behavior**: Remains the same - writes to LocalStorage with debouncing for oninput

---

## Integration Points

### HTML Generation (Python Side)

**Modified Function**: `src/core/multi_env_comparator.py::_render_attribute_section()`

**Changes**:
```python
# Change textarea structure from:
<textarea oninput="debouncedSaveNote(...)"></textarea>

# To:
<textarea 
  oninput="debouncedSaveNote(...)"
  onblur="saveNoteWithBlur(...)">
</textarea>

# Change container from:
<div class="notes-container">

# To:
<details class="notes-container" 
         data-resource="..." 
         data-attribute="..."
         data-mode="preview">
  <summary class="notes-header">
    <span>Q&A Notes</span>
    <button onclick="toggleNoteMode(event, '...', '...')">Edit</button>
  </summary>
  <div class="notes-content">
    <!-- existing textareas -->
    <div class="note-preview" id="note-preview-...">
      <!-- rendered markdown appears here -->
    </div>
  </div>
</details>
```

---

## Error Handling Strategy

### Graceful Degradation

If JavaScript disabled or libraries fail to load:
- Details/summary still provides native collapse functionality
- Textareas remain editable
- LocalStorage saves still work (via existing saveNote)
- Markdown won't render but raw text is visible

### Error Scenarios

| Scenario | Handling |
|----------|----------|
| marked.js fails to load | Display error message in preview, stay in edit mode |
| DOMPurify fails to load | Don't render markdown, show warning |
| Invalid markdown syntax | Render what's valid, display rest as-is |
| LocalStorage quota exceeded | Log error, continue without persistence |
| Missing DOM element | Log error to console, return early |

---

## Testing Contract

### Unit Tests

Test each function in isolation:
```javascript
// Example test for renderMarkdown
test('renderMarkdown handles basic markdown', () => {
  const input = '# Heading\n\n**Bold**';
  const output = renderMarkdown(input);
  expect(output).toContain('<h1>');
  expect(output).toContain('<strong>');
});

test('renderMarkdown strips HTML', () => {
  const input = '<script>alert("xss")</script>';
  const output = renderMarkdown(input);
  expect(output).not.toContain('<script>');
});
```

### Integration Tests

Test full workflows in browser environment:
1. Load report with existing notes → verify preview mode
2. Toggle to edit → verify textarea visible, save triggered
3. Edit content and blur → verify blur save triggered
4. Toggle to preview → verify markdown rendered
5. Collapse section → verify state persisted
6. Refresh page → verify collapsed state restored

---

## Browser Compatibility

**Minimum Requirements**:
- ES6 support (arrow functions, template literals, const/let)
- LocalStorage API
- Details/summary elements
- DOMParser API (for DOMPurify)

**Supported Browsers**:
- Chrome 51+
- Firefox 54+
- Safari 11+
- Edge 79+

**Polyfills**: None required for supported browsers

---

## Performance Considerations

**Optimization Targets**:
- renderMarkdown() should complete in <50ms for typical note (<1KB text)
- toggleNoteMode() should complete in <100ms (includes rendering)
- initializeNoteMode() for 100 notes should complete in <2 seconds

**Bottlenecks**:
- Markdown parsing (marked.js is fast, ~1ms per KB)
- HTML sanitization (DOMPurify, ~5ms per KB)
- DOM manipulation (minimal with targeted updates)

**Mitigation**:
- Debounce auto-save (existing 500ms)
- Only render visible notes initially (lazy load if >100 notes)
- Cache rendered markdown in memory (future enhancement)
