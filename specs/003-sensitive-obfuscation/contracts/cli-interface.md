# CLI Interface Contract: Obfuscate Subcommand

**Date**: 2026-01-14  
**Purpose**: Define command-line interface for the `obfuscate` subcommand

## Overview

The `obfuscate` subcommand replaces sensitive values in Terraform plan JSON files with deterministic hashes, enabling safe sharing while preserving drift detection capabilities.

## Base Command

```bash
python analyze_plan.py obfuscate <plan_file> [options]
```

## Subcommand: `obfuscate`

### Syntax

```bash
python analyze_plan.py obfuscate <plan_file> [--output OUTPUT] [--salt-file SALT] [--force] [--show-stats]
```

### Arguments

**Positional**:
- `plan_file` (required): Path to Terraform plan JSON file to obfuscate

**Options**:
- `--output`, `-o` (optional): Output file path for obfuscated plan
  - Default: `<input_file_stem>-obfuscated.json`
  - Example: `plan.json` → `plan-obfuscated.json`

- `--salt-file`, `-s` (optional): Path to existing encrypted salt file for reuse
  - If not provided: Generate new salt and save to `<output>.salt`
  - If provided: Load salt from file for deterministic hashing
  - Enables consistent hashing across multiple files

- `--force`, `-f` (optional): Overwrite existing output file without prompting
  - Default: Exit with error if output file exists
  - Prevents accidental data loss

- `--show-stats` (optional): Display obfuscation statistics after completion
  - Shows: resources processed, values obfuscated, execution time
  - Default: Minimal output (just file paths)

### Examples

**Basic Usage** (generate new salt):
```bash
# Obfuscate with auto-generated salt
python analyze_plan.py obfuscate plan.json

# Output:
# ✅ Obfuscated plan saved to: plan-obfuscated.json
# 🔐 Salt saved to: plan-obfuscated.json.salt
```

**Custom Output Path**:
```bash
# Specify output location
python analyze_plan.py obfuscate prod-plan.json --output sanitized/prod.json

# Output:
# ✅ Obfuscated plan saved to: sanitized/prod.json
# 🔐 Salt saved to: sanitized/prod.json.salt
```

**Reuse Salt** (for drift detection):
```bash
# Obfuscate first file (generates salt)
python analyze_plan.py obfuscate dev-plan.json --output dev-obf.json

# Obfuscate second file with same salt
python analyze_plan.py obfuscate prod-plan.json --output prod-obf.json --salt-file dev-obf.json.salt

# Now identical sensitive values in both files have matching hashes
```

**Force Overwrite**:
```bash
# Overwrite existing output file
python analyze_plan.py obfuscate plan.json --force

# Without --force, would exit with error if plan-obfuscated.json exists
```

**Show Statistics**:
```bash
python analyze_plan.py obfuscate plan.json --show-stats

# Output:
# ✅ Obfuscated plan saved to: plan-obfuscated.json
# 🔐 Salt saved to: plan-obfuscated.json.salt
# 
# Statistics:
#   Resources processed: 127
#   Values obfuscated: 43
#   Execution time: 0.8s
```

### Exit Codes

- `0`: Success - file obfuscated and saved
- `1`: Input file not found
- `2`: Input file is invalid JSON
- `3`: Input file is not a valid Terraform plan structure
- `4`: Output file already exists (and --force not provided)
- `5`: Salt file not found (when --salt-file specified)
- `6`: Salt file is invalid or corrupted
- `7`: Malformed sensitive_values structure in plan
- `8`: I/O error (permission denied, disk full, etc.)

### Error Messages

**Input File Not Found**:
```bash
$ python analyze_plan.py obfuscate missing.json
Error: Input file not found: missing.json
```

**Invalid JSON**:
```bash
$ python analyze_plan.py obfuscate invalid.json
Error: Failed to parse JSON from invalid.json
  Line 42: Unexpected token '}'
```

**Not a Terraform Plan**:
```bash
$ python analyze_plan.py obfuscate data.json
Error: Input file is not a valid Terraform plan
  Missing required field: resource_changes
```

**Output File Exists**:
```bash
$ python analyze_plan.py obfuscate plan.json
Error: Output file already exists: plan-obfuscated.json
  Use --force to overwrite, or specify different output with --output
```

**Salt File Not Found**:
```bash
$ python analyze_plan.py obfuscate plan.json --salt-file missing.salt
Error: Salt file not found: missing.salt
```

**Malformed Sensitive Values**:
```bash
$ python analyze_plan.py obfuscate plan.json
Error: Malformed sensitive_values structure
  Resource: azurerm_key_vault.main
  Field: config.password
  Expected: boolean true/false, got: {"nested": "object"}
```

### Output Format

The obfuscated plan maintains the exact same JSON structure as the input, with only sensitive values replaced:

**Before** (original plan.json):
```json
{
  "resource_changes": [
    {
      "address": "azurerm_key_vault_secret.db_password",
      "change": {
        "after": {
          "name": "db-password",
          "value": "SuperSecret123!",
          "vault_id": "/subscriptions/abc/..."
        },
        "after_sensitive": {
          "name": false,
          "value": true,
          "vault_id": false
        }
      }
    }
  ]
}
```

**After** (plan-obfuscated.json):
```json
{
  "resource_changes": [
    {
      "address": "azurerm_key_vault_secret.db_password",
      "change": {
        "after": {
          "name": "db-password",
          "value": "obf_a1b2c3d4e5f6789...",
          "vault_id": "/subscriptions/abc/..."
        },
        "after_sensitive": {
          "name": false,
          "value": true,
          "vault_id": false
        }
      }
    }
  ]
}
```

### Salt File Format

Salt files are binary and not human-readable:

```bash
$ file plan-obfuscated.json.salt
plan-obfuscated.json.salt: data

$ ls -lh plan-obfuscated.json.salt
-rw-r--r-- 1 user group 96 Jan 14 10:30 plan-obfuscated.json.salt
```

**Do not**:
- Edit salt files manually
- Share salt files with untrusted parties (they enable hash reversal testing)
- Commit salt files to version control (unless encrypted at rest)

### Help Output

```bash
$ python analyze_plan.py obfuscate --help
usage: analyze_plan.py obfuscate [-h] [--output OUTPUT] [--salt-file SALT] 
                                  [--force] [--show-stats]
                                  plan_file

Obfuscate sensitive values in Terraform plan JSON files

positional arguments:
  plan_file             Path to Terraform plan JSON file

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output file path (default: <input>-obfuscated.json)
  --salt-file SALT, -s SALT
                        Existing salt file for deterministic hashing
  --force, -f           Overwrite existing output file
  --show-stats          Display obfuscation statistics

Examples:
  # Basic obfuscation
  python analyze_plan.py obfuscate plan.json
  
  # Reuse salt for drift detection
  python analyze_plan.py obfuscate dev.json -o dev-obf.json
  python analyze_plan.py obfuscate prod.json -o prod-obf.json -s dev-obf.json.salt
  
  # Force overwrite
  python analyze_plan.py obfuscate plan.json --force
```

## Integration with Existing Subcommands

The `obfuscate` subcommand follows the same pattern as `report` and `compare`:

```bash
# Existing subcommands
python analyze_plan.py report plan.json --html
python analyze_plan.py compare dev.json prod.json --html

# New subcommand
python analyze_plan.py obfuscate plan.json --output obf.json
```

### Argument Parser Structure

```python
# In main() function
subparsers = parser.add_subparsers(dest='subcommand', help='Available subcommands')

# Existing subcommands
report_parser = subparsers.add_parser('report', ...)
compare_parser = subparsers.add_parser('compare', ...)

# NEW: Obfuscate subcommand
obfuscate_parser = subparsers.add_parser(
    'obfuscate',
    help='Obfuscate sensitive values in Terraform plan'
)
obfuscate_parser.add_argument('plan_file', help='Path to plan JSON file')
obfuscate_parser.add_argument('--output', '-o', help='Output file path')
obfuscate_parser.add_argument('--salt-file', '-s', help='Existing salt file')
obfuscate_parser.add_argument('--force', '-f', action='store_true')
obfuscate_parser.add_argument('--show-stats', action='store_true')
```

## Workflow Examples

### Scenario 1: Share Single Plan Safely

```bash
# Developer has plan with secrets
terraform plan -out=tfplan
terraform show -json tfplan > plan.json

# Obfuscate before sharing
python analyze_plan.py obfuscate plan.json

# Share plan-obfuscated.json safely (no secrets exposed)
# Keep plan-obfuscated.json.salt private
```

### Scenario 2: Drift Detection Across Environments

```bash
# Generate plans for each environment
terraform plan -out=dev.tfplan
terraform plan -out=prod.tfplan
terraform show -json dev.tfplan > dev.json
terraform show -json prod.tfplan > prod.json

# Obfuscate both with same salt
python analyze_plan.py obfuscate dev.json -o dev-obf.json
python analyze_plan.py obfuscate prod.json -o prod-obf.json -s dev-obf.json.salt

# Compare obfuscated plans
python analyze_plan.py compare dev-obf.json prod-obf.json --html

# Identical sensitive values show as matching hashes
# Actual drift shows as different hashes
```

### Scenario 3: CI/CD Pipeline Integration

```bash
#!/bin/bash
# In CI/CD pipeline

# Generate plan
terraform plan -out=tfplan -var-file=prod.tfvars
terraform show -json tfplan > plan.json

# Obfuscate for artifact storage
python analyze_plan.py obfuscate plan.json --force

# Upload obfuscated plan as artifact (safe for logs/storage)
upload_artifact plan-obfuscated.json

# Keep salt file secret (don't upload or store in public artifacts)
```

## Backward Compatibility

**No Impact**: This is a new subcommand and does not affect existing `report` or `compare` functionality.

## Future Extensions

Potential enhancements maintaining backward compatibility:
- `--salt-format` flag to choose encryption method
- `--hash-algorithm` flag to select hashing algorithm (SHA-256, SHA-512, BLAKE2)
- `--obf-prefix` flag to customize hash prefix (default: "obf_")
- Support for custom sensitive field detection (beyond Terraform's sensitive_values)
