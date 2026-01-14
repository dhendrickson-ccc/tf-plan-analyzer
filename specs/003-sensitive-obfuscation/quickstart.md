# Quick Start: Sensitive Data Obfuscation

**Purpose**: Get started with obfuscating Terraform plan files in under 5 minutes

## Prerequisites

- Python 3.11+
- Terraform plan JSON file with sensitive values
- tf-plan-analyzer installed

## Installation

```bash
# Install dependencies
pip install cryptography>=41.0.0

# Verify installation
python analyze_plan.py obfuscate --help
```

## Basic Usage

### Step 1: Generate Terraform Plan

```bash
# Create Terraform plan
terraform plan -out=tfplan

# Convert to JSON
terraform show -json tfplan > plan.json
```

### Step 2: Obfuscate Sensitive Values

```bash
# Basic obfuscation (generates new salt)
python analyze_plan.py obfuscate plan.json

# Creates two files:
# - plan-obfuscated.json (safe to share)
# - plan-obfuscated.json.salt (keep private)
```

### Step 3: Verify Obfuscation

```bash
# Check that sensitive values are masked
grep -A 5 '"after_sensitive"' plan-obfuscated.json

# You should see values like "obf_a1b2c3..." instead of actual secrets
```

## Common Workflows

### Share Plan Safely

```bash
# Obfuscate your plan
python analyze_plan.py obfuscate terraform-plan.json

# Share the obfuscated file (safe - no secrets exposed)
cat terraform-plan-obfuscated.json | mail teammate@company.com

# Keep the salt file private (do not share)
```

### Drift Detection Across Environments

```bash
# Get plans from two environments
terraform show -json dev.tfplan > dev-plan.json
terraform show -json prod.tfplan > prod-plan.json

# Obfuscate both with the same salt
python analyze_plan.py obfuscate dev-plan.json -o dev-obf.json
python analyze_plan.py obfuscate prod-plan.json -o prod-obf.json -s dev-obf.json.salt

# Compare the obfuscated plans
python analyze_plan.py compare dev-obf.json prod-obf.json --html

# Open comparison.html - identical secrets show same hash, drift shows different hashes
```

### Force Overwrite Existing Output

```bash
# First run creates output
python analyze_plan.py obfuscate plan.json

# Second run with --force overwrites
python analyze_plan.py obfuscate plan.json --force
```

### View Statistics

```bash
# Show how many values were obfuscated
python analyze_plan.py obfuscate plan.json --show-stats

# Output shows:
# - Number of resources processed
# - Number of sensitive values obfuscated
# - Execution time
```

## File Outputs

### Obfuscated Plan File

**Input** (plan.json):
```json
{
  "resource_changes": [{
    "address": "aws_db_instance.main",
    "change": {
      "after": {
        "username": "admin",
        "password": "MySecretPassword123!"
      },
      "after_sensitive": {
        "username": false,
        "password": true
      }
    }
  }]
}
```

**Output** (plan-obfuscated.json):
```json
{
  "resource_changes": [{
    "address": "aws_db_instance.main",
    "change": {
      "after": {
        "username": "admin",
        "password": "obf_7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
      },
      "after_sensitive": {
        "username": false,
        "password": true
      }
    }
  }]
}
```

### Salt File

**Binary format** - not human-readable:
```bash
$ ls -lh plan-obfuscated.json.salt
-rw-r--r-- 1 user group 96 Jan 14 10:30 plan-obfuscated.json.salt
```

**Purpose**:
- Enables deterministic hashing (same salt = same output)
- Required for drift detection across multiple files
- Should be kept private (enables testing hash reversal)

## Command Reference

```bash
# Basic commands
python analyze_plan.py obfuscate <file>                  # Obfuscate with new salt
python analyze_plan.py obfuscate <file> -o <output>      # Custom output path
python analyze_plan.py obfuscate <file> -s <salt-file>   # Reuse existing salt
python analyze_plan.py obfuscate <file> --force          # Overwrite existing output
python analyze_plan.py obfuscate <file> --show-stats     # Display statistics

# Combinations
python analyze_plan.py obfuscate plan.json -o out.json -s existing.salt --force --show-stats
```

## Troubleshooting

### Error: Output file already exists

```bash
# Problem
$ python analyze_plan.py obfuscate plan.json
Error: Output file already exists: plan-obfuscated.json

# Solution 1: Use --force to overwrite
python analyze_plan.py obfuscate plan.json --force

# Solution 2: Specify different output
python analyze_plan.py obfuscate plan.json -o new-output.json
```

### Error: Salt file not found

```bash
# Problem
$ python analyze_plan.py obfuscate plan.json -s missing.salt
Error: Salt file not found: missing.salt

# Solution: Check file path is correct
ls -la *.salt
python analyze_plan.py obfuscate plan.json -s correct-path.salt
```

### Error: Malformed sensitive_values

```bash
# Problem
$ python analyze_plan.py obfuscate plan.json
Error: Malformed sensitive_values structure
  Resource: azurerm_key_vault.main
  Field: config
  Expected: boolean, got: object

# This indicates the Terraform plan has non-standard structure
# Solution: Verify plan was generated with terraform show -json
terraform show -json tfplan > plan.json
python analyze_plan.py obfuscate plan.json
```

## Best Practices

### Security

✅ **DO**:
- Keep salt files private (do not share or commit)
- Use same salt only for related comparisons (same release, same environment set)
- Store salt files separately from obfuscated plans
- Rotate salts periodically (new salt for each release cycle)

❌ **DON'T**:
- Share salt files publicly or in chat
- Commit salt files to version control (unless encrypted at rest)
- Use the same salt across unrelated projects
- Edit salt files manually

### Workflow Integration

✅ **Recommended**:
```bash
# In CI/CD pipeline
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
python analyze_plan.py obfuscate plan.json --force
# Upload plan-obfuscated.json as artifact (safe)
# Store salt separately in secret manager (if needed for comparison)
```

❌ **Not Recommended**:
```bash
# Don't upload unobfuscated plans
terraform show -json tfplan > plan.json
upload_artifact plan.json  # DANGER: Contains secrets!
```

## Next Steps

- See [CLI Interface Contract](contracts/cli-interface.md) for complete command reference
- See [Data Model](data-model.md) for technical details
- See [Implementation Plan](plan.md) for development roadmap

## FAQ

**Q: Can I reverse the obfuscation to get original values?**  
A: No. SHA-256 hashing is irreversible. Obfuscated values cannot be converted back to original secrets.

**Q: Will the same sensitive value always produce the same hash?**  
A: Only if you use the same salt file. Different salts produce different hashes for the same value.

**Q: What if I lose the salt file?**  
A: You cannot reproduce the same hashes. You'll need to generate a new salt and re-obfuscate all files for comparison.

**Q: Can I use this for compliance/audit?**  
A: Yes, obfuscated plans are safe for sharing with auditors. They can verify infrastructure changes without seeing actual secrets.

**Q: Does this work with all Terraform providers?**  
A: Yes, it uses Terraform's standard `sensitive_values` structure which is provider-agnostic.

**Q: What about values not marked sensitive by Terraform?**  
A: Only values marked in `after_sensitive` are obfuscated. If Terraform doesn't mark a value as sensitive, this tool won't obfuscate it.
