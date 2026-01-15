# Quickstart Guide: Cleanup and Refactoring

**Feature**: 005-cleanup-and-refactor  
**Audience**: Developers implementing the refactoring  
**Prerequisites**: Familiarity with Python imports, pytest, git operations

---

## Overview

This guide provides step-by-step instructions for safely refactoring the tf-plan-analyzer project to reduce technical debt while maintaining 100% backward compatibility. Follow these steps in order and validate at each checkpoint.

---

## Implementation Phases

### Phase 1: Extract Shared CSS (US2)

**Goal**: Consolidate ~400 lines of duplicate CSS into a shared module.

**Impact**: Low risk, high value, no file moves required.

#### Step 1.1: Create Template Module

```bash
# Create new directories
mkdir -p src/templates
touch src/templates/__init__.py

# Create the CSS module
cat > src/templates/html_styles.py << 'EOF'
"""Shared HTML and CSS styles for all report types."""

def get_base_styles() -> str:
    """Return base CSS styles used across all HTML reports.
    
    Returns:
        str: CSS stylesheet as a string
    """
    return """
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        /* Add all shared CSS from research.md Section 2.2 */
        /* ... */
    """

def get_color_palette() -> dict:
    """Return semantic color definitions.
    
    Returns:
        dict: Color palette with semantic keys
    """
    return {
        'primary': '#667eea',
        'success': '#51cf66',
        'warning': '#ffa94d',
        'danger': '#ff6b6b',
        'added_bg': '#d3f9d8',
        'added_text': '#2b8a3e',
        'removed_bg': '#ffe0e0',
        'removed_text': '#c92a2a',
        # ... add all colors from research.md
    }
EOF
```

#### Step 1.2: Update HTML Generators

**File**: `src/core/multi_env_comparator.py`

Find the `generate_html()` method and replace inline CSS with:

```python
from src.templates.html_styles import get_base_styles

def generate_html(self, output_path: str) -> None:
    # ... existing code ...
    
    html_parts.append('<style>')
    html_parts.append(get_base_styles())
    html_parts.append('</style>')
    
    # ... rest of method ...
```

**Repeat for**:
- `src/cli/analyze_plan.py`  (if not moved yet, use `../templates/html_styles.py`)
- Remove `generate_html_report.py` (deprecated)

#### Step 1.3: Validation

```bash
# Run all tests
pytest tests/ -v

# Generate sample reports and visually compare
python analyze_plan.py compare test_data/dev-plan.json test_data/prod-plan.json --html test_after_css.html

# Open both old and new HTML files side-by-side
# They should look identical
```

✅ **Checkpoint**: All tests pass, HTML reports visually identical.

#### Step 1.4: Commit

```bash
git add src/templates/
git add src/core/multi_env_comparator.py
git add src/cli/analyze_plan.py  # or current path
git commit -m "US2: Extract shared CSS to templates module

- Create src/templates/html_styles.py with consolidated CSS
- Update multi_env_comparator.py to use shared styles
- Update analyze_plan.py to use shared styles
- Remove duplicate CSS (~400 lines eliminated)
- All tests passing (158/158)
"
```

---

### Phase 2: File Reorganization (US1)

**Goal**: Move 45+ root files into organized directories.

**Impact**: Medium risk, requires import updates.

#### Step 2.1: Create Directory Structure

```bash
# Create all new directories
mkdir -p src/cli src/core src/security src/utils src/templates
mkdir -p tests/unit tests/e2e tests/fixtures
mkdir -p docs examples/sample_reports examples/demo_data

# Create __init__.py files
touch src/__init__.py
touch src/cli/__init__.py
touch src/core/__init__.py
touch src/security/__init__.py
touch src/utils/__init__.py
touch src/templates/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/e2e/__init__.py
```

#### Step 2.2: Move Source Files (Preserve Git History)

```bash
# CRITICAL: Use 'git mv' to preserve history

# CLI entry point
git mv analyze_plan.py src/cli/

# Core functionality
git mv multi_env_comparator.py src/core/
git mv hcl_value_resolver.py src/core/

# Security modules
git mv salt_manager.py src/security/
git mv sensitive_obfuscator.py src/security/

# Utilities
git mv ignore_utils.py src/utils/

# Demo data generator
git mv generate_large_test_plan.py examples/demo_data/

# Delete deprecated file
git rm generate_html_report.py
```

#### Step 2.3: Move Test Files

```bash
# Unit tests
git mv test_change_detection.py tests/unit/
git mv test_hcl_reference.py tests/unit/
git mv test_ignore_utils.py tests/unit/
git mv test_salt_manager.py tests/unit/
git mv test_sensitive_obfuscator.py tests/unit/
git mv test_multi_env_unit.py tests/unit/
git mv test_compare_enhancements_unit.py tests/unit/

# E2E tests
git mv test_e2e_multi_env.py tests/e2e/
git mv test_e2e_obfuscate.py tests/e2e/
git mv test_e2e_compare_enhancements.py tests/e2e/
git mv test_e2e_sensitive_change.py tests/e2e/

# Test data
git mv test_data tests/fixtures
```

#### Step 2.4: Move Documentation

```bash
git mv IMPLEMENTATION_SUMMARY.md docs/
git mv OBFUSCATION_IMPLEMENTATION_SUMMARY.md docs/
git mv JSON_REPORT_GUIDE.md docs/
```

#### Step 2.5: Handle HTML Demo Files

```bash
# Delete generated output files
rm -f comparison_report.html
rm -f manual_validation.html  
rm -f prod-vs-test-comparison.html
rm -f stage-test-prod-comparison.html
rm -f test-vs-prod-comparison.html
rm -f test_5_env.html
rm -f test_all_resources.html
rm -f test_diff_only.html
rm -f test_filtered.html
rm -f test_us1_manual.html
rm -f test_us2_manual.html
rm -f test_new_style.html
rm -f test_sensitive.html

# Move useful demos
git mv demo-char-diff.html examples/sample_reports/char_level_diff.html
git mv demo-sensitive-char-diff.html examples/sample_reports/sensitive_diff.html
git mv demo-sensitive-fixed.html examples/sample_reports/obfuscated_report.html
git mv test_improved_style.html examples/sample_reports/multi_env_comparison.html

# Move example config
git mv ignore_config.example.json examples/
```

#### Step 2.6: Update ALL Import Statements

**This is the most critical step!**

Use find-and-replace across the entire codebase:

**Pattern 1**: Direct imports from root

```python
# BEFORE:
import analyze_plan
from multi_env_comparator import MultiEnvReport
from ignore_utils import load_ignore_config

# AFTER:
from src.cli import analyze_plan
from src.core.multi_env_comparator import MultiEnvReport
from src.utils.ignore_utils import load_ignore_config
```

**Pattern 2**: Test imports

```python
# BEFORE (in tests):
from analyze_plan import TerraformPlanAnalyzer

# AFTER:
from src.cli.analyze_plan import TerraformPlanAnalyzer
```

**Pattern 3**: Relative imports within src/

```python
# IN: src/cli/analyze_plan.py
from src.core.multi_env_comparator import MultiEnvReport
from src.utils.ignore_utils import load_ignore_config
from src.security.sensitive_obfuscator import SensitiveObfuscator
from src.templates.html_styles import get_base_styles
```

**Files to Update** (check each one manually):
- `src/cli/analyze_plan.py`
- `src/core/multi_env_comparator.py`
- `src/core/hcl_value_resolver.py`
- `src/security/salt_manager.py`
- `src/security/sensitive_obfuscator.py`
- `src/utils/ignore_utils.py`
- All files in `tests/unit/`
- All files in `tests/e2e/`

**Automated approach**:

```bash
# Find all import statements that need updating
grep -r "^from [a-z_]* import" src/ tests/
grep -r "^import [a-z_]*$" src/ tests/

# Use sed or your IDE's find-and-replace to update them
```

#### Step 2.7: Update Test Fixtures Path

In test files, update paths to test data:

```python
# BEFORE:
test_data_dir = "test_data"

# AFTER:
test_data_dir = "tests/fixtures"
```

#### Step 2.8: Create pytest Configuration

```bash
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
EOF
```

#### Step 2.9: Create pyproject.toml

```bash
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "tf-plan-analyzer"
version = "1.0.0"
description = "Terraform plan analysis and comparison tool"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
test = ["pytest>=8.4.2"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```
EOF
```

#### Step 2.10: Validation (CRITICAL!)

```bash
# Run all tests
pytest tests/ -v

# Should see: 158 passed

# If tests fail, check:
# 1. Import errors → fix import statements
# 2. File not found → fix test_data paths to tests/fixtures
# 3. Module not found → check __init__.py files exist
```

#### Step 2.11: Test CLI Manually

```bash
# Test the new import path
python -m src.cli.analyze_plan --help

# Test compare subcommand
python -m src.cli.analyze_plan compare \
  tests/fixtures/dev-plan.json \
  tests/fixtures/prod-plan.json \
  --html test_reorg.html

# Verify HTML report looks correct
open test_reorg.html
```

✅ **Checkpoint**: All 158 tests pass, CLI works, reports generate correctly.

#### Step 2.12: Optional Backward Compatibility Symlink

```bash
# Create symlink for old-style CLI usage
ln -s src/cli/analyze_plan.py analyze_plan.py

# Test it works
python analyze_plan.py --help
```

#### Step 2.13: Commit

```bash
git add .
git status  # Review all changes

git commit -m "US1: Reorganize project structure

- Move source files to src/ with subpackages (cli, core, security, utils)
- Move test files to tests/ with unit/ and e2e/ separation
- Move documentation to docs/
- Move examples to examples/
- Delete generated HTML files
- Update all import statements
- Create pytest.ini and pyproject.toml
- Add __init__.py files for all packages
- All 158 tests passing
- CLI working with 'python -m src.cli.analyze_plan'
"
```

---

### Phase 3: Create Style Guide (US3)

**Goal**: Document UI/UX standards for future development.

#### Step 3.1: Create Style Guide

Create `docs/style-guide.md` using the content from research.md Section 2 as a base.

See the template in `specs/005-cleanup-and-refactor/style-guide.md` (to be created).

#### Step 3.2: Update Constitution

Edit `.specify/memory/constitution.md` to add reference to style guide:

```markdown
### VI. UI Consistency Requires Style Guide Adherence

**Rules**:
- All HTML report features MUST follow the documented style guide in `docs/style-guide.md`
- Before implementing UI changes, developers MUST review the style guide
- Color values, fonts, and spacing MUST match documented standards
- New UI components MUST be added to the style guide after implementation

**Rationale**: Prevents visual inconsistency and makes the codebase maintainable.
```

#### Step 3.3: Commit

```bash
git add docs/style-guide.md
git add .specify/memory/constitution.md
git commit -m "US3: Create UI style guide

- Add comprehensive style guide documenting colors, fonts, spacing
- Update constitution to reference style guide
- Provides reference for future HTML features
"
```

---

### Phase 4: Generate Function Glossary (US4)

**Goal**: Create searchable reference of all functions.

#### Step 4.1: Generate Glossary

Create `docs/function-glossary.md` by cataloging all public functions.

Use the function catalog from `research.md` Section 4 as a starting point.

#### Step 4.2: Update Constitution

Edit `.specify/memory/constitution.md`:

```markdown
### VII. Function Discovery Required Before Implementation

**Rules**:
- Before implementing a new function, developers MUST search `docs/function-glossary.md`
- If similar functionality exists, it MUST be reused or extended
- New public functions MUST be added to the glossary after implementation
- The glossary MUST be kept up-to-date with each feature

**Rationale**: Supports Principle I (Code Duplication Prohibited) by making existing functions discoverable.
```

#### Step 4.3: Commit

```bash
git add docs/function-glossary.md
git add .specify/memory/constitution.md
git commit -m "US4: Create function glossary

- Add comprehensive function reference with 49 functions
- Document location, purpose, parameters, return types
- Update constitution to mandate glossary usage
- Supports code reuse and prevents duplication
"
```

---

### Phase 5: Code Consolidation (US5)

**Goal**: Extract remaining duplicate code to shared utilities.

*(Most of this was already done in Phase 1 with CSS extraction)*

#### Step 5.1: Extract HTML Generation Boilerplate (if needed)

If HTML report generation has shared patterns beyond CSS:

```python
# src/templates/report_template.py

def generate_html_wrapper(title: str, body_content: str, styles: str) -> str:
    """Generate complete HTML document with standard structure.
    
    Args:
        title: Page title
        body_content: HTML content for body
        styles: CSS styles (from get_base_styles())
    
    Returns:
        str: Complete HTML document
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{styles}</style>
</head>
<body>
    {body_content}
</body>
</html>
"""
```

Use this in all HTML generators if there's duplication.

#### Step 5.2: Validation

```bash
pytest tests/ -v
# All 158 tests must pass
```

#### Step 5.3: Commit

```bash
git add src/templates/
git commit -m "US5: Consolidate remaining code duplication

- Extract HTML document wrapper to shared template
- All reports use consistent structure
- Eliminates final instances of duplication
"
```

---

## Final Validation

### Full Test Suite

```bash
# Run all tests with verbose output
pytest tests/ -v --tb=short

# Expected output:
# ====== 158 passed in X.XXs ======
```

### Manual CLI Testing

```bash
# Test help
python -m src.cli.analyze_plan --help

# Test report subcommand
python -m src.cli.analyze_plan report tests/fixtures/dev-plan.json --html report_test.html

# Test compare subcommand
python -m src.cli.analyze_plan compare \
  tests/fixtures/dev-plan.json \
  tests/fixtures/staging-plan.json \
  tests/fixtures/prod-plan.json \
  --html compare_test.html \
  --config examples/ignore_config.example.json

# Test obfuscate subcommand
python -m src.cli.analyze_plan obfuscate \
  tests/fixtures/prod-sensitive.json \
  --html obfuscate_test.html
```

### Visual Validation

Open all generated HTML files and verify:
- ✅ Styling is consistent
- ✅ Colors match expected palette
- ✅ Fonts render correctly (Monaco/Menlo for code)
- ✅ Layout is responsive
- ✅ No visual regressions vs previous version

---

## Rollback Procedures

### If Tests Fail

1. **Identify the failing test**: `pytest tests/ -v --tb=long`
2. **Check import errors**: Most common issue
3. **Fix imports** in the specific test file
4. **Re-run**: `pytest tests/unit/test_specific.py -v`

### If CLI Breaks

1. **Check entry point**: `python -m src.cli.analyze_plan --help`
2. **Verify imports** in `src/cli/analyze_plan.py`
3. **Check symlink** if using backward compat: `ls -la analyze_plan.py`

### If All Else Fails

```bash
# Revert the entire commit
git revert HEAD

# Or reset to previous state
git reset --hard HEAD~1

# Then debug incrementally on a branch
```

---

## Common Pitfalls

### 1. Forgetting `__init__.py`

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Add `__init__.py` to every directory that should be a package:
```bash
touch src/__init__.py
touch src/cli/__init__.py
# etc.
```

### 2. Incorrect Test Paths

**Symptom**: `FileNotFoundError: test_data/dev-plan.json`

**Solution**: Update paths in test files:
```python
# Change all instances of:
"test_data/..."  
# to:
"tests/fixtures/..."
```

### 3. Circular Imports

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Solution**: Use absolute imports instead of relative:
```python
# GOOD:
from src.core.multi_env_comparator import MultiEnvReport

# BAD:
from ..core.multi_env_comparator import MultiEnvReport
```

### 4. pytest Not Finding Tests

**Symptom**: `collected 0 items`

**Solution**: Check `pytest.ini` exists and has correct testpaths:
```ini
[pytest]
testpaths = tests
```

---

## Success Criteria

✅ **Complete** when ALL of the following are true:

- [ ] All 158 tests pass: `pytest tests/ -v`
- [ ] CLI works: `python -m src.cli.analyze_plan --help`
- [ ] All report types generate successfully
- [ ] HTML reports are visually identical or improved
- [ ] Root directory has <10 files (excluding directories)
- [ ] Git history preserved: `git log --follow src/cli/analyze_plan.py`
- [ ] Style guide created and referenced in constitution
- [ ] Function glossary created and referenced in constitution
- [ ] No duplicate CSS code remains
- [ ] README.md updated with new structure

---

## Next Steps After Completion

1. **Update README.md** with new structure and usage examples
2. **Update quickstart guides** in `specs/*/quickstart.md`
3. **Notify team** of new import paths
4. **Update CI/CD** if it references old paths
5. **Create PR** with clear migration notes

---

## Questions?

Refer to:
- [spec.md](./spec.md) - Feature specification
- [plan.md](./plan.md) - Implementation plan
- [research.md](./research.md) - Detailed analysis
- [contracts/directory-structure.md](./contracts/directory-structure.md) - File mapping

**Remember**: Test frequently, commit incrementally, validate thoroughly!
