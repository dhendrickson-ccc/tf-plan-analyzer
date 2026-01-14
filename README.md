# Terraform Plan Analyzer

A Python tool to analyze Terraform plan JSON files and identify resource changes. Supports both single-plan analysis and multi-environment comparison with HTML and text output formats.

## Table of Contents
- [Quick Start](#quick-start)
- [Single Plan Analysis](#single-plan-analysis)
- [Multi-Environment Comparison](#multi-environment-comparison)
- [Sensitive Data Obfuscation](#sensitive-data-obfuscation)
- [Key Features](#key-features)
- [Output Formats](#output-formats)
- [Ignore Configuration](#ignore-configuration)

## Quick Start

### Single Plan Analysis
```bash
# Generate HTML report
python analyze_plan.py report plan.json --html

# Text output with HCL resolution
python analyze_plan.py report plan.json --tf-dir ./terraform

# Verbose text output
python analyze_plan.py report plan.json -v
```

### Multi-Environment Comparison
```bash
# Compare multiple environments (text output)
python analyze_plan.py compare dev.json staging.json prod.json

# Generate HTML comparison report
python analyze_plan.py compare dev.json staging.json --html comparison.html

# Compare with custom environment names
python analyze_plan.py compare dev.json staging.json --env-names "Development,Staging"

# Show only resources with differences
python analyze_plan.py compare dev.json staging.json --diff-only

# Verbose text output
python analyze_plan.py compare dev.json staging.json -v
```

### Sensitive Data Obfuscation
```bash
# Basic obfuscation (sanitize for sharing)
python analyze_plan.py obfuscate plan.json

# Reuse salt for drift detection across environments
python analyze_plan.py obfuscate dev.json -o dev-obf.json
python analyze_plan.py obfuscate prod.json -o prod-obf.json -s dev-obf.json.salt

# Show obfuscation statistics
python analyze_plan.py obfuscate plan.json --show-stats
```

## Single Plan Analysis

The `report` subcommand analyzes a single Terraform plan file and categorizes resource changes.

### Usage
```bash
python analyze_plan.py report <plan_file> [options]
```

### Options
- `--html [OUTPUT]` - Generate HTML report (default: report.html)
- `--config FILE` - Path to ignore configuration JSON file
- `--tf-dir DIR` - Directory containing Terraform .tf files for HCL resolution
- `-v, --verbose` - Show detailed before/after values in text output

### Examples
```bash
# Generate HTML report with HCL resolution (recommended)
python analyze_plan.py report plan.json --config ignore_config.json --html

# Specify custom Terraform directory for HCL resolution
python analyze_plan.py report plan.json --tf-dir ../terraform --html

# Text analysis with ignore config
python analyze_plan.py report plan.json --config ignore_config.json

# Verbose text output
python analyze_plan.py report plan.json -v
```

## Multi-Environment Comparison

The `compare` subcommand compares resource configurations across multiple environments to identify drift and ensure parity.

### Usage
```bash
python analyze_plan.py compare <plan_file1> <plan_file2> [plan_file3 ...] [options]
```

### Options
- `--html [OUTPUT]` - Generate HTML comparison report (default: comparison_report.html)
- `--env-names NAMES` - Comma-separated environment names (e.g., "dev,staging,prod"). If not provided, names are derived from filenames
- `--diff-only` - Show only resources with differences (hide identical resources)
- `--config FILE` - Path to ignore configuration JSON file
- `--tf-dir DIR` - Directory containing Terraform .tf files for HCL resolution
- `--tfvars-files FILES` - Comma-separated list of .tfvars files (one per environment, in same order as plan files)
- `--show-sensitive` - Show actual sensitive values instead of masking them (not recommended for shared reports)
- `-v, --verbose` - Show detailed configurations for each resource in text output

### Examples

**Basic Comparison:**
```bash
# Compare two environments with auto-detected names
python analyze_plan.py compare dev-plan.json prod-plan.json

# Compare three environments with custom names
python analyze_plan.py compare dev.json staging.json prod.json \
  --env-names "Development,Staging,Production"
```

**HTML Reports:**
```bash
# Generate HTML comparison report
python analyze_plan.py compare dev.json staging.json prod.json --html

# Custom output path
python analyze_plan.py compare dev.json staging.json --html reports/comparison.html

# Show only differences
python analyze_plan.py compare dev.json staging.json prod.json --diff-only --html
```

**Advanced Features:**
```bash
# Compare with HCL resolution
python analyze_plan.py compare dev.json staging.json \
  --tf-dir ./terraform \
  --tfvars-files dev.tfvars,staging.tfvars \
  --html

# Compare with ignore configuration
python analyze_plan.py compare dev.json staging.json \
  --config ignore_config.json \
  --diff-only

# Verbose text output with sensitive values visible
python analyze_plan.py compare dev.json staging.json -v --show-sensitive
```

### Multi-Environment Comparison Features

- **Configuration Drift Detection**: Identifies resources with different configurations across environments
- **Character-Level Diff Highlighting**: HTML reports show precise character-by-character differences (e.g., "t2.micro" vs "t2.small" highlights only "micro"/"small")
- **Baseline Comparison**: First environment serves as baseline, others show diffs against it
- **Presence Tracking**: Shows which environments contain each resource
- **Sensitive Value Handling**: Automatically masks sensitive values with [SENSITIVE] markers
- **Side-by-Side Comparison**: HTML reports show configurations from all environments in parallel
- **Difference Highlighting**: Visual indicators for resources with differences vs identical configurations
- **Ignore Configuration**: Filter out expected differences (tags, timeouts, etc.)
- **Flexible Output**: Both HTML and text formats supported


## Sensitive Data Obfuscation

The `obfuscate` subcommand removes sensitive data from Terraform plan files using deterministic one-way hashing, allowing safe sharing while preserving the ability to detect drift across environments.

### Usage
```bash
python analyze_plan.py obfuscate <plan_file> [options]
```

### Options
- `--output, -o OUTPUT` - Output file path (default: `<input>-obfuscated.json`)
- `--salt-file, -s SALT` - Use existing salt file for deterministic hashing
- `--force, -f` - Overwrite existing output file
- `--show-stats` - Display obfuscation statistics

### How It Works

**Obfuscation Process:**
1. Identifies sensitive values marked by Terraform in `after_sensitive` and `before_sensitive` fields
2. Generates a cryptographic salt (or loads existing one)
3. Hashes each sensitive value using SHA-256 with salt inserted at variable positions
4. Replaces sensitive values with `obf_<hash>` format
5. Saves the salt file (encrypted with Fernet) alongside the output

**Key Properties:**
- **One-way hashing**: Original values cannot be recovered from hashes
- **Deterministic**: Same value + same salt = same hash (enables drift detection)
- **Salt randomization**: Different salts produce different hashes (prevents rainbow tables)
- **Position randomization**: Salt inserted at variable positions for extra entropy

### Examples

**Basic Obfuscation:**
```bash
# Obfuscate a plan for safe sharing
python analyze_plan.py obfuscate plan.json

# Output files:
#   plan-obfuscated.json       - Sanitized plan file
#   plan-obfuscated.json.salt  - Encrypted salt (keep secure!)

# Custom output path
python analyze_plan.py obfuscate plan.json --output sanitized/plan.json

# Overwrite existing file
python analyze_plan.py obfuscate plan.json --force
```

**Drift Detection Across Environments:**
```bash
# Step 1: Obfuscate dev environment (generates new salt)
python analyze_plan.py obfuscate dev.json -o dev-obf.json

# Step 2: Obfuscate prod using SAME salt (for comparison)
python analyze_plan.py obfuscate prod.json -o prod-obf.json -s dev-obf.json.salt

# Step 3: Compare obfuscated plans
python analyze_plan.py compare dev-obf.json prod-obf.json --html drift-report.html
```

### Security & Best Practices

- **Keep salt files secure** - Enable hash correlation if attacker has original data
- **Never commit salt files** to version control (add `*.salt` to `.gitignore`)
- Use `TF_ANALYZER_SALT_KEY` environment variable for CI/CD workflows
- Salt files are encrypted using Fernet symmetric encryption
- Processes 10MB files (10,000 resources) in under 0.5 seconds


## Key Features

### 🔒 Sensitive Data Obfuscation
- **Safe sharing**: Remove sensitive data from Terraform plans using cryptographic hashing
- **Drift detection**: Deterministic hashing enables comparison across environments
- **Encrypted salts**: Salt files encrypted with Fernet for secure storage
- **CI/CD ready**: Environment variable encryption for cross-machine workflows

### 🔍 HCL Value Resolution (NEW!)
- **Resolves "known after apply" values** from Terraform source files
### 🔍 HCL Value Resolution
- **Resolves "known after apply" values** from Terraform source files
- **Shows actual configured values** instead of just "(known after apply)"
- **Diffs HCL values against current state** to show real changes
- **Variable resolution** from variables.tf and .tfvars files
- **Visual indicators**:
  - ⚙️ = Value from HCL configuration (may contain unresolved variable references)
  - ⚠️ = Truly unknown (no HCL definition found, computed at apply time)
  - Yellow highlighting for both to indicate values aren't final yet

### 📊 HTML Report (--html)
- Beautiful, interactive web-based report
- Side-by-side diff view for changed values
- Character-level diff highlighting for subtle changes
- Collapsible resource sections
- Syntax highlighting for JSON diffs
- Only highlights actual differences (identical values shown in gray)
- Summary cards with resource counts
- Ignored changes section at bottom
- Mobile-responsive design

### 📝 Text Output (default)
- Console-friendly text format
- Categorized resource changes
- Verbose mode (-v) shows before/after values
- Suitable for piping and grep

### 🔒 Sensitive Value Handling
- Automatically masks sensitive values in multi-environment comparisons
- Use `--show-sensitive` to reveal actual values when needed
- Visual indicators for sensitive value differences

### 🎯 Smart Filtering
- Ignore configuration support to filter out noise
- `--diff-only` flag to show only resources with differences
- Resource-specific and global ignore rules

## Output Formats

### Single Plan Analysis
The `report` subcommand categorizes resources into:
- **Created**: New resources being added
- **Imported**: Resources being imported into state
- **Updated - Config Changes**: Resources with actual configuration changes
- **Updated - Tag-Only**: Resources with only tag changes
- **Deleted**: Resources being removed

### Multi-Environment Comparison
The `compare` subcommand provides:
- **Summary Statistics**: Total resources, differences, consistency metrics
- **Resource-by-Resource Comparison**: Side-by-side view of configurations
- **Presence Tracking**: Shows which environments contain each resource
- **Difference Detection**: Highlights configuration drift across environments

## Ignore Configuration

Create an `ignore_config.json` file to filter out expected differences:

```json
{
  "ignore_fields": {
    "*": ["tags", "timeouts"],
    "aws_instance": ["user_data"],
    "azurerm_resource_group": ["location"]
  }
}
```

- `"*"` applies to all resource types (global ignore rules)
- Specific resource types can have their own ignore rules
- Fields are ignored consistently across all environments in comparisons

Usage:
```bash
# Single plan analysis
python analyze_plan.py report plan.json --config ignore_config.json --html

# Multi-environment comparison
python analyze_plan.py compare dev.json staging.json --config ignore_config.json --html
```
