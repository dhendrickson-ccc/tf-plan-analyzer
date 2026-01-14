# Phase 1: Data Model

**Feature**: Multi-Environment Terraform Plan Comparison
**Date**: 2026-01-13

## Overview

This document defines the data structures for multi-environment comparison functionality. These entities represent the core abstractions for comparing Terraform plan "before" states across multiple environments.

## Entities

### CLISubcommand

Represents the command routing layer that distinguishes between `report` (single-plan) and `compare` (multi-environment) modes.

**Purpose**: Provide isolated argument parsing and validation for each subcommand

**Attributes**:
- `command_name`: str - Either "report" or "compare"
- `args`: Namespace - Parsed arguments specific to this subcommand
- `handler`: Callable - Function to execute for this subcommand

**Behavior**:
- Validates argument count (report=1 file, compare=2+ files)
- Routes to appropriate handler function
- Provides subcommand-specific help text

**Relationships**:
- Routes to existing TerraformPlanAnalyzer for `report` command
- Routes to new MultiEnvComparator for `compare` command

---

### EnvironmentPlan

Represents a single environment's Terraform plan data with extracted "before" state.

**Purpose**: Encapsulate environment-specific plan data and metadata

**Attributes**:
- `label`: str - Human-readable environment name (e.g., "Development", "Production")
- `plan_file_path`: Path - Path to the plan JSON file
- `plan_data`: Dict[str, Any] - Loaded JSON plan data
- `before_values`: Dict[str, Dict] - Extracted "before" state keyed by resource address
- `hcl_resolver`: Optional[HCLValueResolver] - HCL resolution context if --tf-dir provided
- `tfvars_file`: Optional[Path] - Environment-specific tfvars file if provided

**Behavior**:
- Load and parse plan JSON file
- Extract all resources from resource_changes
- Build dictionary of resource_address → before_values
- Apply HCL resolution if resolver provided
- Handle missing/invalid plan files gracefully

**Validation Rules**:
- plan_file must exist and be valid JSON
- plan_data must contain "resource_changes" key
- label must be non-empty string
- If hcl_resolver provided, tfvars_file should be provided for variable resolution

**Example**:
```python
env_plan = EnvironmentPlan(
    label="Development",
    plan_file_path=Path("dev-plan.json"),
    tfvars_file=Path("dev.tfvars")
)
env_plan.load()  # Populates plan_data and before_values
```

---

### ResourceComparison

Represents a single resource address with its configuration across all environments.

**Purpose**: Aggregate resource configuration from multiple environments for side-by-side comparison

**Attributes**:
- `resource_address`: str - Terraform resource address (e.g., "aws_instance.web[0]")
- `resource_type`: str - Terraform resource type (e.g., "aws_instance")
- `env_configs`: Dict[str, Optional[Dict]] - Environment label → configuration mapping
- `is_present_in`: Set[str] - Set of environment labels where resource exists
- `has_differences`: bool - Whether configurations differ across environments

**Behavior**:
- Collect configuration from each environment (None if resource missing)
- Detect differences by comparing configurations pairwise
- Identify which environments have this resource
- Support ignore field filtering (reuse existing ignore config logic)

**Derived Properties**:
- `missing_from`: Set[str] - Environments where resource doesn't exist
- `consistent`: bool - True if all present configs are identical
- `baseline_config`: Optional[Dict] - Configuration from first environment (reference)

**Example**:
```python
comparison = ResourceComparison(
    resource_address="aws_instance.web",
    resource_type="aws_instance",
    env_configs={
        "Dev": {"instance_type": "t2.micro", "ami": "ami-123"},
        "Prod": {"instance_type": "t2.large", "ami": "ami-123"},
        "Staging": None  # Resource doesn't exist in staging
    }
)
# comparison.has_differences = True (instance_type differs)
# comparison.is_present_in = {"Dev", "Prod"}
# comparison.missing_from = {"Staging"}
```

---

### ConfigDifference

Represents a specific configuration attribute that differs across environments.

**Purpose**: Capture granular differences for detailed reporting and highlighting

**Attributes**:
- `attribute_path`: str - Dot-notation path to the attribute (e.g., "instance_type", "tags.Environment")
- `env_values`: Dict[str, Any] - Environment label → attribute value mapping
- `is_sensitive`: bool - Whether this attribute is marked sensitive in any environment
- `diff_type`: str - Type of difference: "value_diff", "missing", "type_mismatch"

**Behavior**:
- Track value differences across environments
- Handle nested attribute paths
- Mark sensitive attributes for masking
- Support different diff types (value changed, key missing, type changed)

**Example**:
```python
diff = ConfigDifference(
    attribute_path="instance_type",
    env_values={
        "Dev": "t2.micro",
        "Staging": "t2.small",
        "Prod": "t2.large"
    },
    is_sensitive=False,
    diff_type="value_diff"
)
```

---

### MultiEnvReport

Represents the complete multi-environment comparison report structure.

**Purpose**: Orchestrate comparison logic and generate output report

**Attributes**:
- `environments`: List[EnvironmentPlan] - Ordered list of environments being compared
- `resource_comparisons`: List[ResourceComparison] - All resources aggregated for comparison
- `summary_stats`: Dict[str, int] - Summary metrics for the report
- `ignore_config`: Optional[Dict] - Ignore configuration (reuse existing format)
- `show_sensitive`: bool - Whether to reveal sensitive values (from --show-sensitive flag)
- `diff_only`: bool - Whether to filter out identical resources (from --diff-only flag)

**Behavior**:
- Aggregate resources from all environments
- Build ResourceComparison objects for each unique resource address
- Detect differences using existing diff logic
- Generate HTML report with columnar layout
- Apply ignore configuration consistently across environments
- Calculate summary statistics

**Methods**:
- `load_environments()`: Load and parse all environment plan files
- `build_comparisons()`: Create ResourceComparison objects for all resources
- `detect_differences()`: Identify which resources/attributes differ
- `generate_html()`: Create multi-column HTML report
- `calculate_summary()`: Compute metrics (total resources, differences, etc.)

**Summary Statistics**:
- `total_environments`: int - Number of environments compared
- `total_unique_resources`: int - Unique resource addresses across all environments
- `resources_with_differences`: int - Resources that differ in at least one attribute
- `resources_consistent`: int - Resources identical across all environments
- `resources_missing_from_some`: int - Resources not present in all environments

**Example**:
```python
report = MultiEnvReport(
    environments=[dev_plan, staging_plan, prod_plan],
    show_sensitive=False,
    diff_only=False
)
report.load_environments()
report.build_comparisons()
report.detect_differences()
html_output = report.generate_html()
```

---

## Data Flow

```
1. CLI Input
   ↓
2. Parse subcommand → CLISubcommand
   ↓
3. Load plan files → List[EnvironmentPlan]
   ↓
4. Extract "before" values from each EnvironmentPlan
   ↓
5. Aggregate resources → MultiEnvReport
   ↓
6. Build ResourceComparison for each unique address
   ↓
7. Detect ConfigDifference instances
   ↓
8. Generate HTML with columnar layout
   ↓
9. Output report file
```

## Integration with Existing Data Structures

**Reused from existing codebase**:
- `TerraformPlanAnalyzer`: Used for `report` subcommand (unchanged)
- `HCLValueResolver`: Used for --tf-dir resolution (unchanged)
- Ignore configuration format (JSON): Reused as-is
- Sensitivity maps from plan JSON: Reused for masking logic

**New structures**:
- All entities defined above are new for multi-environment comparison
- Isolated in `multi_env_comparator.py` to avoid coupling with existing code

## Validation Rules

1. **EnvironmentPlan**:
   - Plan file must exist and be valid JSON
   - Must contain "resource_changes" array
   - tfvars file must exist if specified

2. **ResourceComparison**:
   - resource_address must be non-empty
   - env_configs must have at least one non-None value
   - All configs must be dictionaries when present

3. **MultiEnvReport**:
   - Must have at least 2 environments
   - Environment labels must be unique
   - All plan files must be loadable

## Canonical Data Model Update

These entities should be added to `.specify/memory/data_model.md` before implementation begins (per Constitution Principle II).
