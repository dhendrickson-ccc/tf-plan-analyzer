# Quickstart Guide: Normalization-Based Difference Filtering

**Feature**: 007-normalization-diff-filtering  
**Date**: 2025-01-15  
**For**: DevOps Engineers, Cloud Infrastructure Engineers

## Overview

Normalization-based difference filtering reduces noise in multi-environment comparisons by treating functionally equivalent values (like `-t-` vs `-p-` in resource names, or different subscription IDs) as identical. This guide shows how to use normalization patterns to focus on actual configuration drift.

---

## Quick Start

### 1. Create Normalization Config

Create `examples/normalizations.json`:

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
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f-]{36}/",
      "replacement": "/subscriptions/SUBSCRIPTION_ID/",
      "description": "Normalize Azure subscription IDs"
    }
  ]
}
```

### 2. Reference in Ignore Config

Update your `ignore_config.json`:

```json
{
  "global_ignores": {
    "tags": "Tags managed separately"
  },
  "normalization_config_path": "examples/normalizations.json"
}
```

### 3. Run Comparison

```bash
tf-plan-analyzer compare test-plan.json prod-plan.json \\
  --config ignore_config.json \\
  --html comparison.html
```

### 4. Check Results

Open `comparison.html` and look for:
- **Badge**: "5 ignored (2 config, 3 normalized)"
- **Tooltip**: Hover over badge to see which attributes were normalized
- **Summary**: Console shows normalization statistics

---

## Use Cases

### Use Case 1: Environment Name Normalization

**Problem**: Resource names differ only by environment suffix

**Before**:
```
storage-account-t-eastus (test)
storage-account-p-eastus (prod)
→ Shows as different in comparison
```

**Solution**: Add name pattern

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst|p|prod|prd|d|dev|s|stage|stg)-",
      "replacement": "-ENV-"
    }
  ]
}
```

**After**:
```
Both normalize to: storage-account-ENV-eastus
→ Ignored in comparison report
```

---

### Use Case 2: Subscription ID Normalization

**Problem**: Resource IDs differ only by subscription GUID

**Before**:
```
/subscriptions/abc-123-def-456/resourceGroups/rg-test/...  (test)
/subscriptions/xyz-789-ghi-012/resourceGroups/rg-prod/... (prod)
→ Shows as different
```

**Solution**: Add resource ID pattern

```json
{
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/subscriptions/SUBSCRIPTION_ID"
    }
  ]
}
```

**After**:
```
Both normalize to: /subscriptions/SUBSCRIPTION_ID/resourceGroups/...
→ Ignored in comparison report
```

---

### Use Case 3: Combined Ignore + Normalization

**Problem**: Need to ignore some fields AND normalize environment differences

**Solution**: Use both features together

```json
{
  "global_ignores": {
    "tags": "Tags managed separately",
    "description": "Environment-specific descriptions"
  },
  "normalization_config_path": "examples/normalizations.json"
}
```

**Result**:
- Config ignores: 2 attributes (tags, description)
- Normalization ignores: 3 attributes (name, resource_id, location)
- Badge shows: "5 ignored (2 config, 3 normalized)"

---

## CLI Usage

### Basic Comparison with Normalization

```bash
tf-plan-analyzer compare test.json prod.json \\
  --config ignore_config.json \\
  --html comparison.html
```

### Verbose Logging (See Normalization Details)

```bash
tf-plan-analyzer compare test.json prod.json \\
  --config ignore_config.json \\
  --verbose-normalization
```

**Output**:
```
🔄 Applying normalization patterns...
  ✓ name_patterns: 4 patterns loaded
  ✓ resource_id_patterns: 2 patterns loaded

📝 Normalization details:
  Resource: azurerm_storage_account.main
    Attribute: name
      test: storage-account-t-eastus → storage-account-ENV-eastus
      prod: storage-account-p-eastus → storage-account-ENV-eastus
      Pattern: -(t|test|tst|p|prod|prd)- → -ENV-
      ✓ Normalized difference ignored
```

### Text Output with Normalization

```bash
tf-plan-analyzer compare test.json prod.json \\
  --config ignore_config.json
```

**Summary Output**:
```
Comparing 2 environments: test, prod
✅ Comparison complete

📊 Summary:
   - Resources: 217 total
   - With differences: 45
   - Attributes ignored (config): 23
   - Attributes ignored (normalization): 18
   - Total ignored: 41
```

---

## Configuration Examples

### Minimal Config (Environment Markers Only)

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|p)-",
      "replacement": "-ENV-"
    }
  ]
}
```

### Standard Config (Environments + Regions)

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst)-",
      "replacement": "-ENV-",
      "description": "Test environment"
    },
    {
      "pattern": "-(p|prod|prd)-",
      "replacement": "-ENV-",
      "description": "Production environment"
    },
    {
      "pattern": "eastus|centralus|westus",
      "replacement": "REGION",
      "description": "Azure regions"
    }
  ]
}
```

### Advanced Config (Full Azure Pattern Set)

```json
{
  "name_patterns": [
    {
      "pattern": "-(t|test|tst|testing)-",
      "replacement": "-ENV-",
      "description": "Test environments"
    },
    {
      "pattern": "-(p|prod|prd|production)-",
      "replacement": "-ENV-",
      "description": "Production environments"
    },
    {
      "pattern": "-(d|dev|development)-",
      "replacement": "-ENV-",
      "description": "Development environments"
    },
    {
      "pattern": "-(s|stage|stg|staging)-",
      "replacement": "-ENV-",
      "description": "Staging environments"
    },
    {
      "pattern": "eastus|centralus|westus|northeurope|westeurope",
      "replacement": "REGION",
      "description": "Common Azure regions"
    }
  ],
  "resource_id_patterns": [
    {
      "pattern": "/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/subscriptions/SUBSCRIPTION_ID",
      "description": "Azure subscription GUIDs"
    },
    {
      "pattern": "/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
      "replacement": "/tenants/TENANT_ID",
      "description": "Azure tenant GUIDs"
    },
    {
      "pattern": "/resourceGroups/rg-(t|test|p|prod|d|dev|s|stage)-",
      "replacement": "/resourceGroups/rg-ENV-",
      "description": "Resource group environment prefixes"
    }
  ]
}
```

---

## HTML Report Features

### Badge Indication

Resources with normalized differences show a combined badge:

```
✓ 5 attributes ignored (2 config, 3 normalized)
```

### Tooltip Details

Hover over badge to see breakdown:

```
Config:
  - tags
  - description

Normalized:
  - name
  - resource_id
  - location
```

### Summary Statistics

HTML report header shows:
```
📊 Comparison Summary
Resources: 217 total, 45 with differences
Ignored: 41 attributes (23 config, 18 normalized)
```

---

## Troubleshooting

### Issue: Normalization Not Applied

**Symptom**: Differences still showing despite normalization config

**Checklist**:
1. **Check path**: Is `normalization_config_path` correct in ignore_config.json?
   ```bash
   cat ignore_config.json | grep normalization_config_path
   ```

2. **Check file exists**: Does normalizations.json exist?
   ```bash
   ls -la examples/normalizations.json
   ```

3. **Check patterns**: Are regex patterns correct?
   ```bash
   python -c "import re; re.compile(r'your-pattern-here')"
   ```

4. **Check verbose output**: Run with `--verbose-normalization` to see what's happening
   ```bash
   tf-plan-analyzer compare test.json prod.json --config ignore_config.json --verbose-normalization
   ```

---

### Issue: Invalid Regex Pattern Error

**Error**:
```
Error: Invalid regex pattern at name_patterns[2]: -(t|test
Regex Error: unterminated character set at position 7
```

**Solution**: Fix regex syntax
```json
// Before (invalid)
{"pattern": "-(t|test"}

// After (valid)
{"pattern": "-(t|test)-"}
```

**Test Pattern**:
```bash
python -c "import re; re.compile(r'-(t|test)-')"
# No output = valid pattern
```

---

### Issue: File Not Found

**Error**:
```
Error: Normalization config file not found: examples/normalizations.json
Hint: Check path in ignore_config.json 'normalization_config_path' field
```

**Solutions**:
1. **Check relative path**: Path is relative to ignore_config.json location
2. **Use absolute path**: Provide full path to avoid ambiguity
   ```json
   {
     "normalization_config_path": "/full/path/to/normalizations.json"
   }
   ```
3. **Verify file exists**:
   ```bash
   ls -la examples/normalizations.json
   ```

---

### Issue: Patterns Not Matching

**Symptom**: Patterns load successfully but don't normalize values

**Debug Steps**:
1. **Check value type**: Normalization only works on string values
   - Numbers, booleans, null not normalized
   - Complex objects only normalized for ID-like attributes

2. **Check pattern specificity**: Pattern might be too specific
   ```bash
   # Test pattern against actual value
   python
   >>> import re
   >>> pattern = re.compile(r'-(t|test|tst)-')
   >>> value = "storage-account-TEST-eastus"  # Won't match (uppercase)
   >>> pattern.search(value)
   None
   ```

3. **Make pattern case-insensitive** (if needed):
   ```json
   {
     "pattern": "(?i)-(t|test|tst)-",
     "replacement": "-ENV-"
   }
   ```

---

### Issue: Performance Degradation

**Symptom**: Comparison much slower with normalization

**Checklist**:
1. **Check pattern count**: Limit to <50 total patterns
2. **Optimize patterns**: Use specific patterns, avoid greedy `.*`
3. **Profile**: Run with timing to identify slow patterns
4. **Simplify**: Combine similar patterns with alternation `(a|b|c)`

**Target**: Normalization should add <10% overhead

---

## Best Practices

### 1. Start Simple, Add Gradually

```
Phase 1: Add environment markers only
Phase 2: Add region normalization
Phase 3: Add subscription/tenant IDs
Phase 4: Add resource-specific patterns
```

### 2. Document Patterns

Always include `description` field:
```json
{
  "pattern": "-(t|p)-",
  "replacement": "-ENV-",
  "description": "Normalize test/prod environment markers - added 2025-01-15"
}
```

### 3. Test Patterns Before Adding

```bash
# Test regex syntax
python -c "import re; re.compile(r'your-pattern')"

# Test pattern matching
python
>>> import re
>>> re.compile(r'-(t|p)-').sub('-ENV-', 'storage-t-eastus')
'storage-ENV-eastus'
```

### 4. Use Version Control

Track normalization config changes:
```bash
git add examples/normalizations.json
git commit -m "Add subscription ID normalization pattern"
```

### 5. Review Normalized Differences

Periodically run with `--verbose-normalization` to verify patterns working correctly:
```bash
tf-plan-analyzer compare test.json prod.json \\
  --config ignore_config.json \\
  --verbose-normalization > normalization-report.txt
```

---

## Integration Workflow

### 1. Initial Assessment (No Normalization)

```bash
tf-plan-analyzer compare test.json prod.json --html baseline.html
```

Review `baseline.html` to identify noise patterns.

### 2. Create Normalization Config

Based on noise patterns, create `normalizations.json`:
```json
{
  "name_patterns": [
    {"pattern": "-(t|p)-", "replacement": "-ENV-"}
  ]
}
```

### 3. Add to Ignore Config

Update `ignore_config.json`:
```json
{
  "global_ignores": {"tags": "Managed separately"},
  "normalization_config_path": "examples/normalizations.json"
}
```

### 4. Rerun with Normalization

```bash
tf-plan-analyzer compare test.json prod.json \\
  --config ignore_config.json \\
  --html filtered.html
```

### 5. Compare Reports

- Open both `baseline.html` and `filtered.html`
- Verify noise reduction (fewer differences shown)
- Confirm badge shows normalization counts
- Check that real differences still visible

### 6. Iterate and Refine

Add more patterns as needed, test, commit.

---

## Example: Complete Workflow

```bash
# Step 1: Initial comparison (no filtering)
tf-plan-analyzer compare test-plan.json prod-plan.json --html baseline.html
# Observe: 45 resources with differences

# Step 2: Create normalization config
cat > examples/normalizations.json <<EOF
{
  "name_patterns": [
    {"pattern": "-(t|test)-", "replacement": "-ENV-"},
    {"pattern": "-(p|prod)-", "replacement": "-ENV-"}
  ],
  "resource_id_patterns": [
    {"pattern": "/subscriptions/[0-9a-f-]{36}/", "replacement": "/subscriptions/SUBSCRIPTION_ID/"}
  ]
}
EOF

# Step 3: Update ignore config
cat > ignore_config.json <<EOF
{
  "global_ignores": {
    "tags": "Managed separately"
  },
  "normalization_config_path": "examples/normalizations.json"
}
EOF

# Step 4: Rerun with normalization
tf-plan-analyzer compare test-plan.json prod-plan.json \\
  --config ignore_config.json \\
  --html filtered.html
# Observe: 12 resources with differences (33 filtered by normalization)

# Step 5: Verify with verbose mode
tf-plan-analyzer compare test-plan.json prod-plan.json \\
  --config ignore_config.json \\
  --verbose-normalization
# Check: Console shows which attributes were normalized
```

---

## Summary

| Feature | Command Flag | Output |
|---------|-------------|--------|
| Basic normalization | `--config ignore_config.json` | Badge shows combined counts |
| Verbose details | `--verbose-normalization` | Console shows before/after values |
| HTML report | `--html report.html` | Badge + tooltip with breakdown |
| Text summary | (default) | Console stats with normalization counts |

**Next Steps**:
1. Create your `normalizations.json` with patterns for your environment
2. Test with a sample comparison
3. Review HTML report to verify noise reduction
4. Add more patterns as needed
5. Share config across team for consistency

For more details, see:
- [Normalization Config Schema](contracts/normalization-config-schema.md)
- [Data Model](data-model.md)
- [Research](research.md)
