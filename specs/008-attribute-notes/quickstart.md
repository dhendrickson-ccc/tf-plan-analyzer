# Quickstart Guide: Attribute Change Notes

**Feature**: 008-attribute-notes  
**Date**: January 28, 2026  
**Audience**: Developers implementing this feature

---

## Overview

This guide provides step-by-step instructions for implementing question/answer notes on attribute changes in HTML comparison reports. Implementation is divided into 3 user stories (P1, P1, P2).

**Total Estimated Time**: 6-8 hours

---

## Prerequisites

1. **Environment Setup**:
   ```bash
   cd /Users/danielhendrickson/workspace/promega/tf-plan-analyzer
   source venv/bin/activate  # Activate virtual environment
   ```

2. **Verify Existing Tests Pass**:
   ```bash
   pytest tests/
   ```

3. **Review Existing Code**:
   - `src/lib/html_generation.py` - CSS generation functions
   - `src/core/multi_env_comparator.py` - HTML report generation
   - `specs/008-attribute-notes/research.md` - Technical research
   - `specs/008-attribute-notes/contracts/` - Interface contracts

---

## User Story 1: Add Question Field (Priority P1)

**Goal**: Add question textarea below each attribute change  
**Time Estimate**: 2-3 hours

### Step 1.1: Add CSS for Notes (30 min)

**File**: `src/lib/html_generation.py`

**Action**: Create new function `get_notes_css()`

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
        
        /* Notes labels */
        .note-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
            font-size: 0.85em;
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
        
        /* Spacing between question and answer */
        .note-answer {
            margin-top: 12px;
        }
    """
```

**Action**: Update `generate_full_styles()` to include new CSS

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

### Step 1.2: Add JavaScript Functions (45 min)

**File**: `src/lib/html_generation.py`

**Action**: Create new function `get_notes_javascript()`

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
        
        // Debounce utility to prevent excessive LocalStorage writes
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
                        
                        // Sanitize for HTML ID (replace special chars with -)
                        const sanitizedResource = resourceAddress.replace(/[\\.\\[\\]:\\/]/g, '-');
                        const sanitizedAttribute = attributeName.replace(/[\\.\\[\\]:\\/]/g, '-');
                        
                        const questionField = document.getElementById(`note-q-${sanitizedResource}-${sanitizedAttribute}`);
                        const answerField = document.getElementById(`note-a-${sanitizedResource}-${sanitizedAttribute}`);
                        
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

### Step 1.3: Modify HTML Generation to Include JavaScript (15 min)

**File**: `src/core/multi_env_comparator.py`

**Location**: In `generate_html()` method, add JavaScript before closing `</head>` tag

**Find** (around line 940):
```python
html_parts.append("    </style>")
html_parts.append("</head>")
```

**Replace with**:
```python
html_parts.append("    </style>")
html_parts.append(get_notes_javascript())  # NEW
html_parts.append("</head>")
```

**Import**: Add at top of file:
```python
from ..lib.html_generation import generate_full_styles, highlight_json_diff, get_notes_javascript
```

### Step 1.4: Add Sanitization Helper Function (15 min)

**File**: `src/core/multi_env_comparator.py`

**Action**: Add helper function before `_render_attribute_table()` method

```python
def _sanitize_for_html_id(self, text: str) -> str:
    """Sanitize text for use in HTML ID attribute."""
    return text.replace('.', '-').replace('[', '-').replace(']', '-').replace(':', '-').replace('/', '-')
```

### Step 1.5: Inject Notes HTML into Attribute Sections (45 min)

**File**: `src/core/multi_env_comparator.py`

**Location**: In `_render_attribute_table()` method, after the `.attribute-values` div closes

**Find** (around line 1350):
```python
                parts.append('                            </div>')  # Close attribute-values
                parts.append('                        </div>')  # Close attribute-section
```

**Replace with**:
```python
                parts.append('                            </div>')  # Close attribute-values
                
                # Add notes container (feature 008)
                sanitized_resource = self._sanitize_for_html_id(rc.resource_address)
                sanitized_attribute = self._sanitize_for_html_id(attr_diff.attribute_name)
                
                parts.append('                            <div class="notes-container">')
                parts.append('                                <div>')
                parts.append(f'                                    <label class="note-label" for="note-q-{sanitized_resource}-{sanitized_attribute}">Question:</label>')
                parts.append(f'                                    <textarea class="note-field" id="note-q-{sanitized_resource}-{sanitized_attribute}" placeholder="Add a question..." oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'question\', this.value)" rows="4"></textarea>')
                parts.append('                                </div>')
                parts.append('                            </div>')
                
                parts.append('                        </div>')  # Close attribute-section
```

### Step 1.6: Unit Tests for CSS and JavaScript (30 min)

**File**: `tests/unit/test_html_generation.py`

```python
def test_get_notes_css():
    """Test notes CSS generation."""
    from src.lib.html_generation import get_notes_css
    
    css = get_notes_css()
    assert '.notes-container' in css
    assert '.note-field' in css
    assert '.note-label' in css
    assert 'placeholder' in css


def test_get_notes_javascript():
    """Test notes JavaScript generation."""
    from src.lib.html_generation import get_notes_javascript
    
    js = get_notes_javascript()
    assert 'function getReportId()' in js
    assert 'function debounce(' in js
    assert 'function saveNote(' in js
    assert 'debouncedSaveNote' in js
    assert 'function loadNotes()' in js
    assert 'localStorage' in js


def test_generate_full_styles_includes_notes_css():
    """Test that notes CSS is included in full styles."""
    from src.lib.html_generation import generate_full_styles
    
    styles = generate_full_styles()
    assert '.notes-container' in styles
    assert '.note-field' in styles
```

### Step 1.7: End-to-End Test (30 min)

**File**: `tests/e2e/test_e2e_attribute_notes.py` (NEW)

```python
import subprocess
import os
import pytest


class TestUS1AddQuestionField:
    """End-to-end tests for User Story 1: Add question field."""

    def test_question_field_renders_in_html(self):
        """Test that question textarea is rendered for each attribute."""
        output_file = "test_notes_us1.html"
        if os.path.exists(output_file):
            os.unlink(output_file)

        try:
            result = subprocess.run(
                [
                    "python3",
                    "src/cli/analyze_plan.py",
                    "compare",
                    "tests/fixtures/env-char-diff-1.json",
                    "tests/fixtures/env-char-diff-2.json",
                    "--html",
                    output_file,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"

            with open(output_file, "r") as f:
                html_content = f.read()

            # Verify notes CSS is present
            assert '.notes-container' in html_content
            assert '.note-field' in html_content
            
            # Verify JavaScript functions are embedded
            assert 'function getReportId()' in html_content
            assert 'function saveNote(' in html_content
            assert 'debouncedSaveNote' in html_content
            assert 'function loadNotes()' in html_content
            
            # Verify question textarea exists with correct attributes
            assert '<textarea class="note-field"' in html_content
            assert 'placeholder="Add a question..."' in html_content
            assert 'oninput="debouncedSaveNote(' in html_content
            
            # Verify label exists
            assert '<label class="note-label"' in html_content
            assert 'Question:</label>' in html_content

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
```

### Step 1.8: Run Tests and Verify

```bash
# Run unit tests
pytest tests/unit/test_html_generation.py::test_get_notes_css -v
pytest tests/unit/test_html_generation.py::test_get_notes_javascript -v

# Run E2E test
pytest tests/e2e/test_e2e_attribute_notes.py::TestUS1AddQuestionField::test_question_field_renders_in_html -v

# Generate actual HTML file for manual testing
python3 src/cli/analyze_plan.py compare tests/fixtures/env-char-diff-1.json tests/fixtures/env-char-diff-2.json --html test_notes_manual.html

# Open in browser and verify
open test_notes_manual.html  # macOS
```

**Manual Verification**:
1. Open HTML in browser
2. Locate an attribute change
3. Verify question textarea appears below attribute values
4. Type in question field → wait 500ms
5. Open browser DevTools → Application → LocalStorage
6. Verify key like `tf-notes-test_notes_manual.html#{resource}#{attribute}` exists
7. Verify JSON value contains `question` field with your text

### Step 1.9: Commit User Story 1

```bash
git add src/lib/html_generation.py src/core/multi_env_comparator.py tests/
git commit -m "feat(008): Add question field to attribute changes (US1)

- Add get_notes_css() function with styling for notes container and textareas
- Add get_notes_javascript() with LocalStorage save/load functions
- Inject question textarea into each attribute section
- Add sanitization helper for HTML IDs
- Add unit tests for CSS and JavaScript generation
- Add E2E test verifying question field renders correctly

Closes User Story 1 (Priority P1)"
```

---

## User Story 2: Add Answer Field (Priority P1)

**Goal**: Add answer textarea below question field  
**Time Estimate**: 1-2 hours

### Step 2.1: Add Answer Textarea to HTML Generation (30 min)

**File**: `src/core/multi_env_comparator.py`

**Location**: In `_render_attribute_table()` method, inside `.notes-container` div

**Find**:
```python
                parts.append('                                </div>')
                parts.append('                            </div>')
                
                parts.append('                        </div>')  # Close attribute-section
```

**Replace with**:
```python
                parts.append('                                </div>')
                parts.append('                                <div class="note-answer">')
                parts.append(f'                                    <label class="note-label" for="note-a-{sanitized_resource}-{sanitized_attribute}">Answer:</label>')
                parts.append(f'                                    <textarea class="note-field" id="note-a-{sanitized_resource}-{sanitized_attribute}" placeholder="Add an answer..." oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'answer\', this.value)" rows="4"></textarea>')
                parts.append('                                </div>')
                parts.append('                            </div>')
                
                parts.append('                        </div>')  # Close attribute-section
```

### Step 2.2: Update E2E Tests (30 min)

**File**: `tests/e2e/test_e2e_attribute_notes.py`

```python
class TestUS2AnswerField:
    """End-to-end tests for User Story 2: Add answer field."""

    def test_answer_field_renders_in_html(self):
        """Test that answer textarea is rendered below question field."""
        output_file = "test_notes_us2.html"
        if os.path.exists(output_file):
            os.unlink(output_file)

        try:
            result = subprocess.run(
                [
                    "python3",
                    "src/cli/analyze_plan.py",
                    "compare",
                    "tests/fixtures/env-char-diff-1.json",
                    "tests/fixtures/env-char-diff-2.json",
                    "--html",
                    output_file,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"

            with open(output_file, "r") as f:
                html_content = f.read()

            # Verify answer textarea exists
            assert 'placeholder="Add an answer..."' in html_content
            assert 'Answer:</label>' in html_content
            assert 'class="note-answer"' in html_content
            
            # Verify both question and answer are present
            assert html_content.count('<textarea class="note-field"') >= 2  # At least one q+a pair

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_question_and_answer_persist_together(self):
        """Manual test guide: Verify question and answer both persist in LocalStorage."""
        # This is a manual test - generate HTML and verify in browser
        output_file = "test_notes_persistence.html"
        
        result = subprocess.run(
            [
                "python3",
                "src/cli/analyze_plan.py",
                "compare",
                "tests/fixtures/env-char-diff-1.json",
                "tests/fixtures/env-char-diff-2.json",
                "--html",
                output_file,
            ],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert os.path.exists(output_file)
        
        print(f"\n\nMANUAL TEST INSTRUCTIONS:")
        print(f"1. Open {output_file} in browser")
        print(f"2. Add question: 'Why is this different?'")
        print(f"3. Add answer: 'Historical decision'")
        print(f"4. Wait 1 second for auto-save")
        print(f"5. Refresh page")
        print(f"6. Verify both question AND answer are pre-populated")
        print(f"7. Check browser DevTools → LocalStorage for key with both fields\n")
```

### Step 2.3: Run Tests and Verify

```bash
# Run E2E tests
pytest tests/e2e/test_e2e_attribute_notes.py::TestUS2AnswerField -v

# Generate test HTML
python3 src/cli/analyze_plan.py compare tests/fixtures/env-char-diff-1.json tests/fixtures/env-char-diff-2.json --html test_notes_us2_manual.html

# Manual verification
open test_notes_us2_manual.html
# 1. Add both question and answer
# 2. Refresh page
# 3. Verify both fields persist
```

### Step 2.4: Commit User Story 2

```bash
git add src/core/multi_env_comparator.py tests/e2e/test_e2e_attribute_notes.py
git commit -m "feat(008): Add answer field below question (US2)

- Add answer textarea with label and placeholder
- Apply .note-answer CSS class for spacing
- Update E2E tests to verify answer field renders
- Add manual test guide for persistence verification

Closes User Story 2 (Priority P1)"
```

---

## User Story 3: Review Multiple Annotated Changes (Priority P2)

**Goal**: Ensure users can review notes across multiple attributes  
**Time Estimate**: 1 hour (mostly verification)

### Step 3.1: Verify No Visual Indicator Needed

Per specification decision (clarification session), no special visual indicator is added. Users scroll through report to review notes.

### Step 3.2: Add E2E Test for Multiple Notes (45 min)

**File**: `tests/e2e/test_e2e_attribute_notes.py`

```python
class TestUS3ReviewMultipleNotes:
    """End-to-end tests for User Story 3: Review multiple annotated changes."""

    def test_multiple_attributes_have_independent_notes(self):
        """Test that multiple attributes can each have their own notes."""
        output_file = "test_notes_us3_multiple.html"
        if os.path.exists(output_file):
            os.unlink(output_file)

        try:
            result = subprocess.run(
                [
                    "python3",
                    "src/cli/analyze_plan.py",
                    "compare",
                    "tests/fixtures/env-char-diff-1.json",
                    "tests/fixtures/env-char-diff-2.json",
                    "--html",
                    output_file,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Command failed: {result.stderr}"
            assert os.path.exists(output_file), "HTML file not created"

            with open(output_file, "r") as f:
                html_content = f.read()

            # Count notes containers (one per attribute)
            notes_count = html_content.count('<div class="notes-container">')
            
            # Verify multiple notes containers exist
            assert notes_count >= 2, f"Expected at least 2 notes containers, found {notes_count}"
            
            # Verify unique IDs for each textarea
            question_textareas = html_content.count('id="note-q-')
            answer_textareas = html_content.count('id="note-a-')
            
            assert question_textareas == notes_count, "Each notes container should have one question field"
            assert answer_textareas == notes_count, "Each notes container should have one answer field"

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
```

### Step 3.3: Manual Acceptance Test

**Instructions**:

1. Generate comprehensive comparison HTML:
   ```bash
   python3 src/cli/analyze_plan.py compare Livetest-temp/tfplan-dev-use2-obfuscated.json Livetest-temp/tfplan-stage-use2-obfuscated.json Livetest-temp/tfplan-prod-use2-obfuscated.json --html test_notes_full.html
   ```

2. Open in browser: `open test_notes_full.html`

3. Add questions to 3+ different attributes across different resources

4. Add answers to at least 2 of those questions

5. Refresh page → verify all notes persist

6. Scroll through report → verify you can locate all your annotated attributes

7. Open browser DevTools → Application → LocalStorage → verify multiple keys exist

**Acceptance Criteria** (from spec):
- ✅ Multiple attribute changes have questions/answers
- ✅ All annotated attributes display their question/answer content
- ✅ User can scroll through report to locate attributes with filled-in notes
- ✅ Notes are still present and associated with correct attributes after refresh

### Step 3.4: Run Tests

```bash
pytest tests/e2e/test_e2e_attribute_notes.py::TestUS3ReviewMultipleNotes -v
```

### Step 3.5: Commit User Story 3

```bash
git add tests/e2e/test_e2e_attribute_notes.py
git commit -m "feat(008): Verify multiple notes functionality (US3)

- Add E2E test for multiple independent notes containers
- Verify unique IDs for each attribute's notes fields
- Add manual acceptance test instructions

Closes User Story 3 (Priority P2)"
```

---

## Final Verification Checklist

### Functional Requirements

- [ ] **FR-001**: Question text field displays below each attribute change
- [ ] **FR-002**: Answer text field displays below question field (vertically stacked)
- [ ] **FR-003**: Question and answer fields have clear labels
- [ ] **FR-004**: Text areas display 3-5 rows by default (rows="4")
- [ ] **FR-005**: Empty fields show placeholder text ("Add a question..." / "Add an answer...")
- [ ] **FR-006**: Notes stored in browser LocalStorage
- [ ] **FR-007**: Auto-save triggers on typing (with 500ms debounce)
- [ ] **FR-008**: Composite key uses resource address + attribute name
- [ ] **FR-009**: Notes tied to specific report version (HTML filename)
- [ ] **FR-010**: Previously saved notes load when reopening same report
- [ ] **FR-011**: Users can edit existing answers (overwrite)
- [ ] **FR-012**: Plaintext rendering only (no formatting)
- [ ] **FR-013**: Text preserved exactly as entered (whitespace, line breaks)
- [ ] **FR-014**: Notes fields visible without clicking/toggling

### Success Criteria

- [ ] **SC-001**: Can add question in under 10 seconds (just type)
- [ ] **SC-002**: Notes persist across browser sessions 100%
- [ ] **SC-003**: Can locate annotated changes by scrolling
- [ ] **SC-004**: Notes don't obscure attribute details

### Documentation Updates

Update the following files after implementation:

1. **docs/function-glossary.md**:
   ```markdown
   #### `get_notes_css()`
   
   Generate CSS styling for question/answer notes fields.
   
   **Returns**: `str` - CSS rules for `.notes-container`, `.note-field`, `.note-label` classes
   
   **Usage**:
   ```python
   notes_css = get_notes_css()
   # Included automatically in generate_full_styles()
   ```
   
   ---
   
   #### `get_notes_javascript()`
   
   Generate JavaScript for auto-save and load functionality for notes.
   
   **Returns**: `str` - Complete `<script>` tag with all notes functions
   
   **Functions Included**:
   - `getReportId()` - Extract filename from URL
   - `debounce(func, delay)` - Debouncing utility
   - `saveNote(...)` - Save note to LocalStorage
   - `debouncedSaveNote` - Debounced save wrapper
   - `loadNotes()` - Load notes on page load
   ```

2. **docs/style-guide.md**:
   ```markdown
   ### Notes Components
   
   #### `.notes-container`
   Container for question/answer notes below attribute values.
   
   ```css
   .notes-container {
       margin-top: 15px;
       padding: 15px;
       background: #f8f9fa;
       border-radius: 4px;
       border-left: 3px solid #6c757d;
   }
   ```
   
   #### `.note-field`
   Textarea for question or answer text.
   
   ```css
   .note-field {
       width: 100%;
       padding: 8px;
       border: 1px solid #ced4da;
       border-radius: 3px;
       font-size: 0.9em;
       resize: vertical;
       min-height: 80px;
   }
   
   .note-field:focus {
       border-color: #667eea;
       box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
   }
   ```
   
   #### `.note-label`
   Label for question or answer field.
   
   ```css
   .note-label {
       display: block;
       margin-bottom: 5px;
       font-weight: 600;
       color: #495057;
       font-size: 0.85em;
   }
   ```
   ```

---

## Troubleshooting

### Notes Don't Persist

**Symptom**: Notes disappear after page refresh

**Check**:
1. Browser DevTools → Application → LocalStorage → verify keys exist
2. Verify filename didn't change (notes are tied to filename)
3. Check browser console for JavaScript errors
4. Verify `getReportId()` returns correct filename

**Fix**: Ensure HTML file has consistent name when reopening

### Special Characters in IDs

**Symptom**: Textareas not found by ID in `loadNotes()`

**Check**: Resource address contains `.`, `[`, `]`, `:`, `/`

**Fix**: Verify `_sanitize_for_html_id()` is called consistently in both HTML generation and JavaScript `loadNotes()`

### Auto-Save Not Working

**Symptom**: Must refresh multiple times before notes appear

**Check**:
1. Verify `oninput` event handler is attached to textareas
2. Check 500ms debounce delay is respected
3. Verify LocalStorage quota not exceeded

**Fix**: Wait at least 500ms after typing before refreshing

---

## Performance Notes

- **Debouncing**: 500ms delay prevents excessive LocalStorage writes
- **Load Time**: `loadNotes()` runs on `DOMContentLoaded`, minimal impact (<50ms for typical reports)
- **Storage**: Typical note pair (question + answer) ~500 bytes, well within LocalStorage limits

---

## Browser Compatibility

**Supported**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features**:
- LocalStorage API
- Arrow functions
- Template literals
- `addEventListener`

---

## Next Steps

After completing all 3 user stories:

1. **Final Testing**: Run full E2E test suite
   ```bash
   pytest tests/e2e/test_e2e_attribute_notes.py -v
   ```

2. **Update Documentation**: docs/function-glossary.md, docs/style-guide.md

3. **Create PR**: 
   ```bash
   git push origin 008-attribute-notes
   # Create pull request on GitHub
   ```

4. **Demo**: Generate live HTML with real data and demonstrate notes functionality

---

## Summary

**Implementation Order**:
1. US1: Question field (2-3 hours) → Commit
2. US2: Answer field (1-2 hours) → Commit
3. US3: Multiple notes verification (1 hour) → Commit

**Total Time**: 4-6 hours + documentation updates

**Files Modified**:
- `src/lib/html_generation.py` (2 new functions)
- `src/core/multi_env_comparator.py` (notes HTML injection + sanitization helper)
- `tests/unit/test_html_generation.py` (tests for CSS/JS)
- `tests/e2e/test_e2e_attribute_notes.py` (NEW - E2E tests)
- `docs/function-glossary.md` (documentation)
- `docs/style-guide.md` (CSS documentation)

**Constitution Compliance**: ✅ All principles followed

**Ready for**: `/speckit.tasks` command to generate detailed task breakdown
