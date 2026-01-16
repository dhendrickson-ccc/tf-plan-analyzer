# Research: Multi-Environment Comparison UI Improvements

**Feature**: 006-comparison-ui-improvements  
**Date**: January 15, 2026  
**Purpose**: Document technical research and decisions for UI layout improvements

---

## 1. CSS Scrollbar Behavior for Value Containers

### Decision
Use `overflow: auto` for scrollable value containers with specific max-height and max-width constraints.

### Rationale
- `overflow: auto` only shows scrollbars when content exceeds container dimensions (FR-010 requirement)
- `overflow: scroll` always shows scrollbar tracks even when not needed, creating visual clutter
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+) all support `overflow: auto` consistently
- Prevents layout breaking when JSON values are 100+ lines or strings are 500+ characters

### Implementation Pattern
```css
.value-container {
    max-height: 400px;
    max-width: 600px;
    overflow: auto;
    padding: 10px;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    background: white;
}
```

### Alternatives Considered
- **overflow: scroll** - Rejected: Always shows scrollbars even when unnecessary
- **JavaScript-based virtual scrolling** - Rejected: Violates no-JavaScript constraint
- **No max constraints** - Rejected: Causes page layout to break with large values

### References
- MDN Web Docs: [overflow property](https://developer.mozilla.org/en-US/docs/Web/CSS/overflow)
- CSS Tricks: [overflow auto behavior](https://css-tricks.com/almanac/properties/o/overflow/)

---

## 2. Sticky Header Implementation

### Decision
Use `position: sticky` with `top: 0` for environment column headers only (not attribute headers within resource cards).

### Rationale
- User chose Option A in spec clarification: "Only environment column headers (Test, Prod, etc.)"
- `position: sticky` is well-supported in all target browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Does not require JavaScript or complex z-index management
- Provides natural scroll behavior - headers stick when scrolling vertically through report
- Attribute headers within resource cards scroll normally, reducing visual complexity

### Implementation Pattern
```css
.env-header-row th {
    position: sticky;
    top: 0;
    z-index: 10;
    background: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
    padding: 12px;
}
```

### Alternatives Considered
- **position: fixed** - Rejected: Requires JavaScript to calculate positions and doesn't respect container boundaries
- **Sticky attribute headers** - Rejected: User explicitly chose not to implement this (increases complexity)
- **No sticky headers** - Rejected: Loses context when scrolling through 200+ resources

### Browser Compatibility
All target browsers support `position: sticky`:
- Chrome 56+ (target: 90+) ✅
- Firefox 59+ (target: 88+) ✅
- Safari 13+ (target: 14+) ✅
- Edge 79+ (target: 90+) ✅

### References
- MDN Web Docs: [position: sticky](https://developer.mozilla.org/en-US/docs/Web/CSS/position#sticky)
- Can I Use: [CSS position:sticky](https://caniuse.com/css-sticky)

---

## 3. Collapsible Section for Environment-Specific Resources

### Decision
Use HTML5 `<details>` and `<summary>` elements for the collapsible "Environment-Specific Resources" section, defaulting to expanded state.

### Rationale
- Pure HTML+CSS solution (no JavaScript required per constraint)
- Native browser support in all target browsers
- Built-in keyboard accessibility (Space/Enter to toggle)
- Simple semantic markup that's screen-reader friendly
- Default to `<details open>` so users see environment-specific resources immediately
- Users can collapse section if they want to focus on multi-environment comparisons only

### Implementation Pattern
```html
<details open class="env-specific-section">
    <summary class="env-specific-header">
        <strong>⚠️ Environment-Specific Resources</strong>
        <span class="resource-count">(5 resources)</span>
    </summary>
    <div class="env-specific-content">
        <!-- Resource cards for env-specific resources -->
    </div>
</details>
```

```css
.env-specific-section {
    margin: 20px 0;
    padding: 15px;
    background: #fff4e6;
    border-left: 4px solid #f59e0b;
    border-radius: 4px;
}

.env-specific-header {
    cursor: pointer;
    font-size: 1.1em;
    padding: 10px;
    user-select: none;
}

.env-specific-header::-webkit-details-marker {
    display: none; /* Hide default triangle */
}

.env-specific-header::before {
    content: '▼ ';
    transition: transform 0.2s;
}

details:not([open]) .env-specific-header::before {
    content: '▶ ';
}
```

### Alternatives Considered
- **CSS-only checkbox hack** - Rejected: Less semantic, worse accessibility, more complex
- **Always expanded (no collapse)** - Rejected: User may want to hide env-specific resources to focus on drift
- **JavaScript accordion** - Rejected: Violates no-JavaScript constraint
- **Default to collapsed** - Rejected: Hides important information by default (poor UX)

### Accessibility Benefits
- Keyboard accessible (Space/Enter toggles)
- Screen readers announce expanded/collapsed state
- Semantic HTML conveys structure to assistive technology
- No custom ARIA roles needed

### Browser Compatibility
All target browsers support `<details>` and `<summary>`:
- Chrome 12+ (target: 90+) ✅
- Firefox 49+ (target: 88+) ✅
- Safari 6+ (target: 14+) ✅
- Edge 79+ (target: 90+) ✅

### References
- MDN Web Docs: [details element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
- MDN Web Docs: [summary element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/summary)
- Can I Use: [details/summary](https://caniuse.com/details)

---

## 4. Attribute Header Layout Strategy

### Decision
Transform attribute rows from table cells into header-based sections using flexbox layout for horizontal environment columns.

### Rationale
- Moves from table-based layout (`<tr><td>attribute</td><td>value1</td><td>value2</td></tr>`)
- To section-based layout with attribute as `<h3>` header and values in flex columns
- Provides 20px+ vertical spacing between attributes (FR-002 requirement)
- Better visual hierarchy - attribute names stand out more prominently
- More horizontal space for values by removing attribute name from the row
- Easier to scan and identify which configuration settings differ

### Implementation Pattern
```html
<div class="attribute-section">
    <h3 class="attribute-header">
        <code>security_rule_collection</code>
        <span class="sensitive-badge">🔒 SENSITIVE</span>
    </h3>
    <div class="attribute-values">
        <div class="env-value-column">
            <div class="env-label">Test</div>
            <div class="value-container">
                <!-- Value content with diff highlighting -->
            </div>
        </div>
        <div class="env-value-column">
            <div class="env-label">Production</div>
            <div class="value-container">
                <!-- Value content with diff highlighting -->
            </div>
        </div>
    </div>
</div>
```

```css
.attribute-section {
    margin-bottom: 30px; /* 30px spacing between attributes */
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
}
```

### Alternatives Considered
- **Keep table layout, just increase spacing** - Rejected: Doesn't address horizontal space constraints
- **Use CSS Grid** - Rejected: Flexbox is simpler and more flexible for varying environment counts
- **Nested tables** - Rejected: Poor accessibility, complex markup, difficult to style

### Benefits
- Clear visual hierarchy (headers → values)
- Better use of horizontal space (no attribute name column consuming width)
- Easier to add/remove environments (flex layout adapts)
- More scannable for users comparing many attributes
- Aligns with FR-001 requirement for prominent headers

---

## 5. Environment-Specific Resource Badge Design

### Decision
Use amber/yellow color scheme with warning icon (⚠️) for environment-specific resource badges, distinct from blue/green diff highlighting.

### Rationale
- Amber/yellow conveys "attention" without implying error (red) or success (green)
- Distinguishes from blue (baseline changes) and green (comparison changes) diff colors
- Follows existing style guide warning color: `#ffa94d` (orange) / `#fff4e6` (light orange background)
- Badge shows which environment(s) contain the resource (e.g., "Test only", "Production only")
- Icon (⚠️) provides visual cue that's distinct from diff markers

### Implementation Pattern
```css
.env-specific-badge {
    display: inline-block;
    padding: 4px 10px;
    background: #ffa94d; /* Warning orange */
    color: #333;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: 600;
    margin-left: 10px;
}

.env-specific-section {
    background: #fff4e6; /* Light orange background */
    border-left: 4px solid #f59e0b; /* Darker orange accent */
}
```

### Alternatives Considered
- **Red color scheme** - Rejected: Implies error when resource may be intentionally environment-specific
- **Blue color scheme** - Rejected: Conflicts with baseline diff highlighting
- **Gray/neutral** - Rejected: Doesn't draw enough attention to important distinction
- **No badge, just section grouping** - Rejected: Loses per-resource visibility when scanning

### Color Palette Reference
From `docs/style-guide.md`:
- Warning Main: `#ffa94d` (orange)
- Warning Background: `#fff4e6` (cream)
- Warning Dark: `#e67700` (dark orange)
- Warning Alt: `#ffe8cc` (light orange)

### References
- Project Style Guide: [docs/style-guide.md](../../docs/style-guide.md#action-colors-resource-changes)

---

## Summary of Decisions

| Research Area | Decision | Key Constraint Satisfied |
|--------------|----------|--------------------------|
| Scrollbar Behavior | `overflow: auto` with max-height: 400px, max-width: 600px | FR-003, FR-004, FR-005, FR-010 |
| Sticky Headers | `position: sticky` on environment column headers only | FR-013 (user choice: Option A) |
| Collapsible Section | HTML5 `<details>`/`<summary>`, default open | FR-007, no-JavaScript constraint |
| Attribute Layout | Flexbox section-based layout with H3 headers | FR-001, FR-002 (20px spacing) |
| Env-Specific Badges | Amber/yellow warning color with ⚠️ icon | FR-006, FR-014 (distinct from diff colors) |

All decisions maintain:
- ✅ No JavaScript requirement
- ✅ Browser compatibility (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- ✅ Accessibility (keyboard navigation, screen reader support)
- ✅ Performance (<2 second load for 200 resources)
- ✅ Consistency with existing style guide

---

## Next Steps

Phase 1 will translate these research decisions into:
- **data-model.md**: Document any new CSS class entities (if needed)
- **contracts/html-structure.md**: Define the new HTML structure contract
- **quickstart.md**: Developer guide for implementing the UI changes
