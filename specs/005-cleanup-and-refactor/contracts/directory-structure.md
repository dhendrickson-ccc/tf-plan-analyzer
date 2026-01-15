# Directory Structure Contract

**Feature**: 005-cleanup-and-refactor  
**Version**: 1.0.0  
**Status**: Proposed

---

## Purpose

This contract defines the new project directory structure and the migration path from the current root-heavy organization to a clean, modular layout. It serves as the authoritative reference for file locations and import paths.

---

## Current → New File Mapping

### Python Source Files

| Current Path | New Path | Module Import |
|--------------|----------|---------------|
| `analyze_plan.py` | `src/cli/analyze_plan.py` | `from src.cli import analyze_plan` |
| `multi_env_comparator.py` | `src/core/multi_env_comparator.py` | `from src.core import multi_env_comparator` |
| `hcl_value_resolver.py` | `src/core/hcl_value_resolver.py` | `from src.core import hcl_value_resolver` |
| `ignore_utils.py` | `src/utils/ignore_utils.py` | `from src.utils import ignore_utils` |
| `salt_manager.py` | `src/security/salt_manager.py` | `from src.security import salt_manager` |
| `sensitive_obfuscator.py` | `src/security/sensitive_obfuscator.py` | `from src.security import sensitive_obfuscator` |
| `generate_html_report.py` | **DEPRECATED** | *(functionality merged into analyze_plan.py)* |
| `generate_large_test_plan.py` | `examples/demo_data/generate_large_test_plan.py` | *(not importable, standalone script)* |

### New Template Files (US2 Deliverables)

| New Path | Purpose | Module Import |
|----------|---------|---------------|
| `src/templates/__init__.py` | Package marker | - |
| `src/templates/html_styles.py` | Shared CSS definitions | `from src.templates import html_styles` |
| `src/templates/report_template.py` | Shared HTML structure | `from src.templates import report_template` |

### Test Files

| Current Path | New Path | Purpose |
|--------------|----------|---------|
| `test_change_detection.py` | `tests/unit/test_change_detection.py` | Unit test |
| `test_hcl_reference.py` | `tests/unit/test_hcl_reference.py` | Unit test |
| `test_ignore_utils.py` | `tests/unit/test_ignore_utils.py` | Unit test |
| `test_salt_manager.py` | `tests/unit/test_salt_manager.py` | Unit test |
| `test_sensitive_obfuscator.py` | `tests/unit/test_sensitive_obfuscator.py` | Unit test |
| `test_multi_env_unit.py` | `tests/unit/test_multi_env_unit.py` | Unit test |
| `test_compare_enhancements_unit.py` | `tests/unit/test_compare_enhancements_unit.py` | Unit test |
| `test_e2e_multi_env.py` | `tests/e2e/test_e2e_multi_env.py` | End-to-end test |
| `test_e2e_obfuscate.py` | `tests/e2e/test_e2e_obfuscate.py` | End-to-end test |
| `test_e2e_compare_enhancements.py` | `tests/e2e/test_e2e_compare_enhancements.py` | End-to-end test |
| `test_e2e_sensitive_change.py` | `tests/e2e/test_e2e_sensitive_change.py` | End-to-end test |

### Test Data / Fixtures

| Current Path | New Path |
|--------------|----------|
| `test_data/` | `tests/fixtures/` |

### Documentation Files

| Current Path | New Path |
|--------------|----------|
| `IMPLEMENTATION_SUMMARY.md` | `docs/IMPLEMENTATION_SUMMARY.md` |
| `OBFUSCATION_IMPLEMENTATION_SUMMARY.md` | `docs/OBFUSCATION_IMPLEMENTATION_SUMMARY.md` |
| `JSON_REPORT_GUIDE.md` | `docs/JSON_REPORT_GUIDE.md` |
| *(new)* | `docs/style-guide.md` |

### Configuration & Examples

| Current Path | New Path |
|--------------|----------|
| `ignore_config.example.json` | `examples/ignore_config.example.json` |

### HTML Demos (Clean Up Strategy)

| Current File | Action | Reason |
|--------------|--------|--------|
| `comparison_report.html` | **DELETE** | Generated output, not source |
| `manual_validation.html` | **DELETE** | Generated output, not source |
| `prod-vs-test-comparison.html` | **DELETE** | Generated output, not source |
| `stage-test-prod-comparison.html` | **DELETE** | Generated output, not source |
| `test-vs-prod-comparison.html` | **DELETE** | Generated output, not source |
| `test_5_env.html` | **DELETE** | Generated output, not source |
| `test_all_resources.html` | **DELETE** | Generated output, not source |
| `test_diff_only.html` | **DELETE** | Generated output, not source |
| `test_filtered.html` | **DELETE** | Generated output, not source |
| `test_us1_manual.html` | **DELETE** | Generated output, not source |
| `test_us2_manual.html` | **DELETE** | Generated output, not source |
| `demo-char-diff.html` | **MOVE** → `examples/sample_reports/char_level_diff.html` | Useful demo |
| `demo-sensitive-char-diff.html` | **MOVE** → `examples/sample_reports/sensitive_diff.html` | Useful demo |
| `demo-sensitive-fixed.html` | **MOVE** → `examples/sample_reports/obfuscated_report.html` | Useful demo |
| `test_improved_style.html` | **MOVE** → `examples/sample_reports/multi_env_comparison.html` | Useful demo |
| `test_new_style.html` | **DELETE** | Deprecated by test_improved_style.html |
| `test_sensitive.html` | **DELETE** | Deprecated by demo files |

---

## Import Path Changes

### Internal Imports (within src/)

**Old**:
```python
from multi_env_comparator import MultiEnvReport
from ignore_utils import load_ignore_config
```

**New**:
```python
from src.core.multi_env_comparator import MultiEnvReport
from src.utils.ignore_utils import load_ignore_config
```

### Test Imports

**Old**:
```python
import analyze_plan
from multi_env_comparator import ResourceComparison
```

**New**:
```python
from src.cli import analyze_plan
from src.core.multi_env_comparator import ResourceComparison
```

### Relative Imports (within same package)

**Example** in `src/cli/analyze_plan.py`:
```python
from src.core.multi_env_comparator import MultiEnvReport
from src.utils.ignore_utils import load_ignore_config
from src.security.sensitive_obfuscator import SensitiveObfuscator
from src.templates.html_styles import get_base_styles
```

---

## Backward Compatibility Strategy

### CLI Entry Point

**Option 1: Maintain root-level entry point (symlink)**
```bash
# Create symlink for backward compatibility
ln -s src/cli/analyze_plan.py analyze_plan.py
```

**Option 2: Update usage instructions**
```bash
# Old way (deprecated)
python analyze_plan.py compare dev.json prod.json

# New way (recommended)
python -m src.cli.analyze_plan compare dev.json prod.json
```

**Recommended**: Option 1 for transition period, then Option 2 long-term.

### Python API (if used externally)

If external tools import this project:

**Provide compatibility shims** in root `__init__.py`:
```python
# Root __init__.py (deprecated compatibility layer)
import warnings
from src.core.multi_env_comparator import *  # noqa
from src.utils.ignore_utils import *  # noqa

warnings.warn(
    "Importing from root module is deprecated. "
    "Use 'from src.core import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

---

## pytest Configuration

**File**: `pytest.ini` (create if doesn't exist)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

**File**: `pyproject.toml` (create)

```toml
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
test = ["pytest>=8.0"]

[project.scripts]
tf-plan-analyzer = "src.cli.analyze_plan:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

---

## Migration Checklist

### Phase 1: Create New Structure
- [ ] Create all new directories (`src/`, `tests/`, `docs/`, `examples/`)
- [ ] Create all `__init__.py` files
- [ ] Create `pyproject.toml`
- [ ] Create `pytest.ini`

### Phase 2: Move Source Files
- [ ] `git mv analyze_plan.py src/cli/`
- [ ] `git mv multi_env_comparator.py src/core/`
- [ ] `git mv hcl_value_resolver.py src/core/`
- [ ] `git mv ignore_utils.py src/utils/`
- [ ] `git mv salt_manager.py src/security/`
- [ ] `git mv sensitive_obfuscator.py src/security/`

### Phase 3: Move Test Files
- [ ] `git mv test_*_unit.py tests/unit/`
- [ ] `git mv test_change_detection.py tests/unit/`
- [ ] `git mv test_hcl_reference.py tests/unit/`
- [ ] `git mv test_e2e_*.py tests/e2e/`
- [ ] `git mv test_data/ tests/fixtures/`

### Phase 4: Move Documentation
- [ ] `git mv *SUMMARY.md docs/`
- [ ] `git mv JSON_REPORT_GUIDE.md docs/`

### Phase 5: Handle HTML Files
- [ ] Delete generated HTML files (comparison_report.html, test_*.html, etc.)
- [ ] `git mv demo-*.html examples/sample_reports/`

### Phase 6: Update Imports
- [ ] Update imports in all moved files
- [ ] Update imports in test files
- [ ] Add backward compatibility shims if needed

### Phase 7: Validation
- [ ] Run `pytest tests/ -v` (all 158 tests must pass)
- [ ] Test CLI: `python -m src.cli.analyze_plan --help`
- [ ] Generate sample reports and compare
- [ ] Update README.md with new structure

---

## Rollback Plan

If issues arise:

1. **Git revert** the commit containing file moves
2. **Alternative**: Keep feature branch and address issues incrementally
3. **Restore** from backup if needed (but git history should preserve everything)

**Prevention**: Test thoroughly at each phase before proceeding.

---

## Impact Analysis

### Files to Update After Migration

1. **README.md**: Update usage examples with new import paths
2. **.github/workflows/**: Update any CI/CD paths
3. **.vscode/settings.json**: Update Python paths
4. **specs/*/quickstart.md**: Update code examples
5. **All test files**: Update import statements

### Expected Breakages (Intentional)

- Root-level `import analyze_plan` will fail (use `from src.cli import analyze_plan`)
- Relative imports between modules will fail (use absolute imports with `src.`)
- Any external tools importing this project will need updates

---

## Validation Criteria

✅ **Success** if:
- All 158 tests pass with updated imports
- CLI commands work: `python -m src.cli.analyze_plan compare ...`
- HTML reports generate successfully
- Git history preserved (`git log --follow src/cli/analyze_plan.py` shows full history)
- Root directory has <10 files (excluding directories)

❌ **Failure** if:
- Any tests fail after migration
- Import errors in production code
- Git history lost for any file
- Visual regressions in HTML reports

---

**Approval**: This contract must be reviewed and approved before implementation begins.

**Maintenance**: Update this contract if the proposed structure changes during implementation.
