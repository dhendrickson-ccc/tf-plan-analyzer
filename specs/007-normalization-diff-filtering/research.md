# Research: Normalization-Based Difference Filtering

**Feature**: 007-normalization-diff-filtering  
**Date**: 2025-01-15  
**Status**: Complete

## Overview

This document consolidates research decisions for implementing normalization-based difference filtering. All technical unknowns from the specification have been resolved through analysis of existing codebase patterns, Python regex capabilities, and performance considerations.

---

## 1. Normalization Config Structure & Loading

### Decision: Mirror ignore_utils.py Pattern

**Rationale**: The existing `ignore_utils.py` module provides a proven pattern for loading and validating JSON config files. We'll follow the same structure for `normalizations.json`.

**Config Schema**:
```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst)-",
      "replacement": "-ENV-",
      "description": "Normalize test environment suffixes"
    },
    {
      "pattern": "-(p|prod|prd)-",
      "replacement": "-ENV-",
      "description": "Normalize production environment suffixes"
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f-]{36}/",
      "replacement": "/subscriptions/SUBSCRIPTION_ID/",
      "description": "Normalize Azure subscription IDs"
    },
    {
      "pattern": "/tenants/[0-9a-f-]{36}/",
      "replacement": "/tenants/TENANT_ID/",
      "description": "Normalize Azure tenant IDs"
    }
  ]
}
```

**Validation Rules** (from FR-009 clarifications):
- Valid JSON structure
- Root object with `name_patterns` and/or `resource_id_patterns` arrays
- Each pattern object has required fields: `pattern` (string), `replacement` (string)
- Optional `description` field for documentation
- Regex patterns must compile successfully (use `re.compile()` for validation)
- Error messages include problem type, location (pattern index), and suggestion

**Loading Function** (new file: `src/lib/normalization_utils.py`):
```python
def load_normalization_config(file_path: Path) -> Dict:
    """
    Load and validate normalization configuration from JSON file.
    
    Raises:
        FileNotFoundError: Config file not found (with clear path in message)
        json.JSONDecodeError: Malformed JSON (with line/column info)
        ValueError: Invalid structure or regex patterns (with specific problem)
    """
```

**Integration with Ignore Config**:
- Extend `ignore_config.json` schema with optional `normalization_config_path` field
- Example:
  ```json
  {
    "global_ignores": {"tags": "Managed separately"},
    "normalization_config_path": "examples/normalizations.json"
  }
  ```
- Load normalization config only if path is present and non-empty
- Normalization is completely optional (backward compatible)

---

## 2. Regex Pattern Application Strategy

### Decision: First-Match-Wins with Ordered Application

**Rationale** (from clarification Q3): Predictable behavior, allows specific patterns before general ones, matches common transformation pipeline patterns.

**Application Algorithm**:
```python
def apply_normalization_patterns(value: str, patterns: List[Dict]) -> str:
    """
    Apply normalization patterns in order using first-match-wins strategy.
    
    For each pattern in order:
        1. Compile regex pattern
        2. Attempt re.sub(pattern, replacement, value)
        3. If substitution occurs, use result as new value
        4. Proceed to next pattern (regardless of match)
    
    Returns normalized value after all patterns applied.
    """
    normalized = value
    for pattern_obj in patterns:
        pattern = re.compile(pattern_obj['pattern'])
        normalized = pattern.sub(pattern_obj['replacement'], normalized)
    return normalized
```

**Key Points**:
- Each pattern sees the result of previous patterns (sequential transformation)
- Pattern order matters (place specific patterns before general ones)
- All patterns attempt application (not "stop on first match")
- First-match-wins means each pattern's regex matches once per position

**Performance Consideration**: Pre-compile all regex patterns at config load time, cache in pattern objects. Avoid recompiling on every attribute comparison.

---

## 3. Normalization Timing & Integration Point

### Decision: Apply After Diff Computation, Before Filtering

**Workflow** (in `multi_env_comparator.py`):
```
1. Load plans and build ResourceComparison objects
2. Apply ignore config filtering (existing)
3. Detect differences (existing: compare env_configs_raw)
4. Compute attribute diffs (existing: creates AttributeDiff objects)
5. ⭐ NEW: Apply normalization to attribute values
   - For each AttributeDiff where is_different=True:
     - Apply normalization to all env_values
     - Re-check if normalized values match
     - If match: set ignored_due_to_normalization=True
6. Filter attribute diffs (skip if ignored_due_to_config OR ignored_due_to_normalization)
7. Generate HTML/text output
```

**Integration Location**: In `ResourceComparison.compute_attribute_diffs()` method, after AttributeDiff objects are created but before they're filtered.

**Pseudocode**:
```python
def compute_attribute_diffs(self) -> None:
    # ... existing code creates attribute_diffs list ...
    
    # NEW: Apply normalization if config provided
    if self.normalization_config:
        for attr_diff in self.attribute_diffs:
            if attr_diff.is_different:
                # Apply normalization to all env values
                normalized_values = {}
                for env, value in attr_diff.env_values.items():
                    if value is not None and isinstance(value, str):
                        normalized = apply_normalization(value, self.normalization_config)
                        normalized_values[env] = normalized
                    else:
                        normalized_values[env] = value
                
                # Check if normalized values are identical
                unique_normalized = set(
                    json.dumps(v, sort_keys=True) 
                    for v in normalized_values.values()
                )
                if len(unique_normalized) == 1:
                    attr_diff.ignored_due_to_normalization = True
```

---

## 4. Attribute Value Type Handling

### Decision: Apply Normalization Only to String Values

**Rationale**: Normalization patterns are regex-based, which only makes sense for strings. Other types (numbers, booleans, null, complex objects) should not be normalized.

**Type Handling Rules**:
- **String values**: Apply normalization patterns
- **Numbers**: No normalization (compare as-is)
- **Booleans**: No normalization (compare as-is)
- **null/None**: No normalization (compare as-is)
- **Complex objects** (dict/list): 
  - **Name patterns**: Apply to stringified JSON representation (for attributes like `identity` or `tags`)
  - **Resource ID patterns**: Only apply if attribute name suggests it's a resource ID (e.g., "id", "resource_id", "parent_id")

**Type Detection**:
```python
def should_normalize_value(attr_name: str, value: Any) -> bool:
    """Determine if a value should be normalized."""
    if isinstance(value, str):
        return True
    if isinstance(value, (dict, list)):
        # Only normalize complex values for specific attribute names
        return attr_name.lower() in ['id', 'resource_id', 'parent_id', 'source_id', 'target_id']
    return False
```

---

## 5. Name Normalization vs Resource ID Normalization

### Decision: Two-Phase Application Based on Attribute Name

**Phase 1 - Name Normalization** (applied to all string attributes):
- Patterns from `name_patterns` array
- Examples: environment suffixes (-t-, -p-), region codes (eastus vs centralus)
- Applied to: `name`, `display_name`, `resource_group_name`, etc.

**Phase 2 - Resource ID Normalization** (applied only to ID-like attributes):
- Patterns from `resource_id_patterns` array  
- Examples: subscription IDs, tenant IDs, UUIDs
- Applied to: `id`, `resource_id`, `parent_id`, `source_id`, any attribute ending in `_id`

**Attribute Classification**:
```python
def classify_attribute(attr_name: str) -> str:
    """Classify attribute for normalization strategy."""
    normalized_name = attr_name.lower()
    
    # Resource ID attributes
    if normalized_name in ['id', 'resource_id', 'parent_id', 'source_id', 'target_id']:
        return 'resource_id'
    if normalized_name.endswith('_id'):
        return 'resource_id'
    
    # Name attributes (default)
    return 'name'

def apply_normalization(value: str, config: Dict, attr_name: str) -> str:
    """Apply appropriate normalization based on attribute type."""
    attr_type = classify_attribute(attr_name)
    
    # Always apply name patterns
    result = apply_normalization_patterns(value, config.get('name_patterns', []))
    
    # Apply resource ID patterns if applicable
    if attr_type == 'resource_id':
        result = apply_normalization_patterns(result, config.get('resource_id_patterns', []))
    
    return result
```

---

## 6. Tracking & UI Integration

### Decision: Extend AttributeDiff with Normalization Flag

**AttributeDiff Extension** (in `src/core/multi_env_comparator.py`):
```python
class AttributeDiff:
    def __init__(self, attribute_name, env_values, is_different, attribute_type):
        self.attribute_name = attribute_name
        self.env_values = env_values
        self.is_different = is_different
        self.attribute_type = attribute_type
        # NEW: Normalization tracking
        self.ignored_due_to_normalization = False
        self.normalized_values = {}  # Optional: for debugging/verbose mode
```

**Filtering Logic Update**:
```python
# In _render_attribute_table() and text output
for attr_diff in resource_comparison.attribute_diffs:
    # Skip if ignored by config OR normalization
    if attr_diff.ignored_due_to_config or attr_diff.ignored_due_to_normalization:
        continue
    # Render attribute...
```

**Badge Rendering Update** (in `src/lib/html_generation.py`):
```python
# Calculate counts
config_ignored_count = sum(1 for ad in rc.attribute_diffs if ad.ignored_due_to_config)
norm_ignored_count = sum(1 for ad in rc.attribute_diffs if ad.ignored_due_to_normalization)
total_ignored = config_ignored_count + norm_ignored_count

# Badge HTML
if total_ignored > 0:
    badge_html = f'''
    <span class="badge badge-ignored" title="Config: {config_ignored_count}, Normalized: {norm_ignored_count}">
        {total_ignored} ignored ({config_ignored_count} config, {norm_ignored_count} normalized)
    </span>
    '''
```

**Tooltip Enhancement**: Use existing custom tooltip CSS (from feature 006) to show breakdown on hover.

---

## 7. Logging & Observability

### Decision: Summary Stats Always, Verbose Mode Optional

**Console Output - Summary Stats** (from clarification Q4):
```
Comparing 3 environments: dev, staging, prod
✅ Comparison complete
📊 Summary:
   - Resources: 217 total
   - With differences: 45
   - Attributes ignored (config): 23
   - Attributes ignored (normalization): 18  ⭐ NEW
   - Total ignored: 41
```

**Verbose Logging Mode** (optional `--verbose-normalization` flag):
```
🔄 Applying normalization patterns...
  ✓ name_patterns: 2 patterns loaded
  ✓ resource_id_patterns: 3 patterns loaded
  
📝 Normalization details:
  Resource: azurerm_storage_account.main
    Attribute: name
      Before: storage-account-t-eastus
      After:  storage-account-ENV-eastus
      Pattern: -(t|test|tst)- → -ENV-
      ✓ Normalized difference ignored
    
  Resource: azurerm_app_service.api
    Attribute: resource_id
      Before: /subscriptions/abc-123-def-456/resourceGroups/rg-test/...
      After:  /subscriptions/SUBSCRIPTION_ID/resourceGroups/rg-test/...
      Pattern: /subscriptions/[0-9a-f-]{36}/ → /subscriptions/SUBSCRIPTION_ID/
      ✓ Normalized difference ignored
```

**Implementation**:
```python
def apply_normalization_with_logging(
    attr_diff: AttributeDiff, 
    config: Dict, 
    verbose: bool = False
) -> None:
    """Apply normalization and optionally log details."""
    # ... normalization logic ...
    
    if verbose and attr_diff.ignored_due_to_normalization:
        print(f"  Resource: {resource_address}")
        print(f"    Attribute: {attr_diff.attribute_name}")
        for env, original in attr_diff.env_values.items():
            normalized = attr_diff.normalized_values[env]
            print(f"      {env}: {original} → {normalized}")
        print(f"      ✓ Normalized difference ignored")
```

---

## 8. Error Handling & Validation

### Decision: Fail Fast with Detailed Messages

**Config Load Errors** (from clarification Q2):
```python
# File not found
raise FileNotFoundError(
    f"Normalization config file not found: {file_path}\n"
    f"Hint: Check path in ignore_config.json 'normalization_config_path' field"
)

# Invalid JSON
raise json.JSONDecodeError(
    f"Malformed JSON in normalization config: {file_path}",
    doc, pos
)

# Invalid structure
raise ValueError(
    f"Invalid normalization config: missing required field 'pattern' "
    f"at name_patterns[2]\n"
    f"Expected structure: {{'pattern': 'regex', 'replacement': 'text'}}"
)

# Regex compilation error
raise ValueError(
    f"Invalid regex pattern at resource_id_patterns[1]: {pattern}\n"
    f"Error: {str(regex_error)}\n"
    f"Hint: Check pattern syntax. Test with: python -c \"import re; re.compile(r'{pattern}')\""
)
```

**Runtime Errors**:
- If normalization fails during comparison, log warning but don't abort (graceful degradation)
- Track failed normalizations in statistics for visibility

---

## 9. Performance Optimization

### Decision: Pre-compile Patterns, Minimize String Operations

**Optimization Strategies**:
1. **Pattern Pre-compilation**: Compile all regex patterns at config load time
   ```python
   class NormalizationConfig:
       def __init__(self, config_dict):
           self.name_patterns = [
               {'regex': re.compile(p['pattern']), 'replacement': p['replacement']}
               for p in config_dict.get('name_patterns', [])
           ]
   ```

2. **Early Exit**: Skip normalization if no patterns defined or value is None
   ```python
   if not patterns or value is None:
       return value
   ```

3. **String Type Check**: Only normalize if isinstance(value, str) to avoid type conversion overhead

4. **Lazy Normalization**: Only normalize when `is_different=True` (don't waste cycles on identical attributes)

**Performance Target** (from clarification Q1): 
- Baseline: Comparison without normalization config
- With normalization: ≤10% slower on same dataset
- Measurement: Time full comparison with/without normalization_config_path

**Profiling Points**:
- Time spent in `apply_normalization_patterns()`
- Number of regex operations performed
- Memory overhead of storing normalized_values

---

## 10. Example Normalization Patterns

### Reference Patterns (from az-env-compare-config)

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst|testing)-",
      "replacement": "-ENV-",
      "description": "Normalize test environment markers"
    },
    {
      "pattern": "-(p|prod|prd|production)-",
      "replacement": "-ENV-",
      "description": "Normalize production environment markers"
    },
    {
      "pattern": "-(d|dev|development)-",
      "replacement": "-ENV-",
      "description": "Normalize dev environment markers"
    },
    {
      "pattern": "-(s|stage|stg|staging)-",
      "replacement": "-ENV-",
      "description": "Normalize staging environment markers"
    },
    {
      "pattern": "eastus|centralus|westus",
      "replacement": "REGION",
      "description": "Normalize Azure region names"
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/subscriptions/SUBSCRIPTION_ID",
      "description": "Normalize Azure subscription GUIDs"
    },
    {
      "pattern": "/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/tenants/TENANT_ID",
      "description": "Normalize Azure tenant GUIDs"
    },
    {
      "pattern": "/resourceGroups/rg-(t|test|tst|p|prod|prd|d|dev|s|stage|stg)-",
      "replacement": "/resourceGroups/rg-ENV-",
      "description": "Normalize resource group environment prefixes"
    }
  ]
}
```

**Usage in examples/normalizations.json**:
- Copy patterns above as starting point
- Include comment about source: "Patterns adapted from az-env-compare-config repository"
- Add instructions for customization in README.md

---

## 11. Testing Strategy

### Unit Tests (tests/unit/test_normalization_utils.py)

**Test Coverage**:
- ✅ Load valid normalization config
- ✅ Load config with only name_patterns
- ✅ Load config with only resource_id_patterns
- ✅ File not found raises FileNotFoundError with clear message
- ✅ Malformed JSON raises JSONDecodeError
- ✅ Invalid pattern (bad regex) raises ValueError with pattern location
- ✅ Missing required fields raises ValueError
- ✅ Pattern compilation and caching works
- ✅ apply_normalization_patterns() with single pattern
- ✅ apply_normalization_patterns() with multiple ordered patterns
- ✅ apply_normalization_patterns() with no matches returns original
- ✅ Normalization only applied to string values (not int, bool, None, dict)
- ✅ Resource ID patterns only applied to ID-like attributes

### End-to-End Tests (tests/e2e/test_e2e_normalization.py)

**Test Scenarios**:
- ✅ Compare with normalization config reduces differences
- ✅ Badge shows combined counts (config + normalized)
- ✅ Tooltip shows separate sections for config vs normalized
- ✅ Summary stats show normalization counts
- ✅ Verbose mode shows before/after values
- ✅ Invalid normalization config fails with clear error
- ✅ Missing normalization file fails with helpful message
- ✅ Backward compatibility: comparison works without normalization config

### Live Testing

**Test Data** (from az-env-compare-config patterns):
- Create test plan JSONs with environment-specific naming: `storage-t-eastus` vs `storage-p-eastus`
- Create test plan JSONs with subscription ID differences
- Verify normalization reduces differences in HTML output
- Verify badge shows "X ignored (Y config, Z normalized)"

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Config Structure | Mirror ignore_utils.py pattern | Proven, consistent, familiar to users |
| Pattern Strategy | First-match-wins, ordered application | Predictable, allows specific→general ordering |
| Timing | After diff computation, before filtering | Preserves original values, integrates cleanly |
| Type Handling | String values only | Regex only makes sense for strings |
| Name vs ID | Two-phase based on attribute name | Different patterns for different use cases |
| Tracking | Extend AttributeDiff with flag | Minimal changes, clear separation of concerns |
| Logging | Summary always + verbose optional | Visibility without noise |
| Error Handling | Fail fast with detailed messages | Clear user feedback, easy troubleshooting |
| Performance | Pre-compile patterns, lazy normalization | Meets ≤10% overhead target |
| Testing | Unit + E2E + Live | Comprehensive coverage following Principle III |

**All research complete. Ready for Phase 1: Data Model & Contracts.**
