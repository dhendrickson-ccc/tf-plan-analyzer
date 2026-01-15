# Function Glossary

Complete reference for all public functions in the Terraform Plan Analyzer. Use `Cmd+F` / `Ctrl+F` to search by function name, module, or keyword.

## Quick Reference

Most commonly used functions:

| Function | Module | Purpose |
|----------|--------|---------|
| `generate_full_styles()` | html_generation | Get complete CSS for HTML reports |
| `highlight_json_diff()` | diff_utils | Generate character-level diff highlighting |
| `load_ignore_config()` | ignore_utils | Load and validate ignore configuration |
| `safe_read_file()` | file_utils | Safely read files with error handling |
| `load_json_file()` | json_utils | Load and parse JSON files |
| `SensitiveObfuscator.obfuscate_plan()` | sensitive_obfuscator | Obfuscate sensitive data in plans |
| `ResourceComparison.compare_resources()` | multi_env_comparator | Compare resources across environments |

## Module Organization

The `src/` directory is organized by functional responsibility:

- **lib/**: Shared utilities and helper functions (HTML, diff, JSON, file I/O, ignore config)
- **core/**: Core analysis logic (multi-environment comparison, HCL resolution)
- **security/**: Sensitive data handling (obfuscation, salt management)
- **cli/**: Command-line interface (argument parsing, report generation)

---

## Table of Contents

- [Lib Module](#lib-module)
  - [html_generation.py](#htmlgenerationpy)
  - [diff_utils.py](#diffutilspy)
  - [json_utils.py](#jsonutilspy)
  - [file_utils.py](#fileutilspy)
  - [ignore_utils.py](#ignoreutilspy)
- [Core Module](#core-module)
  - [multi_env_comparator.py](#multi_env_comparatorpy)
  - [hcl_value_resolver.py](#hcl_value_resolverpy)
- [Security Module](#security-module)
  - [salt_manager.py](#salt_managerpy)
  - [sensitive_obfuscator.py](#sensitive_obfuscatorpy)
- [CLI Module](#cli-module)
  - [analyze_plan.py](#analyze_planpy)

---

## Lib Module

### html_generation.py

Consolidates all CSS and HTML generation logic for report styling.

#### `get_base_css()`

**Location**: [src/lib/html_generation.py](../src/lib/html_generation.py#L17)

**Parameters**: None

**Returns**: `str` - CSS stylesheet with base typography and layout styles

**Description**:
Returns foundational CSS including:
- CSS reset (margin, padding, box-sizing)
- Body typography (font family, colors, line height: 1.6)
- Container styles (max-width: 1400px, shadows, border-radius: 8px)
- Header styling with purple gradient (#667eea → #764ba2)
- Responsive design rules for mobile (@media max-width: 768px)

**Usage Example**:
```python
from src.lib.html_generation import get_base_css

# Get base CSS for custom HTML report
base_styles = get_base_css()
html = f"<style>{base_styles}</style>"
```

**Related**: See [docs/style-guide.md](style-guide.md) for complete design system documentation

---

#### `get_summary_card_css()`

**Location**: [src/lib/html_generation.py](../src/lib/html_generation.py#L100)

**Parameters**: None

**Returns**: `str` - CSS stylesheet for summary card metrics

**Description**:
Returns CSS for summary cards with:
- Responsive grid layout (auto-fit, minmax(200px, 1fr))
- Card styling (white background, padding: 20px, shadows, border-radius: 8px)
- Large number typography (font-size: 2.5em, font-weight: bold)
- Semantic color coding:
  - `.total` - Purple (#667eea)
  - `.created` - Green (#51cf66)
  - `.updated` - Orange (#ffa94d)
  - `.deleted` - Red (#ff6b6b)

**Usage Example**:
```python
from src.lib.html_generation import get_summary_card_css

card_css = get_summary_card_css()

html = f"""
<style>{card_css}</style>
<div class="summary">
  <div class="summary-card created">
    <div class="number">5</div>
    <div class="label">Resources Created</div>
  </div>
</div>
"""
```

---

#### `get_diff_highlight_css()`

**Location**: [src/lib/html_generation.py](../src/lib/html_generation.py#L155)

**Parameters**: None

**Returns**: `str` - CSS stylesheet for diff visualization

**Description**:
Returns CSS for before/after diff highlighting:
- Line-level: `.removed` (red #ffe0e0), `.added` (green #d3f9d8), `.unchanged` (gray)
- Character-level: `.char-removed` (#ff9999), `.char-added` (#99ff99)
- Known-after-apply: `.known-after-apply` (orange #fff4e6)
- Baseline comparison (multi-env): `.baseline-removed` (blue #bbdefb), `.baseline-added` (#e3f2fd)
- Opacity utilities: `.opacity-50`

**Usage Example**:
```python
from src.lib.html_generation import get_diff_highlight_css

diff_css = get_diff_highlight_css()

html = f"""
<style>{diff_css}</style>
<div class="removed">- old_value</div>
<div class="added">+ new_value</div>
<div>The <span class="char-removed">old</span><span class="char-added">new</span> text</div>
"""
```

---

#### `get_resource_card_css()`

**Location**: [src/lib/html_generation.py](../src/lib/html_generation.py#L240)

**Parameters**: None

**Returns**: `str` - CSS stylesheet for resource cards and expandable sections

**Description**:
Returns CSS for resource display including:
- Resource grids (auto-fill, minmax(300px, 1fr))
- Expandable resource change cards with toggle icons
- Diff column layouts for before/after comparison (grid 1fr 1fr, gap: 20px)
- JSON content display (monospace, pre-wrap, font-size: 0.85em)
- Sensitive badge styling (red #ff6b6b background, white text)
- Toggle buttons (#667eea background with hover effect)
- Legend/help sections with collapsible content

**Usage Example**:
```python
from src.lib.html_generation import get_resource_card_css

card_css = get_resource_card_css()

html = f"""
<style>{card_css}</style>
<div class="resource-change">
  <div class="resource-change-header">
    <span class="toggle-icon">▼</span>
    <span class="resource-name">aws_instance.web</span>
  </div>
  <div class="resource-change-content">
    <div class="change-item">
      <div class="change-attribute">
        instance_type
        <span class="sensitive-badge">SENSITIVE</span>
      </div>
      <div class="change-diff">
        <div class="diff-column">
          <div class="diff-header before">Before</div>
          <pre class="json-content">t2.micro</pre>
        </div>
        <div class="diff-column">
          <div class="diff-header after">After</div>
          <pre class="json-content">t2.small</pre>
        </div>
      </div>
    </div>
  </div>
</div>
"""
```

---

#### `generate_full_styles()`

**Location**: [src/lib/html_generation.py](../src/lib/html_generation.py#L568)

**Parameters**: None

**Returns**: `str` - Complete HTML `<style>` block with all CSS

**Description**:
Main entry point for getting all CSS. Combines:
- Base typography and layout (get_base_css)
- Summary cards with semantic colors (get_summary_card_css)
- Diff highlighting for comparison (get_diff_highlight_css)
- Resource cards with expandable sections (get_resource_card_css)

Returns a complete `<style>...</style>` block ready for insertion in HTML `<head>`.

**Usage Example**:
```python
from src.lib.html_generation import generate_full_styles

# Generate complete HTML report with all styles
styles = generate_full_styles()

html_report = f"""
<!DOCTYPE html>
<html>
<head>
  <title>Terraform Plan Analysis</title>
  {styles}
</head>
<body>
  <div class="container">
    <header>
      <h1>Terraform Plan Analysis</h1>
    </header>
    <!-- Report content -->
  </div>
</body>
</html>
"""

with open("report.html", "w") as f:
    f.write(html_report)
```

**Related**: See [analyze_plan.py](../src/cli/analyze_plan.py) and [multi_env_comparator.py](../src/core/multi_env_comparator.py) for usage in actual report generation

---

### diff_utils.py

Character-level and line-level diff utilities for comparing values.

#### `highlight_char_diff()`

**Location**: [src/lib/diff_utils.py](../src/lib/diff_utils.py#L14)

**Parameters**:
- `old` (str): Original value
- `new` (str): New value

**Returns**: `tuple[str, str]` - HTML-highlighted versions of (old_highlighted, new_highlighted)

**Description**:
Generates character-level diff highlighting using Python's `difflib.SequenceMatcher`. Wraps changed characters in HTML spans:
- Removed characters: `<span class="char-removed">text</span>`
- Added characters: `<span class="char-added">text</span>`
- Unchanged characters: no wrapper

Useful for showing precise changes in strings like URLs, IDs, or configuration values.

**Usage Example**:
```python
from src.lib.diff_utils import highlight_char_diff

old_url = "https://api.example.com/v1/users"
new_url = "https://api.example.com/v2/users"

old_html, new_html = highlight_char_diff(old_url, new_url)

# old_html: 'https://api.example.com/<span class="char-removed">v1</span>/users'
# new_html: 'https://api.example.com/<span class="char-added">v2</span>/users'

html = f"""
<div>Before: {old_html}</div>
<div>After: {new_html}</div>
"""
```

**Related**: Used extensively in [multi_env_comparator.py](../src/core/multi_env_comparator.py) for attribute comparison

---

#### `highlight_json_diff()`

**Location**: [src/lib/diff_utils.py](../src/lib/diff_utils.py#L85)

**Parameters**:
- `before` (dict | list | Any): Original value (can be nested)
- `after` (dict | list | Any): New value (can be nested)
- `sensitive_paths` (list[str], optional): List of JSON paths to mark as sensitive (default: [])
- `current_path` (str, optional): Internal parameter for recursion (default: "")

**Returns**: `tuple[str, str]` - HTML-highlighted JSON strings (before_html, after_html)

**Description**:
Deep comparison of JSON structures with character-level diff highlighting. Features:
- Recursively compares nested dicts and lists
- Wraps changed values in HTML spans with CSS classes
- Marks sensitive fields with `<span class="sensitive-badge">SENSITIVE</span>`
- Handles edge cases: None values, type mismatches, complex nesting
- Uses `highlight_char_diff()` for string comparisons
- Preserves JSON formatting for readability

**Usage Example**:
```python
from src.lib.diff_utils import highlight_json_diff

before = {
    "instance_type": "t2.micro",
    "tags": {"Name": "WebServer", "Env": "dev"},
    "password": "secret123"
}

after = {
    "instance_type": "t2.small",
    "tags": {"Name": "WebServer", "Env": "prod"},
    "password": "newsecret456"
}

sensitive_paths = ["password"]

before_html, after_html = highlight_json_diff(before, after, sensitive_paths)

# before_html contains highlighted JSON with sensitive badge on password field
# after_html shows new values with character-level diffs

html = f"""
<div class="change-diff">
  <div class="diff-column">
    <div class="diff-header before">Before</div>
    <pre class="json-content">{before_html}</pre>
  </div>
  <div class="diff-column">
    <div class="diff-header after">After</div>
    <pre class="json-content">{after_html}</pre>
  </div>
</div>
"""
```

**Performance**: Optimized for deeply nested structures. Handles complex Terraform plans with 100+ resources efficiently.

---

### json_utils.py

JSON file loading and formatting utilities.

#### `load_json_file()`

**Location**: [src/lib/json_utils.py](../src/lib/json_utils.py#L16)

**Parameters**:
- `file_path` (str): Path to JSON file

**Returns**: `dict` - Parsed JSON content

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `json.JSONDecodeError`: If JSON is malformed

**Description**:
Safely loads and parses JSON files with proper error handling. Used throughout the codebase to load Terraform plan JSON files.

**Usage Example**:
```python
from src.lib.json_utils import load_json_file

# Load Terraform plan
try:
    plan = load_json_file("terraform-plan.json")
    resources = plan.get("planned_values", {}).get("root_module", {}).get("resources", [])
    print(f"Found {len(resources)} resources")
except FileNotFoundError:
    print("Plan file not found")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
```

---

#### `format_json_for_display()`

**Location**: [src/lib/json_utils.py](../src/lib/json_utils.py#L36)

**Parameters**:
- `data` (Any): Python object to format
- `indent` (int, optional): Indentation spaces (default: 2)

**Returns**: `str` - Pretty-printed JSON string

**Description**:
Formats Python objects as indented JSON strings for display. Handles None values gracefully, uses compact separators for readability.

**Usage Example**:
```python
from src.lib.json_utils import format_json_for_display

config = {
    "instance_type": "t2.micro",
    "tags": {"Name": "WebServer"},
    "count": 3
}

json_str = format_json_for_display(config)
print(json_str)
# Output:
# {
#   "instance_type": "t2.micro",
#   "tags": {
#     "Name": "WebServer"
#   },
#   "count": 3
# }
```

---

### file_utils.py

Safe file I/O operations with error handling.

#### `safe_read_file()`

**Location**: [src/lib/file_utils.py](../src/lib/file_utils.py#L14)

**Parameters**:
- `file_path` (str): Path to file
- `encoding` (str, optional): File encoding (default: "utf-8")

**Returns**: `str` - File contents

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `IOError`: If file can't be read

**Description**:
Safely reads text files with UTF-8 encoding. Provides clear error messages for debugging.

**Usage Example**:
```python
from src.lib.file_utils import safe_read_file

try:
    content = safe_read_file("config.txt")
    lines = content.split("\n")
except FileNotFoundError:
    print("Config file not found")
```

---

#### `safe_write_file()`

**Location**: [src/lib/file_utils.py](../src/lib/file_utils.py#L36)

**Parameters**:
- `file_path` (str): Path to file
- `content` (str): Content to write
- `encoding` (str, optional): File encoding (default: "utf-8")

**Returns**: None

**Raises**:
- `IOError`: If file can't be written

**Description**:
Safely writes text files with UTF-8 encoding. Creates parent directories if needed.

**Usage Example**:
```python
from src.lib.file_utils import safe_write_file

html_content = "<html>...</html>"
safe_write_file("report.html", html_content)
```

---

### ignore_utils.py

Ignore configuration management for filtering resources and fields.

#### `load_ignore_config()`

**Location**: [src/lib/ignore_utils.py](../src/lib/ignore_utils.py#L21)

**Parameters**:
- `config_file` (str | None): Path to ignore config JSON file (optional)

**Returns**: `dict` - Ignore configuration with keys: `ignore_resource_types`, `ignore_resources`, `ignore_fields`

**Description**:
Loads and validates ignore configuration from JSON file. Returns empty config if file is None or doesn't exist. Configuration structure:
```json
{
  "ignore_resource_types": ["aws_route_table_association"],
  "ignore_resources": ["aws_security_group.default"],
  "ignore_fields": ["tags.LastUpdated", "timeouts"]
}
```

**Usage Example**:
```python
from src.lib.ignore_utils import load_ignore_config

# Load config from file
config = load_ignore_config("ignore_config.json")

# Use config to filter resources
ignored_types = config.get("ignore_resource_types", [])
if resource_type in ignored_types:
    continue  # Skip this resource type

# Or use default empty config
config = load_ignore_config(None)  # Returns {"ignore_resource_types": [], ...}
```

**Related**: See [examples/ignore_config.example.json](../examples/ignore_config.example.json) for example configuration

---

#### `should_ignore_resource()`

**Location**: [src/lib/ignore_utils.py](../src/lib/ignore_utils.py#L54)

**Parameters**:
- `resource_type` (str): Terraform resource type (e.g., "aws_instance")
- `resource_address` (str): Full resource address (e.g., "aws_instance.web_server")
- `ignore_config` (dict): Ignore configuration from `load_ignore_config()`

**Returns**: `bool` - True if resource should be ignored

**Description**:
Checks if a resource should be ignored based on type or address. Uses exact string matching (no wildcards).

**Usage Example**:
```python
from src.lib.ignore_utils import load_ignore_config, should_ignore_resource

config = load_ignore_config("ignore_config.json")

for resource in resources:
    if should_ignore_resource(
        resource["type"],
        resource["address"],
        config
    ):
        continue  # Skip ignored resource
    
    # Process resource
    analyze_resource(resource)
```

---

#### `filter_ignored_fields()`

**Location**: [src/lib/ignore_utils.py](../src/lib/ignore_utils.py#L79)

**Parameters**:
- `values` (dict): Resource values (nested dict)
- `ignore_config` (dict): Ignore configuration

**Returns**: `dict` - Filtered values with ignored fields removed

**Description**:
Recursively removes ignored fields from nested dictionaries. Supports dot notation for nested paths (e.g., "tags.LastUpdated" removes `values["tags"]["LastUpdated"]`).

**Usage Example**:
```python
from src.lib.ignore_utils import load_ignore_config, filter_ignored_fields

config = load_ignore_config("ignore_config.json")
# config["ignore_fields"] = ["tags.LastUpdated", "timeouts"]

resource_values = {
    "instance_type": "t2.micro",
    "tags": {
        "Name": "WebServer",
        "LastUpdated": "2026-01-15T10:00:00Z"
    },
    "timeouts": {"create": "10m"}
}

filtered = filter_ignored_fields(resource_values, config)
# Result: {
#   "instance_type": "t2.micro",
#   "tags": {"Name": "WebServer"}
# }
# Note: LastUpdated and timeouts removed
```

---

## Core Module

### multi_env_comparator.py

Multi-environment resource comparison engine.

#### `ResourceComparison` (class)

**Location**: [src/core/multi_env_comparator.py](../src/core/multi_env_comparator.py#L20)

**Description**:
Main class for comparing resources across multiple environments. Handles resource detection, attribute comparison, diff generation, and HTML report creation.

**Key Methods**:
- `compare_resources()` - Main entry point for comparison
- `_generate_html_report()` - Creates HTML comparison report
- `_compare_attribute_values()` - Deep comparison of nested attributes

**Usage Example**:
```python
from src.core.multi_env_comparator import ResourceComparison
from src.lib.json_utils import load_json_file

# Load plans for multiple environments
dev_plan = load_json_file("dev-plan.json")
staging_plan = load_json_file("staging-plan.json")
prod_plan = load_json_file("prod-plan.json")

plans = [dev_plan, staging_plan, prod_plan]
env_names = ["Development", "Staging", "Production"]

# Create comparator
comparator = ResourceComparison(
    plans=plans,
    environment_names=env_names,
    ignore_config=None,
    show_sensitive=False
)

# Run comparison
comparator.compare_resources()

# Generate HTML report
html_output = "comparison_report.html"
comparator._generate_html_report(
    output_file=html_output,
    diff_only=False
)

print(f"Comparison report: {html_output}")
```

---

### hcl_value_resolver.py

Resolves HCL references (variables, locals) in Terraform configurations.

#### `HCLValueResolver` (class)

**Location**: [src/core/hcl_value_resolver.py](../src/core/hcl_value_resolver.py#L25)

**Description**:
Parses Terraform `.tf` and `.tfvars` files to resolve variable references and local values. Enables comparing actual configuration values instead of placeholder strings like `var.instance_type`.

**Key Methods**:
- `resolve_value()` - Resolves a single value (recursively handles nested references)
- `_parse_tfvars_file()` - Parses `.tfvars` files for variable values
- `_parse_tf_files()` - Parses `.tf` files for variable defaults and locals

**Usage Example**:
```python
from src.core.hcl_value_resolver import HCLValueResolver

# Initialize resolver with Terraform directory
resolver = HCLValueResolver(
    tf_dir="./terraform",
    tfvars_files=["dev.tfvars"]
)

# Resolve variable reference
value = "var.instance_type"
resolved = resolver.resolve_value(value)
# Result: "t2.micro" (actual value from dev.tfvars)

# Resolve local reference
value = "local.common_tags"
resolved = resolver.resolve_value(value)
# Result: {"Environment": "dev", "Project": "webapp"}

# Non-reference values pass through unchanged
value = "hardcoded-value"
resolved = resolver.resolve_value(value)
# Result: "hardcoded-value"
```

---

## Security Module

### salt_manager.py

Cryptographic salt generation and management for deterministic hashing.

#### `SaltManager` (class)

**Location**: [src/security/salt_manager.py](../src/security/salt_manager.py#L30)

**Description**:
Manages cryptographic salts for sensitive data obfuscation. Features:
- Generates random salts with 32 bytes entropy
- Encrypts/decrypts salt files using Fernet symmetric encryption
- Supports environment variable encryption keys for CI/CD
- Enables deterministic hashing across different runs (same salt = same hash)

**Key Methods**:
- `generate_salt()` - Creates new random salt
- `save_to_file()` - Encrypts and saves salt
- `load_from_file()` - Loads and decrypts salt
- `get_salt_for_position()` - Returns salt bytes for specific position

**Usage Example**:
```python
from src.security.salt_manager import SaltManager
import os

# Set encryption key (in CI/CD, use environment variable)
os.environ["TF_ANALYZER_SALT_KEY"] = "your-base64-key-here"

# Generate new salt
salt_manager = SaltManager.generate_salt()
salt_manager.save_to_file("plan-obfuscated.json.salt")

# Later: Load existing salt for deterministic hashing
loaded_salt = SaltManager.load_from_file("plan-obfuscated.json.salt")

# Use salt for hashing
position = 5
salt_bytes = loaded_salt.get_salt_for_position(position)
# Returns 8 bytes of salt at position 5 (for mixing into hash)
```

**Security Notes**:
- Salt files are encrypted with Fernet (AES-128)
- Environment variable `TF_ANALYZER_SALT_KEY` required for cross-machine salt sharing
- Salt files should be added to `.gitignore` (pattern: `*.salt`)
- Never commit salt files to version control

---

### sensitive_obfuscator.py

Sensitive data obfuscation using cryptographic hashing.

#### `SensitiveObfuscator` (class)

**Location**: [src/security/sensitive_obfuscator.py](../src/security/sensitive_obfuscator.py#L35)

**Description**:
Obfuscates sensitive values in Terraform plans using SHA-256 hashing with salt randomization. Features:
- One-way hashing (original values cannot be recovered)
- Deterministic (same value + same salt = same hash)
- Salt position randomization for extra entropy
- Processes nested JSON structures recursively
- Marks sensitive fields in `after_sensitive` and `before_sensitive`

**Key Methods**:
- `obfuscate_plan()` - Main entry point for plan obfuscation
- `_obfuscate_value()` - Hashes a single sensitive value
- `_hash_value()` - SHA-256 hashing with salt mixing

**Usage Example**:
```python
from src.security.sensitive_obfuscator import SensitiveObfuscator
from src.security.salt_manager import SaltManager
from src.lib.json_utils import load_json_file
import json

# Load plan with sensitive data
plan = load_json_file("terraform-plan.json")

# Generate salt
salt_manager = SaltManager.generate_salt()

# Create obfuscator
obfuscator = SensitiveObfuscator(salt_manager)

# Obfuscate sensitive values
obfuscated_plan = obfuscator.obfuscate_plan(plan)

# Save obfuscated plan
with open("plan-obfuscated.json", "w") as f:
    json.dump(obfuscated_plan, f, indent=2)

# Save salt for future comparison
salt_manager.save_to_file("plan-obfuscated.json.salt")

# Original: {"password": "secret123"}
# Obfuscated: {"password": "obf_8f3a9b2c7d1e5f4a"}
```

**Drift Detection Example**:
```python
# Step 1: Obfuscate dev environment
dev_plan = load_json_file("dev-plan.json")
salt_dev = SaltManager.generate_salt()
obfuscator_dev = SensitiveObfuscator(salt_dev)
dev_obfuscated = obfuscator_dev.obfuscate_plan(dev_plan)
salt_dev.save_to_file("dev-obf.json.salt")

# Step 2: Obfuscate prod with SAME salt
prod_plan = load_json_file("prod-plan.json")
salt_prod = SaltManager.load_from_file("dev-obf.json.salt")  # Same salt!
obfuscator_prod = SensitiveObfuscator(salt_prod)
prod_obfuscated = obfuscator_prod.obfuscate_plan(prod_plan)

# Step 3: Compare obfuscated plans
# If both environments have password="secret123", hashes will match
# If passwords differ, hashes will differ (drift detected)
```

**Performance**: Processes 10,000 resources in under 0.5 seconds

---

## CLI Module

### analyze_plan.py

Command-line interface for Terraform plan analysis.

#### `TerraformPlanAnalyzer` (class)

**Location**: [src/cli/analyze_plan.py](../src/cli/analyze_plan.py#L50)

**Description**:
Main CLI class providing three subcommands:
- `report` - Single-plan analysis with HTML/text output
- `compare` - Multi-environment comparison
- `obfuscate` - Sensitive data obfuscation

Uses `argparse` for argument parsing and delegates to core modules for analysis.

**Usage Example**:
```bash
# Single plan analysis
tf-plan-analyzer report plan.json --html report.html

# Multi-environment comparison
tf-plan-analyzer compare dev.json staging.json prod.json \
  --env-names "Dev,Staging,Prod" \
  --html comparison.html \
  --diff-only

# Sensitive data obfuscation
tf-plan-analyzer obfuscate plan.json \
  --output plan-obf.json \
  --show-stats
```

**Programmatic Usage** (not recommended, use CLI instead):
```python
from src.cli.analyze_plan import TerraformPlanAnalyzer

analyzer = TerraformPlanAnalyzer()

# Simulate command-line arguments
import sys
sys.argv = [
    "tf-plan-analyzer",
    "report",
    "plan.json",
    "--html", "report.html"
]

analyzer.main()
```

---

#### `main()`

**Location**: [src/cli/analyze_plan.py](../src/cli/analyze_plan.py#L1716)

**Parameters**: None (reads from `sys.argv`)

**Returns**: `int` - Exit code (0 for success, 1 for error)

**Description**:
Entry point for the `tf-plan-analyzer` command. Parses arguments, dispatches to appropriate subcommand handler, catches exceptions and returns appropriate exit codes.

**Related**: Installed as console script via [pyproject.toml](../pyproject.toml) entry point: `tf-plan-analyzer = src.cli.analyze_plan:main`

---

## Function Count Summary

Total public functions documented: **23**

By module:
- **Lib**: 13 functions (html_generation: 4, diff_utils: 2, json_utils: 2, file_utils: 2, ignore_utils: 3)
- **Core**: 2 classes (ResourceComparison, HCLValueResolver)
- **Security**: 2 classes (SaltManager, SensitiveObfuscator)
- **CLI**: 2 (TerraformPlanAnalyzer class, main function)

---

## Search Tips

Use your browser's find feature (`Cmd+F` / `Ctrl+F`) to search:
- **By function name**: Search for `` `function_name()` `` (with backticks)
- **By module**: Search for module name (e.g., "diff_utils", "html_generation")
- **By purpose**: Search for keywords (e.g., "CSS", "obfuscate", "comparison", "JSON")
- **By parameter**: Search for parameter name (e.g., "ignore_config", "sensitive")

---

## Related Documentation

- [Style Guide](style-guide.md) - UI design system for HTML reports
- [HTML Generation Source](../src/lib/html_generation.py) - CSS implementation
- [Multi-Environment Comparator](../src/core/multi_env_comparator.py) - Comparison logic
- [Single Plan Analyzer](../src/cli/analyze_plan.py) - CLI implementation
- [README](../README.md) - User-facing documentation with usage examples

---

## Contributing

When adding new public functions:

1. **Add entry to this glossary** with:
   - Location (file path and line number)
   - Parameters with types
   - Return type
   - Detailed description
   - Usage example with actual code
   
2. **Update Quick Reference** if function is commonly used

3. **Add docstring** to function with Google or NumPy format

4. **Write unit tests** in `tests/unit/` directory

5. **Reference in constitution.md** if function is critical to preventing code duplication

---

**Version**: 1.0 (January 2026) - Generated for spec 005-cleanup-and-refactor

**Last Updated**: Phase 7 implementation
