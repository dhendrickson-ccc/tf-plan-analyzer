# Quickstart Guide: Compare Subcommand Enhancements

**Feature**: Compare environments with ignore file support and attribute-level diff view  
**Date**: 2026-01-14

## What's New

The `compare` subcommand now supports:
- **Ignore Configuration**: Filter out known acceptable differences (tags, descriptions, etc.)
- **Attribute-Level Diff View**: See only changed attributes instead of full JSON configurations

## Installation

No new dependencies required - uses Python 3.9+ and stdlib only.

```bash
cd /path/to/tf-plan-analyzer
# Existing installation works as-is
```

## Quick Examples

### Before: Noisy comparison with 50+ differences

```bash
python analyze_plan.py compare dev.json prod.json --html
# HTML shows full JSON for each resource
# 50 resources with differences, mostly tags and descriptions
```

### After: Clean comparison with ignore config

```bash
# Create ignore_config.json
cat > ignore_config.json <<EOF
{
  "global_ignores": {
    "tags": "Tags managed separately",
    "description": "Environment-specific descriptions"
  }
}
EOF

# Run comparison with config
python analyze_plan.py compare dev.json prod.json --config ignore_config.json --html filtered.html
# HTML shows only 12 resources with actionable differences
# Attribute-level view shows only changed attributes
```

---

## Usage Scenarios

### Scenario 1: Filter Environment-Specific Tags

**Problem**: Dev and prod have different tags, causing noise in comparison.

**Solution**:
```json
{
  "global_ignores": {
    "tags": "Tags are managed separately and don't affect resource functionality"
  }
}
```

**Command**:
```bash
python analyze_plan.py compare dev.json staging.json prod.json \
  --config ignore_config.json \
  --html comparison.html
```

**Result**: Tags differences ignored, HTML shows only functional configuration drift.

---

### Scenario 2: Resource-Specific Ignores

**Problem**: Azure Monitor alerts have dynamic block conversion differences that are non-functional.

**Solution**:
```json
{
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion causes inconsequential changes",
      "description": "Description varies by environment"
    }
  }
}
```

**Command**:
```bash
python analyze_plan.py compare dev.json prod.json \
  --config ignore_config.json \
  --diff-only \
  --html
```

**Result**: Only shows resources with meaningful differences, filters out monitor alert noise.

---

### Scenario 3: Combine with Diff-Only for Clean Reports

**Problem**: 100 resources total, only 5 have meaningful differences after filtering.

**Solution**:
```bash
# Create comprehensive ignore config
cat > ignore_config.json <<EOF
{
  "global_ignores": {
    "tags": "Managed separately",
    "description": "Environment-specific",
    "created_at": "Timestamps not actionable"
  },
  "resource_ignores": {
    "azurerm_storage_account": {
      "network_rules.bypass": "Bypass rules differ by design"
    }
  }
}
EOF

# Compare with diff-only
python analyze_plan.py compare dev.json staging.json prod.json \
  --config ignore_config.json \
  --diff-only \
  --html actionable_diffs.html
```

**Result**: HTML report shows only 5 resources, each with only changed attributes displayed.

---

## Ignore Config Examples

### Minimal Config

```json
{
  "global_ignores": {
    "tags": "Tags managed separately"
  }
}
```

### Comprehensive Config

```json
{
  "global_ignores": {
    "tags": "Tags managed via separate tagging policy",
    "description": "Descriptions are environment-specific for documentation",
    "identity.user_assigned_identity_ids": "Identity IDs are environment-specific"
  },
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion causes empty map vs null differences",
      "description": "Alert descriptions vary by environment"
    },
    "azurerm_application_insights_workbook": {
      "display_name": "Display names include environment prefix"
    },
    "azurerm_storage_account": {
      "network_rules.bypass": "Network bypass rules intentionally differ",
      "enable_https_traffic_only": "HTTPS enforcement varies by security policy"
    }
  }
}
```

### Nested Attributes

```json
{
  "global_ignores": {
    "identity.type": "Identity type varies (SystemAssigned vs UserAssigned)",
    "settings.config.enabled": "Config enabled flag differs by environment"
  }
}
```

---

## Understanding Attribute-Level Diff View

### Old HTML Output (Full JSON)

```html
<div class="resource">
  <h3>azurerm_storage_account.main</h3>
  <table>
    <tr><th>dev</th><th>prod</th></tr>
    <tr>
      <td><pre>{"location": "eastus", "sku": "Standard_LRS", "tags": {...}, ...}</pre></td>
      <td><pre>{"location": "westus", "sku": "Standard_LRS", "tags": {...}, ...}</pre></td>
    </tr>
  </table>
</div>
```
**Problem**: Hard to spot the actual difference (location)

### New HTML Output (Attribute-Level)

```html
<div class="resource">
  <h3>azurerm_storage_account.main <span class="ignore-badge">1 attribute ignored</span></h3>
  <table>
    <tr><th>Attribute</th><th>dev</th><th>prod</th></tr>
    <tr>
      <td><strong>location</strong></td>
      <td>eastus</td>
      <td>westus</td>
    </tr>
  </table>
</div>
```
**Benefit**: Immediately see that only location differs, tags were filtered

---

## Reading HTML Reports

### Resource Header

```
azurerm_storage_account.main [2 attributes ignored]
```
- Resource address
- Ignore indicator shows how many attributes were filtered

### Attribute Diff Table

| Attribute | dev | staging | prod |
|-----------|-----|---------|------|
| location | eastus | centralus | westus |
| sku | Standard_LRS | Premium_LRS | Standard_GRS |

- Only changed attributes shown
- Side-by-side values for easy comparison
- Primitive values shown inline, complex objects shown as JSON blocks

### Special States

**No Differences**:
```
azurerm_resource.identical
No differences detected
```

**All Changes Ignored**:
```
azurerm_resource.filtered [3 attributes ignored]
No actionable differences (tags, description, identity ignored)
```

---

## Creating an Ignore Config

### Step 1: Run Initial Comparison

```bash
python analyze_plan.py compare dev.json prod.json --html initial.html
```

### Step 2: Review HTML Report

Open `initial.html` and identify noisy attributes:
- Tags appearing on many resources
- Descriptions varying by environment
- Timestamps, metadata fields
- Environment-specific networking rules

### Step 3: Create Config File

```bash
cat > ignore_config.json <<EOF
{
  "global_ignores": {
    "tags": "Tags managed separately",
    "description": "Environment-specific"
  },
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion"
    }
  }
}
EOF
```

### Step 4: Rerun with Config

```bash
python analyze_plan.py compare dev.json prod.json --config ignore_config.json --html filtered.html
```

### Step 5: Verify

- Open `filtered.html`
- Check "Ignore Statistics" section in summary
- Verify resources show "N attributes ignored" indicators
- Confirm actionable differences stand out

---

## Troubleshooting

### Config File Not Found

**Error**: `Error: Ignore config file not found: ignore_config.json`

**Solution**: Check file path is correct, use absolute path if needed
```bash
python analyze_plan.py compare dev.json prod.json --config /full/path/to/ignore_config.json --html
```

### Malformed JSON

**Error**: `Error: Failed to parse ignore config file: ...`

**Solution**: Validate JSON syntax
```bash
python3 -m json.tool ignore_config.json
# Should output formatted JSON if valid
```

### Attributes Not Being Ignored

**Problem**: Config specifies `tags` but tags still appear in diff

**Possible Causes**:
1. **Typo in attribute name**: Check exact spelling (case-sensitive)
2. **Nested attribute**: Use dot notation (e.g., `identity.type` not `identity`)
3. **Wrong resource type**: Check resource type matches exactly

**Solution**: Add debug output
```bash
# Check ignore statistics in text output
python analyze_plan.py compare dev.json prod.json --config ignore_config.json
# Look for "Total Attributes Ignored" count
```

### All Resources Filtered Out

**Message**: `No actionable differences found (45 attributes filtered by ignore rules)`

**Meaning**: All differences were covered by ignore rules

**Action**: This is success! Environments are identical after filtering. If unexpected, review ignore config to ensure rules aren't too broad.

---

## Command Reference

### Basic Comparison

```bash
# Text output
python analyze_plan.py compare env1.json env2.json

# HTML output
python analyze_plan.py compare env1.json env2.json --html

# Custom HTML path
python analyze_plan.py compare env1.json env2.json --html custom_report.html
```

### With Ignore Config

```bash
# Filter with ignore config
python analyze_plan.py compare env1.json env2.json --config ignore_config.json

# Filter + HTML
python analyze_plan.py compare env1.json env2.json --config ignore_config.json --html

# Filter + diff-only
python analyze_plan.py compare env1.json env2.json --config ignore_config.json --diff-only --html
```

### With Custom Environment Names

```bash
python analyze_plan.py compare dev.json prod.json \
  --env-names "Development,Production" \
  --config ignore_config.json \
  --html
```

### Multiple Environments

```bash
python analyze_plan.py compare dev.json qa.json staging.json preprod.json prod.json \
  --env-names "Dev,QA,Staging,PreProd,Prod" \
  --config ignore_config.json \
  --diff-only \
  --html 5_env_comparison.html
```

---

## Best Practices

### 1. Start Broad, Then Refine

```json
{
  "global_ignores": {
    "tags": "First pass: filter all tags"
  }
}
```

Review results, then add resource-specific rules as needed.

### 2. Document Reasons

```json
{
  "global_ignores": {
    "tags": "Tags managed via separate tagging policy, not infrastructure drift"
  }
}
```

Helps team understand why attributes are ignored.

### 3. Use Version Control

Store `ignore_config.json` in Git:
```bash
git add ignore_config.json
git commit -m "Add ignore config for multi-env comparisons"
```

Share config across team for consistent filtering.

### 4. Use Diff-Only for Large Comparisons

```bash
# 500 resources, 50 with differences, 40 filtered
python analyze_plan.py compare dev.json prod.json \
  --config ignore_config.json \
  --diff-only \
  --html
# Result: HTML shows only 10 resources with actionable differences
```

Dramatically reduces report size and cognitive load.

### 5. Combine with CI/CD

```yaml
# .github/workflows/terraform-compare.yml
- name: Compare Terraform plans
  run: |
    terraform plan -out=dev.tfplan
    terraform show -json dev.tfplan > dev.json
    
    python analyze_plan.py compare dev.json prod.json \
      --config .terraform/ignore_config.json \
      --diff-only \
      --html comparison.html
    
    # Fail if actionable differences found
    grep "Resources with Differences: 0" comparison.html || exit 1
```

---

## Next Steps

- **Learn More**: See [cli-interface.md](contracts/cli-interface.md) for complete CLI documentation
- **Schema Reference**: See [ignore-config-schema.md](contracts/ignore-config-schema.md) for detailed schema
- **Examples**: Check `test_data/ignore_config.json` for real-world ignore config

## Questions?

Common scenarios:
- **Q**: Can I ignore nested attributes?  
  **A**: Yes, use dot notation: `"identity.type": "reason"`

- **Q**: What if I want to ignore a field only for specific resources?  
  **A**: Use `resource_ignores` instead of `global_ignores`

- **Q**: Does this change existing compare behavior?  
  **A**: No, without `--config` flag, behavior is identical (but HTML shows attribute-level view)

- **Q**: Can I see what was ignored?  
  **A**: Yes, check "Ignore Statistics" in text output or "N attributes ignored" in HTML

- **Q**: Will exit code change if all differences are ignored?  
  **A**: No, exit code 0 (success) even when all changes filtered
