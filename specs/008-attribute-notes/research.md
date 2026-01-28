# Research: Attribute Change Notes

**Date**: January 28, 2026  
**Purpose**: Research existing implementation patterns for adding client-side notes functionality to HTML comparison reports

---

## 1. Current HTML Generation Structure for Attributes

### Attribute Rendering in MultiEnvReport

**Location**: `src/core/multi_env_comparator.py`, lines 1240-1380

The `_render_attribute_table()` method generates HTML for each attribute in a resource comparison:

```python
def _render_attribute_table(self, rc: "ResourceComparison", env_labels: List[str]) -> str:
    """
    Render attribute-level diff sections for a resource (v2.0).
    Uses header-based flexbox layout instead of tables for better readability.
    Each attribute becomes a section with H3 header and horizontally aligned values.
    """
    parts = []
    parts.append('                    <div class="attribute-table-container">')
    
    # ... iterate through rc.attribute_diffs ...
    
    for attr_diff in rc.attribute_diffs:
        # Start attribute section
        parts.append(f'                        <div class="{section_class}">')
        
        # Attribute header (H3 with attribute name)
        parts.append('                            <h3 class="attribute-header">')
        parts.append(f"                                <code>{html.escape(attr_diff.attribute_name)}</code>")
        parts.append("                            </h3>")
        
        # Attribute values container (flexbox)
        parts.append('                            <div class="attribute-values">')
        
        # Value columns for each environment
        for env_label in env_labels:
            value_html = self._render_attribute_value(value, attr_diff, env_labels, env_label)
            parts.append('                                <div class="env-value-column">')
            parts.append(f'                                    <div class="env-label">{html.escape(env_label)}</div>')
            parts.append(f'                                    {value_html}')
            parts.append('                                </div>')
        
        parts.append('                            </div>')  # Close attribute-values
        parts.append('                        </div>')  # Close attribute-section
```

**Key Structure**:
- Each attribute is wrapped in `.attribute-section`
- Header shows attribute name in `<code>` tag
- Values displayed in `.attribute-values` flexbox container
- Each environment gets `.env-value-column` div

**Injection Point for Notes**: After the `.attribute-values` div closes, before the `.attribute-section` div closes

---

## 2. LocalStorage API and Key Structure

### LocalStorage Best Practices

**API Overview**:
- `localStorage.setItem(key, value)` - Store data (value must be string)
- `localStorage.getItem(key)` - Retrieve data (returns null if not found)
- `localStorage.removeItem(key)` - Delete data
- Storage limit: ~5-10MB per origin (browser-dependent)

**Auto-Save with Debouncing**:

```javascript
// Debounce utility to prevent excessive writes
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Auto-save function with debouncing
const debouncedSave = debounce(function(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (e) {
        console.error('LocalStorage quota exceeded', e);
    }
}, 500);  // 500ms delay
```

### Key Naming Convention

**Decision**: Use composite key pattern with `#` separator

**Format**: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`

**Examples**:
- `tf-notes-comparison.html#azurerm_storage_account.main#location`
- `tf-notes-stage-prod.html#aws_instance.web#instance_type`

**Rationale**:
- `tf-notes-` prefix prevents collisions with other tools
- `reportId` from filename ensures notes are version-specific
- `#{resource}#{attribute}` creates unique key per attribute
- `#` separator allows easy parsing if needed

### Data Structure

**Stored Value**: JSON string

```json
{
  "question": "Why is location different in prod?",
  "answer": "Historical decision - prod was in westus before eastus datacenter opened",
  "lastModified": 1706486400000
}
```

**Access Pattern**:

```javascript
// Save
function saveNote(resourceAddress, attributeName, field, value) {
    const reportId = getReportId();
    const key = `tf-notes-${reportId}#${resourceAddress}#${attributeName}`;
    const existing = localStorage.getItem(key);
    const note = existing ? JSON.parse(existing) : { question: '', answer: '' };
    note[field] = value;
    note.lastModified = Date.now();
    localStorage.setItem(key, JSON.stringify(note));
}

// Load
function loadNotes() {
    const reportId = getReportId();
    const prefix = `tf-notes-${reportId}#`;
    
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(prefix)) {
            const noteData = JSON.parse(localStorage.getItem(key));
            const [, resourceAndAttr] = key.split(`${prefix}`);
            const [resource, attribute] = resourceAndAttr.split('#');
            
            // Populate textareas
            const questionField = document.getElementById(`note-q-${resource}-${attribute}`);
            const answerField = document.getElementById(`note-a-${resource}-${attribute}`);
            if (questionField) questionField.value = noteData.question || '';
            if (answerField) answerField.value = noteData.answer || '';
        }
    }
}
```

---

## 3. CSS Organization and Extension Pattern

### Current CSS Structure

**Location**: `src/lib/html_generation.py`

**Organization**:
- Separate function for each major CSS component
- `get_base_css()` - Core layout, typography, colors
- `get_summary_card_css()` - Summary statistics cards
- `get_diff_highlight_css()` - Character-level diff highlighting
- `get_resource_card_css()` - Resource card styling
- `get_attribute_section_css()` - Attribute section layout (added in feature 006)
- `generate_full_styles()` - Aggregates all CSS functions

**Extension Pattern**:

```python
def get_notes_css() -> str:
    """Generate CSS for question/answer notes fields."""
    return """
        /* Notes container */
        .notes-container {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #6c757d;
        }
        
        /* Notes textareas */
        .note-field {
            width: 100%;
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.9em;
            resize: vertical;
            min-height: 80px;  /* ~3-5 rows */
        }
        
        .note-field:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
        }
        
        .note-field::placeholder {
            color: #868e96;
            font-style: italic;
        }
        
        /* Notes labels */
        .note-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
            font-size: 0.85em;
        }
        
        /* Spacing between question and answer */
        .note-answer {
            margin-top: 12px;
        }
    """
```

**Integration**:

```python
def generate_full_styles() -> str:
    """Generate complete stylesheet for HTML reports."""
    return "\n".join([
        get_base_css(),
        get_summary_card_css(),
        get_diff_highlight_css(),
        get_resource_card_css(),
        get_attribute_section_css(),
        get_scrollable_container_css(),
        get_sticky_header_css(),
        get_env_specific_section_css(),
        get_notes_css(),  # NEW
    ])
```

---

## 4. Existing JavaScript in HTML Reports

### Current JavaScript Usage

**Location**: Embedded in HTML generated by `MultiEnvReport.generate_html()`

**Example** (lines ~950-970 in `multi_env_comparator.py`):

```python
html_parts.append("""
    <script>
        function toggleResource(header) {
            const icon = header.querySelector('.toggle-icon');
            const content = header.nextElementSibling;
            
            if (icon.classList.contains('collapsed')) {
                icon.classList.remove('collapsed');
                content.style.display = 'block';
            } else {
                icon.classList.add('collapsed');
                content.style.display = 'none';
            }
        }
    </script>
""")
```

**Pattern**: 
- JavaScript embedded in `<script>` tag in HTML head or before `</body>`
- Simple vanilla JS (no frameworks)
- DOM manipulation via `querySelector` and `getElementById`

### Proposed JavaScript Functions

**Location**: New function `get_notes_javascript()` in `src/lib/html_generation.py`

```python
def get_notes_javascript() -> str:
    """Generate JavaScript for notes auto-save and load functionality."""
    return """
    <script>
        // Extract report filename from URL for LocalStorage key
        function getReportId() {
            const path = window.location.pathname;
            const filename = path.substring(path.lastIndexOf('/') + 1);
            return filename || 'unknown-report';
        }
        
        // Debounce utility
        function debounce(func, delay) {
            let timeoutId;
            return function(...args) {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        }
        
        // Save note to LocalStorage
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
        
        // Debounced save (500ms delay)
        const debouncedSaveNote = debounce(saveNote, 500);
        
        // Load all notes on page load
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
        
        // Load notes when page loads
        document.addEventListener('DOMContentLoaded', loadNotes);
    </script>
    """
```

---

## 5. Report Filename Extraction from Browser Context

### Challenge

Static HTML files opened via `file://` protocol need to extract filename for LocalStorage keys.

### Solution: window.location.pathname

**Browser Behavior**:
- `file:///Users/user/reports/comparison.html` → `window.location.pathname` = `/Users/user/reports/comparison.html`
- Extract filename: `comparison.html`

**Implementation**:

```javascript
function getReportId() {
    const path = window.location.pathname;
    const filename = path.substring(path.lastIndexOf('/') + 1);
    return filename || 'unknown-report';
}
```

**Edge Cases**:
- If opened from browser history or bookmark, pathname may be empty → fallback to `'unknown-report'`
- Works across all major browsers (Chrome, Firefox, Safari, Edge)

**Alternative Considered**: Using `document.title` or embedding report ID in HTML meta tag
- **Rejected**: Requires modifying HTML generation to embed unique ID; filename is simpler and sufficient

---

## Decision Summary

### 1. HTML Injection Point
**Decision**: Add notes container after `.attribute-values` div, before `.attribute-section` closes  
**Rationale**: Keeps notes visually associated with attribute but doesn't interrupt environment value comparison

### 2. LocalStorage Key Pattern
**Decision**: `tf-notes-{reportId}#{resourceAddress}#{attributeName}`  
**Rationale**: Composite key ensures uniqueness, `#` separator allows parsing, report ID isolates versions

### 3. Auto-Save Mechanism
**Decision**: Debounced auto-save with 500ms delay on textarea `input` event  
**Rationale**: Balances UX (no manual save button) with performance (prevents excessive writes)

### 4. CSS Organization
**Decision**: New `get_notes_css()` function added to `html_generation.py`  
**Rationale**: Follows existing pattern of modular CSS functions, easy to maintain and test

### 5. JavaScript Placement
**Decision**: New `get_notes_javascript()` function, embedded in HTML `<head>` or before `</body>`  
**Rationale**: Consistent with existing `toggleResource()` pattern, no external dependencies

---

## Gotchas & Risks

### 1. LocalStorage Quota Limits
**Risk**: If users add extensive notes across many reports, LocalStorage may exceed quota (~5-10MB)  
**Mitigation**: 
- Document this limitation in user-facing docs
- JavaScript catches quota errors and logs to console
- Typical usage (100-500 char notes) unlikely to hit limits

### 2. Filename Collisions
**Risk**: Two reports with same filename but different content → notes may apply incorrectly  
**Mitigation**:
- Document best practice: use descriptive unique filenames (e.g., `comparison-2026-01-28.html`)
- Consider future enhancement: content hash in meta tag

### 3. Special Characters in Resource/Attribute Names
**Risk**: Resource addresses with special chars (e.g., `aws_instance.web[0]`) may cause ID issues  
**Mitigation**:
- Sanitize IDs: replace `[`, `]`, `.` with safe chars (`-` or `_`)
- Example: `note-q-aws_instance-web-0-instance_type`

### 4. Browser Compatibility
**Risk**: Older browsers may not support LocalStorage or arrow functions  
**Mitigation**:
- Target modern browsers only (Chrome, Firefox, Safari, Edge - last 2 versions)
- Document minimum browser requirements

---

## Files to Modify

### Python Files

1. **src/lib/html_generation.py**
   - Add `get_notes_css()` function
   - Add `get_notes_javascript()` function
   - Update `generate_full_styles()` to include notes CSS

2. **src/core/multi_env_comparator.py**
   - Modify `_render_attribute_table()` to inject notes HTML after attribute values
   - Sanitize resource/attribute names for HTML IDs

### Test Files

3. **tests/unit/test_html_generation.py**
   - Add tests for `get_notes_css()` function
   - Add tests for `get_notes_javascript()` function

4. **tests/e2e/test_e2e_attribute_notes.py** (NEW)
   - E2E test: Generate HTML report and verify notes fields exist
   - E2E test: Verify JavaScript functions are embedded
   - E2E test: Verify textarea IDs are correctly generated

### Documentation Files

5. **docs/function-glossary.md**
   - Document `get_notes_css()` and `get_notes_javascript()` functions

6. **docs/style-guide.md**
   - Add `.notes-container`, `.note-field`, `.note-label` CSS class documentation

---

## Next Steps

1. Create `data-model.md` - Define AttributeNote entity and LocalStorage schema
2. Create `contracts/` - Define HTML structure, JavaScript API, and LocalStorage schema contracts
3. Create `quickstart.md` - Step-by-step implementation guide with code examples
4. Update `.specify/memory/data_model.md` - Add AttributeNote to canonical data model
