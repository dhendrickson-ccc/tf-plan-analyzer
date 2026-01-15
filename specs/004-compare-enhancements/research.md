# Research: Compare Subcommand Enhancements

**Date**: January 14, 2026  
**Purpose**: Research existing implementation patterns for adding ignore file support and attribute-level diff view to the `compare` subcommand.

---

## 1. Existing Ignore Configuration Implementation

### Current Implementation in `analyze_plan.py`

#### Location: Lines 1833-1920 (handle_report_subcommand)

The ignore configuration system in `analyze_plan.py` supports two data structures:

**JSON Schema** (from [ignore_config.example.json](../../ignore_config.example.json)):
```json
{
  "global_ignores": {
    "tags": "Tags are managed separately and don't affect resource functionality"
  },
  "resource_ignores": {
    "azurerm_monitor_metric_alert": {
      "action": "Dynamic block conversion causes inconsequential changes",
      "description": "Description is conditionally set based on environment"
    }
  }
}
```

**Supported Formats**:
1. **global_ignores**: Can be either:
   - `List<string>`: Simple list of field names to ignore globally
   - `Dict<string, string>`: Map of field name → reason for ignoring

2. **resource_ignores**: Should be a dict where:
   - Key: Resource type (e.g., `azurerm_monitor_metric_alert`)
   - Value: Either a list of field names OR dict of field name → reason

#### Code Implementation (Lines 1833-1865)

```python
# Load global ignores from config (supports both list and dict formats)
if 'global_ignores' in config:
    if isinstance(config['global_ignores'], list):
        custom_ignore_fields.update(config['global_ignores'])
    elif isinstance(config['global_ignores'], dict):
        for field, reason in config['global_ignores'].items():
            custom_ignore_fields.add(field)
            global_ignore_reasons[field] = reason
    else:
        print("Warning: 'global_ignores' should be a list or dict")

# Load resource-specific ignores from config (supports both list and dict formats)
if 'resource_ignores' in config:
    if isinstance(config['resource_ignores'], dict):
        for resource_type, fields in config['resource_ignores'].items():
            if isinstance(fields, list):
                resource_specific_ignores[resource_type] = set(fields)
            elif isinstance(fields, dict):
                resource_specific_ignores[resource_type] = set(fields.keys())
                resource_ignore_reasons[resource_type] = fields
            else:
                print(f"Warning: Fields for '{resource_type}' should be a list or dict")
    else:
        print("Warning: 'resource_ignores' should be a dict")
```

#### How Ignore Rules Are Applied

**Location**: [analyze_plan.py#L130-200](../../analyze_plan.py) (_get_changed_attributes method)

The ignore logic happens during change detection:

```python
# Build combined ignore set (global + resource-specific)
ignore_set = self.ignore_fields.copy()  # Contains DEFAULT_IGNORE_FIELDS + custom global ignores
if resource_type in self.resource_specific_ignores:
    ignore_set.update(self.resource_specific_ignores[resource_type])

# Filter out ignored values and track what was ignored
real_changes = {}
for k, v in changes_dict.items():
    if k in self.DEFAULT_IGNORE_FIELDS:
        # Skip default ignored fields without tracking
        continue
    elif k in ignore_set:
        # Track this ignored change
        if resource_type not in self.ignored_changes:
            self.ignored_changes[resource_type] = {}
        if k not in self.ignored_changes[resource_type]:
            self.ignored_changes[resource_type][k] = []
        self.ignored_changes[resource_type][k].append(resource_address)
    else:
        # This is a real change
        real_changes[k] = v
```

**DEFAULT_IGNORE_FIELDS** (Line 37):
```python
DEFAULT_IGNORE_FIELDS = {
    'id', 'etag', 'default_hostname', 
    'outbound_ip_addresses', 'outbound_ip_address_list',
    'possible_outbound_ip_addresses', 'possible_outbound_ip_address_list'
}
```

**Key Finding**: Ignore rules are applied **at the top-level attribute level only**. Nested attributes are not individually filtered.

### Current Implementation in `multi_env_comparator.py`

**Location**: Lines 518-550 (_apply_ignore_config method)

```python
def _apply_ignore_config(self, config: Dict, resource_type: str) -> Dict:
    """Apply ignore configuration to filter out ignored fields."""
    if not self.ignore_config:
        return config
    
    import copy
    filtered_config = copy.deepcopy(config)
    
    # Get ignore rules for this resource type
    ignore_rules = self.ignore_config.get('ignore_fields', {})
    global_ignore = ignore_rules.get('*', [])
    type_specific_ignore = ignore_rules.get(resource_type, [])
    
    fields_to_ignore = set(global_ignore + type_specific_ignore)
    
    # Remove ignored fields
    for field in fields_to_ignore:
        if field in filtered_config:
            del filtered_config[field]
    
    return filtered_config
```

**Current Schema Mismatch**: The `multi_env_comparator.py` expects a different schema:
```json
{
  "ignore_fields": {
    "*": ["global_field1", "global_field2"],
    "aws_instance": ["specific_field"]
  }
}
```

This differs from `analyze_plan.py` which uses `global_ignores` and `resource_ignores`.

**Location of Application**: Lines 500-506 (build_comparisons method)

```python
# Add config from each environment (with ignore config applied)
for env in self.environments:
    config = env.before_values.get(address)
    config_raw = env.before_values_raw.get(address)
    
    if config is not None and self.ignore_config:
        config = self._apply_ignore_config(config, resource_type)
    if config_raw is not None and self.ignore_config:
        config_raw = self._apply_ignore_config(config_raw, resource_type)
```

**Critical Finding**: Ignore config is applied to BOTH masked config AND raw config before comparison.

### Refactoring Recommendation

**Create a shared utility module**: `ignore_utils.py`

This should contain:
1. Schema validation for ignore config files
2. Parser that handles both list and dict formats for `global_ignores` and `resource_ignores`
3. Function to build combined ignore set for a given resource type
4. Function to apply ignore rules to a configuration dict (top-level only)

**Signature**:
```python
def load_ignore_config(config_path: str) -> Dict:
    """Load and validate ignore configuration."""

def build_ignore_set(resource_type: str, global_ignores: Set, 
                     resource_specific_ignores: Dict) -> Set:
    """Build combined ignore set for a resource type."""

def apply_ignore_rules(config: Dict, ignore_fields: Set) -> Dict:
    """Remove ignored fields from configuration."""
```

---

## 2. HTML Generation Architecture

### Current Structure (MultiEnvReport.generate_html)

**Location**: Lines 563-700+ in [multi_env_comparator.py](../../multi_env_comparator.py)

#### Table-Based Columnar Layout

The HTML uses a **CSS Grid** layout for multi-column comparison:

```python
html_parts.append('        .change-diff { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }')
```

Each environment gets its own column (`.diff-column`):
```python
for idx, env_label in enumerate(env_labels):
    config = rc.env_configs.get(env_label)
    html_parts.append('                        <div class="diff-column">')
    html_parts.append(f'                            <div class="diff-header">{env_label}</div>')
    html_parts.append('                            <div class="env-content">')
    # ... render config ...
    html_parts.append('                            </div>')
    html_parts.append('                        </div>')
```

#### Full JSON Rendering Per Environment

Currently, **entire resource configuration** is rendered as JSON for each environment:

**Lines 746-762**:
```python
# First environment (baseline) shows blue-highlighted diff
if idx == 0:
    # Find next available environment to compare against
    next_config = None
    for next_idx in range(1, len(env_labels)):
        next_config = rc.env_configs.get(env_labels[next_idx])
        if next_config is not None:
            break
    
    if next_config is not None:
        # Show baseline with blue highlighting
        before_html, _ = _highlight_json_diff(config, next_config)
        # Replace red/green classes with blue for baseline
        baseline_html = (before_html
            .replace('class="removed"', 'class="baseline-removed"')
            .replace('class="added"', 'class="baseline-added"')
            .replace('char-added', 'baseline-char-added')
            .replace('char-removed', 'baseline-char-removed'))
        html_parts.append(f'                                {baseline_html}')
```

**Lines 764-780**:
```python
else:
    # Non-baseline environments: show character-level diff against baseline
    if baseline_config is None:
        # Baseline doesn't have this resource, show as added
        config_json = json.dumps(config, indent=2, sort_keys=True)
        # ... show all lines as "added" ...
    else:
        # Generate character-level diff HTML
        _, after_html = _highlight_json_diff(baseline_config, config)
        html_parts.append(f'                                {after_html}')
```

**Helper Function**: `_highlight_json_diff` (Lines 47-130+)

This function:
1. Converts configs to formatted JSON strings
2. Splits into lines
3. Uses `difflib.SequenceMatcher` to find line-level differences
4. For replaced lines with similar content, applies character-level highlighting
5. Returns `(before_html, after_html)` tuples

#### Collapsible Resource Blocks

Each resource is wrapped in a collapsible section:

```python
html_parts.append('            <div class="resource-change">')
html_parts.append('                <div class="resource-change-header" onclick="toggleResource(this)">')
html_parts.append('                    <span class="toggle-icon collapsed">▼</span>')
html_parts.append(f'                    <span class="resource-name">{rc.resource_address}</span>')
html_parts.append(f'                    <span class="resource-status {status_class}">{status_text}</span>')
```

JavaScript handles expand/collapse via CSS class toggling.

#### Where to Inject Attribute-Level Rendering

**Injection Point**: Inside the `for idx, env_label in enumerate(env_labels):` loop at **Line 719**

**Current**:
```python
html_parts.append('                            <div class="env-content">')
# ... full JSON rendering ...
html_parts.append('                            </div>')
```

**Proposed**:
```python
html_parts.append('                            <div class="env-content">')

# Check if attribute-level view should be used
if self.attribute_level_view:
    # Render attribute-level diff table
    self._render_attribute_level_diff(html_parts, rc, env_label, baseline_config)
else:
    # Original full JSON rendering
    # ... existing code ...
    
html_parts.append('                            </div>')
```

---

## 3. Diff Detection Mechanism

### ResourceComparison Class

**Location**: Lines 294-459 in [multi_env_comparator.py](../../multi_env_comparator.py)

#### Data Structure

```python
class ResourceComparison:
    def __init__(self, resource_address: str, resource_type: str):
        self.resource_address = resource_address
        self.resource_type = resource_type
        self.env_configs: Dict[str, Optional[Dict]] = {}        # Masked configs (for display)
        self.env_configs_raw: Dict[str, Optional[Dict]] = {}   # Unmasked configs (for comparison)
        self.is_present_in: Set[str] = set()
        self.has_differences = False
```

**Critical Design**: Maintains TWO versions of each config:
1. **env_configs**: Sensitive values masked with `[SENSITIVE]` - used for HTML rendering
2. **env_configs_raw**: Original unmasked values - used for diff detection

#### Difference Detection (Lines 326-350)

```python
def detect_differences(self) -> None:
    """Detect if configurations differ across environments using RAW unmasked values."""
    # Get all non-None RAW configs for accurate comparison
    raw_configs = [cfg for cfg in self.env_configs_raw.values() if cfg is not None]
    
    # If resource exists in some but not all environments, that's a difference
    total_envs = len(self.env_configs_raw)
    if len(raw_configs) < total_envs:
        self.has_differences = True
        return
    
    if len(raw_configs) <= 1:
        self.has_differences = False
        return
    
    # Compare first config with all others using RAW values
    baseline = json.dumps(raw_configs[0], sort_keys=True)
    for cfg in raw_configs[1:]:
        if json.dumps(cfg, sort_keys=True) != baseline:
            self.has_differences = True
            return
    
    self.has_differences = False
```

**Key Algorithm**:
1. Uses **JSON string comparison** (not dict equality)
2. Compares against baseline (first environment)
3. Uses `sort_keys=True` for deterministic comparison
4. **Operates on RAW unmasked configs only**

#### env_configs vs env_configs_raw Usage

**env_configs_raw** is used for:
- Diff detection (detect_differences method)
- Marking changed sensitive values (mark_changed_sensitive_values method)

**env_configs** is used for:
- HTML rendering
- Display to users

**Data Flow** (from EnvironmentPlan.load, Lines 200-212):

```python
# Store raw version (before masking) for comparison
import copy
before_raw = copy.deepcopy(before)
self.before_values_raw[address] = before_raw

# Handle sensitive values (masks them)
before = self._process_sensitive_values(before, rc)

self.before_values[address] = before
```

### Where Ignore Filtering Should Be Applied

**Current Implementation**: Lines 500-506 in build_comparisons()

```python
for env in self.environments:
    config = env.before_values.get(address)
    config_raw = env.before_values_raw.get(address)
    
    if config is not None and self.ignore_config:
        config = self._apply_ignore_config(config, resource_type)
    if config_raw is not None and self.ignore_config:
        config_raw = self._apply_ignore_config(config_raw, resource_type)
```

**Critical Finding**: Ignore filtering is applied **BEFORE** diff detection.

**Rationale**: 
- If we ignore a field, differences in that field should not trigger `has_differences = True`
- Both masked and raw configs need filtering to ensure consistency

**Risk**: If ignore config removes fields from raw but not from masked (or vice versa), comparison could be inaccurate. Current implementation avoids this by applying to both.

---

## 4. Attribute-Level Diff Strategy

### Problem Statement

Need to efficiently extract and compare **top-level attributes** across multiple environments for 100+ resources.

### Current Full-Config Comparison

**Limitation**: The current approach compares entire JSON documents as strings. To show attribute-level diffs, we need:
1. Identify which top-level keys changed
2. Show before/after values for changed keys only
3. Handle null/missing attributes gracefully
4. Maintain performance for large datasets

### Proposed Algorithm

#### Step 1: Extract Changed Top-Level Keys

For a given resource across all environments:

```python
def get_changed_top_level_keys(resource_comparison: ResourceComparison) -> Set[str]:
    """
    Identify which top-level keys differ across environments.
    
    Returns:
        Set of top-level attribute names that differ
    """
    all_keys = set()
    
    # Collect all top-level keys across environments
    for config in resource_comparison.env_configs_raw.values():
        if config is not None:
            all_keys.update(config.keys())
    
    changed_keys = set()
    
    # For each key, check if values differ across environments
    for key in all_keys:
        values = []
        for config in resource_comparison.env_configs_raw.values():
            if config is None:
                values.append(None)
            else:
                values.append(config.get(key))
        
        # Check if all values are identical
        if not all_values_equal(values):
            changed_keys.add(key)
    
    return changed_keys
```

#### Step 2: Compare Top-Level Attributes

```python
def all_values_equal(values: List[Any]) -> bool:
    """Check if all values in list are equal using JSON serialization."""
    if len(values) <= 1:
        return True
    
    # Serialize for comparison (handles nested structures)
    baseline = json.dumps(values[0], sort_keys=True)
    for val in values[1:]:
        if json.dumps(val, sort_keys=True) != baseline:
            return False
    
    return True
```

#### Step 3: Handle Null/Missing Attributes

```python
def get_attribute_value_for_env(config: Optional[Dict], key: str) -> Tuple[Any, str]:
    """
    Get attribute value and display status.
    
    Returns:
        (value, status) where status is "present", "null", or "missing"
    """
    if config is None:
        return (None, "missing")  # Resource doesn't exist
    
    if key not in config:
        return (None, "missing")  # Attribute doesn't exist
    
    value = config[key]
    if value is None:
        return (None, "null")  # Attribute is explicitly null
    
    return (value, "present")
```

#### Step 4: Render Attribute-Level Table

Proposed HTML structure:

```html
<table class="attribute-diff-table">
  <thead>
    <tr>
      <th>Attribute</th>
      <th>dev</th>
      <th>staging</th>
      <th>prod</th>
    </tr>
  </thead>
  <tbody>
    <tr class="attribute-row changed">
      <td class="attribute-name">instance_type</td>
      <td class="attribute-value">
        <span class="value-badge different">t2.micro</span>
      </td>
      <td class="attribute-value">
        <span class="value-badge different">t2.small</span>
      </td>
      <td class="attribute-value">
        <span class="value-badge different">t2.medium</span>
      </td>
    </tr>
  </tbody>
</table>
```

**CSS Classes**:
- `.attribute-row.changed` - Highlight changed attributes
- `.attribute-row.unchanged` - Gray out unchanged attributes (if showing all)
- `.value-badge.different` - Distinct value (yellow background)
- `.value-badge.identical` - Same as baseline (green background)
- `.value-badge.missing` - Attribute not present (gray)

### Performance Considerations

For 100+ resources with ~50 attributes each:
- **Time Complexity**: O(n × m × e) where:
  - n = number of resources
  - m = average attributes per resource
  - e = number of environments
- **Worst Case**: 100 × 50 × 5 = 25,000 comparisons

**Optimization**: 
1. Only compute changed keys when `has_differences = True`
2. Cache JSON serializations of repeated values
3. Use set operations for key diff detection (fast)

**Memory**: Minimal overhead - only storing sets of changed keys, not duplicating configs

### Complex Nested Values

For complex nested structures (lists, dicts), show abbreviated representation:

```python
def format_value_for_display(value: Any, max_length: int = 100) -> str:
    """Format value for attribute table display."""
    if value is None:
        return "null"
    elif isinstance(value, (bool, int, float)):
        return str(value)
    elif isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + "..."
        return value
    elif isinstance(value, list):
        return f"[list: {len(value)} items]"
    elif isinstance(value, dict):
        return f"{{dict: {len(value)} keys}}"
    else:
        return str(type(value).__name__)
```

**Expandable Details**: Add a "View Full Value" button that shows the complete JSON in a modal/collapsible section.

---

## Decision Summary & Recommendations

### 1. Ignore Configuration Refactoring

**Decision**: Create shared `ignore_utils.py` module

**Approach**:
1. Standardize on `analyze_plan.py` schema (`global_ignores`, `resource_ignores`)
2. Update `multi_env_comparator.py` to use the same schema
3. Support both list and dict formats (dict includes reasons)
4. Apply ignore filtering to BOTH `env_configs` and `env_configs_raw` before diff detection

**Code to Refactor**:
- `analyze_plan.py` lines 1833-1882 → Extract to `ignore_utils.load_ignore_config()`
- `analyze_plan.py` lines 170-187 → Extract to `ignore_utils.apply_ignore_rules()`
- `multi_env_comparator.py` lines 518-550 → Replace with `ignore_utils.apply_ignore_rules()`

**Risk**: Breaking existing multi-env comparisons that use the old `ignore_fields` schema
**Mitigation**: Support both schemas during transition, deprecate old schema

---

### 2. HTML Generation for Attribute-Level View

**Decision**: Add mode toggle for full JSON vs. attribute-level view

**Approach**:
1. Add `--attribute-level` CLI flag to `compare` subcommand
2. Store as `self.attribute_level_view` in `MultiEnvReport`
3. Inject attribute rendering at Line 730 (inside env_content div)
4. Use table-based layout for attributes (easier to scan than JSON)
5. Only show changed attributes by default (optionally show all with `--show-all-attributes`)

**Rendering Strategy**:
```python
def _render_attribute_level_diff(self, html_parts, resource_comparison, environments):
    changed_keys = self._get_changed_top_level_keys(resource_comparison)
    
    # Render table header with environment columns
    # Render each changed attribute as a row
    # Apply highlighting based on value equality
```

**Risk**: Large nested values making table cells unwieldy
**Mitigation**: Truncate complex values, add "expand" buttons for full details

---

### 3. Diff Detection Enhancement

**Decision**: No changes needed to core diff detection logic

**Rationale**:
- Current implementation correctly uses `env_configs_raw` for comparison
- JSON serialization approach is simple and reliable
- Ignore filtering is correctly applied before diff detection

**New Requirement**: Add method to extract changed top-level keys
```python
class ResourceComparison:
    def get_changed_attributes(self) -> Set[str]:
        """Return set of top-level attribute names that differ."""
```

**Risk**: None - this is purely additive

---

### 4. Attribute-Level Diff Implementation

**Decision**: Use set-based key diff with JSON value comparison

**Algorithm**:
1. Collect all top-level keys across environments → `all_keys`
2. For each key, serialize values from all environments → `json.dumps(value, sort_keys=True)`
3. Compare serialized values to detect differences
4. Return set of keys with differing values

**Performance**: O(k × e) per resource where k = number of keys, e = environments
- For 100 resources × 50 keys × 5 envs = 25,000 operations
- JSON serialization is fast (~1μs per value)
- **Total time: ~25ms** - negligible

**Null/Missing Handling**:
- `config is None` → Resource not present (gray badge)
- `key not in config` → Attribute missing (gray badge with "—")
- `config[key] is None` → Attribute is null (show "null")

**Risk**: False positives from floating-point precision differences
**Mitigation**: Consider normalizing numbers to fixed precision if needed

---

## Gotchas & Risks Identified

### 1. Schema Incompatibility

**Issue**: `multi_env_comparator.py` uses different ignore config schema than `analyze_plan.py`

**Impact**: Users can't reuse same ignore config file for both report and compare

**Solution**: Standardize on one schema, provide migration path

---

### 2. Ignore Timing

**Issue**: Must apply ignore rules BEFORE diff detection, not after

**Current**: ✅ Correctly done in `build_comparisons()` before `detect_differences()`

**Verify**: Ensure new attribute-level diff also uses filtered configs

---

### 3. Sensitive Value Masking

**Issue**: `env_configs` (masked) and `env_configs_raw` (unmasked) can diverge

**Current Mitigation**: Ignore filtering applied to both versions

**New Risk**: Attribute-level view must use `env_configs` (masked) for display, but detect changes using `env_configs_raw`

**Solution**:
```python
def _get_changed_top_level_keys(self, rc: ResourceComparison) -> Set[str]:
    # Use env_configs_raw for detection
    all_keys = set()
    for config in rc.env_configs_raw.values():
        if config is not None:
            all_keys.update(config.keys())
    # ... detect differences using raw values ...

def _render_attribute_value(self, rc: ResourceComparison, env_label: str, key: str) -> str:
    # Use env_configs for display (respects sensitive masking)
    config = rc.env_configs.get(env_label)
    if config is None or key not in config:
        return "—"
    return format_value(config[key])
```

---

### 4. Character-Level Diff for Nested Values

**Issue**: Attribute-level view shows abbreviated nested values, losing character-level diff detail

**Impact**: Users can't see exact line-by-line changes in complex attributes

**Solution**: Hybrid approach
- Default: Show abbreviated attribute table
- Click attribute row → Expand to show full JSON diff with character highlighting
- Reuse existing `_highlight_json_diff()` function

---

### 5. Top-Level Only Limitation

**Issue**: Ignore rules and attribute diff both operate at top-level only

**Example**: Can't ignore `tags.environment` or show diff for `network.vpc_id`

**Impact**: Less granular than ideal for deeply nested configs

**Future Enhancement**: Support JSONPath-like syntax for nested field selection
- Not in scope for current feature
- Document as known limitation

---

## Files Analyzed

| File | Lines Analyzed | Purpose |
|------|----------------|---------|
| [analyze_plan.py](../../analyze_plan.py) | 1-250, 1833-1920 | Ignore config parsing, ignore application logic |
| [multi_env_comparator.py](../../multi_env_comparator.py) | 1-876 (full file) | HTML generation, diff detection, resource comparison |
| [ignore_config.example.json](../../ignore_config.example.json) | 1-100 | Schema understanding |

---

## Next Steps

1. **Create `ignore_utils.py`** module with shared ignore configuration logic
2. **Add `get_changed_attributes()` method** to `ResourceComparison` class
3. **Implement `_render_attribute_level_diff()` method** in `MultiEnvReport`
4. **Add CLI flag** `--attribute-level` to compare subcommand
5. **Write unit tests** for attribute diff detection with null/missing/present cases
6. **Update documentation** to explain attribute-level view and ignore config
