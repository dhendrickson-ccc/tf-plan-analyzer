# Normalization Configuration Schema

**Feature**: 007-normalization-diff-filtering  
**Date**: 2025-01-15  
**Status**: Complete

## Overview

This document defines the JSON schema for normalization configuration files (`normalizations.json`) used to filter environment-specific differences. Normalization patterns are referenced from `ignore_config.json` via the `normalization_config_path` field.

---

## Schema Definition

```json
{
  "name_patterns": [
    {
      "pattern": "<regex_pattern>",
      "replacement": "<replacement_string>",
      "description": "<optional_human_readable_description>"
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "<regex_pattern>",
      "replacement": "<replacement_string>",
      "description": "<optional_human_readable_description>"
    }
  ]
}
```

### Root Object

**Type**: Object  
**Required**: At least one of `name_patterns` or `resource_id_patterns`  
**Optional**: Both arrays can be present, one can be empty

---

### name_patterns

**Type**: Array of Pattern Objects  
**Purpose**: Normalize attribute names and values (environment suffixes, region names, etc.)  
**Applied To**: All string attribute values  
**Execution**: Patterns applied in array order with first-match-wins strategy

**Pattern Object Fields**:
- `pattern` (string, required): Valid Python regex pattern to match
- `replacement` (string, required): Replacement string (can include backreferences like `\1`, `\2`)
- `description` (string, optional): Human-readable explanation of what pattern does

**Example**:
```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst|testing)-",
      "replacement": "-ENV-",
      "description": "Normalize test environment markers to generic ENV"
    },
    {
      "pattern": "-(p|prod|prd|production)-",
      "replacement": "-ENV-",
      "description": "Normalize production environment markers to generic ENV"
    },
    {
      "pattern": "eastus|centralus|westus",
      "replacement": "REGION",
      "description": "Normalize Azure region names to generic REGION"
    }
  ]
}
```

**Validation Rules**:
- ✅ Must be an array (can be empty: `[]`)
- ✅ Each element must be an object with required fields `pattern` and `replacement`
- ✅ `pattern` must be a valid Python regex (compilable via `re.compile()`)
- ✅ `replacement` must be a string (can be empty: `""`)
- ✅ `description` is optional (if absent, pattern/replacement used for logging)
- ❌ Invalid regex patterns cause config load to fail with error location

---

### resource_id_patterns

**Type**: Array of Pattern Objects  
**Purpose**: Normalize resource IDs, subscription IDs, tenant IDs, GUIDs  
**Applied To**: Attributes with names like `id`, `resource_id`, `parent_id`, or ending in `_id`  
**Execution**: Patterns applied in array order AFTER name_patterns (two-phase normalization)

**Pattern Object Fields**: Same as name_patterns

**Example**:
```json
{
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/subscriptions/SUBSCRIPTION_ID",
      "description": "Normalize Azure subscription GUIDs to placeholder"
    },
    {
      "pattern": "/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/tenants/TENANT_ID",
      "description": "Normalize Azure tenant GUIDs to placeholder"
    },
    {
      "pattern": "/resourceGroups/rg-(t|test|p|prod|d|dev|s|stage)-",
      "replacement": "/resourceGroups/rg-ENV-",
      "description": "Normalize resource group environment prefixes"
    }
  ]
}
```

**Validation Rules**: Same as name_patterns

---

## Complete Example

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst)-",
      "replacement": "-ENV-",
      "description": "Normalize test environment markers"
    },
    {
      "pattern": "-(p|prod|prd)-",
      "replacement": "-ENV-",
      "description": "Normalize production environment markers"
    },
    {
      "pattern": "-(d|dev)-",
      "replacement": "-ENV-",
      "description": "Normalize dev environment markers"
    },
    {
      "pattern": "-(s|stage|stg|staging)-",
      "replacement": "-ENV-",
      "description": "Normalize staging environment markers"
    },
    {
      "pattern": "eastus|centralus|westus|westus2",
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
      "pattern": "/providers/[^/]+/",
      "replacement": "/providers/PROVIDER/",
      "description": "Normalize provider namespaces"
    }
  ]
}
```

---

## Validation Rules

### File Level
- ✅ File must be valid JSON
- ✅ Root object must contain at least one of: `name_patterns`, `resource_id_patterns`
- ⚠️ Unknown keys at root level: Ignored with warning
- ✅ Empty arrays are valid (no patterns to apply)

### Pattern Arrays
- ✅ Must be arrays (not objects or strings)
- ✅ Can be empty arrays (`[]`)
- ✅ Each element must be a pattern object

### Pattern Objects
- ✅ Must have `pattern` field (non-empty string)
- ✅ Must have `replacement` field (string, can be empty)
- ✅ `description` is optional
- ✅ Pattern must compile as valid Python regex
- ❌ Invalid patterns fail config load immediately

---

## Integration with Ignore Config

The normalization config is referenced from `ignore_config.json` via the `normalization_config_path` field:

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

**Path Resolution**:
- Absolute paths: Used as-is
- Relative paths: Resolved relative to ignore_config.json location
- Path must point to valid, readable JSON file

**Loading Sequence**:
1. Load ignore_config.json
2. If `normalization_config_path` present and non-empty:
   - Resolve path (absolute or relative)
   - Load normalization config from resolved path
   - Validate schema
   - Pre-compile all regex patterns
3. If path absent or field not present: Skip normalization (backward compatible)

---

## Error Handling

### File Not Found
```
Error: Normalization config file not found: examples/normalizations.json
Hint: Check path in ignore_config.json 'normalization_config_path' field
```
**Exit Code**: 1

### Malformed JSON
```
Error: Failed to parse normalization config file: examples/normalizations.json
JSON Error: Expecting property name enclosed in double quotes: line 5 column 3 (char 89)
```
**Exit Code**: 2

### Invalid Regex Pattern
```
Error: Invalid regex pattern at name_patterns[2]: -(t|test
Regex Error: unterminated character set at position 7
Hint: Check pattern syntax. Test with: python -c "import re; re.compile(r'-(t|test')"
```
**Exit Code**: 2

### Missing Required Field
```
Error: Invalid normalization config: missing required field 'pattern' at resource_id_patterns[1]
Expected structure: {'pattern': 'regex', 'replacement': 'text'}
```
**Exit Code**: 2

### Invalid Structure
```
Error: Invalid normalization config: 'name_patterns' must be an array, got string
```
**Exit Code**: 2

---

## Usage Patterns

### Basic Usage (Environment Normalization Only)
```json
{
  "name_patterns": [
    {
      "pattern": "-(t|p|d|s)-",
      "replacement": "-ENV-"
    }
  ]
}
```

### Full Usage (Environment + Subscription IDs)
```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst|p|prod|prd|d|dev|s|stage|stg)-",
      "replacement": "-ENV-"
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f-]{36}/",
      "replacement": "/subscriptions/SUBSCRIPTION_ID/"
    }
  ]
}
```

### Advanced Usage (With Backreferences)
```json
{
  "name_patterns": [
    {
      "pattern": "(storage|app|vm)-(t|p)-(\\w+)",
      "replacement": "\\1-ENV-\\3",
      "description": "Preserve resource type and suffix, normalize environment marker"
    }
  ]
}
```
Result: `storage-t-eastus` → `storage-ENV-eastus`

---

## Testing

Test cases must validate:

✅ **Valid Schemas**:
- name_patterns only
- resource_id_patterns only
- Both arrays present
- Empty arrays (valid but no-op)
- Patterns with backreferences
- Complex regex patterns

✅ **Invalid Schemas**:
- Missing both required keys
- name_patterns as string (not array)
- Missing `pattern` field
- Missing `replacement` field
- Invalid regex syntax
- Malformed JSON
- File not found

✅ **Edge Cases**:
- Pattern that doesn't match any values (silently no-op)
- Multiple patterns matching same string (first-match-wins)
- Replacement that introduces new differences (normalization doesn't match)
- Very long regex patterns (performance test)
- Patterns with special regex characters (proper escaping)

---

## Best Practices

1. **Order Matters**: Place specific patterns before general ones
   ```json
   [
     {"pattern": "-test-regional-", "replacement": "-ENV-"},
     {"pattern": "-(t|test)-", "replacement": "-ENV-"}
   ]
   ```

2. **Test Patterns**: Validate regex before adding to config
   ```bash
   python -c "import re; re.compile(r'your-pattern-here')"
   ```

3. **Document Patterns**: Always include `description` field for maintainability

4. **Use Anchors**: Prevent over-matching with `^` and `$` where appropriate
   ```json
   {"pattern": "^rg-(t|p)-", "replacement": "rg-ENV-"}
   ```

5. **Escape Special Characters**: Use raw strings in testing, escape in JSON
   ```json
   {"pattern": "\\.", "replacement": "-"}
   ```

6. **Performance**: Limit total patterns to <50 for optimal performance

---

## Migration from az-env-compare-config

If you have existing normalization patterns from `az-env-compare-config` repository:

1. **Extract patterns from normalizations.json**
2. **Convert to this schema format**:
   ```python
   # Old format (example)
   {"name_pattern": "-(t|p)-", "replacement": "-ENV-"}
   
   # New format
   {
     "pattern": "-(t|p)-",
     "replacement": "-ENV-",
     "description": "Normalize environment markers"
   }
   ```
3. **Test with sample comparison**
4. **Add to examples/normalizations.json**

---

**Schema definition complete.**
