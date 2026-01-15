# CLI Interface Contract

**Feature**: 004-compare-enhancements  
**Date**: 2026-01-14

## Overview

This document defines the command-line interface contract for the enhanced `compare` subcommand with ignore file support and attribute-level diff view.

---

## Command Syntax

```bash
python analyze_plan.py compare <plan_files...> [options]
```

### Arguments

**`plan_files`** (positional, required, 2+)
- Type: File paths
- Description: Paths to Terraform plan JSON files (minimum 2 required)
- Example: `dev.json staging.json prod.json`
- Validation: Each file must exist and be valid JSON

### Options

**`--config <path>`** (optional) **[ENHANCED]**
- Type: File path
- Description: Path to ignore configuration JSON file
- Default: None (no filtering applied)
- Example: `--config ignore_config.json`
- Validation:
  - File must exist (exit code 1 if not found)
  - File must contain valid JSON (exit code 2 if malformed)
  - JSON must match ignore configuration schema (see ignore-config-schema.md)
- **New Behavior**: Previously stub for compare subcommand, now fully functional

**`--html [<path>]`** (optional, existing)
- Type: File path (optional)
- Description: Generate HTML comparison report
- Default: `comparison_report.html` if flag used without path
- Example: `--html custom_report.html`
- **Modified Behavior**: HTML now shows attribute-level diff instead of full JSON

**`--diff-only`** (optional, existing)
- Type: Flag
- Description: Show only resources with differences
- Default: False (show all resources)
- **Modified Behavior**: Works with ignore config - resources with all changes ignored are excluded

**`--env-names <names>`** (optional, existing)
- Type: Comma-separated string
- Description: Custom environment labels
- Example: `--env-names "Development,Staging,Production"`
- Validation: Count must match number of plan files
- Behavior: Unchanged

**`--show-sensitive`** (optional, existing)
- Type: Flag
- Description: Show actual sensitive values instead of masking
- Default: False (mask sensitive values)
- Behavior: Unchanged

**`--tf-dir <path>`** (optional, existing)
- Type: Directory path
- Description: Directory containing Terraform .tf files for HCL resolution
- Behavior: Unchanged

**`--tfvars-files <paths>`** (optional, existing)
- Type: Comma-separated file paths
- Description: Environment-specific tfvars files
- Behavior: Unchanged

---

## Exit Codes

| Code | Meaning | Trigger | User Action |
|------|---------|---------|-------------|
| 0 | Success | Comparison completed successfully | Review output/HTML report |
| 1 | File not found | Plan file or config file doesn't exist | Check file paths |
| 2 | Invalid JSON | Config file or plan file contains malformed JSON | Validate JSON syntax |
| 1 | Validation error | < 2 plan files, env-names count mismatch | Fix command arguments |

**Note**: Exit code 0 even when `--diff-only` results in zero differences after filtering.

---

## Usage Examples

### Basic Comparison (Unchanged)

```bash
# Compare two environments
python analyze_plan.py compare dev.json prod.json

# Compare three environments with HTML output
python analyze_plan.py compare dev.json staging.json prod.json --html
```

### With Ignore Configuration (New)

```bash
# Filter tags and descriptions
python analyze_plan.py compare dev.json staging.json --config ignore_config.json --html

# Combined with diff-only
python analyze_plan.py compare dev.json prod.json --config ignore_config.json --diff-only --html
```

### Custom Environment Names with Ignores (New)

```bash
python analyze_plan.py compare dev.json prod.json \
  --env-names "Development,Production" \
  --config ignore_config.json \
  --html deployment_comparison.html
```

---

## Output Formats

### Text Output (stdout)

**Unchanged Structure**:
```
Comparing 3 environments: dev, staging, prod

SUMMARY
─────────────────────────────
Total Environments:           3
Total Unique Resources:       45
Resources with Differences:   12
Resources Consistent:         33
```

**New Addition** (when --config used):
```
IGNORE STATISTICS
─────────────────────────────
Total Attributes Ignored:     28
Resources with Ignores:       10
All Changes Ignored:          2

Breakdown by Attribute:
  tags:                       22
  description:                6
```

### HTML Output

**New Structure**: Attribute-level diff tables

**Before** (existing):
```html
<div class="resource">
  <h3>azurerm_storage_account.main</h3>
  <table>
    <tr>
      <th>dev</th>
      <th>staging</th>
      <th>prod</th>
    </tr>
    <tr>
      <td><pre>{ "location": "eastus", "sku": "Standard_LRS", ... }</pre></td>
      <td><pre>{ "location": "centralus", "sku": "Standard_LRS", ... }</pre></td>
      <td><pre>{ "location": "westus", "sku": "Standard_LRS", ... }</pre></td>
    </tr>
  </table>
</div>
```

**After** (new - attribute-level):
```html
<div class="resource">
  <h3>azurerm_storage_account.main <span class="ignore-badge">2 attributes ignored</span></h3>
  <table class="attribute-diff-table">
    <thead>
      <tr>
        <th>Attribute</th>
        <th>dev</th>
        <th>staging</th>
        <th>prod</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>location</strong></td>
        <td>eastus</td>
        <td>centralus</td>
        <td>westus</td>
      </tr>
      <!-- Only changed attributes shown, not full JSON -->
    </tbody>
  </table>
</div>
```

**Ignore Indicator** (new):
- Badge/tooltip showing "N attributes ignored"
- Displayed on resources with `ignored_attributes` > 0
- Hover/click shows list of ignored attribute names

**Empty State** (new):
```html
<div class="resource">
  <h3>azurerm_resource.identical</h3>
  <p class="no-diff">No differences detected</p>
</div>
```

**All Changes Ignored State** (new):
```html
<div class="resource">
  <h3>azurerm_resource.filtered</h3>
  <p class="all-ignored">No actionable differences (3 attributes ignored: tags, description, identity)</p>
</div>
```

---

## Error Messages

### File Not Found
```
Error: File not found: ignore_config.json
```

### Invalid JSON
```
Error: Failed to parse ignore config file: Expecting property name enclosed in double quotes: line 3 column 1 (char 15)
```

### Validation Errors
```
Error: The 'compare' subcommand requires at least 2 plan files.
Tip: For single plan analysis, use the 'report' subcommand instead:
  python analyze_plan.py report dev.json
```

### Diff-Only with All Filtered
```
Comparing 2 environments: dev, prod

SUMMARY
─────────────────────────────
Total Environments:           2
Total Unique Resources:       10
Resources with Differences:   0 (5 filtered by ignore rules)
Resources Consistent:         10

No actionable differences found (15 attributes filtered by ignore rules)
```

---

## Backward Compatibility

### Unchanged Behavior

When `--config` flag is **not provided**:
- ✅ All existing functionality works identically
- ✅ HTML output shows attribute-level view (new) but with ALL attributes (since none ignored)
- ✅ Text output unchanged
- ✅ Exit codes unchanged

### Migration Path

Existing scripts can adopt new features incrementally:
1. **No changes needed**: Scripts without `--config` continue working
2. **Add ignore config**: Add `--config ignore_config.json` to filter noise
3. **Benefit from attribute view**: Automatically get cleaner HTML reports

---

## Testing Requirements

Per Constitution Principle V, end-to-end tests must cover:

✅ **Default Behavior**:
- Compare without --config flag (ensure unchanged)
- Compare with --html (verify attribute-level rendering works without ignores)

✅ **Common Use Cases**:
- Compare with --config (verify ignores applied)
- Compare with --config + --diff-only (verify filtered resources excluded)
- Compare with --config + --html (verify attribute-level diff with ignores)

✅ **Critical Edge Cases**:
- --config with nonexistent file (verify exit code 1)
- --config with malformed JSON (verify exit code 2)
- --config with all changes ignored (verify exit code 0, special message)
- --config + --diff-only with all resources filtered (verify empty report)

✅ **Option Combinations**:
- --config + --env-names
- --config + --show-sensitive
- --config + --tf-dir + --tfvars-files
