# Data Model: Cleanup and Refactoring

**Feature**: 005-cleanup-and-refactor  
**Status**: N/A (No Data Model Changes)

---

## Overview

This feature is a **pure refactoring effort** that does not introduce or modify any data structures. All existing data models remain unchanged.

---

## Existing Data Models (Preserved)

The following data structures are already documented in the canonical data model (`.specify/memory/data_model.md`) and are **not modified** by this feature:

### Core Entities (Unchanged)

1. **TerraformPlan**: Representation of a Terraform plan JSON
   - No changes to schema or parsing logic
   - File location changes only (moved to `src/cli/analyze_plan.py`)

2. **ResourceComparison**: Multi-environment comparison data
   - No changes to comparison algorithm
   - File location changes only (moved to `src/core/multi_env_comparator.py`)

3. **SensitiveConfig**: Sensitive value configuration
   - No changes to obfuscation logic
   - File location changes only (moved to `src/security/`)

4. **IgnoreConfig**: Ignore rules configuration
   - No changes to filtering logic
   - File location changes only (moved to `src/utils/ignore_utils.py`)

### Configuration Schemas (Unchanged)

All JSON schemas remain identical:
- Terraform plan JSON format (external, from Terraform)
- Ignore configuration JSON (defined in feature 004)
- Salt configuration JSON (defined in feature 003)

---

## New Configuration Files (Non-Data)

This feature introduces **project configuration** files, not data models:

### pyproject.toml

**Purpose**: Python project metadata and build configuration

**Content**: Standard Python packaging metadata (not a data model)

```toml
[project]
name = "tf-plan-analyzer"
version = "1.0.0"
requires-python = ">=3.9"
```

### pytest.ini

**Purpose**: pytest test runner configuration

**Content**: Test discovery settings (not a data model)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

---

## Data Flow (Unchanged)

The data flow through the system remains identical:

```
Terraform Plan JSON (input)
    ↓
TerraformPlanAnalyzer.parse() [moved to src/cli/]
    ↓
Analysis/Comparison Logic [moved to src/core/]
    ↓
HTML Report (output)
```

Only the **file locations** of the processing code change. The data structures themselves are unchanged.

---

## Style Configuration (Presentation Layer)

### New: CSS Configuration

**File**: `src/templates/html_styles.py`

**Purpose**: Centralized CSS definitions (presentation, not data)

**Type**: Python functions returning strings, not data classes

```python
def get_base_styles() -> str:
    """Returns CSS as a string."""
    
def get_color_palette() -> dict:
    """Returns color configuration as a dict."""
```

**Note**: These are **template functions**, not data models. They define presentation layer configuration, not business data.

---

## Documentation Metadata (Non-Data)

### Function Glossary Schema

**File**: `docs/function-glossary.md`

**Purpose**: Documentation about functions (metadata, not runtime data)

**Format**: Markdown table

| Field | Description |
|-------|-------------|
| Function Name | Identifier |
| File Path | Location |
| Parameters | Input description |
| Return Type | Output description |
| Purpose | What it does |

**Note**: This is **documentation metadata**, not a runtime data model.

---

## Canonical Data Model Reference

The canonical data model is maintained in:
- **Location**: `.specify/memory/data_model.md`
- **Status**: No updates required for this feature
- **Validation**: All existing entities remain valid

If this feature required data model changes, they would be documented there first (per Constitution Principle II). Since it doesn't, no updates are needed.

---

## Summary

**Data Model Changes**: ❌ None

**Why**: This is a code organization and presentation layer refactoring. All business logic, data structures, and schemas remain identical. Only file locations and CSS extraction are affected.

**Impact**: ✅ Zero impact on data layer, schema validation, or business logic

---

## Validation

To verify data models are unchanged:

```python
# Test that all data structures still work
from src.cli.analyze_plan import TerraformPlanAnalyzer
from src.core.multi_env_comparator import ResourceComparison
from src.security.sensitive_obfuscator import SensitiveObfuscator
from src.utils.ignore_utils import load_ignore_config

# If all imports work and tests pass, data models are preserved ✅
```

---

**Conclusion**: This feature requires no data modeling work. All 158 existing tests validate that data structures remain intact after refactoring.
