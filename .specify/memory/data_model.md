# Canonical Data Model

**Project**: Terraform Plan Analyzer  
**Last Updated**: 2026-01-13

## Overview

This document serves as the single source of truth for all data structures in the Terraform Plan Analyzer project. All features must reference and update this model before introducing new entities.

---

## Feature: Multi-Environment Terraform Plan Comparison (001)

### CLISubcommand

**Purpose**: Command routing layer distinguishing between `report` and `compare` modes

**Attributes**:
- `command_name`: str - Either "report" or "compare"
- `args`: Namespace - Parsed arguments specific to this subcommand
- `handler`: Callable - Function to execute for this subcommand

**Relationships**:
- Routes to TerraformPlanAnalyzer for `report` command
- Routes to MultiEnvComparator for `compare` command

---

### EnvironmentPlan

**Purpose**: Encapsulate single environment's Terraform plan data with extracted "before" state

**Attributes**:
- `label`: str - Human-readable environment name
- `plan_file_path`: Path - Path to plan JSON file
- `plan_data`: Dict[str, Any] - Loaded JSON plan data
- `before_values`: Dict[str, Dict] - Extracted "before" state keyed by resource address
- `hcl_resolver`: Optional[HCLValueResolver] - HCL resolution context
- `tfvars_file`: Optional[Path] - Environment-specific tfvars file

**Validation**:
- plan_file must exist and be valid JSON
- plan_data must contain "resource_changes" key
- label must be non-empty string

---

### ResourceComparison

**Purpose**: Aggregate resource configuration from multiple environments for side-by-side comparison

**Attributes**:
- `resource_address`: str - Terraform resource address (e.g., "aws_instance.web[0]")
- `resource_type`: str - Terraform resource type (e.g., "aws_instance")
- `env_configs`: Dict[str, Optional[Dict]] - Environment label → configuration mapping
- `is_present_in`: Set[str] - Set of environment labels where resource exists
- `has_differences`: bool - Whether configurations differ across environments

**Derived Properties**:
- `missing_from`: Set[str] - Environments where resource doesn't exist
- `consistent`: bool - True if all present configs are identical
- `baseline_config`: Optional[Dict] - Configuration from first environment

---

### ConfigDifference

**Purpose**: Capture granular differences for detailed reporting

**Attributes**:
- `attribute_path`: str - Dot-notation path to attribute
- `env_values`: Dict[str, Any] - Environment label → attribute value mapping
- `is_sensitive`: bool - Whether attribute is marked sensitive
- `diff_type`: str - Type: "value_diff", "missing", "type_mismatch"

---

### MultiEnvReport

**Purpose**: Orchestrate comparison logic and generate output report

**Attributes**:
- `environments`: List[EnvironmentPlan] - Ordered list of environments
- `resource_comparisons`: List[ResourceComparison] - All resources for comparison
- `summary_stats`: Dict[str, int] - Summary metrics
- `ignore_config`: Optional[Dict] - Ignore configuration
- `show_sensitive`: bool - Whether to reveal sensitive values
- `diff_only`: bool - Filter out identical resources

**Methods**:
- `load_environments()`: Load and parse all environment plan files
- `build_comparisons()`: Create ResourceComparison objects
- `detect_differences()`: Identify differing resources/attributes
- `generate_html()`: Create multi-column HTML report
- `calculate_summary()`: Compute metrics

**Summary Statistics**:
- `total_environments`: int
- `total_unique_resources`: int
- `resources_with_differences`: int
- `resources_consistent`: int
- `resources_missing_from_some`: int

---

## Future Features

(Add new features' data models below as they are specified)
