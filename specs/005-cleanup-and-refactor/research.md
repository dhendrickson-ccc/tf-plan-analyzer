# Cleanup and Refactoring - Research Document

**Project:** tf-plan-analyzer  
**Feature:** 005-cleanup-and-refactor  
**Date:** January 15, 2026  
**Status:** Research Phase

---

## Executive Summary

This document provides a comprehensive analysis of the tf-plan-analyzer project's current structure, identifying opportunities for cleanup and refactoring. The analysis reveals significant code duplication, inconsistent styling, and organizational issues that impact maintainability and developer experience.

**Key Findings:**
- 45+ Python files scattered in root directory (source, tests, utilities)
- 13+ HTML demo/test files in root directory
- Duplicate CSS/styling code across 3 files (~400 lines of duplicated CSS)
- Duplicate diff highlighting logic across 3 files
- Duplicate JSON formatting and file I/O patterns
- 49 public functions across 19 Python files

---

## Section 1: Current File Organization

### 1.1 Root Directory File Count

| Category | Count | Files |
|----------|-------|-------|
| **Python Source** | 8 | analyze_plan.py, generate_html_report.py, multi_env_comparator.py, hcl_value_resolver.py, ignore_utils.py, salt_manager.py, sensitive_obfuscator.py, generate_large_test_plan.py |
| **Test Files** | 11 | test_change_detection.py, test_compare_enhancements_unit.py, test_e2e_compare_enhancements.py, test_e2e_multi_env.py, test_e2e_obfuscate.py, test_e2e_sensitive_change.py, test_hcl_reference.py, test_ignore_utils.py, test_multi_env_unit.py, test_salt_manager.py, test_sensitive_obfuscator.py |
| **HTML Demos/Reports** | 13 | comparison_report.html, demo-char-diff.html, demo-sensitive-char-diff.html, demo-sensitive-fixed.html, manual_validation.html, prod-vs-test-comparison.html, stage-test-prod-comparison.html, test-vs-prod-comparison.html, test_5_env.html, test_all_resources.html, test_diff_only.html, test_filtered.html, test_improved_style.html, test_new_style.html, test_sensitive.html, test_us1_manual.html, test_us2_manual.html |
| **Markdown Docs** | 4 | README.md, IMPLEMENTATION_SUMMARY.md, OBFUSCATION_IMPLEMENTATION_SUMMARY.md, JSON_REPORT_GUIDE.md |
| **Config Files** | 2 | ignore_config.example.json, .gitignore |
| **Directories** | 3 | specs/, test_data/, .vscode/ |

### 1.2 Current Structure Issues

**Problems:**
1. **No separation of concerns**: Source files, tests, demos, and docs all in root
2. **Test file pollution**: 11 test files in root instead of dedicated test directory
3. **HTML demo clutter**: 13+ HTML files make it hard to find actual code
4. **Deprecated code**: `generate_html_report.py` is deprecated but still present
5. **Unclear entry points**: Multiple Python files at root level

**Impact:**
- Cognitive overload when navigating project
- Difficult for new contributors to understand structure
- Hard to distinguish test artifacts from production code
- IDE file trees are cluttered and hard to navigate

---

## Section 2: CSS/Styling Analysis

### 2.1 CSS Code Duplication

Three files contain nearly identical CSS definitions:
1. [analyze_plan.py](analyze_plan.py#L932-L1300) (~370 lines)
2. [generate_html_report.py](generate_html_report.py#L323-L550) (~230 lines)
3. [multi_env_comparator.py](multi_env_comparator.py#L671-L720) (~50 lines)

### 2.2 Color Inconsistencies

| Semantic Meaning | File | Color Value | Line |
|------------------|------|-------------|------|
| **Primary brand color** | analyze_plan.py | `#667eea` | 992, 1006, 1238, 1291 |
| **Primary brand color** | generate_html_report.py | `#667eea` | 379, 393 |
| **Primary brand color** | multi_env_comparator.py | `#667eea` | 680, 685, 690 |
| **Green (added/created)** | analyze_plan.py | `#51cf66` | 993 |
| **Green (added/created)** | generate_html_report.py | `#51cf66` | 380 |
| **Green (added/created)** | multi_env_comparator.py | `#51cf66` | 682 |
| **Orange (updated)** | analyze_plan.py | `#ffa94d` | 994 |
| **Orange (updated)** | generate_html_report.py | `#ffa94d` | 381 |
| **Orange (updated)** | multi_env_comparator.py | `#ffa94d` | 681 |
| **Red (removed/deleted)** | analyze_plan.py | `#c92a2a` | 1126, 1160, 1199 |
| **Red (removed/deleted)** | generate_html_report.py | `#c92a2a` | 489, 518, 536 |
| **Red (removed/deleted)** | multi_env_comparator.py | `#c92a2a` | 705, 711 |
| **Light green background (added)** | analyze_plan.py | `#d3f9d8` | 1165, 694 |
| **Light green background (added)** | generate_html_report.py | `#d3f9d8` | 523 |
| **Light green background (added)** | multi_env_comparator.py | `#d3f9d8` | 694, 703, 712 |
| **Light red background (removed)** | analyze_plan.py | `#ffe0e0` | 1159, 705 |
| **Light red background (removed)** | generate_html_report.py | `#ffe0e0` | 517 |
| **Light red background (removed)** | multi_env_comparator.py | `#ffe0e0` | 705, 711 |

**Finding:** Colors are mostly consistent, but scattered across files. Good opportunity to centralize.

### 2.3 Font Family Inconsistencies

| Usage | File | Font Family | Line |
|-------|------|-------------|------|
| **Monospace (code)** | analyze_plan.py | `'Courier New', monospace` | 1020, 1039, 1143, 1192, 1268 |
| **Monospace (code)** | generate_html_report.py | `'Courier New', monospace` | 407, 423, 501, 529 |
| **Monospace (code)** | multi_env_comparator.py | `"Monaco", "Menlo", monospace` | 692, 708, 709 |

**Inconsistency Found:** 
- `analyze_plan.py` and `generate_html_report.py` use `'Courier New', monospace`
- `multi_env_comparator.py` uses `"Monaco", "Menlo", monospace`
- **Impact:** Monaco/Menlo provides better rendering on macOS, but inconsistent application

### 2.4 Duplicate Style Blocks

**Exact duplicates found:**

1. **Body styles** - All 3 files:
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}
```

2. **Summary card color classes** - All 3 files:
```css
.summary-card.total .number { color: #667eea; }
.summary-card.created .number { color: #51cf66; }
.summary-card.updated .number { color: #ffa94d; }
```

3. **Diff highlighting classes**:
```css
.removed { background-color: #ffe0e0; color: #c92a2a; }
.added { background-color: #d3f9d8; color: #2b8a3e; }
.unchanged { color: #495057; }
```

**Total Duplication:** ~200-300 lines of CSS duplicated 2-3 times each.

---

## Section 3: Code Duplication Analysis

### 3.1 Duplicate HTML Generation Patterns

**Pattern 1: HTML Header Generation**

Found in:
- [analyze_plan.py](analyze_plan.py#L920-L960) (lines 920-960)
- [generate_html_report.py](generate_html_report.py#L310-L350) (lines 310-350)
- [multi_env_comparator.py](multi_env_comparator.py#L665-L675) (lines 665-675)

Nearly identical structure:
```python
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Plan Analysis Report</title>
    <style>
        /* CSS here */
    </style>
</head>
"""
```

### 3.2 Duplicate Diff Highlighting Logic

**Function: `_highlight_char_diff()`**

Duplicated in:
1. [analyze_plan.py](analyze_plan.py#L666-L698) - `TerraformPlanAnalyzer._highlight_char_diff()` (lines 666-698)
2. [multi_env_comparator.py](multi_env_comparator.py#L37-L66) - `_highlight_char_diff()` (lines 37-66)

**Code similarity:** ~95% identical. Both use:
- `SequenceMatcher` from difflib
- Same logic for equal/delete/insert/replace tags
- Same HTML span class names (`char-removed`, `char-added`)

**Function: `_highlight_json_diff()`**

Duplicated in:
1. [analyze_plan.py](analyze_plan.py#L700-L870) - `TerraformPlanAnalyzer._highlight_json_diff()` (lines 700-870, ~170 lines)
2. [generate_html_report.py](generate_html_report.py#L36-L118) - `highlight_json_diff()` (lines 36-118, ~80 lines)
3. [multi_env_comparator.py](multi_env_comparator.py#L68-L167) - `_highlight_json_diff()` (lines 68-167, ~100 lines)

**Code similarity:** 70-80% identical core logic:
- JSON serialization with `json.dumps(indent=2, sort_keys=True)`
- Line-by-line comparison with `SequenceMatcher`
- Similar handling of equal/delete/insert/replace operations
- Character-level diff for similar lines (ratio > 0.5)

**Variations:**
- `analyze_plan.py` version has additional handling for:
  - Sensitive value redaction
  - "known after apply" styling
  - Azure casing normalization
- `generate_html_report.py` and `multi_env_comparator.py` are simpler versions

### 3.3 Duplicate JSON Formatting Logic

**Pattern: JSON loading from files**

Found in 15+ locations:
- [analyze_plan.py](analyze_plan.py#L81-L82): `with open(self.plan_file, 'r') as f: self.plan_data = json.load(f)`
- [ignore_utils.py](ignore_utils.py#L41-L43): `with open(file_path, 'r') as f: config = json.load(f)`
- [multi_env_comparator.py](multi_env_comparator.py#L200): `with open(self.plan_file_path, 'r') as f:`
- All test files: Similar patterns repeated

**Common patterns:**
```python
# Pattern 1: Load JSON file
with open(file_path, 'r') as f:
    data = json.load(f)

# Pattern 2: Write JSON file
with open(output_path, 'w') as f:
    json.dump(data, f, indent=2)

# Pattern 3: Pretty-print JSON
json.dumps(data, indent=2, sort_keys=True)
```

### 3.4 Duplicate File I/O Patterns

**Pattern: HTML file writing**

Found in:
- [analyze_plan.py](analyze_plan.py#L1673): `with open(output_path, 'w', encoding='utf-8', errors='surrogatepass') as f:`
- [generate_html_report.py](generate_html_report.py#L722): Similar pattern
- [multi_env_comparator.py](multi_env_comparator.py#L834): `with open(output_path, 'w') as f:`

**Pattern: Plan JSON file loading**

Found in:
- [analyze_plan.py](analyze_plan.py#L81-L83)
- [analyze_plan.py](analyze_plan.py#L2145-L2146) (obfuscate subcommand)
- [multi_env_comparator.py](multi_env_comparator.py#L200-L201)

### 3.5 Similar Error Handling Blocks

**Pattern: Try-except for JSON loading**

Found in:
- [ignore_utils.py](ignore_utils.py#L40-L50):
```python
try:
    with open(file_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    raise ValueError(f"Config file not found: {file_path}")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in config file {file_path}: {e}")
```

Similar pattern in test files for loading test data.

**Pattern: Import error handling**

Found in:
- [analyze_plan.py](analyze_plan.py#L16-L28):
```python
try:
    from hcl_value_resolver import HCLValueResolver
except ImportError:
    HCLValueResolver = None  # Optional dependency

try:
    from salt_manager import generate_salt, generate_position_seed, store_salt, load_salt
    from sensitive_obfuscator import traverse_and_obfuscate
except ImportError as e:
    print(f"Warning: Obfuscate subcommand dependencies not available: {e}", file=sys.stderr)
    generate_salt = None
    # ... etc
```

---

## Section 4: Function Catalog

### 4.1 Core Source Files

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `TerraformPlanAnalyzer.__init__` | analyze_plan.py | 35-77 | Initialize analyzer with plan file and config |
| `TerraformPlanAnalyzer.load_plan` | analyze_plan.py | 79-83 | Load terraform plan JSON from file |
| `TerraformPlanAnalyzer.analyze` | analyze_plan.py | 85-285 | Main analysis - categorize resource changes |
| `TerraformPlanAnalyzer._highlight_char_diff` | analyze_plan.py | 666-698 | Character-level diff highlighting |
| `TerraformPlanAnalyzer._highlight_json_diff` | analyze_plan.py | 700-870 | JSON diff with line/char highlighting |
| `TerraformPlanAnalyzer.generate_html_report` | analyze_plan.py | 920-1673 | Generate HTML report from analysis |
| `load_config` | analyze_plan.py | 1805-1816 | Load ignore config JSON file |
| `handle_report_subcommand` | analyze_plan.py | 1818-1968 | CLI handler for `report` command |
| `handle_compare_subcommand` | analyze_plan.py | 1970-2110 | CLI handler for `compare` command |
| `handle_obfuscate_subcommand` | analyze_plan.py | 2112-2280 | CLI handler for `obfuscate` command |
| `main` | analyze_plan.py | 2282-2594 | CLI entry point |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `highlight_json_diff` | generate_html_report.py | 36-118 | JSON diff highlighting (DEPRECATED) |
| `parse_text_report` | generate_html_report.py | 120-183 | Parse text report into structured data |
| `parse_changes` | generate_html_report.py | 185-304 | Parse change details from text |
| `generate_html_report` | generate_html_report.py | 306-720 | Generate HTML from parsed text |
| `main` | generate_html_report.py | 722-742 | CLI entry point (DEPRECATED) |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `_highlight_char_diff` | multi_env_comparator.py | 37-66 | Character-level diff highlighting |
| `_highlight_json_diff` | multi_env_comparator.py | 68-167 | JSON diff highlighting |
| `EnvironmentPlan.__init__` | multi_env_comparator.py | 173-198 | Load plan for one environment |
| `ResourceComparison.__init__` | multi_env_comparator.py | 317-542 | Compare resource across environments |
| `MultiEnvReport.generate_html` | multi_env_comparator.py | 546-834 | Generate multi-env comparison HTML |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `load_ignore_config` | ignore_utils.py | 17-76 | Load and validate ignore config JSON |
| `apply_ignore_config` | ignore_utils.py | 78-128 | Apply ignore rules to resource config |
| `get_ignored_attributes` | ignore_utils.py | 130-178 | Get set of ignored attribute paths |
| `supports_dot_notation` | ignore_utils.py | 180-217 | Check if path uses dot notation |
| `_remove_nested_attribute` | ignore_utils.py | 219-264 | Remove nested attribute from config |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `HCLValueResolver.__init__` | hcl_value_resolver.py | 18-35 | Initialize resolver with TF directory |
| `HCLValueResolver.get_resource_attribute` | hcl_value_resolver.py | ~150 | Get attribute value from HCL definition |
| `HCLValueResolver.resolve_value` | hcl_value_resolver.py | ~250 | Resolve variables in HCL expressions |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `get_encryption_key` | salt_manager.py | 22-55 | Get/generate encryption key from env |
| `generate_salt` | salt_manager.py | 57-68 | Generate cryptographic salt (32 bytes) |
| `generate_position_seed` | salt_manager.py | 70-81 | Generate position seed (32 bytes) |
| `store_salt` | salt_manager.py | 83-120 | Encrypt and store salt to file |
| `load_salt` | salt_manager.py | 122-164 | Load and decrypt salt from file |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `get_salt_position` | sensitive_obfuscator.py | 18-43 | Determine salt insertion position |
| `obfuscate_value` | sensitive_obfuscator.py | 45-79 | Hash value with salt at position |
| `traverse_and_obfuscate` | sensitive_obfuscator.py | 81-187 | Recursively obfuscate sensitive fields |

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `generate_large_plan` | generate_large_test_plan.py | 7-85 | Generate large test plan JSON |

### 4.2 Test Files (Selected Examples)

| Function Name | File | Lines | Purpose |
|--------------|------|-------|---------|
| `run_obfuscate` | test_e2e_obfuscate.py | 22-48 | Helper to run obfuscate CLI |
| `test_basic_obfuscation` | test_e2e_obfuscate.py | 50-83 | Test basic sensitive value obfuscation |
| `test_deterministic_same_file` | test_e2e_obfuscate.py | 358-398 | Test deterministic hashing |
| `test_drift_detection` | test_e2e_obfuscate.py | 472-553 | Test drift detection with obfuscation |

*(Note: 40+ additional test functions exist across 11 test files)*

---

## Section 5: Recommendations

### 5.1 Proposed New Directory Structure

```
tf-plan-analyzer/
├── src/
│   ├── __init__.py
│   ├── analyzer.py              # TerraformPlanAnalyzer class
│   ├── cli.py                   # CLI entry point and command handlers
│   ├── comparator.py            # Multi-env comparison logic
│   ├── hcl_resolver.py          # HCL value resolution
│   ├── ignore.py                # Ignore config utilities
│   ├── obfuscation/
│   │   ├── __init__.py
│   │   ├── salt.py              # Salt manager
│   │   └── obfuscator.py        # Sensitive value obfuscation
│   └── html/
│       ├── __init__.py
│       ├── styles.py            # Centralized CSS styles
│       ├── diff_renderer.py     # Diff highlighting logic
│       └── report_generator.py  # HTML report generation
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_analyzer.py
│   │   ├── test_comparator.py
│   │   ├── test_ignore.py
│   │   ├── test_hcl_resolver.py
│   │   ├── test_salt.py
│   │   └── test_obfuscator.py
│   ├── e2e/
│   │   ├── test_report.py
│   │   ├── test_compare.py
│   │   ├── test_obfuscate.py
│   │   └── test_compare_enhancements.py
│   └── fixtures/
│       └── (move test_data here)
├── docs/
│   ├── README.md
│   ├── implementation/
│   │   ├── sensitive-obfuscation.md
│   │   └── multi-env-comparison.md
│   └── guides/
│       └── json-report.md
├── examples/
│   ├── basic_report.html
│   ├── multi_env_comparison.html
│   └── sensitive_obfuscation.html
├── specs/                       # Keep as-is
├── .gitignore
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # Fallback for older pip
└── README.md
```

### 5.2 Refactoring Priorities

#### Priority 1: Extract CSS to Centralized Module (High Impact, Low Risk)

**Action:** Create `src/html/styles.py`

```python
class TerraformReportStyles:
    """Centralized CSS styles for Terraform plan reports."""
    
    # Color palette
    COLORS = {
        'brand_primary': '#667eea',
        'brand_secondary': '#764ba2',
        'success': '#51cf66',
        'warning': '#ffa94d',
        'danger': '#ff6b6b',
        'green_light': '#d3f9d8',
        'green_dark': '#2b8a3e',
        'red_light': '#ffe0e0',
        'red_dark': '#c92a2a',
        'blue_light': '#e3f2fd',
        'blue_dark': '#1976d2',
        # ... etc
    }
    
    # Font families
    FONTS = {
        'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
        'mono': '"Monaco", "Menlo", "Consolas", "Courier New", monospace',
    }
    
    @classmethod
    def get_base_styles(cls) -> str:
        """Return base CSS styles."""
        return f"""
        body {{
            font-family: {cls.FONTS['system']};
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        /* ... */
        """
    
    @classmethod
    def get_diff_styles(cls) -> str:
        """Return diff highlighting styles."""
        # ...
```

**Benefit:** Single source of truth for colors, fonts, and styles. Easy to maintain consistency.

#### Priority 2: Extract Diff Highlighting to Shared Module (High Impact, Medium Risk)

**Action:** Create `src/html/diff_renderer.py`

```python
class DiffRenderer:
    """Shared diff rendering logic for JSON and text comparisons."""
    
    @staticmethod
    def highlight_char_diff(before_str: str, after_str: str, 
                           style_classes: Dict[str, str] = None) -> Tuple[str, str]:
        """Character-level diff highlighting with configurable CSS classes."""
        # Unified implementation
    
    @staticmethod
    def highlight_json_diff(before: Any, after: Any,
                           normalize_fn: Callable = None,
                           style_classes: Dict[str, str] = None) -> Tuple[str, str]:
        """JSON diff highlighting with optional normalization."""
        # Unified implementation with strategy pattern for variations
```

**Benefit:** Eliminates 200+ lines of duplicate code. Single place to fix bugs.

#### Priority 3: Reorganize File Structure (Medium Impact, Medium Risk)

**Action Steps:**
1. Create `src/` and `tests/` directories
2. Move source files to `src/`
3. Move test files to `tests/unit/` and `tests/e2e/`
4. Move HTML demos to `examples/`
5. Move docs to `docs/`
6. Update imports and paths
7. Add `__init__.py` files
8. Update `pyproject.toml` or `setup.py`

**Benefit:** Professional structure, easier navigation, clearer separation of concerns.

#### Priority 4: Extract Common Utilities (Low Impact, Low Risk)

**Action:** Create `src/utils.py` or `src/io.py`

```python
def load_json_file(file_path: str) -> Dict:
    """Load JSON from file with error handling."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def write_json_file(data: Any, file_path: str, indent: int = 2) -> None:
    """Write data to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)

def write_html_file(content: str, file_path: str) -> None:
    """Write HTML content to file with proper encoding."""
    with open(file_path, 'w', encoding='utf-8', errors='surrogatepass') as f:
        f.write(content)
```

**Benefit:** DRY, consistent error handling, easier to add logging/validation.

#### Priority 5: Remove Deprecated Code (Low Impact, Low Risk)

**Action:** Delete or archive `generate_html_report.py`

The file header states:
> DEPRECATED: This script is deprecated in favor of the built-in HTML generation in analyze_plan.py.

**Benefit:** Reduces confusion, removes ~740 lines of unmaintained code.

### 5.3 Refactoring Approach

**Recommended Strategy: Incremental Refactoring**

1. **Phase 1: CSS Extraction** (1-2 days)
   - Create `src/html/styles.py`
   - Update all 3 files to use centralized styles
   - Test all HTML generation paths
   - No breaking changes to API

2. **Phase 2: Diff Logic Extraction** (2-3 days)
   - Create `src/html/diff_renderer.py`
   - Extract `_highlight_char_diff()` and `_highlight_json_diff()`
   - Update all consumers
   - Add comprehensive tests
   - No breaking changes to API

3. **Phase 3: File Reorganization** (3-4 days)
   - Create new directory structure
   - Move files gradually
   - Update imports
   - Update CI/CD if needed
   - Update documentation
   - **Breaking change:** Import paths will change

4. **Phase 4: Utilities & Cleanup** (1-2 days)
   - Extract common I/O functions
   - Remove deprecated files
   - Clean up imports

5. **Phase 5: Documentation** (1 day)
   - Update README.md
   - Create architecture docs
   - Update contribution guidelines

**Total Estimated Time:** 8-12 days

### 5.4 Testing Strategy

**For each phase:**
1. Run existing test suite before changes
2. Make incremental changes
3. Run tests after each logical change
4. Add new tests for extracted code
5. Verify HTML output manually (spot check examples)
6. Check for import errors

**Regression Prevention:**
- Keep all existing tests passing
- Add golden file tests for HTML output
- Use visual regression testing for CSS changes (optional)

### 5.5 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking imports for users | Medium | High | Provide deprecation warnings, maintain backwards compatibility for 1-2 releases |
| CSS changes affect rendering | Low | Medium | Compare before/after HTML outputs, use browser testing |
| Test paths break | High | Low | Update test imports systematically, use IDE refactoring tools |
| Lost functionality during extraction | Low | High | Incremental extraction, comprehensive testing, code review |

---

## Appendix A: Detailed CSS Comparison

### Common CSS Classes Across Files

| Class Name | analyze_plan.py | generate_html_report.py | multi_env_comparator.py |
|------------|----------------|------------------------|------------------------|
| `.removed` | ✓ | ✓ | ✓ |
| `.added` | ✓ | ✓ | ✓ |
| `.unchanged` | ✓ | ✓ | ✓ |
| `.char-removed` | ✓ | - | ✓ |
| `.char-added` | ✓ | - | ✓ |
| `.summary-card` | ✓ | ✓ | ✓ |
| `.json-content` | ✓ | ✓ | ✓ |
| `.resource-name` | ✓ | - | ✓ |
| `.diff-header` | ✓ | ✓ | ✓ |

### Unique CSS Classes by File

**analyze_plan.py only:**
- `.known-after-apply` - Yellow styling for computed values
- `.char-known-after-apply` - Character-level styling for computed values
- `.sensitive-badge` - Sensitive value indicator
- `.legend` / `.legend-content` - Expandable legend section
- `.hcl-marker` - HCL reference indicator

**multi_env_comparator.py only:**
- `.baseline-removed` / `.baseline-added` - Baseline comparison highlighting
- `.baseline-char-removed` / `.baseline-char-added` - Baseline character diffs
- `.env-action` - Environment action badges (create/update/delete/no-op/missing)
- `.resource-status.identical` / `.different` - Resource comparison status

---

## Appendix B: Import Graph

Current import dependencies (simplified):

```
analyze_plan.py
├── hcl_value_resolver (optional)
├── salt_manager (optional)
├── sensitive_obfuscator (optional)
└── (no imports from other project files)

multi_env_comparator.py
└── ignore_utils

generate_html_report.py
└── (no imports from other project files)

salt_manager.py
└── (no imports from other project files)

sensitive_obfuscator.py
└── (no imports from other project files)

ignore_utils.py
└── (no imports from other project files)

hcl_value_resolver.py
└── (no imports from other project files)
```

**Finding:** Good modularity, low coupling. Refactoring should maintain this.

---

## Appendix C: Lines of Code Summary

| File | Total Lines | Comments/Docs | Code | Blank |
|------|------------|---------------|------|-------|
| analyze_plan.py | 2,594 | ~300 | ~2,100 | ~194 |
| generate_html_report.py | 742 | ~80 | ~600 | ~62 |
| multi_env_comparator.py | 1,073 | ~150 | ~850 | ~73 |
| hcl_value_resolver.py | 402 | ~60 | ~320 | ~22 |
| ignore_utils.py | ~264 | ~40 | ~200 | ~24 |
| salt_manager.py | ~164 | ~30 | ~120 | ~14 |
| sensitive_obfuscator.py | 187 | ~40 | ~130 | ~17 |
| **Total Source** | **~5,426** | **~700** | **~4,320** | **~406** |

---

## Conclusion

The tf-plan-analyzer project has grown organically and would benefit significantly from cleanup and refactoring. The primary opportunities are:

1. **CSS Consolidation**: ~400 lines of duplicate CSS can be centralized
2. **Diff Logic Extraction**: ~200-300 lines of duplicate diff highlighting
3. **Directory Reorganization**: 45+ root-level files need proper structure
4. **Deprecated Code Removal**: ~740 lines in deprecated file

**Expected Benefits:**
- 20-30% reduction in total lines of code through deduplication
- Improved maintainability and developer experience
- Easier onboarding for new contributors
- More professional project structure
- Single source of truth for styling and diff logic

**Next Steps:**
1. Review this research document with team
2. Prioritize refactoring phases
3. Create detailed tasks in specs/005-cleanup-and-refactor/tasks.md
4. Begin incremental implementation starting with Phase 1

---

**Document Version:** 1.0  
**Author:** GitHub Copilot  
**Last Updated:** January 15, 2026
