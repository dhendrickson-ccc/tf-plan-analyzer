# Research: Q&A Notes Markdown Support

**Feature**: 009-qa-markdown-preview  
**Date**: 2026-01-28  
**Status**: Phase 0 Complete

## Overview

This document consolidates research findings for implementing markdown support in Q&A notes with preview/edit toggle and collapsible sections.

---

## 1. Client-Side Markdown Rendering Libraries

### Decision: marked.js + DOMPurify

**Rationale**: 
- Smallest combined footprint (~50KB total: ~30KB marked + ~20KB DOMPurify)
- Best CommonMark compliance (100%)
- Fastest performance
- Most active development (36.5k stars, 1.5M+ dependents)
- Works purely client-side via CDN
- No build tools required
- Perfect for offline HTML files

**Alternatives Considered**:
1. **markdown-it** (~45KB) - Rejected: Slightly larger, more complex API for our needs, though excellent for plugin-based customization we don't require
2. **Showdown** (~40KB) - Rejected: Legacy browser support unnecessary, not 100% CommonMark compliant
3. **Roll our own** - Rejected: Markdown parsing is complex, security-critical, and error-prone

### Implementation Approach

```html
<!-- CDN includes (add to HTML template) -->
<script src="https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>

<!-- Usage pattern -->
<script>
  function renderMarkdown(rawMarkdown) {
    const dirty = marked.parse(rawMarkdown);
    const clean = DOMPurify.sanitize(dirty, {
      ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 
                     'pre', 'code', 'em', 'strong', 'blockquote', 'a', 'br'],
      ALLOWED_ATTR: ['href'],
      KEEP_CONTENT: true
    });
    return clean;
  }
</script>
```

**Security Configuration**:
- Strip ALL HTML tags (per clarification session)
- DOMPurify configured with strict whitelist
- Only allow safe markdown-generated HTML elements
- Remove all script tags, iframes, event handlers
- Escape user-provided HTML entities

---

## 2. State Management for Mode Toggle

### Decision: Simple DOM-based state with CSS classes

**Rationale**:
- Existing Q&A notes use vanilla JavaScript + LocalStorage
- No framework overhead
- CSS classes provide instant visual feedback
- Minimal JavaScript required
- Consistent with current codebase patterns

**Alternatives Considered**:
1. **React/Vue components** - Rejected: Would require build system, framework dependencies, major refactor of static HTML generation
2. **Web Components** - Rejected: Browser compatibility concerns for generated offline HTML files
3. **Data attributes only** - Rejected: Less declarative than CSS classes for styling

### Implementation Pattern

```javascript
// State representation
const QA_NOTE_STATE = {
  mode: 'preview' | 'edit',  // Current view mode
  hasContent: boolean,        // Determines default mode
  isCollapsed: boolean        // Section visibility
};

// DOM structure
<div class="notes-container" data-mode="preview" data-collapsed="false">
  <div class="notes-header">
    <button class="toggle-mode">Edit</button>
    <button class="toggle-collapse">▼</button>
  </div>
  <div class="notes-content">
    <textarea class="note-edit" style="display: none;">...</textarea>
    <div class="note-preview">...</div>
  </div>
</div>
```

**CSS Classes**:
- `.notes-container[data-mode="edit"]` - Show textarea, hide preview
- `.notes-container[data-mode="preview"]` - Show preview, hide textarea
- `.notes-container[data-collapsed="true"]` - Hide content, show header only
- `.mode-button-active` - Highlight active mode button

---

## 3. LocalStorage Persistence Patterns

### Decision: Per-report keyed persistence with mode/collapse state

**Rationale**:
- Existing notes already use LocalStorage with `tf-notes-${reportId}#${resource}#${attribute}` keys
- Extend existing pattern rather than create new system
- Collapsed state should persist per-report (clarification session)
- Mode state should NOT persist - always use smart defaults (clarification session)

**Current Storage Schema**:
```javascript
// Existing (feature 008)
{
  "question": "Why does this value differ?",
  "answer": "Different environment configuration",
  "lastModified": 1706400000000
}
```

**Extended Schema**:
```javascript
// Add collapse state (mode NOT persisted per clarification)
{
  "question": "## Why differ?\n\n- Config\n- Environment",
  "answer": "**Answer**: Different env vars",
  "lastModified": 1706400000000,
  "isCollapsed": false  // NEW: per-report persistence
}
// Note: mode is NOT stored - determined by content presence on load
```

**Storage Keys**:
- Note data: `tf-notes-${reportId}#${resourceAddress}#${attributeName}`
- Collapse state: Stored within same key (integrated with note data)
- Mode: NOT stored (always computed from content presence)

**Alternatives Considered**:
1. **Separate keys for state** - Rejected: More storage operations, harder to clean up orphaned data
2. **SessionStorage** - Rejected: Loses state on browser close, requirement specifies persistence across refreshes
3. **IndexedDB** - Rejected: Overkill for simple key-value data, more complex API

---

## 4. Collapsible Section Patterns

### Decision: Details/summary elements with JavaScript enhancement

**Rationale**:
- Native HTML `<details>/<summary>` provides accessibility
- Semantic HTML with built-in keyboard navigation
- CSS can override default browser styling
- JavaScript adds state persistence
- Graceful degradation if JavaScript disabled

**Alternatives Considered**:
1. **Pure div + JavaScript** - Rejected: Less accessible, more code, no semantic meaning
2. **Accordion library** - Rejected: Unnecessary dependency for single collapsible section
3. **CSS-only checkbox hack** - Rejected: Can't persist state across reloads

### Implementation Pattern

```html
<details class="notes-container" data-resource="..." data-attribute="...">
  <summary class="notes-header">
    <span class="notes-title">Q&A Notes</span>
    <button class="toggle-mode" onclick="toggleMode(event)">Preview</button>
  </summary>
  <div class="notes-content">
    <!-- textarea and preview content -->
  </div>
</details>

<script>
  // Restore collapsed state from LocalStorage
  function restoreCollapseState(reportId, resource, attribute) {
    const key = `tf-notes-${reportId}#${resource}#${attribute}`;
    const data = JSON.parse(localStorage.getItem(key) || '{}');
    const details = document.querySelector(`[data-resource="${resource}"][data-attribute="${attribute}"]`);
    details.open = !data.isCollapsed;  // Invert because 'open' attribute means expanded
  }
  
  // Save collapsed state when toggled
  details.addEventListener('toggle', (e) => {
    const key = `tf-notes-${reportId}#${resource}#${attribute}`;
    const data = JSON.parse(localStorage.getItem(key) || '{}');
    data.isCollapsed = !e.target.open;  // Store collapsed state
    data.lastModified = Date.now();
    localStorage.setItem(key, JSON.stringify(data));
  });
</script>
```

---

## 5. Save Trigger Mechanisms

### Decision: Multiple save triggers with debouncing

**Rationale** (from clarification session):
- Existing auto-save continues to work (every keystroke with debounce)
- Add explicit save on mode switch (preview→edit or edit→preview)
- Add explicit save on blur (focus leaves textarea)
- Prevents data loss while minimizing storage writes

**Save Points**:
1. **Auto-save (existing)**: 500ms debounce on textarea `oninput`
2. **Mode switch save (NEW)**: Immediate save when clicking toggle button
3. **Blur save (NEW)**: Save when textarea loses focus

### Implementation Pattern

```javascript
// Existing debounced auto-save (keep)
const debouncedSaveNote = debounce(saveNote, 500);

// NEW: Save on mode switch
function toggleMode(event, resource, attribute) {
  event.preventDefault();
  event.stopPropagation();  // Don't trigger details toggle
  
  const textarea = document.getElementById(`note-edit-${resource}-${attribute}`);
  
  // Save before switching modes
  saveNote(resource, attribute, 'question', textarea.value);
  
  // Switch mode
  const container = textarea.closest('.notes-container');
  const currentMode = container.dataset.mode;
  const newMode = currentMode === 'edit' ? 'preview' : 'edit';
  
  if (newMode === 'preview') {
    // Render markdown
    const preview = document.getElementById(`note-preview-${resource}-${attribute}`);
    preview.innerHTML = renderMarkdown(textarea.value);
  }
  
  container.dataset.mode = newMode;
}

// NEW: Save on blur
textarea.addEventListener('blur', () => {
  saveNote(resource, attribute, 'question', textarea.value);
});
```

---

## 6. Smart Default Mode Selection

### Decision: Content-based initialization

**Logic**:
- On page load, check if Q&A note has content
- If content exists → default to preview mode
- If empty/no content → default to edit mode
- This runs on every page load (mode NOT persisted per clarification)

### Implementation Pattern

```javascript
function initializeNoteMode(reportId, resource, attribute) {
  const key = `tf-notes-${reportId}#${resource}#${attribute}`;
  const data = JSON.parse(localStorage.getItem(key) || '{}');
  
  const hasContent = (data.question && data.question.trim()) || 
                     (data.answer && data.answer.trim());
  
  const container = document.querySelector(`[data-resource="${resource}"][data-attribute="${attribute}"]`);
  const defaultMode = hasContent ? 'preview' : 'edit';
  
  container.dataset.mode = defaultMode;
  
  if (defaultMode === 'preview') {
    renderPreview(resource, attribute, data);
  }
}

// Call on page load for all notes
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.notes-container').forEach(container => {
    const resource = container.dataset.resource;
    const attribute = container.dataset.attribute;
    initializeNoteMode(getReportId(), resource, attribute);
  });
});
```

---

## 7. Markdown Styling Best Practices

### Decision: Reuse existing style guide + markdown-specific additions

**Rationale**:
- Project has established style guide (`docs/style-guide.md`)
- Maintain visual consistency with existing HTML report design
- Add markdown-specific styles for preview container

**Style Requirements**:
- Consistent typography (match existing `.json-content` font stacks)
- Code blocks: Match existing monospace font, background colors
- Headings: Use established color palette (#495057 for text)
- Links: Use primary brand color (#667eea)
- Blockquotes: Subtle left border + background (#f8f9fa)
- Spacing: Match existing padding/margin rhythm

**New CSS Classes**:
```css
.note-preview {
  padding: 12px;
  background: white;
  border-radius: 4px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
}

.note-preview h1, .note-preview h2, .note-preview h3 {
  color: #495057;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.note-preview code {
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
}

.note-preview pre {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.note-preview blockquote {
  border-left: 4px solid #667eea;
  padding-left: 12px;
  margin-left: 0;
  color: #6c757d;
}

.note-preview a {
  color: #667eea;
  text-decoration: none;
}

.note-preview a:hover {
  text-decoration: underline;
}
```

---

## 8. Accessibility Considerations

### Decision: WCAG 2.1 AA compliance

**Requirements**:
- Keyboard navigation for mode toggle and collapse
- ARIA labels for screen readers
- Focus indicators for all interactive elements
- Semantic HTML (details/summary)
- Sufficient color contrast (4.5:1 for text)

**Implementation**:
```html
<details class="notes-container" 
         role="group" 
         aria-labelledby="notes-header-${resource}-${attribute}">
  <summary class="notes-header" 
           id="notes-header-${resource}-${attribute}"
           aria-expanded="true">
    <span>Q&A Notes</span>
    <button class="toggle-mode"
            aria-label="Toggle between edit and preview mode"
            aria-pressed="false">
      <span aria-hidden="true">✏️</span> Edit
    </button>
  </summary>
  <div class="notes-content" role="region" aria-live="polite">
    <textarea aria-label="Question field (markdown supported)" ...></textarea>
    <div class="note-preview" role="article" aria-label="Rendered markdown preview">...</div>
  </div>
</details>
```

**Keyboard Shortcuts**:
- Enter/Space on summary: Toggle collapse
- Enter/Space on mode button: Toggle mode
- Tab: Navigate between controls
- Escape (optional): Exit edit mode

---

## Summary of Key Decisions

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Markdown Library** | marked.js + DOMPurify | Smallest size, best compliance, active development |
| **HTML Sanitization** | Strip all HTML tags | Security requirement from clarification |
| **State Management** | DOM data attributes + CSS | Simple, no framework, consistent with codebase |
| **Persistence** | LocalStorage (extend existing) | Reuse proven pattern, per-report keys |
| **Collapse State** | Persist per-report | User preference should survive refresh |
| **Mode State** | Smart default (no persist) | Content-based: empty→edit, existing→preview |
| **Collapsible Pattern** | `<details>/<summary>` | Semantic HTML, accessibility, minimal code |
| **Save Triggers** | Auto + mode-switch + blur | Multi-layered data protection |
| **Styling** | Extend style guide | Visual consistency with existing reports |
| **Accessibility** | WCAG 2.1 AA | Keyboard nav, ARIA, semantic HTML |

---

## Outstanding Questions

None - All clarifications resolved in spec.md clarification session.

---

## Next Phase

Proceed to Phase 1: Design (data-model.md, contracts/, quickstart.md)
