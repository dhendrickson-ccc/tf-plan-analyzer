# Quick Start: Implementing Multi-Environment Comparison UI Improvements

**Feature**: 006-comparison-ui-improvements  
**Date**: January 15, 2026  
**Audience**: Developers implementing the UI changes  
**Estimated Time**: 4-6 hours total across 3 user stories

---

## Overview

This feature improves the multi-environment comparison HTML report with:
1. **Attribute headers with spacing** (P1) - 1.5 hours
2. **Scrollable value containers** (P1) - 2 hours
3. **Environment-specific resource grouping** (P2) - 2.5 hours

All changes are HTML/CSS only - no logic changes to comparison algorithms.

---

## Prerequisites

- Python 3.9.6+ with virtual environment activated
- Existing `tf-plan-analyzer` package installed (`pip install -e .`)
- Real Terraform plan files for testing (e.g., `tfplan-test-2.json`, `tfplan-prod.json`)
- Familiarity with:
  - `src/core/multi_env_comparator.py` - rendering functions
  - `src/lib/html_generation.py` - CSS generation
  - `docs/style-guide.md` - color palette and design system
  - `docs/function-glossary.md` - existing function signatures

---

## Architecture Overview

```text
tf-plan-analyzer compare → MultiEnvironmentComparator
                            ├── compare_resources()      [No changes]
                            ├── _detect_diffs()           [No changes]
                            └── generate_html_report()    
                                ├── _render_resource_card()
                                │   └── _render_attribute_table()   [MODIFY - v2.0 layout]
                                │       └── _render_attribute_value() [MODIFY - add containers]
                                └── HTML template                      [MODIFY - add env-specific section]

html_generation.generate_full_styles()     [MODIFY - add new CSS]
├── get_base_css()                         [No changes]
├── get_summary_card_css()                 [No changes]
├── get_diff_highlight_css()               [No changes - reuse existing]
└── [NEW] get_scrollable_container_css()   [ADD]
└── [NEW] get_env_specific_section_css()   [ADD]
```

---

## User Story 1: Attribute Headers with Improved Spacing (P1)

**Goal**: Transform attribute table rows into header-based sections  
**Time**: ~1.5 hours  
**Priority**: Must implement first (foundation for other stories)

### Step 1.1: Add CSS for Attribute Sections (30 min)

**File**: `src/lib/html_generation.py`

Add new CSS function:

```python
def get_attribute_section_css() -> str:
    """CSS for attribute header-based layout (v2.0)."""
    return """
        .attribute-section {
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .attribute-header {
            font-size: 1.2em;
            margin: 0 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            color: #495057;
        }
        
        .attribute-header code {
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            color: #667eea;
        }
        
        .attribute-values {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .env-value-column {
            flex: 1;
            min-width: 300px;
        }
        
        .env-label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #495057;
            font-size: 0.95em;
        }
    """
```

Update `generate_full_styles()` to include new function:

```python
def generate_full_styles() -> str:
    """Generate complete stylesheet for HTML reports."""
    return "\n".join([
        get_base_css(),
        get_summary_card_css(),
        get_diff_highlight_css(),
        get_resource_card_css(),
        get_attribute_section_css(),  # ADD THIS
        # ... other CSS functions
    ])
```

### Step 1.2: Modify Attribute Rendering (45 min)

**File**: `src/core/multi_env_comparator.py`

Replace `_render_attribute_table()` function (lines ~811-920):

**Old structure**: Table-based layout
```python
<table class="attribute-table">
    <tr>
        <td>attribute_name</td>
        <td>value1</td>
        <td>value2</td>
    </tr>
</table>
```

**New structure**: Section-based layout
```python
for attr_diff in rc.attribute_diffs:
    parts.append('<div class="attribute-section">')
    
    # Attribute header
    parts.append(f'<h3 class="attribute-header">')
    parts.append(f'<code>{html.escape(attr_diff.attribute_name)}</code>')
    
    # Sensitive badge if needed
    if any(isinstance(val, str) and "SENSITIVE" in val for val in attr_diff.env_values.values()):
        parts.append('<span class="sensitive-badge">🔒 SENSITIVE</span>')
    
    parts.append('</h3>')
    
    # Attribute values in flex columns
    parts.append('<div class="attribute-values">')
    
    for env_label in env_labels:
        parts.append('<div class="env-value-column">')
        parts.append(f'<div class="env-label">{env_label}</div>')
        
        value = attr_diff.env_values.get(env_label)
        value_html = self._render_attribute_value(value, attr_diff, env_labels, env_label)
        parts.append(f'<div>{value_html}</div>')  # Will add .value-container in Story 2
        
        parts.append('</div>')  # Close env-value-column
    
    parts.append('</div>')  # Close attribute-values
    parts.append('</div>')  # Close attribute-section
```

**Key Changes**:
- Remove `<table>`, `<tr>`, `<td>` elements
- Add `.attribute-section` wrapper div
- Change attribute name to `<h3>` with `.attribute-header` class
- Use flexbox `.attribute-values` container
- Each environment gets `.env-value-column` div

### Step 1.3: Test with Real Plans (15 min)

```bash
# From repository root
tf-plan-analyzer compare \
    --html \
    --output test-story1.html \
    /Users/danielhendrickson/workspace/promega/gsp-infrastructure-tf/2_deployApp/tfplan-test-2.json \
    /Users/danielhendrickson/workspace/promega/tmp/tfplan-prod.json

# Open in browser
open test-story1.html
```

**Validation Checklist**:
- [ ] Each attribute appears as `<h3>` header (not table cell)
- [ ] Minimum 30px spacing between attribute sections
- [ ] Attribute names fully visible (no truncation)
- [ ] Environment columns aligned horizontally
- [ ] Diff highlighting still works (existing classes preserved)

### Step 1.4: Commit Story 1

```bash
git add src/lib/html_generation.py src/core/multi_env_comparator.py
git commit -m "Implement attribute headers with improved spacing (Story 1)

- Replace table-based attribute layout with section-based layout
- Attribute names now displayed as H3 headers
- 30px vertical spacing between attribute sections
- Flexbox layout for environment value columns
- Preserves all existing diff highlighting classes

Addresses FR-001, FR-002, FR-009 from spec 006"
```

---

## User Story 2: Scrollable Value Containers (P1)

**Goal**: Add scrollbars to value containers for large content  
**Time**: ~2 hours  
**Priority**: Implements immediately after Story 1

### Step 2.1: Add Scrollable Container CSS (30 min)

**File**: `src/lib/html_generation.py`

Add new CSS function:

```python
def get_scrollable_container_css() -> str:
    """CSS for scrollable value containers (v2.0)."""
    return """
        .value-container {
            max-height: 400px;
            max-width: 600px;
            overflow: auto;
            padding: 10px;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            background: white;
        }
        
        /* Ensure diff highlighting works inside containers */
        .value-container pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        /* Scrollbar styling for webkit browsers (optional) */
        .value-container::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        .value-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        .value-container::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        .value-container::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    """
```

Update `generate_full_styles()`:

```python
def generate_full_styles() -> str:
    return "\n".join([
        get_base_css(),
        get_summary_card_css(),
        get_diff_highlight_css(),
        get_resource_card_css(),
        get_attribute_section_css(),
        get_scrollable_container_css(),  # ADD THIS
    ])
```

### Step 2.2: Add Sticky Header CSS (30 min)

**File**: `src/lib/html_generation.py`

Add sticky header CSS function:

```python
def get_sticky_header_css() -> str:
    """CSS for sticky environment headers (v2.0)."""
    return """
        .env-headers {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            position: sticky;
            top: 0;
            z-index: 10;
            background: white;
            padding: 10px 0;
            border-bottom: 3px solid #667eea;
        }
        
        .env-header {
            flex: 1;
            min-width: 300px;
            font-weight: 700;
            font-size: 1.1em;
            color: #667eea;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .sticky-header {
            position: sticky;
            top: 0;
            background: #f8f9fa;
        }
    """
```

Update `generate_full_styles()` again.

### Step 2.3: Wrap Values in Containers (45 min)

**File**: `src/core/multi_env_comparator.py`

Modify `_render_attribute_value()` to wrap values in `.value-container`:

**In `_render_attribute_table()` function, update the value rendering**:

```python
# Around line where value_html is used
value_html = self._render_attribute_value(value, attr_diff, env_labels, env_label)

# OLD: parts.append(f'<div>{value_html}</div>')
# NEW:
parts.append('<div class="value-container">')
parts.append(value_html)
parts.append('</div>')
```

**Add sticky environment headers** at the top of resource body:

In `_render_resource_card()` or `_render_attribute_table()`, add before attribute sections:

```python
# After resource header, before attribute sections
parts.append('<div class="env-headers">')
for env_label in env_labels:
    parts.append(f'<div class="env-header sticky-header">{env_label}</div>')
parts.append('</div>')
```

### Step 2.4: Test Scrollbar Behavior (15 min)

```bash
tf-plan-analyzer compare \
    --html \
    --output test-story2.html \
    /path/to/plans/with/large/json/objects
    
open test-story2.html
```

**Validation Checklist**:
- [ ] Values >400px height show vertical scrollbar
- [ ] Values >600px width show horizontal scrollbar
- [ ] Values <400px height do NOT show scrollbar
- [ ] Scrolling one container doesn't affect others
- [ ] Diff highlighting visible inside containers
- [ ] Environment headers stick when scrolling vertically

### Step 2.5: Commit Story 2

```bash
git add src/lib/html_generation.py src/core/multi_env_comparator.py
git commit -m "Implement scrollable value containers with sticky headers (Story 2)

- Wrap all attribute values in .value-container divs
- Add max-height: 400px and max-width: 600px constraints
- Scrollbars appear only when content exceeds container size
- Add sticky environment column headers (position: sticky, top: 0)
- Preserve diff highlighting within scrollable containers

Addresses FR-003, FR-004, FR-005, FR-010, FR-011, FR-012, FR-013 from spec 006"
```

---

## User Story 3: Environment-Specific Resource Grouping (P2)

**Goal**: Separate and mark resources that exist in only some environments  
**Time**: ~2.5 hours  
**Priority**: Implements last (builds on Stories 1-2)

### Step 3.1: Add Environment-Specific CSS (30 min)

**File**: `src/lib/html_generation.py`

```python
def get_env_specific_section_css() -> str:
    """CSS for environment-specific resource section (v2.0)."""
    return """
        .env-specific-section {
            margin: 30px 0;
            padding: 0;
            background: #fff4e6;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
        }
        
        .env-specific-header {
            cursor: pointer;
            font-size: 1.2em;
            padding: 15px 20px;
            user-select: none;
            background: #ffe8cc;
            border-radius: 4px 4px 0 0;
        }
        
        .env-specific-header:hover {
            background: #ffd8a8;
        }
        
        /* Hide default details marker */
        .env-specific-header::-webkit-details-marker {
            display: none;
        }
        
        /* Custom toggle icon */
        .env-specific-header::before {
            content: '▼ ';
            transition: transform 0.2s;
            display: inline-block;
        }
        
        details:not([open]) .env-specific-header::before {
            content: '▶ ';
        }
        
        .env-specific-content {
            padding: 20px;
        }
        
        .env-specific-badge {
            display: inline-block;
            padding: 4px 10px;
            background: #ffa94d;
            color: #333;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .resource-count {
            color: #e67700;
            font-size: 0.9em;
            margin-left: 8px;
        }
        
        .presence-info {
            padding: 15px;
            background: #fff4e6;
            border-left: 4px solid #f59e0b;
            margin-bottom: 15px;
            font-size: 0.95em;
        }
    """
```

Update `generate_full_styles()`.

### Step 3.2: Detect Environment-Specific Resources (45 min)

**File**: `src/core/multi_env_comparator.py`

In `generate_html_report()` method, separate resources into two lists:

```python
def generate_html_report(self, ...) -> str:
    # Existing sorting logic
    sorted_comparisons = sorted(...)
    
    # NEW: Separate into regular vs environment-specific
    regular_resources = []
    env_specific_resources = []
    
    for rc in sorted_comparisons:
        if len(rc.is_present_in) < len(env_labels):
            # Resource exists in only some environments
            env_specific_resources.append(rc)
        else:
            # Resource exists in all environments (may or may not have diffs)
            regular_resources.append(rc)
```

### Step 3.3: Render Regular Resources Section (15 min)

```python
# Render regular resources (existing logic)
for rc in regular_resources:
    parts.append(self._render_resource_card(rc, env_labels, baseline_env))
```

### Step 3.4: Render Environment-Specific Section (60 min)

**File**: `src/core/multi_env_comparator.py`

After regular resources:

```python
# Render environment-specific section
if env_specific_resources:
    parts.append('<details open class="env-specific-section">')
    parts.append('<summary class="env-specific-header">')
    parts.append('<strong>⚠️ Environment-Specific Resources</strong>')
    parts.append(f'<span class="resource-count">({len(env_specific_resources)} resources)</span>')
    parts.append('</summary>')
    
    parts.append('<div class="env-specific-content">')
    
    for rc in env_specific_resources:
        # Render resource card with badge
        parts.append('<div class="resource-card">')
        
        # Resource header with env-specific badge
        parts.append('<div class="resource-header">')
        parts.append('<h2 class="resource-name">')
        parts.append(f'<span class="resource-type-badge">{html.escape(rc.resource_type)}</span>')
        parts.append(f'<code>{html.escape(rc.resource_name)}</code>')
        
        # Add environment-specific badge
        present_envs = ", ".join(sorted(rc.is_present_in))
        if len(rc.is_present_in) == 1:
            badge_text = f"{list(rc.is_present_in)[0]} only"
        else:
            badge_text = f"Present in: {present_envs}"
        parts.append(f'<span class="env-specific-badge">⚠️ {badge_text}</span>')
        
        parts.append('</h2>')
        parts.append('</div>')  # Close resource-header
        
        # Resource body with presence info
        parts.append('<div class="resource-body">')
        parts.append('<div class="presence-info">')
        parts.append(f'<strong>Present in:</strong> {present_envs}<br>')
        missing = set(env_labels) - rc.is_present_in
        parts.append(f'<strong>Missing from:</strong> {", ".join(sorted(missing))}')
        parts.append('</div>')
        
        # Render attributes only for environments where resource exists
        # Filter env_labels to only those in rc.is_present_in
        present_env_labels = [env for env in env_labels if env in rc.is_present_in]
        parts.append(self._render_attribute_table(rc, present_env_labels))
        
        parts.append('</div>')  # Close resource-body
        parts.append('</div>')  # Close resource-card
    
    parts.append('</div>')  # Close env-specific-content
    parts.append('</details>')  # Close env-specific-section
```

### Step 3.5: Test Environment-Specific Detection (20 min)

```bash
# Use plans with environment-specific resources
tf-plan-analyzer compare \
    --html \
    --output test-story3.html \
    test-plan.json prod-plan.json

open test-story3.html
```

**Validation Checklist**:
- [ ] Environment-specific section appears at bottom of report
- [ ] Section shows resource count correctly
- [ ] Section is expanded by default (`<details open>`)
- [ ] Can collapse/expand section by clicking header
- [ ] Each env-specific resource has amber warning badge
- [ ] Badge shows correct environment(s) (e.g., "Test only")
- [ ] Presence info shows which envs have/missing resource
- [ ] Attributes only shown for relevant environments
- [ ] Regular resources still in main section (not moved)

### Step 3.6: Commit Story 3

```bash
git add src/lib/html_generation.py src/core/multi_env_comparator.py
git commit -m "Implement environment-specific resource grouping (Story 3)

- Detect resources present in only some environments
- Group env-specific resources in collapsible section at bottom
- Add amber warning badges showing which environments contain resource
- Display presence info (present in / missing from)
- Only show attributes for environments where resource exists
- Use HTML5 <details> element (no JavaScript required)
- Default to expanded state for visibility

Addresses FR-006, FR-007, FR-008, FR-014 from spec 006"
```

---

## End-to-End Validation

After all 3 stories complete:

### Test 1: Real Production Plans

```bash
tf-plan-analyzer compare \
    --html \
    --output prod-comparison-v2.html \
    /Users/danielhendrickson/workspace/promega/gsp-infrastructure-tf/2_deployApp/tfplan-test-2.json \
    /Users/danielhendrickson/workspace/promega/tmp/tfplan-prod.json

open prod-comparison-v2.html
```

**Verify**:
- 199 total resources display correctly
- 196 resources with differences show in main section
- Environment-specific resources (if any) grouped at bottom
- Attributes displayed as H3 headers with 30px spacing
- Large JSON values have scrollbars (test network_rules, tags, etc.)
- Diff highlighting (blue/green) works inside scrollable containers
- Environment headers (Test, Production) stick when scrolling
- Collapsible section expands/collapses with keyboard (Space/Enter)

### Test 2: CLI Backward Compatibility

```bash
# Ensure existing flags still work
tf-plan-analyzer compare --help
tf-plan-analyzer compare --html plan1.json plan2.json
tf-plan-analyzer compare --diff-only plan1.json plan2.json
```

### Test 3: Browser Compatibility

Open generated HTML in:
- Chrome 90+
- Firefox 88+
- Safari 14+ (if on macOS)
- Edge 90+ (if on Windows)

Verify all features work identically across browsers.

---

## Update Documentation

### Update docs/style-guide.md

Add new sections for:
- Scrollable container patterns
- Sticky header patterns
- Environment-specific badge colors
- Collapsible section patterns

### Update docs/function-glossary.md

Document modified functions:
- `_render_attribute_table()` - v2.0 structure change
- `_render_attribute_value()` - now wrapped in `.value-container`
- `generate_full_styles()` - new CSS functions added

---

## Common Issues & Solutions

### Issue 1: Scrollbars appear even when content fits

**Cause**: Using `overflow: scroll` instead of `overflow: auto`  
**Solution**: Ensure CSS uses `overflow: auto`

### Issue 2: Sticky headers don't stick

**Cause**: Missing `position: sticky` or `top: 0`  
**Solution**: Verify `.sticky-header` CSS is applied and z-index is sufficient

### Issue 3: Diff highlighting breaks inside containers

**Cause**: CSS selector specificity issue  
**Solution**: Ensure diff classes have same or higher specificity when inside `.value-container`

### Issue 4: Environment-specific section doesn't collapse

**Cause**: `<details>` not supported or CSS hiding it  
**Solution**: Verify browser support and check for CSS `display: none` overrides

### Issue 5: Flexbox columns too narrow on mobile

**Cause**: `min-width: 300px` too large for narrow screens  
**Solution**: Add media query for smaller screens (out of scope for this feature - desktop only)

---

## Success Criteria Validation

After implementation, validate against spec success criteria:

- [ ] Users can identify attribute differences 40% faster (subjective - test with real users)
- [ ] Large JSON values don't break page layout (test with 1000+ line objects)
- [ ] Environment-specific resources clearly distinguished (visual inspection)
- [ ] HTML renders correctly 1024px to 4K (test multiple resolutions)
- [ ] Report with 200 resources loads in <2 seconds (performance test)
- [ ] Users report improved satisfaction (usability testing - post-release)

---

## Next Steps After Implementation

1. Run full test suite: `pytest tests/`
2. Update test assertions for new HTML structure
3. Generate comparison report with real plans and share with stakeholders
4. Gather feedback on readability improvements
5. Consider additional enhancements:
   - Search/filter within report
   - Export specific attributes
   - Customizable scroll container dimensions
   - Dark mode color scheme

---

## Resources

- [HTML Structure Contract](contracts/html-structure.md)
- [Data Model](data-model.md)
- [Research Decisions](research.md)
- [Project Style Guide](../../docs/style-guide.md)
- [Function Glossary](../../docs/function-glossary.md)
- [Feature Specification](spec.md)
