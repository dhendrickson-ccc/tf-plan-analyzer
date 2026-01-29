# Quickstart Guide: Q&A Notes with Markdown Support

**Feature**: 009-qa-markdown-preview  
**Audience**: Developers implementing this feature  
**Date**: 2026-01-28

## Overview

This guide provides a step-by-step walkthrough for implementing markdown support in Q&A notes with preview/edit toggle and collapsible sections.

---

## Prerequisites

- Python 3.9+ with virtual environment activated
- Existing Q&A notes feature (Feature 008) working
- Understanding of HTML generation patterns in `src/lib/html_generation.py`
- Understanding of multi-environment comparison in `src/core/multi_env_comparator.py`

---

## Architecture Quick Reference

```
┌─────────────────────────────────────────────────┐
│          HTML Generation (Python)               │
│  src/lib/html_generation.py                     │
│  ├─ get_notes_markdown_css()    [NEW]          │
│  ├─ get_notes_markdown_javascript() [NEW]      │
│  └─ generate_full_styles()      [MODIFIED]     │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│     Multi-Env Comparator (Python)               │
│  src/core/multi_env_comparator.py               │
│  └─ _render_attribute_section() [MODIFIED]     │
│      └─ Generates <details> with mode toggle   │
└─────────────────────────────────────────────────┘
                     │
                     ▼ Generates HTML file
┌─────────────────────────────────────────────────┐
│     Generated HTML (Client-Side)                │
│  ┌───────────────────────────────────────────┐ │
│  │  marked.js (CDN)                          │ │
│  │  DOMPurify (CDN)                          │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  JavaScript Functions:                    │ │
│  │  ├─ renderMarkdown()                      │ │
│  │  ├─ toggleNoteMode()                      │ │
│  │  ├─ initializeNoteMode()                  │ │
│  │  ├─ saveCollapseState()                   │ │
│  │  ├─ restoreCollapseState()                │ │
│  │  └─ saveNoteWithBlur()                    │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  LocalStorage:                            │ │
│  │  tf-notes-{report}#{resource}#{attr}     │ │
│  │  {                                        │ │
│  │    question: "# Markdown text",           │ │
│  │    answer: "**Answer**",                  │
│  │    isCollapsed: false                     │ │
│  │  }                                        │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Python CSS/JS Generation Functions

**Location**: `src/lib/html_generation.py`

**Step 1.1**: Create markdown CSS function

```python
def get_notes_markdown_css() -> str:
    """
    Get CSS for markdown-enabled Q&A notes.
    
    Returns complete CSS from contracts/css-styling.md
    including details/summary, mode toggle, markdown preview styles.
    """
    return """
        /* Copy CSS from contracts/css-styling.md */
        details.notes-container {
            ...
        }
        .note-preview h1 {
            ...
        }
        /* etc. */
    """
```

**Step 1.2**: Create markdown JavaScript function

```python
def get_notes_markdown_javascript() -> str:
    """
    Get JavaScript for markdown rendering and mode toggling.
    
    Returns complete JS from contracts/javascript-api.md
    including marked.js/DOMPurify integration, toggle logic, state management.
    """
    return """
        <script src="https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>
        <script>
        function renderMarkdown(rawMarkdown) {
            /* Implementation from contracts/javascript-api.md */
        }
        
        function toggleNoteMode(event, resource, attribute) {
            /* Implementation from contracts/javascript-api.md */
        }
        
        /* Other functions... */
        </script>
    """
```

**Step 1.3**: Integrate into full styles

```python
def generate_full_styles() -> str:
    """
    Existing function - add markdown CSS.
    """
    return f"""
        <style>
        {get_badge_css()}
        {get_summary_card_css()}
        /* ... other CSS ... */
        {get_notes_css()}  # Existing
        {get_notes_markdown_css()}  # NEW
        </style>
    """
```

**Testing**:
```python
# In tests/unit/test_html_generation.py
def test_get_notes_markdown_css():
    css = get_notes_markdown_css()
    assert "details.notes-container" in css
    assert ".note-preview h1" in css
    assert ".toggle-mode" in css

def test_get_notes_markdown_javascript():
    js = get_notes_markdown_javascript()
    assert "function renderMarkdown" in js
    assert "function toggleNoteMode" in js
    assert "marked.umd.js" in js
    assert "dompurify" in js
```

---

### Phase 2: Modify HTML Generation

**Location**: `src/core/multi_env_comparator.py`

**Step 2.1**: Update `_render_attribute_section()` method

**Current Structure** (simplified):
```python
def _render_attribute_section(...):
    # ... existing code ...
    
    # Add notes container
    parts.append('<div class="notes-container">')
    parts.append(f'<label>Question:</label>')
    parts.append(f'<textarea id="note-q-..." oninput="..."></textarea>')
    parts.append(f'<label>Answer:</label>')
    parts.append(f'<textarea id="note-a-..." oninput="..."></textarea>')
    parts.append('</div>')
```

**New Structure**:
```python
def _render_attribute_section(...):
    # ... existing code ...
    
    sanitized_resource = self._sanitize_for_html_id(rc.resource_address)
    sanitized_attribute = self._sanitize_for_html_id(attr_diff.attribute_name)
    
    # Change to details/summary with mode toggle
    parts.append(f'<details class="notes-container" ')
    parts.append(f'        data-resource="{rc.resource_address}" ')
    parts.append(f'        data-attribute="{attr_diff.attribute_name}" ')
    parts.append(f'        data-mode="preview" ')
    parts.append(f'        open>')
    
    # Summary header with toggle button
    parts.append('  <summary class="notes-header">')
    parts.append('    <span class="notes-title">Q&A Notes</span>')
    parts.append(f'   <button class="toggle-mode" ')
    parts.append(f'           onclick="toggleNoteMode(event, \'{rc.resource_address}\', \'{attr_diff.attribute_name}\')" ')
    parts.append(f'           aria-label="Toggle between edit and preview mode" ')
    parts.append(f'           aria-pressed="false">')
    parts.append('      Edit')
    parts.append('    </button>')
    parts.append('  </summary>')
    
    # Content area
    parts.append('  <div class="notes-content">')
    
    # Question field (edit mode)
    parts.append('    <div>')
    parts.append(f'     <label class="note-label" for="note-q-{sanitized_resource}-{sanitized_attribute}">Question:</label>')
    parts.append(f'     <textarea class="note-edit" ')
    parts.append(f'               id="note-q-{sanitized_resource}-{sanitized_attribute}" ')
    parts.append(f'               placeholder="Add a question (markdown supported)..." ')
    parts.append(f'               oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'question\', this.value)" ')
    parts.append(f'               onblur="saveNoteWithBlur(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'question\')" ')
    parts.append(f'               rows="4"></textarea>')
    
    # Question preview (preview mode)
    parts.append(f'     <div class="note-preview" id="note-preview-q-{sanitized_resource}-{sanitized_attribute}"></div>')
    parts.append('    </div>')
    
    # Answer field (edit mode)
    parts.append('    <div class="note-answer">')
    parts.append(f'     <label class="note-label" for="note-a-{sanitized_resource}-{sanitized_attribute}">Answer:</label>')
    parts.append(f'     <textarea class="note-edit" ')
    parts.append(f'               id="note-a-{sanitized_resource}-{sanitized_attribute}" ')
    parts.append(f'               placeholder="Add an answer (markdown supported)..." ')
    parts.append(f'               oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'answer\', this.value)" ')
    parts.append(f'               onblur="saveNoteWithBlur(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'answer\')" ')
    parts.append(f'               rows="4"></textarea>')
    
    # Answer preview (preview mode)
    parts.append(f'     <div class="note-preview" id="note-preview-a-{sanitized_resource}-{sanitized_attribute}"></div>')
    parts.append('    </div>')
    
    parts.append('  </div>')  # Close notes-content
    parts.append('</details>')  # Close notes-container
```

**Step 2.2**: Include markdown JavaScript in HTML template

Update the method that generates the complete HTML (likely in `generate_comparison_html()`):

```python
def generate_comparison_html(...):
    # ... existing code ...
    
    html_parts.append(f"    {src.lib.html_generation.get_notes_javascript()}")  # Existing
    html_parts.append(f"    {src.lib.html_generation.get_notes_markdown_javascript()}")  # NEW
    
    # ... rest of HTML ...
```

**Testing**:
```python
# In tests/e2e/test_e2e_qa_markdown.py
def test_qa_notes_html_structure():
    """Test that generated HTML includes markdown-enabled structure."""
    # Generate comparison report
    result = generate_test_comparison_html()
    
    # Verify structure
    assert '<details class="notes-container"' in result
    assert 'data-mode="preview"' in result
    assert '<button class="toggle-mode"' in result
    assert 'onclick="toggleNoteMode(' in result
    assert '<textarea class="note-edit"' in result
    assert '<div class="note-preview"' in result
    assert 'onblur="saveNoteWithBlur(' in result
```

---

### Phase 3: End-to-End Testing

**Step 3.1**: Create test HTML file

```python
# tests/e2e/test_e2e_qa_markdown.py

def test_markdown_rendering_full_workflow():
    """
    Generate an actual HTML file, open in browser,
    verify markdown rendering works.
    """
    # Setup test data
    env_plans = create_test_environment_plans_with_diffs()
    
    # Generate HTML
    comparator = MultiEnvComparator(env_plans)
    html_output = comparator.generate_comparison_html()
    
    # Write to file
    test_file = Path("test-markdown-notes.html")
    test_file.write_text(html_output)
    
    # Manual verification step (or use Selenium/Playwright)
    # Open test-markdown-notes.html in browser
    # 1. Verify edit mode shows textareas
    # 2. Enter markdown: "# Hello\n\n**World**"
    # 3. Click "Preview" button
    # 4. Verify rendered output shows <h1> and <strong>
    # 5. Click collapse arrow
    # 6. Refresh page
    # 7. Verify collapsed state persists
    
    assert test_file.exists()
    assert "function renderMarkdown" in html_output
    assert "marked.umd.js" in html_output
```

**Step 3.2**: Test markdown rendering

```python
def test_markdown_content_types():
    """Test all supported markdown syntax renders correctly."""
    test_cases = [
        ("# Heading 1", "<h1>Heading 1</h1>"),
        ("**Bold**", "<strong>Bold</strong>"),
        ("*Italic*", "<em>Italic</em>"),
        ("`code`", "<code>code</code>"),
        ("- List item", "<li>List item</li>"),
        ("> Quote", "<blockquote>"),
        ("[Link](http://example.com)", '<a href="http://example.com">'),
    ]
    
    # These would be tested in browser environment
    # or using a headless browser like Playwright
```

**Step 3.3**: Test XSS prevention

```python
def test_html_sanitization():
    """Verify HTML tags are stripped."""
    malicious_inputs = [
        '<script>alert("xss")</script>',
        '<img src=x onerror="alert(1)">',
        '<iframe src="evil.com"></iframe>',
        '<a href="javascript:alert(1)">Click</a>',
    ]
    
    # Generate HTML with these inputs
    # Verify in output that:
    # 1. Script tags are completely removed
    # 2. Event handlers are stripped
    # 3. Dangerous elements are removed
```

---

### Phase 4: Documentation Updates

**Step 4.1**: Update function glossary

Add to `docs/function-glossary.md`:

```markdown
### get_notes_markdown_css()

**Module**: `src.lib.html_generation`

**Purpose**: Generate CSS for markdown-enabled Q&A notes

**Parameters**: None

**Returns**: `str` - Complete CSS stylesheet

**Example**:
```python
css = get_notes_markdown_css()
assert ".note-preview h1" in css
```

**Related**:
- `get_notes_css()` - Original notes CSS
- `generate_full_styles()` - Integrates all CSS

---

### get_notes_markdown_javascript()

**Module**: `src.lib.html_generation`

**Purpose**: Generate JavaScript for markdown rendering and mode toggling

**Parameters**: None

**Returns**: `str` - Complete JavaScript including CDN links and functions

**Example**:
```python
js = get_notes_markdown_javascript()
assert "function renderMarkdown" in js
```

**Related**:
- `get_notes_javascript()` - Original notes JS
```

**Step 4.2**: Update style guide

Add to `docs/style-guide.md`:

```markdown
## Q&A Notes Markdown Preview

### Component: .note-preview

Markdown-rendered content within Q&A notes.

**Usage**:
```html
<div class="note-preview">
  <h1>Rendered Markdown</h1>
  <p><strong>Bold text</strong></p>
</div>
```

**Styling**:
- Headings: Use text-primary color (#495057)
- Code blocks: Use code-background (#f8f9fa)
- Links: Use primary brand color (#667eea)
- Blockquotes: Left border with primary color

**States**:
- Visible when `data-mode="preview"`
- Hidden when `data-mode="edit"`
```

**Step 4.3**: Update README (optional)

Add section to main README.md:

```markdown
### Q&A Notes with Markdown

Q&A notes support markdown formatting for better documentation:

- **Headings**: `# H1`, `## H2`, `### H3`
- **Emphasis**: `**bold**`, `*italic*`
- **Lists**: `- item` or `1. item`
- **Code**: `` `inline` `` or triple backticks for blocks
- **Links**: `[text](url)`
- **Blockquotes**: `> quote`

Toggle between edit and preview modes using the button in the notes header.
Notes automatically save as you type and when you switch modes.
```

---

## Testing Checklist

### Unit Tests (Python)

- [ ] `test_get_notes_markdown_css()` - CSS function returns valid styles
- [ ] `test_get_notes_markdown_javascript()` - JS function includes all required functions
- [ ] `test_render_attribute_section_includes_markdown_structure()` - HTML generation correct

### Integration Tests (Python + HTML)

- [ ] `test_generated_html_includes_cdn_links()` - marked.js and DOMPurify present
- [ ] `test_generated_html_includes_data_attributes()` - resource/attribute data attributes
- [ ] `test_generated_html_includes_event_handlers()` - onclick, onblur handlers present

### End-to-End Tests (Browser)

- [ ] Open HTML file → Q&A notes in preview mode if content exists
- [ ] Open HTML file → Q&A notes in edit mode if empty
- [ ] Click "Edit" button → Switch to edit mode, show textareas
- [ ] Type markdown → Auto-save to LocalStorage
- [ ] Click "Preview" button → Render markdown, hide textareas
- [ ] Verify markdown rendering: headings, bold, lists, code blocks, links
- [ ] Enter HTML tags → Verify stripped/sanitized in preview
- [ ] Blur textarea → Verify blur save triggered
- [ ] Click collapse arrow → Section collapses
- [ ] Refresh page → Collapsed state persists
- [ ] Refresh page with content → Defaults to preview mode
- [ ] Keyboard navigation → Tab through controls, Enter/Space toggles

### Accessibility Tests

- [ ] Screen reader announces mode changes
- [ ] Keyboard-only navigation works
- [ ] Focus indicators visible
- [ ] ARIA labels present and correct

---

## Common Pitfalls & Solutions

### Pitfall 1: Event Propagation on Toggle Button

**Problem**: Clicking toggle button also triggers details collapse

**Solution**: Use `event.stopPropagation()` in toggleNoteMode()

```javascript
function toggleNoteMode(event, resource, attribute) {
  event.preventDefault();
  event.stopPropagation();  // CRITICAL: Don't trigger details toggle
  // ... rest of function
}
```

### Pitfall 2: Escaping Single Quotes in HTML Generation

**Problem**: Resource addresses with single quotes break onclick handlers

**Solution**: Use proper escaping or double quotes

```python
# Bad
parts.append(f"onclick=\"toggleNoteMode(event, '{resource}', '{attribute}')\"")

# Good - escape single quotes
resource_escaped = resource.replace("'", "\\'")
parts.append(f"onclick=\"toggleNoteMode(event, '{resource_escaped}', ...)\"")

# Better - use JavaScript template literals in Python
parts.append(f"onclick='toggleNoteMode(event, `{resource}`, `{attribute}`)'")
```

### Pitfall 3: CDN Loading Failures

**Problem**: marked.js or DOMPurify fails to load from CDN

**Solution**: Add fallback error handling

```javascript
window.addEventListener('load', () => {
  if (typeof marked === 'undefined') {
    console.error('marked.js failed to load from CDN');
    // Disable markdown preview, stay in edit mode
  }
  if (typeof DOMPurify === 'undefined') {
    console.error('DOMPurify failed to load from CDN');
    // Disable markdown preview, stay in edit mode
  }
});
```

### Pitfall 4: LocalStorage Quota Exceeded

**Problem**: Large markdown content fills LocalStorage quota

**Solution**: Catch quota errors gracefully

```javascript
try {
  localStorage.setItem(key, JSON.stringify(data));
} catch (e) {
  if (e.name === 'QuotaExceededError') {
    console.error('LocalStorage quota exceeded');
    alert('Note too large to save. Please shorten content.');
  }
}
```

---

## Performance Optimization Tips

1. **Lazy Load Notes**: Only initialize markdown rendering for visible notes
2. **Debounce Rendering**: Don't re-render on every keystroke, use debounce
3. **Cache Rendered HTML**: Store rendered output to avoid re-parsing
4. **Limit Note Size**: Consider max character limit (e.g., 10KB)

---

## Next Steps

After implementation:

1. Run full test suite: `pytest tests/`
2. Generate sample HTML report with markdown notes
3. Test in multiple browsers (Chrome, Firefox, Safari)
4. Verify accessibility with screen reader
5. Update agent context: `.specify/scripts/bash/update-agent-context.sh copilot`
6. Commit work: `git commit -m "feat: add markdown support to Q&A notes"`
7. Update CHANGELOG.md with feature description

---

## Support Resources

- **Markdown Specification**: https://commonmark.org/
- **marked.js Docs**: https://marked.js.org/
- **DOMPurify Docs**: https://github.com/cure53/DOMPurify
- **Details Element MDN**: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details
- **LocalStorage API**: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
