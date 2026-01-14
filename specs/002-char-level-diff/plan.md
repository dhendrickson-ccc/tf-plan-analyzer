# Implementation Plan: Character-Level Diff Highlighting for Multi-Environment Comparison

**Feature**: Character-Level Diff Highlighting  
**Branch**: `002-char-level-diff`  
**Created**: January 14, 2026

## Overview

This feature adds character-level diff highlighting to multi-environment comparison HTML reports, making it easier to spot subtle configuration differences between environments (e.g., "t2.micro" vs "t2.small").

## Tech Stack

### Language & Runtime
- **Python 3.9+**: Existing project language
- **Standard Library**: `difflib.SequenceMatcher` for similarity detection, `html` for escaping, `json` for serialization

### Dependencies
- No new external dependencies required
- Leverages existing `generate_html_report.py` implementation

### Files to Modify
- `multi_env_comparator.py`: Add character-level diff generation to `MultiEnvReport.generate_html()`
- Potentially create new module or import from `generate_html_report.py`

### Files to Create
- No new files required (may refactor existing code for reuse)

## Project Structure

```
tf-plan-analyzer/
├── multi_env_comparator.py         # MODIFY: Add char-level diff to HTML generation
├── generate_html_report.py          # REFERENCE: Existing highlight_json_diff() function
├── test_e2e_multi_env.py           # MODIFY: Add tests for char-level diff
└── specs/002-char-level-diff/
    ├── spec.md                      # Feature specification
    ├── plan.md                      # This file
    └── tasks.md                     # Task breakdown (to be generated)
```

## Design Decisions

### 1. Code Reuse Strategy
**Decision**: Extract `highlight_json_diff()` from `generate_html_report.py` into a shared utility function that both `report` and `compare` subcommands can use.

**Rationale**: 
- DRY principle - avoid duplicating the complex diff logic
- Consistency - ensures identical highlighting behavior across both subcommands
- Maintainability - single source of truth for diff algorithm

**Implementation**:
- Option A: Create `diff_utils.py` with `highlight_json_diff()` and import in both files
- Option B: Import directly from `generate_html_report.py` into `multi_env_comparator.py`
- **Chosen**: Option B (simpler, no new files)

### 2. Baseline Environment Selection
**Decision**: First environment (leftmost column) is always the baseline. All other environments show diffs relative to the first environment.

**Rationale**:
- Clear, predictable behavior
- Avoids confusion of pairwise comparison (env2 vs env1, env3 vs env2)
- Matches user mental model of "compare everything to production" or "compare to dev"

**Implementation**:
- When generating HTML, iterate through environments
- First environment: render plain JSON without highlighting
- Subsequent environments: call `highlight_json_diff(baseline_config, current_config)`

### 3. Display Strategy
**Decision**: Baseline environment shows plain JSON, all other environments show character-level diff highlighting.

**Rationale**:
- Reduces visual clutter
- Makes it immediately obvious which is the reference configuration
- Focuses attention on what differs from the baseline

**CSS Classes**: Reuse existing `.added`, `.removed`, `.unchanged` classes from `report` subcommand

### 4. Missing Field Handling
**Decision**: When a field exists in one environment but not another, highlight the entire field line as added/removed (not character-level diff).

**Rationale**:
- Character-level diff requires two strings to compare
- Field-level highlighting is clearer for completely missing fields
- Matches git diff conventions (added/removed lines)

### 5. Similarity Threshold
**Decision**: Apply character-level diff only to lines that are >50% similar (using `difflib.SequenceMatcher`).

**Rationale**:
- Existing behavior in `report` subcommand
- Prevents confusing character-level diffs for completely different values
- Falls back to line-level highlighting for dissimilar lines

## Architecture

### Current State (Before)
```python
# In multi_env_comparator.py, line ~475
for env_label in env_labels:
    config = rc.env_configs.get(env_label)
    if config is None:
        html_parts.append('NOT PRESENT')
    else:
        config_json = json.dumps(config, indent=2, sort_keys=True)
        html_parts.append(f'<pre class="config-json">{config_json}</pre>')
```

### Target State (After)
```python
# In multi_env_comparator.py
from generate_html_report import highlight_json_diff

# Get baseline (first environment's config)
baseline_config = rc.env_configs.get(env_labels[0])

for idx, env_label in enumerate(env_labels):
    config = rc.env_configs.get(env_label)
    
    if config is None:
        html_parts.append('NOT PRESENT')
    elif idx == 0:
        # First environment: plain JSON (no highlighting)
        config_json = json.dumps(config, indent=2, sort_keys=True)
        html_parts.append(f'<pre class="config-json">{config_json}</pre>')
    else:
        # Non-baseline: apply character-level diff vs baseline
        _, highlighted_html = highlight_json_diff(baseline_config, config)
        html_parts.append(highlighted_html)
```

## Testing Strategy

### Unit Tests
Not needed - the core `highlight_json_diff()` function is already tested in the `report` subcommand.

### End-to-End Tests
Add to `test_e2e_multi_env.py`:
1. Test character-level diff with subtle differences (e.g., instance type change)
2. Test baseline environment shows plain JSON
3. Test non-baseline environments show highlighted diffs
4. Test field-level highlighting for missing fields
5. Test identical configs show no highlighting
6. Test deep nesting still applies character-level diff
7. Test sensitive values don't show character diffs

### Manual Testing
- Generate comparison reports with real Terraform plans
- Verify visual consistency with `report` subcommand diffs
- Test with 2, 3, 4, and 5 environments
- Verify collapsible UI still works

## Performance Considerations

- Character-level diff adds minimal overhead (already used in `report` subcommand)
- `difflib.SequenceMatcher` is O(n*m) but operates on individual lines, not entire configs
- Target: <10 seconds for 100 resources across 5 environments (same as current)
- No additional memory overhead beyond what's already used for config storage

## Rollout Plan

1. **Phase 1**: Extract/import `highlight_json_diff()` function
2. **Phase 2**: Modify `MultiEnvReport.generate_html()` to apply character-level diff
3. **Phase 3**: Add end-to-end tests
4. **Phase 4**: Verify no regression in existing tests
5. **Phase 5**: Manual testing with real plans

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing HTML layout | High | Verify CSS classes are preserved, test collapsible UI |
| Performance degradation | Medium | Benchmark with 100 resources, optimize if needed |
| Visual inconsistency with report subcommand | Medium | Reuse exact same `highlight_json_diff()` function |
| Edge case handling (missing fields, sensitive values) | Low | Explicit handling in code, covered by tests |

## Success Criteria

- ✅ All existing tests pass (no regression)
- ✅ Character-level diff visually matches `report` subcommand
- ✅ Users can identify exact character differences within 5 seconds
- ✅ HTML generation completes in <10 seconds for 100 resources across 5 environments
- ✅ New end-to-end tests cover all edge cases

## Open Questions

None - all clarifications completed in spec.md
