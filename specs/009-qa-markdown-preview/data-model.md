# Data Model: Q&A Notes Markdown Support

**Feature**: 009-qa-markdown-preview  
**Date**: 2026-01-28  
**Status**: Phase 1

## Overview

This document extends the canonical data model in `.specify/memory/data_model.md` with entities specific to markdown-enabled Q&A notes. These entities represent client-side state and data structures for the enhanced Q&A notes feature.

---

## New Entities

### QANoteData

**Purpose**: Represents persisted Q&A note content and state in LocalStorage

**Attributes**:
- `question`: string - User-entered markdown text for the question field
- `answer`: string - User-entered markdown text for the answer field
- `lastModified`: number - Unix timestamp of last save operation
- `isCollapsed`: boolean - Whether the Q&A section is collapsed for this note (persists across page loads)

**Storage**:
- Location: Browser LocalStorage
- Key format: `tf-notes-${reportId}#${resourceAddress}#${attributeName}`
- Serialization: JSON

**Validation**:
- `question` and `answer` may be empty strings (default)
- `lastModified` must be valid Unix timestamp
- `isCollapsed` defaults to `false` if not present

**Example**:
```json
{
  "question": "## Why does this value differ?\n\n- Config change\n- Environment",
  "answer": "**Answer**: Different environment variables set in prod vs stage.",
  "lastModified": 1706483256789,
  "isCollapsed": false
}
```

**Relationships**:
- One QANoteData per (reportId, resourceAddress, attributeName) tuple
- Loaded by `loadNotes()` JavaScript function on page initialization
- Modified by `saveNote()`, `toggleMode()`, and collapse event handlers

---

### QANoteViewState

**Purpose**: Represents transient UI state for Q&A note display (not persisted)

**Attributes**:
- `mode`: enum('edit', 'preview') - Current viewing mode
- `hasContent`: boolean - Whether question or answer contains non-whitespace text
- `isCollapsed`: boolean - Current collapsed/expanded state (synced from QANoteData)
- `resourceAddress`: string - Terraform resource address this note belongs to
- `attributeName`: string - Terraform attribute name this note belongs to

**Lifecycle**:
- Created on page load for each Q&A note container
- `mode` determined by smart default logic (content → preview, empty → edit)
- `mode` NOT persisted to storage (always recomputed on load)
- `isCollapsed` initialized from persisted QANoteData
- Destroyed when page unloads

**Determination Logic**:
```javascript
const hasContent = (noteData.question?.trim() || noteData.answer?.trim()) ? true : false;
const defaultMode = hasContent ? 'preview' : 'edit';
```

**Representation**:
- DOM: `data-mode` attribute on `.notes-container` element
- DOM: `data-collapsed` attribute (or `open` attribute on `<details>`)
- CSS: Class-based styling based on mode

**Example DOM**:
```html
<details class="notes-container" 
         data-resource="aws_instance.web_server" 
         data-attribute="instance_type"
         data-mode="preview"
         open>
  <!-- content -->
</details>
```

---

### MarkdownRenderResult

**Purpose**: Represents sanitized HTML output from markdown rendering

**Attributes**:
- `rawMarkdown`: string - Original markdown input
- `dirtyHtml`: string - Unsanitized HTML from marked.parse()
- `cleanHtml`: string - Sanitized HTML from DOMPurify (final output)
- `hasInvalidSyntax`: boolean - Whether markdown contained invalid/malformed syntax

**Processing Pipeline**:
```
rawMarkdown 
  → marked.parse() → dirtyHtml 
  → DOMPurify.sanitize() → cleanHtml 
  → DOM innerHTML
```

**Sanitization Rules** (per clarification):
- Strip ALL HTML tags from user input
- Allow only markdown-generated HTML: `h1-h6`, `p`, `ul`, `ol`, `li`, `pre`, `code`, `em`, `strong`, `blockquote`, `a`, `br`
- Allow only `href` attribute (for links)
- Remove all event handlers (onclick, onerror, etc.)
- Remove script tags, iframes, objects

**Lifecycle**:
- Created on-demand when switching to preview mode
- Created on page load for notes with existing content (when mode=preview)
- Recreated when textarea content changes and mode is preview

**Example**:
```javascript
// Input
rawMarkdown = "# Heading\n\n<script>alert('xss')</script>\n\n**Bold text**"

// After marked.parse()
dirtyHtml = "<h1>Heading</h1>\n<script>alert('xss')</script>\n<p><strong>Bold text</strong></p>"

// After DOMPurify.sanitize() - script tag removed
cleanHtml = "<h1>Heading</h1>\n<p><strong>Bold text</strong></p>"

hasInvalidSyntax = false
```

---

## Modified Existing Entities

### AttributeDiff (from feature 001)

**Changes**: No structural changes required

**Integration**: Q&A notes HTML generation occurs after attribute value rendering in `multi_env_comparator.py`. The existing `AttributeDiff` structure remains unchanged; Q&A notes are appended to each attribute section as additional UI elements.

**Relationship**:
- Each `AttributeDiff` MAY have one associated `QANoteData` (one-to-one optional)
- Note key includes both `resource_address` (from parent `ResourceComparison`) and `attribute_name` (from `AttributeDiff`)

---

## State Transition Diagrams

### Mode Switching

```
┌─────────────┐
│  Page Load  │
└──────┬──────┘
       │
       ├─── hasContent=true ──→ mode='preview' ──┐
       │                                         │
       └─── hasContent=false ─→ mode='edit' ────┤
                                                  │
       ┌──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│  User Interaction   │
└──────────┬──────────┘
           │
           ├─── Click "Edit" button (from preview)
           │     ├─→ Save current content
           │     ├─→ mode='edit'
           │     └─→ Show textarea
           │
           └─── Click "Preview" button (from edit)
                 ├─→ Save current content
                 ├─→ Render markdown → HTML
                 ├─→ Sanitize HTML
                 ├─→ mode='preview'
                 └─→ Show rendered output
```

### Collapse State

```
┌─────────────┐
│  Page Load  │
└──────┬──────┘
       │
       ├─── Load from LocalStorage
       │     ├─→ isCollapsed=true  → <details open=false>
       │     └─→ isCollapsed=false → <details open=true>
       │
       ▼
┌─────────────────────┐
│  User Toggles       │
└──────────┬──────────┘
           │
           ├─── Click summary (collapse)
           │     ├─→ details.open = false
           │     ├─→ Save isCollapsed=true to LocalStorage
           │     └─→ Visual: Hide content
           │
           └─── Click summary (expand)
                 ├─→ details.open = true
                 ├─→ Save isCollapsed=false to LocalStorage
                 └─→ Visual: Show content
```

### Save Operations

```
┌─────────────────────────┐
│  User Types in Textarea │
└────────┬────────────────┘
         │
         ├─→ oninput event
         │    └─→ debouncedSaveNote (500ms delay)
         │         └─→ saveNote() → LocalStorage
         │
         ├─→ blur event (textarea loses focus)
         │    └─→ saveNote() (immediate) → LocalStorage
         │
         └─→ Mode switch click
              └─→ saveNote() (immediate) → LocalStorage
                   └─→ Switch mode
```

---

## Storage Schema

### LocalStorage Keys

**Pattern**: `tf-notes-${reportId}#${resourceAddress}#${attributeName}`

**Examples**:
```
tf-notes-stage-test-prod-compare.html#aws_instance.web_server#instance_type
tf-notes-multi-env-report.html#azurerm_virtual_network.main#address_space
```

**reportId Extraction**:
```javascript
const path = window.location.pathname;
const reportId = path.substring(path.lastIndexOf('/') + 1);
```

### Cleanup Strategy

- Old/orphaned keys should be cleaned if report file is deleted (manual cleanup)
- Consider future enhancement: TTL-based cleanup (not in this feature)
- No automatic cleanup in initial implementation

---

## Dependencies on Existing Data Model

### From Feature 001 (Multi-Environment Comparison)

**Used Entities**:
- `ResourceComparison.resource_address` - Used in LocalStorage key and DOM data attributes
- `AttributeDiff.attribute_name` - Used in LocalStorage key and DOM data attributes
- `EnvironmentPlan.label` - Displayed in attribute headers (no changes needed)

**Integration Points**:
- Q&A notes container appended to each attribute section in comparison HTML
- Renders after attribute value columns
- Uses same sanitization helper from `_sanitize_for_html_id()`

---

## Security Considerations

### XSS Prevention

**Threat**: User-provided markdown could contain malicious HTML/JavaScript

**Mitigation**:
1. All markdown rendered through marked.parse() + DOMPurify.sanitize()
2. DOMPurify configured to strip ALL user-provided HTML tags
3. Only allow markdown-generated HTML elements
4. No `onclick`, `onerror`, or other event attributes allowed
5. `href` attributes allowed but should be validated (DOMPurify handles this)

**Example Attack & Defense**:
```javascript
// Attack attempt
const malicious = `<img src=x onerror="alert('XSS')">`;

// Defense
DOMPurify.sanitize(marked.parse(malicious));
// Result: <p><img src="x"></p>  (onerror removed)

// With ALLOWED_TAGS configuration
DOMPurify.sanitize(marked.parse(malicious), {
  ALLOWED_TAGS: ['h1', 'h2', 'h3', 'p', ...],  // img not in list
  ALLOWED_ATTR: ['href']  // onerror not in list
});
// Result: <p></p>  (entire img tag stripped)
```

---

## Next Phase

Proceed to creating contracts/ directory and quickstart.md
