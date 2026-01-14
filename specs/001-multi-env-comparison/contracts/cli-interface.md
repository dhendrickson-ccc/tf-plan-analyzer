# CLI Interface Contract

**Feature**: Multi-Environment Terraform Plan Comparison  
**Date**: 2026-01-13

## Overview

This document defines the command-line interface contract for the Terraform Plan Analyzer with multi-environment comparison support. The tool uses a subcommand-based architecture (like AWS CLI, git, kubectl).

## Base Command

```bash
python analyze_plan.py <subcommand> [arguments] [options]
```

## Subcommands

### `report` - Single Plan Analysis

Analyzes a single Terraform plan file and generates before/after diff report (existing behavior).

**Syntax**:
```bash
python analyze_plan.py report <plan_file> [options]
```

**Arguments**:
- `plan_file` (required): Path to Terraform plan JSON file

**Options**:
- `--html [output_file]`: Generate HTML report (optional output path)
- `--config <file>`: Path to ignore configuration JSON file
- `--tf-dir <directory>`: Terraform source directory for HCL resolution
- `-v, --verbose`: Verbose output with before/after values
- `--ignore-azure-casing`: Ignore Azure resource name casing differences
- `--show-sensitive`: Show sensitive values in output (masked by default)

**Examples**:
```bash
# Text output to console
python analyze_plan.py report plan.json

# HTML report with HCL resolution
python analyze_plan.py report plan.json --html --tf-dir ./terraform

# Verbose text with custom ignore config
python analyze_plan.py report plan.json -v --config ignore_config.json
```

**Exit Codes**:
- `0`: Success
- `1`: Plan file not found or invalid JSON
- `2`: Invalid arguments

---

### `compare` - Multi-Environment Comparison

Compares "before" state across 2 or more environment plan files with side-by-side columnar report.

**Syntax**:
```bash
python analyze_plan.py compare <plan_file_1> <plan_file_2> [plan_file_3...] [options]
```

**Arguments**:
- `plan_files` (required, 2+): Paths to Terraform plan JSON files (one per environment)

**Options**:
- `--html [output_file]`: Generate HTML report (optional output path, default: comparison_report.html)
- `--env-names <name1,name2,...>`: Comma-separated environment labels (default: derived from filenames)
- `--tfvars-files <file1,file2,...>`: Comma-separated tfvars files (same order as plan files)
- `--tf-dir <directory>`: Terraform source directory for HCL resolution (used with --tfvars-files)
- `--config <file>`: Path to ignore configuration JSON file
- `--diff-only`: Show only resources with differences (hide identical resources)
- `--show-sensitive`: Show sensitive values in output (masked by default)
- `--ignore-azure-casing`: Ignore Azure resource name casing differences
- `-v, --verbose`: Verbose output

**Examples**:
```bash
# Basic comparison with auto-detected environment names
python analyze_plan.py compare dev.json staging.json prod.json --html

# Custom environment labels
python analyze_plan.py compare plan1.json plan2.json plan3.json \
  --env-names "Development,Staging,Production" \
  --html

# With HCL resolution using environment-specific tfvars
python analyze_plan.py compare dev.json staging.json prod.json \
  --tf-dir ./terraform \
  --tfvars-files dev.tfvars,staging.tfvars,prod.tfvars \
  --html

# Show only differences with custom config
python analyze_plan.py compare dev.json prod.json \
  --diff-only \
  --config ignore_config.json \
  --html comparison.html
```

**Argument Matching**:
- Plan files and environment names: matched by position (1st plan → 1st name)
- Plan files and tfvars files: matched by position (1st plan → 1st tfvars)
- Number of env-names (if provided) must equal number of plan files
- Number of tfvars-files (if provided) must equal number of plan files

**Exit Codes**:
- `0`: Success
- `1`: Plan file not found, invalid JSON, or parse error
- `2`: Invalid arguments (wrong file count, mismatched counts, etc.)
- `3`: Less than 2 plan files provided

**Error Messages**:
```bash
# Example: Only 1 file provided
Error: compare subcommand requires at least 2 plan files.
Provided: 1 file(s)
For single-plan analysis, use: python analyze_plan.py report <plan_file>

# Example: Mismatched env-names count
Error: Number of environment names (2) does not match number of plan files (3)
Provided: --env-names "Dev,Prod"
Plan files: dev.json staging.json prod.json

# Example: Mismatched tfvars count
Error: Number of tfvars files (2) does not match number of plan files (3)
```

---

## General Behavior

### Help & Usage

```bash
# Show main help
python analyze_plan.py --help
python analyze_plan.py -h

# Show subcommand-specific help
python analyze_plan.py report --help
python analyze_plan.py compare --help
```

### No Subcommand

```bash
# Running without subcommand shows usage
$ python analyze_plan.py
usage: analyze_plan.py [-h] {report,compare} ...

Terraform Plan Analyzer

positional arguments:
  {report,compare}
    report          Analyze single Terraform plan (before/after diff)
    compare         Compare multiple environments (before states only)

optional arguments:
  -h, --help        show this help message and exit
```

### Environment Name Derivation

When `--env-names` is not provided, environment labels are derived from plan filenames:

| Filename | Derived Label |
|----------|---------------|
| `dev-plan.json` | `dev-plan` |
| `staging.json` | `staging` |
| `/path/to/prod.json` | `prod` |
| `plan-1.json` | `plan-1` |

Rules:
1. Strip directory path
2. Remove `.json` extension
3. Use remaining string as label

### HTML Output Paths

**report subcommand**:
- `--html` (no path): `<plan_name>_report.html` (e.g., `plan_report.html`)
- `--html <path>`: Use specified path

**compare subcommand**:
- `--html` (no path): `comparison_report.html`
- `--html <path>`: Use specified path

### Configuration File Format

Ignore configuration uses existing JSON format (unchanged):

```json
{
  "ignore_fields": ["id", "etag"],
  "resource_specific_ignores": {
    "azurerm_app_service": ["outbound_ip_addresses"]
  }
}
```

Applied consistently across all environments in `compare` mode.

## Backward Compatibility

**Breaking Changes**: None

**Migration Path**:
```bash
# Old usage (before this feature)
python analyze_plan.py plan.json --html

# New equivalent (still works via report subcommand)
python analyze_plan.py report plan.json --html
```

**Deprecation**: 
- Direct plan file argument (without subcommand) should be deprecated in future major version
- For now, shows deprecation warning but still works:
  ```
  Warning: Direct plan file argument is deprecated. Please use 'report' subcommand:
    python analyze_plan.py report plan.json --html
  ```

## Future Extensions

Potential future subcommands maintaining this architecture:
- `validate` - Validate plan files for correctness
- `diff` - Raw diff between two specific plans
- `stats` - Generate statistics across multiple plans

This subcommand structure provides natural extension points without breaking existing functionality.
