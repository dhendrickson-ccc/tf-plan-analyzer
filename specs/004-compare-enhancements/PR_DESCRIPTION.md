# Compare Subcommand Enhancements

## Summary

Adds ignore file support and attribute-level diff views to the `compare` subcommand, making multi-environment Terraform plan comparisons cleaner and more actionable.

## Changes

### New Features

1. **Ignore File Support**
   - Filter out known acceptable differences using `--config ignore_config.json`
   - Supports global and resource-specific ignore rules
   - Same configuration format as existing single-plan report subcommand
   - Example: Ignore environment-specific tags, descriptions, or dynamic blocks

2. **Attribute-Level Diff View**
   - HTML reports now show only changed attributes instead of full resource JSON
   - Clean side-by-side tables with one column per environment
   - Preserves character-level diff highlighting for primitive values
   - Maintains sensitive value protection with badges
   - Reduces noise and clutter in multi-environment comparisons

3. **Combined Functionality**
   - Ignore rules automatically filter the attribute-level view
   - Seamless integration between both features

### Files Added
- `ignore_utils.py` - Shared ignore configuration utilities (297 lines)
- `test_ignore_utils.py` - Unit tests for ignore logic (362 lines)
- `test_e2e_compare_enhancements.py` - E2E tests for all features (371 lines)
- `test_compare_enhancements_unit.py` - Unit tests for attribute diffs (119 lines)

### Files Modified
- `multi_env_comparator.py` - Attribute-level diff rendering
- `analyze_plan.py` - Ignore config integration

## Usage Examples

### Filter Out Tags
```bash
python analyze_plan.py compare dev.json staging.json prod.json \
  --config ignore_config.json --html report.html
```

**ignore_config.json:**
```json
{
  "global_ignores": {
    "tags": "Tags vary by environment"
  }
}
```

### Resource-Specific Ignores
```json
{
  "resource_specific_ignores": {
    "azurerm_monitor_metric_alert": {
      "description": "Descriptions change frequently"
    }
  }
}
```

## Testing

- **158 tests passing** (55 new, 103 existing)
- **100% backward compatible** - All existing tests pass unchanged
- **Performance**: <1s for 100+ resources (target: <3s)
- **Manual validation**: Verified with real Terraform plan data

### Test Coverage
- 33 unit tests for ignore utilities
- 7 e2e tests for ignore file support
- 5 e2e tests for attribute-level diff view
- 6 e2e tests for combined functionality
- 4 unit tests for attribute diff logic

## Breaking Changes

None. Changes are opt-in via `--config` flag. Default behavior unchanged.

## Review Notes

- HTML-only feature: Attribute-level view affects HTML output only; text format unchanged for automation compatibility
- Architecture: Ignore filtering integrated directly into attribute comparison for automatic filtering
- Error handling: Proper exit codes (1 for file not found, 2 for malformed JSON)

## Commits

1. `9c14b7c` - Implement US1: Ignore file support
2. `516bf87` - Implement US2: Attribute-level diff view
3. `ee4adeb` - Implement US3: Combined functionality
4. `5f4c216` - Complete Phase 6: Polish and validation

## Checklist

- [x] All tests passing
- [x] Backward compatible
- [x] Performance validated
- [x] Manual testing complete
- [x] Code follows existing patterns
- [x] No debug logging
