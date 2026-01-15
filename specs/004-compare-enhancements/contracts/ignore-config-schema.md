# Ignore Configuration Schema

**Feature**: 004-compare-enhancements  
**Date**: 2026-01-14

## Overview

This document defines the JSON schema for ignore configuration files used with the `compare` subcommand's `--config` flag. This schema is shared with the `report` subcommand for consistency.

---

## Schema Definition

```json
{
  "global_ignores": {
    "<attribute_name>": "<reason_string>"
  },
  "resource_ignores": {
    "<resource_type>": {
      "<attribute_name>": "<reason_string>"
    }
  }
}
```

### Root Object

**Type**: Object  
**Required**: At least one of `global_ignores` or `resource_ignores`  
**Optional**: Both can be present

---

## global_ignores

**Purpose**: Define attributes to ignore across ALL resource types.

**Type**: Object (Dictionary)  
**Key**: Attribute name (string) - supports top-level and nested attributes with dot notation  
**Value**: Reason string (string) - human-readable explanation for why the attribute is ignored  

**Examples**:

```json
{
  "global_ignores": {
    "tags": "Tags are managed separately and don't affect resource functionality",
    "description": "Descriptions vary by environment for documentation purposes",
    "identity.user_assigned_identity_ids": "Identity IDs are environment-specific"
  }
}
```

**Behavior**:
- Applied to every resource in the comparison
- Removes specified attributes from ALL env_configs before difference detection
- Nested attributes use dot notation (e.g., `identity.type`, `settings.config.enabled`)

---

## resource_ignores

**Purpose**: Define attributes to ignore for SPECIFIC resource types only.

**Type**: Object (Dictionary)  
**Key**: Resource type (string) - Terraform resource type (e.g., `azurerm_storage_account`, `aws_instance`)  
**Value**: Object mapping attribute names to reason strings

**Examples**:

```json
{
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion causes inconsequential changes",
      "description": "Description is conditionally set based on environment"
    },
    "azurerm_storage_account": {
      "network_rules.bypass": "Bypass rules differ by environment design"
    }
  }
}
```

**Behavior**:
- Applied only to resources matching the specified type
- Combines with global_ignores (both applied)
- More specific than global ignores
- Nested attributes supported with dot notation

---

## Attribute Name Syntax

### Top-Level Attributes

**Format**: Simple string matching top-level JSON key  
**Examples**: `tags`, `location`, `sku`, `enabled`

**Matching**:
```json
// Resource config
{
  "location": "eastus",
  "tags": { "env": "dev" }
}

// Ignore config
{
  "global_ignores": {
    "tags": "reason"
  }
}

// Result: "tags" removed, "location" remains
```

### Nested Attributes (Dot Notation)

**Format**: Dot-separated path to nested key  
**Examples**: `identity.type`, `settings.config.enabled`, `network_rules.bypass`

**Matching**:
```json
// Resource config
{
  "identity": {
    "type": "SystemAssigned",
    "principal_id": "abc123"
  }
}

// Ignore config
{
  "global_ignores": {
    "identity.type": "reason"
  }
}

// Result: "identity.type" removed from nested object
// Note: If removing nested key makes parent empty, parent is also removed
```

**Limitation**: Currently supports removal at any nesting level, but UI shows only top-level attribute changes (nested content displayed as blocks).

---

## Complete Example

```json
{
  "global_ignores": {
    "tags": "Tags are managed separately and don't affect resource functionality",
    "created_at": "Timestamp varies and is not actionable",
    "identity.user_assigned_identity_ids": "Identity IDs are environment-specific"
  },
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion causes inconsequential changes (empty map to null, casing differences)",
      "description": "Description is conditionally set based on environment"
    },
    "azurerm_monitor_activity_log_alert": {
      "action": "Dynamic block conversion causes inconsequential changes"
    },
    "azurerm_application_insights_workbook": {
      "display_name": "Display name is conditionally set based on environment"
    },
    "azurerm_storage_account": {
      "network_rules.bypass": "Bypass rules intentionally differ by environment",
      "enable_https_traffic_only": "HTTPS enforcement varies by environment policy"
    }
  }
}
```

---

## Validation Rules

### File Level
- ✅ File must be valid JSON
- ✅ Root object must contain at least one of: `global_ignores`, `resource_ignores`
- ⚠️ Unknown keys at root level: Ignored with warning

### global_ignores
- ✅ Must be an object (dictionary)
- ✅ Keys must be non-empty strings
- ✅ Values must be strings
- ⚠️ Empty value string: Allowed but discouraged (reason helps documentation)

### resource_ignores
- ✅ Must be an object (dictionary)
- ✅ Outer keys (resource types) must be non-empty strings
- ✅ Inner values must be objects mapping attribute names (strings) to reasons (strings)
- ⚠️ Resource type not found in plans: Silently ignored (no error)
- ⚠️ Attribute not found in resource: Silently ignored (no error)

**Rationale for Silent Failures**:
- Ignore configs may be shared across multiple comparisons
- Some resources/attributes may not exist in all environments
- Typos in attribute names should not break the comparison
- Users can verify effectiveness via "N attributes ignored" indicators

---

## Alternative Schema (Legacy Support)

**Note**: The `report` subcommand also supports list-based schemas for backward compatibility. The `compare` subcommand only supports the dict-based schema shown above for consistency and clarity.

### Legacy Format (NOT supported in compare)
```json
{
  "global_ignores": ["tags", "description"],
  "resource_ignores": {
    "azurerm_storage_account": ["network_rules", "identity"]
  }
}
```

**Reason for Exclusion**: Dict-based format with reasons provides better documentation and auditability.

---

## Usage with compare Subcommand

### Basic Usage
```bash
python analyze_plan.py compare dev.json prod.json --config ignore_config.json --html
```

### Creating an Ignore Config

1. **Run comparison without config first**:
   ```bash
   python analyze_plan.py compare dev.json prod.json --html comparison.html
   ```

2. **Review HTML report** and identify noisy attributes (tags, descriptions, etc.)

3. **Create ignore config**:
   ```json
   {
     "global_ignores": {
       "tags": "Managed separately",
       "description": "Environment-specific"
     }
   }
   ```

4. **Rerun with config**:
   ```bash
   python analyze_plan.py compare dev.json prod.json --config ignore_config.json --html filtered.html
   ```

5. **Verify in HTML report**:
   - Resources should show "N attributes ignored" indicator
   - Filtered attributes should not appear in attribute diff tables
   - Summary should show ignore statistics

---

## Error Handling

### File Not Found
```
Error: Ignore config file not found: ignore_config.json
```
**Exit Code**: 1

### Malformed JSON
```
Error: Failed to parse ignore config file: Expecting property name enclosed in double quotes: line 3 column 1 (char 15)
```
**Exit Code**: 2

### Invalid Schema (Missing Required Keys)
```
Warning: Ignore config is empty or missing 'global_ignores' and 'resource_ignores' keys. No filtering will be applied.
```
**Exit Code**: 0 (continues without filtering)

### Type Errors
```
Warning: 'global_ignores' should be a dict (found list). Skipping global ignores.
```
**Exit Code**: 0 (continues with partial filtering)

---

## Testing

Test cases must validate:

✅ **Valid Schemas**:
- Global ignores only
- Resource ignores only
- Both global and resource ignores
- Nested attribute dot notation
- Empty reasons (allowed but warned)

✅ **Invalid Schemas**:
- Missing both required keys
- global_ignores as list (warning)
- resource_ignores with list values (warning)
- Malformed JSON (exit code 2)
- File not found (exit code 1)

✅ **Edge Cases**:
- Typo in attribute name (silently ignored)
- Resource type not in plan (silently ignored)
- Nested attribute where parent doesn't exist (silently ignored)
- All attributes of a resource ignored (resource marked identical)

---

## Future Enhancements (Out of Scope)

Potential schema extensions:
- Wildcard patterns: `"identity.*": "All identity fields"`
- Conditional ignores: Only ignore if value matches pattern
- Value-based ignores: Ignore attribute only if value equals X
- Regex support: `"tags\\..*": "All tags"`

**Rationale for Deferral**: Current exact-match approach is simple, predictable, and covers 90% of use cases.
