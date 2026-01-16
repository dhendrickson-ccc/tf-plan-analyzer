# Data Model: Normalization-Based Difference Filtering

**Feature**: 007-normalization-diff-filtering  
**Date**: 2025-01-15  
**Status**: Complete

## Overview

This document defines the data entities for normalization-based difference filtering. All entities extend or integrate with the existing canonical data model in `.specify/memory/data_model.md`.

---

## New Entities

### NormalizationConfig

Represents loaded and validated normalization patterns from `normalizations.json`.

**Purpose**: Store pre-compiled regex patterns for efficient normalization during comparison.

**Fields**:
- `name_patterns` (List[NormalizationPattern]): Patterns for normalizing attribute names and values
- `resource_id_patterns` (List[NormalizationPattern]): Patterns for normalizing Azure resource IDs, subscription IDs, tenant IDs
- `source_file` (Path): Path to the normalization config file (for error messages)

**Behavior**:
- Loaded via `load_normalization_config(file_path: Path)` in `normalization_utils.py`
- Patterns pre-compiled at load time for performance
- Validation ensures all patterns are valid regex
- Immutable after loading (patterns don't change during comparison)

**Example**:
```python
config = NormalizationConfig(
    name_patterns=[
        NormalizationPattern(
            pattern=re.compile(r'-(t|test|tst)-'),
            replacement='-ENV-',
            description='Normalize test environment markers'
        ),
        NormalizationPattern(
            pattern=re.compile(r'-(p|prod|prd)-'),
            replacement='-ENV-',
            description='Normalize production environment markers'
        )
    ],
    resource_id_patterns=[
        NormalizationPattern(
            pattern=re.compile(r'/subscriptions/[0-9a-f-]{36}/'),
            replacement='/subscriptions/SUBSCRIPTION_ID/',
            description='Normalize Azure subscription IDs'
        )
    ],
    source_file=Path('examples/normalizations.json')
)
```

**Validation Rules**:
- At least one of `name_patterns` or `resource_id_patterns` must be non-empty
- All pattern strings must compile as valid Python regex
- Replacement strings can contain backreferences (\1, \2, etc.) if pattern has groups

---

### NormalizationPattern

Represents a single regex find/replace transformation.

**Purpose**: Encapsulate a compiled regex pattern with its replacement string for efficient application.

**Fields**:
- `pattern` (re.Pattern): Compiled regex pattern to match
- `replacement` (str): String to replace matches with (can include backreferences)
- `description` (str): Human-readable explanation of what the pattern does (optional, for documentation)
- `original_pattern` (str): Original pattern string (for error messages and verbose logging)

**Behavior**:
- Compiled at config load time via `re.compile()`
- Applied via `pattern.sub(replacement, value)`
- First-match-wins strategy: each pattern attempts one replacement, then proceeds to next

**Example**:
```python
pattern = NormalizationPattern(
    pattern=re.compile(r'-(t|test|tst)-'),
    replacement='-ENV-',
    description='Normalize test environment markers',
    original_pattern='-(t|test|tst)-'
)

# Usage
value = "storage-account-t-eastus"
normalized = pattern.pattern.sub(pattern.replacement, value)
# Result: "storage-account-ENV-eastus"
```

---

## Modified Entities

### AttributeDiff (extended)

**Existing Purpose**: Represents a single attribute's values across environments for HTML table rendering.

**New Fields**:
- `ignored_due_to_normalization` (bool): Whether this attribute was filtered because normalized values matched
  - Default: False
  - Set to True if: is_different was True, but after normalization all env_values are identical
- `normalized_values` (Dict[str, Any]): Environment label → normalized value mapping (optional, for verbose logging)
  - Default: {} (empty dict)
  - Populated when: (1) verbose logging mode enabled (--verbose-normalization flag), OR (2) ignored_due_to_normalization=True (for debugging/audit trail)
  - Allows users to see what the normalized values were and verify pattern application correctness

**Modified Behavior**:
- During `compute_attribute_diffs()`: After AttributeDiff created, apply normalization if config present
- Normalization check:
  1. If `is_different=True` and normalization config provided
  2. Apply patterns to all `env_values`
  3. Compare normalized values for equality
  4. If all normalized values identical: set `ignored_due_to_normalization=True`
- Rendering: Skip attribute in HTML/text output if `ignored_due_to_config OR ignored_due_to_normalization`

**Example**:
```python
attr_diff = AttributeDiff(
    attribute_name="name",
    env_values={
        "test": "storage-account-t-eastus",
        "prod": "storage-account-p-eastus"
    },
    is_different=True,
    attribute_type="primitive"
)

# After normalization applied:
attr_diff.ignored_due_to_normalization = True
attr_diff.normalized_values = {
    "test": "storage-account-ENV-eastus",
    "prod": "storage-account-ENV-eastus"
}
# Both normalized to same value, so difference ignored
```

---

### ResourceComparison (extended)

**Existing Purpose**: Represents a single resource address with configuration across all environments.

**New Fields**:
- `normalization_config` (Optional[NormalizationConfig]): Normalization patterns to apply, if any
  - Default: None
  - Passed from MultiEnvReport during initialization
  - Used in `compute_attribute_diffs()` to apply normalization

**Modified Methods**:
- `compute_attribute_diffs()`:
  - **Before**: Create AttributeDiff for each attribute, mark is_different based on value comparison
  - **After**: Same as before, PLUS apply normalization if config present:
    ```python
    if self.normalization_config:
        for attr_diff in self.attribute_diffs:
            if attr_diff.is_different:
                normalized_match = apply_normalization_check(attr_diff, self.normalization_config)
                if normalized_match:
                    attr_diff.ignored_due_to_normalization = True
    ```

**Example**:
```python
rc = ResourceComparison(
    resource_address="azurerm_storage_account.main",
    resource_type="azurerm_storage_account"
)
rc.normalization_config = loaded_normalization_config  # Set from MultiEnvReport
rc.add_environment_config("test", test_config)
rc.add_environment_config("prod", prod_config)
rc.detect_differences()
rc.compute_attribute_diffs()  # Now includes normalization logic
```

---

### IgnoreConfig (extended schema)

**Existing Purpose**: Configuration for filtering known acceptable differences (from `ignore_config.json`).

**New Field** (schema extension, not code class):
- `normalization_config_path` (Optional[str]): Path to `normalizations.json` file
  - If provided: Load normalization config from this path
  - If absent or empty: Skip normalization (backward compatible)
  - Can be absolute or relative (relative to ignore_config.json location)

**Updated Schema**:
```json
{
  "global_ignores": {
    "tags": "Tags managed separately"
  },
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "description": "Environment-specific"
    }
  },
  "normalization_config_path": "examples/normalizations.json"
}
```

**Validation**:
- Field is optional (can be omitted)
- If present, must be non-empty string
- File must exist and be readable (checked during load)
- Path can be relative (resolved from ignore config directory)

---

## Data Flow

### Comparison Workflow with Normalization

```
1. Load Configuration
   ├─ Load ignore_config.json (existing)
   │  └─ If normalization_config_path present:
   │     └─ Load normalizations.json → NormalizationConfig
   │
2. Build Comparisons (existing)
   ├─ For each resource:
   │  ├─ Apply ignore config filtering (existing)
   │  ├─ Detect differences (existing)
   │  └─ Pass normalization_config to ResourceComparison
   │
3. Compute Attribute Diffs (modified)
   ├─ For each attribute:
   │  ├─ Create AttributeDiff with env_values
   │  ├─ Check if values differ (existing)
   │  └─ ⭐ NEW: If normalization_config present:
   │     ├─ Apply name_patterns to value
   │     ├─ If attribute is ID: apply resource_id_patterns
   │     ├─ Compare normalized values
   │     └─ If match: set ignored_due_to_normalization=True
   │
4. Generate Output
   ├─ Skip attributes where:
   │  ├─ ignored_due_to_config=True (existing), OR
   │  └─ ignored_due_to_normalization=True (new)
   │
5. Render Summary
   ├─ Count config-ignored: sum(ignored_due_to_config)
   ├─ Count norm-ignored: sum(ignored_due_to_normalization)
   └─ Display: "X ignored (Y config, Z normalized)"
```

---

## Integration with Canonical Data Model

All entities will be added to `.specify/memory/data_model.md` under new section:

```markdown
## Feature: Normalization-Based Difference Filtering (007)

### NormalizationConfig
[Full definition as above]

### NormalizationPattern
[Full definition as above]

### Extensions to Existing Entities:

#### AttributeDiff
- Added: `ignored_due_to_normalization` (bool)
- Added: `normalized_values` (Dict[str, Any])

#### ResourceComparison
- Added: `normalization_config` (Optional[NormalizationConfig])

#### IgnoreConfig (schema)
- Added: `normalization_config_path` (Optional[str])
```

---

## Backward Compatibility

**No Breaking Changes**:
- All new fields are optional with sensible defaults
- Normalization only occurs if `normalization_config_path` provided in ignore config
- Existing comparisons work unchanged without normalization config
- Existing tests pass without modification (validated via Principle V)

**Default Values**:
- `ignored_due_to_normalization`: False
- `normalized_values`: {} (empty dict)
- `normalization_config`: None
- `normalization_config_path`: undefined (field absent from ignore config schema)

**Validation**:
- Existing test suite must pass with no normalization config (Constitution Principle VI requirement)
- New tests added for normalization features

---

## Summary

| Entity | Type | Purpose |
|--------|------|---------|
| NormalizationConfig | New | Store pre-compiled normalization patterns |
| NormalizationPattern | New | Encapsulate single regex transformation |
| AttributeDiff | Extended | Track normalization-ignored attributes |
| ResourceComparison | Extended | Apply normalization during diff computation |
| IgnoreConfig | Extended | Reference normalization config file |

**Data model complete. Ready for contracts and quickstart.**
