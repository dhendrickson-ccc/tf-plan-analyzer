# Data Model: Multi-Environment Comparison UI Improvements

**Feature**: 006-comparison-ui-improvements  
**Date**: January 15, 2026  
**Purpose**: Document UI component entities and their relationships

---

## Overview

This feature does NOT introduce new data structures for comparison logic. All comparison entities (`ResourceComparison`, `AttributeDiff`, etc.) remain unchanged and are already documented in `.specify/memory/data_model.md`.

This document defines the **UI component entities** (CSS classes, HTML structure patterns) that represent the visual presentation layer for multi-environment comparison reports.

---

## UI Component Entities

### 1. Attribute Section

**Purpose**: Container for a single attribute comparison across environments

**HTML Structure**:
```html
<div class="attribute-section">
    <h3 class="attribute-header">...</h3>
    <div class="attribute-values">...</div>
</div>
```

**CSS Classes**:
- `.attribute-section` - Outer container with spacing, background, shadow
- `.attribute-header` - H3 header for attribute name
- `.attribute-values` - Flexbox container for environment value columns

**Properties**:
- Margin-bottom: 30px (provides 20px+ spacing per FR-002)
- Padding: 20px
- Background: white
- Border-radius: 8px
- Box-shadow: 0 1px 3px rgba(0,0,0,0.1)

**Relationship**: Contains one `Attribute Header` and one `Attribute Values Container`

---

### 2. Value Container

**Purpose**: Scrollable container for individual attribute values (one per environment)

**HTML Structure**:
```html
<div class="value-container">
    <!-- HTML-formatted value content with diff highlighting -->
</div>
```

**CSS Classes**:
- `.value-container` - Scrollable div with overflow constraints

**Properties**:
- Max-height: 400px (FR-004)
- Max-width: 600px (FR-005)
- Overflow: auto (FR-003, FR-010)
- Padding: 10px
- Border: 1px solid #e9ecef
- Border-radius: 4px
- Background: white

**Behavior**:
- Scrollbars appear only when content exceeds max dimensions (auto behavior)
- Independent scroll state per container (no interference between containers)
- Preserves existing diff highlighting classes (baseline-removed, baseline-added, char-removed, char-added)

**Relationship**: Child of `Environment Value Column`

---

### 3. Environment Value Column

**Purpose**: Groups environment label and value container for one environment in a flex layout

**HTML Structure**:
```html
<div class="env-value-column">
    <div class="env-label">Test</div>
    <div class="value-container">...</div>
</div>
```

**CSS Classes**:
- `.env-value-column` - Flex item for one environment's value
- `.env-label` - Environment name label

**Properties**:
- Flex: 1 (equal width distribution)
- Min-width: 300px (prevents excessive compression)
- Env label font-weight: 600
- Env label margin-bottom: 8px

**Relationship**: Parent of one `Value Container`, sibling of other environment columns within `Attribute Values Container`

---

### 4. Sticky Environment Header

**Purpose**: Column headers that remain visible when scrolling vertically through report

**HTML Structure**:
```html
<tr class="env-header-row">
    <th class="sticky-header">Test</th>
    <th class="sticky-header">Production</th>
</tr>
```

**CSS Classes**:
- `.env-header-row` - Table row for environment headers
- `.sticky-header` - Individual sticky header cell

**Properties**:
- Position: sticky
- Top: 0
- Z-index: 10 (above scrollable content)
- Background: #f8f9fa (opaque to prevent content showing through)
- Border-bottom: 2px solid #dee2e6
- Padding: 12px

**Behavior**:
- Sticks to top of viewport when scrolling vertically
- Only environment column headers stick (per FR-013 and user choice)
- Attribute headers within resource cards scroll normally

---

### 5. Environment-Specific Resource Badge

**Purpose**: Visual indicator for resources existing in only one environment

**HTML Structure**:
```html
<span class="env-specific-badge">⚠️ Test only</span>
```

**CSS Classes**:
- `.env-specific-badge` - Badge component

**Properties**:
- Display: inline-block
- Padding: 4px 10px
- Background: #ffa94d (warning orange per style guide)
- Color: #333 (dark text for contrast)
- Border-radius: 4px
- Font-size: 0.85em
- Font-weight: 600
- Margin-left: 10px

**Text Content Patterns**:
- Single environment: "{Environment} only" (e.g., "Test only")
- Multiple but not all: "Present in: Test, Staging" 
- Icon prefix: ⚠️ (warning triangle)

**Color Rationale**: Uses warning color (#ffa94d) distinct from diff highlighting (blue/green per FR-014)

**Relationship**: Inline with resource name or header

---

### 6. Environment-Specific Section

**Purpose**: Collapsible grouping for resources existing in limited environments

**HTML Structure**:
```html
<details open class="env-specific-section">
    <summary class="env-specific-header">
        <strong>⚠️ Environment-Specific Resources</strong>
        <span class="resource-count">(5 resources)</span>
    </summary>
    <div class="env-specific-content">
        <!-- Resource cards -->
    </div>
</details>
```

**CSS Classes**:
- `.env-specific-section` - Outer details container
- `.env-specific-header` - Summary clickable header
- `.env-specific-content` - Container for resource cards
- `.resource-count` - Badge showing count

**Properties**:
- Background: #fff4e6 (light orange warning background)
- Border-left: 4px solid #f59e0b (darker orange accent)
- Border-radius: 4px
- Padding: 15px
- Margin: 20px 0

**Behavior**:
- Default state: Expanded (`<details open>` per user choice)
- Collapsible via native HTML5 `<details>` mechanism (no JavaScript)
- Keyboard accessible (Space/Enter toggles)
- Screen reader announces expanded/collapsed state

**Relationship**: Container for multiple `Resource Card` entities (environment-specific resources only)

---

## CSS Class Relationships

```text
.attribute-section
├── .attribute-header (H3)
└── .attribute-values (flex container)
    ├── .env-value-column (Test)
    │   ├── .env-label
    │   └── .value-container
    ├── .env-value-column (Production)
    │   ├── .env-label
    │   └── .value-container
    └── ... (additional environments)

.env-specific-section (details element)
├── .env-specific-header (summary)
│   ├── (icon + title)
│   └── .resource-count
└── .env-specific-content
    ├── (resource card 1 with .env-specific-badge)
    ├── (resource card 2 with .env-specific-badge)
    └── ...
```

---

## Integration with Existing Entities

### Preserved Entities (from `.specify/memory/data_model.md`)

These entities remain unchanged:

- **ResourceComparison**: Core comparison logic entity
  - Fields: resource_name, resource_type, is_present_in, attribute_diffs, has_differences
  - No changes to data structure
  - UI presentation changes only

- **AttributeDiff**: Attribute-level diff entity
  - Fields: attribute_name, env_values, is_different
  - No changes to data structure
  - Values are now rendered in scrollable containers

### CSS Class Reuse (from `docs/style-guide.md`)

Existing diff highlighting classes are preserved within new Value Containers:

- `.baseline-removed` - Background: #bbdefb (light blue)
- `.baseline-char-removed` - Background: #90caf9 (medium blue)
- `.baseline-added` - Background: #c8e6c9 (light green)
- `.baseline-char-added` - Background: #81c784 (medium green)
- `.char-removed` - Background: #ff9999 (light red)
- `.char-added` - Background: #99ff99 (light green)
- `.known-after-apply` - Background: #ffe8a1 (light yellow)

---

## Summary

| Entity | Type | Purpose | Key CSS Class |
|--------|------|---------|---------------|
| Attribute Section | Container | Groups attribute header + values | `.attribute-section` |
| Value Container | Component | Scrollable value display | `.value-container` |
| Environment Value Column | Layout | Flex column for one environment | `.env-value-column` |
| Sticky Environment Header | Component | Persistent column headers | `.sticky-header` |
| Environment-Specific Badge | Component | Visual indicator for limited-env resources | `.env-specific-badge` |
| Environment-Specific Section | Container | Collapsible group of env-specific resources | `.env-specific-section` |

All entities are **presentational only** - no changes to comparison data structures or logic.
