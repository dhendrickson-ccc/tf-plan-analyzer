# Quickstart Guide: Multi-Environment Comparison

**Feature**: Multi-Environment Terraform Plan Comparison  
**Date**: 2026-01-13

## Overview

This quickstart guide demonstrates how to use the multi-environment comparison feature to identify configuration drift across dev, staging, and production environments.

## Prerequisites

- Python 3.8+
- Terraform plan JSON files from 2+ environments
- (Optional) Terraform source code for HCL resolution

## Basic Usage

### 1. Compare Two Environments

The simplest use case: compare dev vs prod.

```bash
python analyze_plan.py compare dev-plan.json prod-plan.json --html
```

**Output**: `comparison_report.html` showing side-by-side configuration

**What you'll see**:
- Resources in columns: "dev-plan" | "prod-plan"
- Configuration differences highlighted in yellow
- Resources missing from one environment shown as "N/A"

---

### 2. Compare Three Environments with Custom Names

Add meaningful labels instead of using filenames.

```bash
python analyze_plan.py compare \
  dev-plan.json staging-plan.json prod-plan.json \
  --env-names "Development,Staging,Production" \
  --html
```

**Output**: Columns labeled "Development" | "Staging" | "Production"

---

### 3. Show Only Differences

For large infrastructures, filter out resources that are identical across environments.

```bash
python analyze_plan.py compare dev.json staging.json prod.json \
  --diff-only \
  --html
```

**Result**: Report only shows resources with configuration differences

---

### 4. HCL Resolution with Environment-Specific Variables

Resolve "known after apply" values using Terraform source code and environment-specific tfvars.

```bash
python analyze_plan.py compare \
  dev-plan.json staging-plan.json prod-plan.json \
  --tf-dir ./terraform \
  --tfvars-files dev.tfvars,staging.tfvars,prod.tfvars \
  --html
```

**What this does**:
- Loads Terraform source from `./terraform/`
- Applies `dev.tfvars` to resolve dev plan variables
- Applies `staging.tfvars` to resolve staging plan variables
- Applies `prod.tfvars` to resolve prod plan variables
- Shows actual configured values instead of "(known after apply)"

---

### 5. Using Ignore Configuration

Apply existing ignore configuration to suppress noise.

```bash
python analyze_plan.py compare dev.json prod.json \
  --config ignore_config.json \
  --html
```

**ignore_config.json**:
```json
{
  "ignore_fields": ["id", "etag", "default_hostname"],
  "resource_specific_ignores": {
    "azurerm_app_service": ["outbound_ip_addresses"]
  }
}
```

**Effect**: Ignored fields excluded from difference detection across all environments

---

## Common Workflows

### Workflow 1: Pre-Deployment Validation

Verify staging matches production before promoting code.

```bash
# Generate plans
cd terraform
terraform plan -out=staging.tfplan
terraform show -json staging.tfplan > staging-plan.json

# Compare with current prod plan
cd ..
python analyze_plan.py compare staging-plan.json prod-plan.json \
  --env-names "Staging (Proposed),Production (Current)" \
  --diff-only \
  --html validation.html

# Review validation.html for unexpected differences
open validation.html
```

---

### Workflow 2: Configuration Drift Detection

Identify where dev has diverged from production baseline.

```bash
python analyze_plan.py compare prod-plan.json dev-plan.json \
  --env-names "Production (Baseline),Development (Drift Check)" \
  --diff-only \
  --html drift-report.html
```

**Interpretation**:
- Highlighted differences = configuration drift
- "N/A" in dev column = resources need to be added to dev
- "N/A" in prod column = resources in dev shouldn't be there

---

### Workflow 3: Multi-Region Consistency Check

Ensure consistent configuration across regional deployments.

```bash
python analyze_plan.py compare \
  us-east-plan.json us-west-plan.json eu-west-plan.json \
  --env-names "US East,US West,EU West" \
  --diff-only \
  --html regions.html
```

---

## Reading the HTML Report

### Report Structure

```
┌─────────────────────────────────────┐
│  Summary Card                       │
│  - Environments: 3                  │
│  - Total Resources: 42              │
│  - With Differences: 8              │
│  - Consistent: 34                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Resource Comparison Table          │
├──────────┬──────┬─────────┬─────────┤
│ Resource │ Dev  │ Staging │ Prod    │
├──────────┼──────┼─────────┼─────────┤
│ aws_...  │ {...}│ {...}   │ {...}   │  ← Click to expand
└──────────┴──────┴─────────┴─────────┘
```

### Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| **Yellow highlight** | Configuration value differs from other environments |
| **Green text** | Value added (not present in reference environment) |
| **Red text** | Value removed (present in reference, not here) |
| **Gray text** | Identical across all environments |
| **"N/A"** | Resource doesn't exist in this environment |
| **⚙️ emoji** | Value resolved from HCL configuration |
| **⚠️ emoji** | Value truly unknown (no HCL definition) |
| **[SENSITIVE]** | Masked sensitive value (use --show-sensitive to reveal) |
| **[SENSITIVE] ⚠️** | Masked sensitive value that DIFFERS across environments |

---

## Tips & Best Practices

### 1. Meaningful Environment Names

```bash
# ❌ Not helpful
--env-names "env1,env2,env3"

# ✅ Descriptive
--env-names "Dev (us-east-1),Staging (us-west-2),Prod (eu-west-1)"
```

### 2. Order Matters

Provide files in logical progression for easier comparison:

```bash
# ✅ Good: dev → staging → prod
python analyze_plan.py compare dev.json staging.json prod.json

# ⚠️ Confusing: random order
python analyze_plan.py compare prod.json dev.json staging.json
```

### 3. Use --diff-only for Large Infrastructures

```bash
# For 200+ resources, filter to just differences
python analyze_plan.py compare dev.json prod.json --diff-only --html
```

### 4. Combine with Existing Tools

```bash
# Generate comparison, then open in browser
python analyze_plan.py compare *.json --html report.html && open report.html

# CI/CD integration: fail if differences found
python analyze_plan.py compare staging.json prod.json --diff-only --html
if [ $? -eq 0 ] && grep -q "With Differences: 0" report.html; then
  echo "✓ Environments are consistent"
else
  echo "✗ Configuration drift detected"
  exit 1
fi
```

---

## Troubleshooting

### Error: "compare subcommand requires at least 2 plan files"

**Problem**: Only provided 1 file

**Solution**: Use `report` subcommand for single-plan analysis
```bash
python analyze_plan.py report plan.json --html
```

### Error: "Number of environment names does not match"

**Problem**: Mismatch between --env-names count and plan file count

**Solution**: Ensure counts match
```bash
# 3 files = 3 names
python analyze_plan.py compare f1.json f2.json f3.json \
  --env-names "Name1,Name2,Name3"
```

### Error: "Plan file not found"

**Problem**: Path to plan file is incorrect

**Solution**: Use absolute paths or verify relative paths
```bash
python analyze_plan.py compare /full/path/dev.json /full/path/prod.json --html
```

### Wide Tables (Too Many Columns)

**Problem**: 5+ environments make table too wide

**Solution**: 
1. Compare subsets (e.g., dev+staging, then staging+prod)
2. Use browser zoom out
3. Collapse nested structures (default behavior)

---

## Next Steps

- **Automate in CI/CD**: Add comparison to deployment pipeline
- **Create Baselines**: Store comparison reports for trend analysis
- **Custom Ignore Configs**: Tune ignore_config.json to reduce noise
- **HCL Resolution**: Set up --tf-dir and --tfvars-files for accurate resolution

For single-plan analysis (before/after diff), see:
```bash
python analyze_plan.py report --help
```
