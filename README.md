# Terraform Plan Analyzer

A Python tool to analyze Terraform plan JSON files and categorize resource changes. Supports both text and beautiful HTML report output with intelligent HCL value resolution.

## Quick Start

```bash
# Generate HTML report with HCL resolution (recommended)
python analyze_plan.py plan.json --config ignore_config.json --html

# Specify custom Terraform directory for HCL resolution
python analyze_plan.py plan.json --tf-dir ../terraform --html

# Text output to console
python analyze_plan.py plan.json

# Verbose text output
python analyze_plan.py plan.json -v

# Custom HTML output path
python analyze_plan.py plan.json --html my_report.html
```

## Key Features

### 🔍 HCL Value Resolution (NEW!)
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

## How HCL Resolution Works

When a Terraform plan shows a field as "known after apply", the analyzer:

1. **Parses your .tf files** in the specified directory (defaults to plan file location)
2. **Extracts resource definitions** and their configured attribute values
3. **Resolves variables** from:
   - .tfvars files (highest priority)
   - Environment variables (TF_VAR_*)
   - variables.tf defaults
4. **Substitutes resolved values** for "known after apply" fields
5. **Diffs against current state** to show what will actually change
6. **Displays with visual cues** to distinguish HCL-resolved vs truly unknown values

### Example

**Before (without HCL resolution):**
```
app_settings: (known after apply)  ⚠️
```

**After (with HCL resolution):**
```
app_settings: {
  "APPINSIGHTS_INSTRUMENTATIONKEY": "${azurerm_application_insights.main.instrumentation_key}",
  "WEBSITE_RUN_FROM_PACKAGE": "1",
  "LOCATION": "eastus2"
}  ⚙️
```

The ⚙️ emoji indicates these values come from HCL configuration and shows both literal values (like `"1"`) and unresolved variable references (like `${...}`).

## Output Formats

## Example

```bash
# Generate HTML report with HCL resolution
python analyze_plan.py ../gsp-infrastructure-tf/2_deployApp/tfplan-test-2.json --config ignore_config.example.json --html

# Specify custom Terraform directory
python analyze_plan.py plan.json --tf-dir ../my-terraform-code --html

# Text analysis with ignore config
python analyze_plan.py ../gsp-infrastructure-tf/2_deployApp/tfplan-test-2.json --config ignore_config.example.json

# Verbose text output
python analyze_plan.py tfplan.json -v
```

## Resource Categories

The script categorizes resources into:
- **Created**: New resources being added
- **Imported**: Resources being imported into state
- **Updated - Config Changes**: Resources with actual configuration changes
- **Updated - Tag-Only**: Resources with only tag changes
- **Deleted**: Resources being removed

## Features

- **HCL Value Resolution**: Resolves "known after apply" values from Terraform source files
- **Variable Substitution**: Resolves variables from .tfvars and variables.tf
- **HTML Report Generation**: Beautiful, interactive HTML reports with diff highlighting
- **Character-Level Diffs**: Highlights subtle differences like "IotHubs" vs "iotHubs"
- **Smart Diff Highlighting**: Only highlights actual changes, shows identical values in context
- **Flexible Ignore Configuration**: Filter out noise from your analysis
- Filters out computed values (when not resolvable from HCL)
- Distinguishes between tag-only and configuration changes
- Provides detailed breakdown of which attributes changed
- Clean, readable output format (both HTML and text)
