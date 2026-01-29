# CSS Contract: Q&A Notes Markdown Styling

**Feature**: 009-qa-markdown-preview  
**Type**: CSS Stylesheet Contract  
**Date**: 2026-01-28

## Overview

This contract defines CSS classes and styles required for markdown preview, mode toggling, and collapsible Q&A notes sections.

---

## Design Tokens (from style-guide.md)

**Colors** (reuse existing):
```css
--primary: #667eea;
--text-primary: #495057;
--text-secondary: #6c757d;
--background-light: #f8f9fa;
--background-white: #ffffff;
--border-color: #e9ecef;
--link-color: #667eea;
--code-background: #f8f9fa;
```

**Typography**:
```css
--font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
--font-mono: Monaco, Menlo, Consolas, 'Courier New', monospace;
--line-height-body: 1.6;
--line-height-heading: 1.3;
```

**Spacing**:
```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 20px;
```

---

## Modified Classes (Extend Existing)

### .notes-container

**Current** (from get_notes_css()):
```css
.notes-container {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #6c757d;
}
```

**Enhanced** (details element):
```css
details.notes-container {
  margin-top: 15px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  overflow: hidden;
}

details.notes-container[open] {
  border-left: 3px solid #667eea;
}

details.notes-container:not([open]) {
  border-left: 3px solid #6c757d;
}
```

**States**:
- `[open]`: Expanded (blue left border)
- `:not([open])`: Collapsed (gray left border)
- `[data-mode="edit"]`: Edit mode active
- `[data-mode="preview"]`: Preview mode active

---

## New Classes

### .notes-header

**Purpose**: Summary element containing title and mode toggle button

```css
.notes-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  background: #e9ecef;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
  color: #495057;
}

.notes-header:hover {
  background: #dee2e6;
}

.notes-header::marker {
  content: "▼ ";
  font-size: 0.9em;
  color: #6c757d;
}

details.notes-container:not([open]) .notes-header::marker {
  content: "▶ ";
}
```

**Children**:
- `.notes-title`: Text label
- `.toggle-mode`: Mode switch button

---

### .notes-title

**Purpose**: "Q&A Notes" label text

```css
.notes-title {
  font-size: 0.95em;
  color: #495057;
  flex-grow: 1;
}
```

---

### .toggle-mode

**Purpose**: Button to switch between edit and preview modes

```css
.toggle-mode {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-left: 10px;
}

.toggle-mode:hover {
  background: #5568d3;
  transform: translateY(-1px);
}

.toggle-mode:active {
  transform: translateY(0);
}

.toggle-mode:focus {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

/* Active state indicator */
.toggle-mode[aria-pressed="true"] {
  background: #5568d3;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}
```

**Text Content** (managed by JavaScript):
- Edit mode: "Preview" (button shows what clicking will do)
- Preview mode: "Edit"

---

### .notes-content

**Purpose**: Container for editable textareas and preview divs

```css
.notes-content {
  padding: 15px;
  background: white;
}

/* Hide when collapsed */
details.notes-container:not([open]) .notes-content {
  display: none;
}
```

---

### .note-edit

**Purpose**: Textarea for editing markdown (replaces .note-field in edit mode)

```css
.note-edit {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  line-height: 1.5;
  resize: vertical;
  background: white;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  min-height: 100px;
}

.note-edit:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.note-edit::placeholder {
  color: #adb5bd;
  font-style: italic;
}

/* Hide in preview mode */
.notes-container[data-mode="preview"] .note-edit {
  display: none;
}

/* Show in edit mode */
.notes-container[data-mode="edit"] .note-edit {
  display: block;
}
```

---

### .note-preview

**Purpose**: Container for rendered markdown HTML

```css
.note-preview {
  padding: 12px;
  background: white;
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 0.95em;
  line-height: 1.6;
  color: #495057;
  min-height: 50px;
}

/* Hide in edit mode */
.notes-container[data-mode="edit"] .note-preview {
  display: none;
}

/* Show in preview mode */
.notes-container[data-mode="preview"] .note-preview {
  display: block;
}

/* Empty state message */
.note-preview:empty::after {
  content: "No content to preview";
  color: #adb5bd;
  font-style: italic;
}
```

---

## Markdown Content Styles (within .note-preview)

### Headings

```css
.note-preview h1,
.note-preview h2,
.note-preview h3,
.note-preview h4,
.note-preview h5,
.note-preview h6 {
  color: #495057;
  font-weight: 600;
  line-height: 1.3;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.note-preview h1 {
  font-size: 1.75em;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 0.3em;
}

.note-preview h2 {
  font-size: 1.5em;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 0.3em;
}

.note-preview h3 { font-size: 1.25em; }
.note-preview h4 { font-size: 1.1em; }
.note-preview h5 { font-size: 1em; }
.note-preview h6 { font-size: 0.9em; color: #6c757d; }

/* First heading has no top margin */
.note-preview h1:first-child,
.note-preview h2:first-child,
.note-preview h3:first-child {
  margin-top: 0;
}
```

### Paragraphs & Text

```css
.note-preview p {
  margin: 0 0 1em 0;
  line-height: 1.6;
}

.note-preview p:last-child {
  margin-bottom: 0;
}

.note-preview strong {
  font-weight: 600;
  color: #495057;
}

.note-preview em {
  font-style: italic;
}
```

### Lists

```css
.note-preview ul,
.note-preview ol {
  margin: 0 0 1em 0;
  padding-left: 2em;
}

.note-preview ul {
  list-style-type: disc;
}

.note-preview ol {
  list-style-type: decimal;
}

.note-preview li {
  margin: 0.25em 0;
  line-height: 1.5;
}

.note-preview li > p {
  margin: 0.5em 0;
}

/* Nested lists */
.note-preview ul ul,
.note-preview ol ol,
.note-preview ul ol,
.note-preview ol ul {
  margin: 0.5em 0;
}
```

### Code

```css
.note-preview code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #e83e8c;
}

.note-preview pre {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid #e9ecef;
}

.note-preview pre code {
  background: transparent;
  padding: 0;
  color: #495057;
  font-size: 0.85em;
  line-height: 1.5;
}
```

### Blockquotes

```css
.note-preview blockquote {
  margin: 1em 0;
  padding: 0.5em 0 0.5em 1em;
  border-left: 4px solid #667eea;
  background: #f8f9fa;
  color: #6c757d;
  font-style: italic;
}

.note-preview blockquote p {
  margin: 0.5em 0;
}

.note-preview blockquote p:first-child {
  margin-top: 0;
}

.note-preview blockquote p:last-child {
  margin-bottom: 0;
}
```

### Links

```css
.note-preview a {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s, text-decoration 0.2s;
}

.note-preview a:hover {
  color: #5568d3;
  text-decoration: underline;
}

.note-preview a:focus {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

/* External link indicator (optional) */
.note-preview a[href^="http"]::after {
  content: " ↗";
  font-size: 0.8em;
  opacity: 0.6;
}
```

### Horizontal Rules

```css
.note-preview hr {
  border: none;
  border-top: 2px solid #e9ecef;
  margin: 2em 0;
}
```

### Tables (if needed)

```css
.note-preview table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.note-preview th,
.note-preview td {
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  text-align: left;
}

.note-preview th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.note-preview tr:hover {
  background: #f8f9fa;
}
```

---

## Responsive Design

### Mobile (<768px)

```css
@media (max-width: 767px) {
  .notes-header {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .toggle-mode {
    margin-left: 0;
    flex-basis: 100%;
  }
  
  .note-preview {
    font-size: 0.9em;
  }
  
  .note-preview h1 { font-size: 1.5em; }
  .note-preview h2 { font-size: 1.3em; }
  .note-preview h3 { font-size: 1.15em; }
}
```

---

## Accessibility

### Focus Indicators

```css
/* Visible focus for keyboard navigation */
.toggle-mode:focus-visible,
.notes-header:focus-visible {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

/* Remove default outline for mouse users */
.toggle-mode:focus:not(:focus-visible),
.notes-header:focus:not(:focus-visible) {
  outline: none;
}
```

### High Contrast Mode

```css
@media (prefers-contrast: high) {
  .notes-container {
    border: 2px solid currentColor;
  }
  
  .toggle-mode {
    border: 2px solid currentColor;
  }
  
  .note-preview code {
    border: 1px solid currentColor;
  }
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .toggle-mode,
  .notes-header,
  .note-edit {
    transition: none;
  }
}
```

---

## Print Styles

```css
@media print {
  details.notes-container {
    page-break-inside: avoid;
  }
  
  .toggle-mode {
    display: none;
  }
  
  /* Always show content when printing */
  details.notes-container:not([open]) .notes-content {
    display: block;
  }
  
  /* Always show preview, hide edit */
  .note-edit {
    display: none !important;
  }
  
  .note-preview {
    display: block !important;
  }
  
  .notes-header::marker {
    content: "";
  }
}
```

---

## Dark Mode (Future Enhancement)

```css
@media (prefers-color-scheme: dark) {
  details.notes-container {
    background: #2d3748;
    border-color: #4a5568;
  }
  
  .notes-header {
    background: #1a202c;
    color: #e2e8f0;
  }
  
  .notes-content,
  .note-preview {
    background: #2d3748;
    color: #e2e8f0;
  }
  
  .note-edit {
    background: #1a202c;
    border-color: #4a5568;
    color: #e2e8f0;
  }
  
  .note-preview code {
    background: #1a202c;
  }
  
  .note-preview pre {
    background: #1a202c;
    border-color: #4a5568;
  }
  
  .note-preview blockquote {
    background: #1a202c;
    color: #cbd5e0;
  }
}
```

---

## CSS Function Integration

### Python Function: get_notes_markdown_css()

**Location**: `src/lib/html_generation.py`

**Purpose**: Generate complete CSS for markdown-enabled notes

**Signature**:
```python
def get_notes_markdown_css() -> str:
    """
    Get CSS for markdown-enabled Q&A notes with preview/edit toggle.
    
    Returns:
        str: Complete CSS stylesheet including:
            - Notes container with details/summary styling
            - Mode toggle button styles
            - Edit textarea and preview div styles
            - Markdown content formatting (headings, lists, code, etc.)
            - Responsive, accessibility, and print styles
    
    Example:
        >>> css = get_notes_markdown_css()
        >>> "note-preview h1" in css
        True
    """
    return """
        /* CSS content from this contract */
    """
```

**Replaces**: Extends existing `get_notes_css()` function

**Integration Point**: Called from `generate_full_styles()` or directly in HTML template

---

## Class Naming Conventions

**Pattern**: BEM-style with semantic prefixes

- `.notes-*`: Notes section components
- `.note-*`: Individual note elements
- `.toggle-*`: Interactive toggle controls
- `[data-mode]`: State attribute selectors
- `[open]`: Native details state

**Consistency**: Aligns with existing codebase patterns (`.resource-card`, `.diff-column`, etc.)

---

## Browser Compatibility

**Modern Browsers** (95%+ of users):
- Chrome 51+
- Firefox 54+
- Safari 11+
- Edge 79+

**Features Used**:
- CSS Grid (for responsive layouts)
- CSS Custom Properties (for theming)
- Details/Summary elements
- CSS Flexbox
- CSS Transitions

**Fallbacks**: None required for target browsers

---

## Performance Considerations

**Optimization**:
- No expensive selectors (avoid universal `*`, complex nesting)
- CSS-only animations (no JavaScript reflow)
- Hardware-accelerated transforms
- Minimal specificity conflicts

**File Size**: ~5KB unminified CSS (minimal addition to existing stylesheet)

---

## Testing Requirements

### Visual Regression Tests

1. Edit mode: Textarea visible, preview hidden
2. Preview mode: Preview visible, textarea hidden
3. Collapsed state: Only header visible
4. Expanded state: Full content visible
5. Empty preview: "No content" placeholder
6. Markdown rendering: All element types styled correctly

### Cross-Browser Testing

Test in Chrome, Firefox, Safari, Edge:
- Mode toggle functionality
- Collapse/expand animation
- Focus indicators
- Print layout
- Responsive breakpoints

### Accessibility Tests

- Keyboard navigation (Tab, Enter, Space)
- Screen reader announcement (ARIA labels)
- High contrast mode rendering
- Reduced motion preference
