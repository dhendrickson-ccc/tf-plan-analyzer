# Data Model: Compare Subcommand Enhancements

**Feature**: 004-compare-enhancements  
**Date**: 2026-01-14

## Overview

This document defines the data entities introduced or modified for the compare subcommand enhancements feature. These entities support ignore file configuration and attribute-level diff views in multi-environment comparisons.

---

## New Entities

### AttributeDiff

Represents a single changed top-level attribute across multiple environments.

**Purpose**: Enable attribute-level granularity in comparison reports, showing only what changed rather than full resource configurations.

**Fields**:
- `attribute_name` (str): Top-level attribute key (e.g., "location", "identity", "tags")
- `env_values` (Dict[str, Any]): Mapping of environment name → attribute value
  - Key: environment label (e.g., "dev", "prod")
  - Value: attribute value in that environment (can be primitive, dict, list, or None)
- `is_different` (bool): Whether values differ across any environments
- `attribute_type` (str): Type classification for rendering ("primitive", "object", "array", "null")

**Example**:
```python
AttributeDiff(
    attribute_name="location",
    env_values={
        "dev": "eastus",
        "staging": "centralus",
        "prod": "westus"
    },
    is_different=True,
    attribute_type="primitive"
)
```

**Usage**: Stored in ResourceComparison objects, iterated during HTML generation to render attribute-level diff tables.

---

### IgnoreStatistics

Tracks statistics about ignored attributes in a comparison.

**Purpose**: Provide transparency to users about how many attributes were filtered by ignore rules.

**Fields**:
- `total_ignored_attributes` (int): Total count of attribute instances ignored across all resources
- `resources_with_ignores` (int): Count of resources that had at least one attribute ignored
- `all_changes_ignored` (int): Count of resources where all changes were ignored
- `ignore_breakdown` (Dict[str, int]): Mapping of attribute name → times ignored

**Example**:
```python
IgnoreStatistics(
    total_ignored_attributes=45,
    resources_with_ignores=12,
    all_changes_ignored=3,
    ignore_breakdown={
        "tags": 38,
        "description": 7
    }
)
```

**Usage**: Calculated during build_comparisons(), displayed in HTML report summary and per-resource indicators.

---

## Modified Entities

### ResourceComparison (extended)

**Existing Purpose**: Represents a single resource address with configuration across all environments.

**New Fields**:
- `ignored_attributes` (Set[str]): Set of top-level attribute names filtered by ignore rules
  - Populated during ignore config application
  - Used to display "N attributes ignored" indicator in HTML
- `attribute_diffs` (List[AttributeDiff]): List of top-level attributes that changed
  - Computed after ignore filtering
  - Used for attribute-level HTML rendering
  - Empty if no differences or all changes ignored

**Modified Behavior**:
- After ignore config applied: `ignored_attributes` populated, configurations filtered
- After diff detection: `attribute_diffs` computed from remaining differences
- Summary calculation: If `attribute_diffs` is empty and `ignored_attributes` is not, resource counted as "identical after filtering"

**Example**:
```python
ResourceComparison(
    resource_address="azurerm_storage_account.main",
    env_configs={
        "dev": {"location": "eastus", "sku": "Standard_LRS"},
        "prod": {"location": "westus", "sku": "Standard_LRS"}
    },
    ignored_attributes={"tags", "description"},  # NEW
    attribute_diffs=[                             # NEW
        AttributeDiff(attribute_name="location", env_values={"dev": "eastus", "prod": "westus"}, is_different=True)
    ]
)
```

---

### MultiEnvReport (extended)

**Existing Purpose**: Orchestrates multi-environment comparison and report generation.

**New Fields**:
- `ignore_statistics` (Optional[IgnoreStatistics]): Statistics about ignored attributes
  - None if no ignore config provided
  - Populated during build_comparisons()
  - Displayed in HTML report header

**New Methods**:
- `_compute_attribute_diffs(resource_comparison: ResourceComparison) -> List[AttributeDiff]`
  - Extracts changed top-level attributes from env_configs
  - Handles null/missing attributes across environments
  - Returns list of AttributeDiff objects
- `_apply_ignore_config_to_comparison(resource_comparison: ResourceComparison) -> None`
  - Applies global and resource-specific ignore rules
  - Populates `ignored_attributes` set
  - Filters env_configs in-place
- `_calculate_ignore_statistics() -> IgnoreStatistics`
  - Aggregates ignored attribute counts across all comparisons
  - Calculates resources with all changes ignored

**Modified Methods**:
- `build_comparisons()`: Now calls ignore application and attribute diff computation
- `generate_html()`: Renders attribute-level diff tables instead of full JSON

---

## Entity Relationships

```text
MultiEnvReport
├── environments: List[EnvironmentPlan]                 (existing)
├── resource_comparisons: List[ResourceComparison]      (existing, extended)
│   └── ResourceComparison
│       ├── env_configs: Dict[str, Dict]                (existing)
│       ├── ignored_attributes: Set[str]                (NEW)
│       └── attribute_diffs: List[AttributeDiff]        (NEW)
│           └── AttributeDiff
│               ├── attribute_name: str
│               ├── env_values: Dict[str, Any]
│               ├── is_different: bool
│               └── attribute_type: str
├── ignore_statistics: Optional[IgnoreStatistics]       (NEW)
│   └── IgnoreStatistics
│       ├── total_ignored_attributes: int
│       ├── resources_with_ignores: int
│       ├── all_changes_ignored: int
│       └── ignore_breakdown: Dict[str, int]
└── summary_stats: Dict[str, int]                       (existing, modified calculation)
```

---

## Data Flow

1. **Load Phase**: EnvironmentPlan objects load plan JSON files
2. **Build Phase**:
   - Extract all unique resource addresses
   - Create ResourceComparison objects with env_configs
   - **NEW**: Apply ignore configuration → populate `ignored_attributes`, filter configs
   - Detect differences (existing logic)
   - **NEW**: Compute attribute-level diffs → populate `attribute_diffs`
   - **NEW**: Calculate ignore statistics
3. **Summary Phase**: Calculate summary stats considering filtered resources
4. **Render Phase**:
   - **NEW**: Display ignore statistics in header
   - Iterate resources → **NEW**: Iterate attribute_diffs instead of full JSON
   - **NEW**: Show "N attributes ignored" indicator per resource

---

## Backward Compatibility

All new fields are optional and default-initialized:
- `ignored_attributes` defaults to empty set
- `attribute_diffs` defaults to empty list
- `ignore_statistics` defaults to None

When no `--config` flag provided:
- Ignore logic skipped
- `ignored_attributes` remains empty
- `attribute_diffs` computed from full configs
- Existing behavior fully preserved

---

## Performance Considerations

- **AttributeDiff creation**: O(k × n) where k = top-level keys, n = environments
  - For 100 resources × 10 attributes × 3 environments = 3000 comparisons
  - Estimated: < 25ms total (based on research findings)
- **Memory overhead**: 
  - AttributeDiff: ~200 bytes per instance
  - 100 resources × 10 attributes = 1000 instances = ~200KB
  - Negligible compared to full JSON configs in memory
- **HTML rendering**: Attribute-level iteration reduces HTML size
  - Old: Full JSON for each env × resources
  - New: Only changed attributes × resources
  - Expected 30-50% reduction in HTML file size

---

## Future Extensions

Potential enhancements (out of scope for this feature):
- Deep attribute path tracking (show nested change paths, not just top-level)
- Attribute change type classification (added/removed/modified)
- Value diff highlighting within complex objects
- Ignore rule wildcards (e.g., "identity.*")
