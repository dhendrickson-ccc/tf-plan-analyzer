# HTML Structure Contract: Attribute Notes

**Feature**: 008-attribute-notes  
**Version**: 1.0  
**Created**: January 28, 2026

---

## Overview

This contract defines the HTML structure for question/answer notes fields added to each attribute in multi-environment comparison reports.

---

## Notes Container Structure

### Placement

**Location**: Within `.attribute-section` div, after `.attribute-values` div closes

**Before** (existing):
```html
<div class="attribute-section">
    <h3 class="attribute-header">
        <code>location</code>
    </h3>
    <div class="attribute-values">
        <!-- Environment value columns -->
    </div>
</div>
```

**After** (with notes):
```html
<div class="attribute-section">
    <h3 class="attribute-header">
        <code>location</code>
    </h3>
    <div class="attribute-values">
        <!-- Environment value columns -->
    </div>
    
    <!-- NEW: Notes container -->
    <div class="notes-container">
        <div>
            <label class="note-label" for="note-q-{sanitized_resource}-{sanitized_attribute}">
                Question:
            </label>
            <textarea 
                class="note-field" 
                id="note-q-{sanitized_resource}-{sanitized_attribute}"
                placeholder="Add a question..."
                oninput="debouncedSaveNote('{resource_address}', '{attribute_name}', 'question', this.value)"
                rows="4"></textarea>
        </div>
        <div class="note-answer">
            <label class="note-label" for="note-a-{sanitized_resource}-{sanitized_attribute}">
                Answer:
            </label>
            <textarea 
                class="note-field" 
                id="note-a-{sanitized_resource}-{sanitized_attribute}"
                placeholder="Add an answer..."
                oninput="debouncedSaveNote('{resource_address}', '{attribute_name}', 'answer', this.value)"
                rows="4"></textarea>
        </div>
    </div>
</div>
```

---

## HTML Element Specifications

### `.notes-container`

**Tag**: `<div>`  
**Class**: `notes-container`  
**Purpose**: Wrapper for question and answer fields

**CSS**:
```css
.notes-container {
    margin-top: 15px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 4px;
    border-left: 3px solid #6c757d;
}
```

---

### `.note-label`

**Tag**: `<label>`  
**Class**: `note-label`  
**Attributes**:
- `for`: ID of associated textarea (e.g., `note-q-azurerm_storage_account-main-location`)

**Text Content**:
- Question label: `"Question:"`
- Answer label: `"Answer:"`

**CSS**:
```css
.note-label {
    display: block;
    margin-bottom: 5px;
    font-weight: 600;
    color: #495057;
    font-size: 0.85em;
}
```

---

### `.note-field` (Question Textarea)

**Tag**: `<textarea>`  
**Class**: `note-field`  
**ID**: `note-q-{sanitized_resource}-{sanitized_attribute}`  
**Attributes**:
- `placeholder`: `"Add a question..."`
- `oninput`: `debouncedSaveNote('{resource}', '{attribute}', 'question', this.value)`
- `rows`: `4` (approx 3-5 visible rows)

**Example**:
```html
<textarea 
    class="note-field" 
    id="note-q-azurerm_storage_account-main-location"
    placeholder="Add a question..."
    oninput="debouncedSaveNote('azurerm_storage_account.main', 'location', 'question', this.value)"
    rows="4"></textarea>
```

**CSS**:
```css
.note-field {
    width: 100%;
    padding: 8px;
    border: 1px solid #ced4da;
    border-radius: 3px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 0.9em;
    resize: vertical;
    min-height: 80px;
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
```

---

### `.note-field` (Answer Textarea)

**Tag**: `<textarea>`  
**Class**: `note-field`  
**ID**: `note-a-{sanitized_resource}-{sanitized_attribute}`  
**Attributes**:
- `placeholder`: `"Add an answer..."`
- `oninput`: `debouncedSaveNote('{resource}', '{attribute}', 'answer', this.value)`
- `rows`: `4` (approx 3-5 visible rows)

**Parent Wrapper**:
- `<div class="note-answer">` - Adds spacing between question and answer

**CSS** (for wrapper):
```css
.note-answer {
    margin-top: 12px;
}
```

---

## ID Naming Convention

### Pattern

`note-{type}-{sanitized_resource}-{sanitized_attribute}`

Where:
- `{type}`: `q` (question) or `a` (answer)
- `{sanitized_resource}`: Resource address with special chars replaced
- `{sanitized_attribute}`: Attribute name with special chars replaced

### Sanitization Rules

Replace the following characters with `-`:
- `.` (dot)
- `[` (left bracket)
- `]` (right bracket)
- `:` (colon)
- `/` (slash)

**Examples**:

| Resource Address | Attribute | Question ID |
|-----------------|-----------|-------------|
| `azurerm_storage_account.main` | `location` | `note-q-azurerm_storage_account-main-location` |
| `aws_instance.web[0]` | `instance_type` | `note-q-aws_instance-web-0--instance_type` |
| `module.vpc.aws_vpc.main` | `cidr_block` | `note-q-module-vpc-aws_vpc-main-cidr_block` |

### Python Implementation

```python
def sanitize_for_html_id(text: str) -> str:
    """Sanitize text for use in HTML ID attribute."""
    return text.replace('.', '-').replace('[', '-').replace(']', '-').replace(':', '-').replace('/', '-')

# Usage
resource_address = "azurerm_storage_account.main"
attribute_name = "location"
question_id = f"note-q-{sanitize_for_html_id(resource_address)}-{sanitize_for_html_id(attribute_name)}"
# Result: "note-q-azurerm_storage_account-main-location"
```

---

## Event Handlers

### `oninput` Event

**Purpose**: Trigger auto-save when user types

**Signature**:
```javascript
debouncedSaveNote(resourceAddress, attributeName, field, value)
```

**Parameters**:
- `resourceAddress`: string - Original (unsanitized) resource address (e.g., `"azurerm_storage_account.main"`)
- `attributeName`: string - Original attribute name (e.g., `"location"`)
- `field`: string - Either `"question"` or `"answer"`
- `value`: string - Current textarea value (`this.value`)

**Example**:
```html
<textarea 
    oninput="debouncedSaveNote('azurerm_storage_account.main', 'location', 'question', this.value)">
</textarea>
```

---

## Accessibility

### Labels

All textareas MUST have associated `<label>` elements with `for` attribute matching textarea `id`.

**Example**:
```html
<label class="note-label" for="note-q-azurerm_storage_account-main-location">
    Question:
</label>
<textarea id="note-q-azurerm_storage_account-main-location"></textarea>
```

### Placeholder Text

Placeholders provide guidance but MUST NOT be the only indicator of field purpose (labels required for accessibility).

**Question Placeholder**: `"Add a question..."`  
**Answer Placeholder**: `"Add an answer..."`

### Keyboard Navigation

- Textareas are focusable by default (tab order)
- No custom tab index needed
- Vertical stacking ensures logical flow (question before answer)

---

## Responsive Behavior

### Mobile/Narrow Screens

- Textareas set to `width: 100%` to fill container
- `resize: vertical` allows users to adjust height
- Min-height prevents textareas from collapsing too small

### Wide Screens

- Notes container spans full width of attribute section
- No horizontal scrolling required
- Textareas remain readable at all viewport sizes

---

## Validation

### HTML Validation

- All IDs MUST be unique per page
- No special characters in IDs except `-` and `_`
- All `for` attributes MUST match corresponding `id` attributes

### CSS Validation

- All CSS properties use standard syntax
- Color values use hex or rgb/rgba
- No vendor prefixes needed for target browsers

---

## Example: Complete Attribute Section with Notes

```html
<div class="attribute-section" style="background: #fff3cd;">
    <h3 class="attribute-header">
        <code>location</code>
    </h3>
    <div class="attribute-values">
        <div class="env-value-column">
            <div class="env-label">dev</div>
            <code style="background: #f8d7da; padding: 2px 6px; border-radius: 3px;">eastus</code>
        </div>
        <div class="env-value-column">
            <div class="env-label">staging</div>
            <code style="background: #f8d7da; padding: 2px 6px; border-radius: 3px;">centralus</code>
        </div>
        <div class="env-value-column">
            <div class="env-label">prod</div>
            <code style="background: #f8d7da; padding: 2px 6px; border-radius: 3px;">westus</code>
        </div>
    </div>
    
    <!-- Notes Container -->
    <div class="notes-container">
        <div>
            <label class="note-label" for="note-q-azurerm_storage_account-main-location">
                Question:
            </label>
            <textarea 
                class="note-field" 
                id="note-q-azurerm_storage_account-main-location"
                placeholder="Add a question..."
                oninput="debouncedSaveNote('azurerm_storage_account.main', 'location', 'question', this.value)"
                rows="4"></textarea>
        </div>
        <div class="note-answer">
            <label class="note-label" for="note-a-azurerm_storage_account-main-location">
                Answer:
            </label>
            <textarea 
                class="note-field" 
                id="note-a-azurerm_storage_account-main-location"
                placeholder="Add an answer..."
                oninput="debouncedSaveNote('azurerm_storage_account.main', 'location', 'answer', this.value)"
                rows="4"></textarea>
        </div>
    </div>
</div>
```

---

## Testing Checklist

- [ ] Notes container appears below attribute values for every attribute
- [ ] Question and answer labels are correct
- [ ] Textarea IDs are unique and correctly formatted
- [ ] Placeholder text displays correctly
- [ ] `oninput` event handlers call correct JavaScript function with correct parameters
- [ ] Labels `for` attributes match textarea `id` attributes
- [ ] Textareas are keyboard-accessible (tab navigation works)
- [ ] CSS classes are applied correctly
- [ ] Special characters in resource/attribute names are sanitized in IDs

---

## Version History

- **1.0** (2026-01-28): Initial contract for feature 008-attribute-notes
