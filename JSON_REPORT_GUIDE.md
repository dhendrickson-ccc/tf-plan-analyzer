# JSON Report Guide

## Overview

The JSON report provides a machine-readable analysis of Terraform plan changes, designed for programmatic consumption in CI/CD pipelines, automated validation, and integration with other tools.

## Report Structure

### `metadata`
Contains information about the report generation and analysis configuration.

```json
{
  "generated_at": "2026-01-12T10:30:00.123456",
  "plan_file": "tfplan-test-2.json",
  "analyzer_version": "1.0",
  "ignore_azure_casing": true
}
```

- **generated_at**: ISO 8601 timestamp of when the report was created
- **plan_file**: Path to the Terraform plan file that was analyzed
- **analyzer_version**: Version of the analyzer tool
- **ignore_azure_casing**: Whether case-insensitive comparison was enabled for Azure resource IDs

### `summary`
High-level statistics about the plan changes.

```json
{
  "total": 150,
  "created": 5,
  "imported": 0,
  "updated": 45,
  "tag_only": 30,
  "config_changes": 15,
  "deleted": 2,
  "ignored_changes": 68
}
```

- **total**: Total number of resources in the plan
- **created**: New resources being created
- **imported**: Resources being imported into Terraform state
- **updated**: Total resources being updated (tag_only + config_changes)
- **tag_only**: Resources with only tag changes
- **config_changes**: Resources with configuration changes beyond tags
- **deleted**: Resources being destroyed
- **ignored_changes**: Total number of changes filtered out by ignore rules

### `created_resources`
Array of resource addresses for newly created resources.

```json
[
  "azurerm_storage_account.example",
  "azurerm_key_vault.vault"
]
```

### `imported_resources`
Array of resource addresses being imported (resources that exist but are being brought under Terraform management).

```json
[
  "azurerm_resource_group.existing"
]
```

### `updated_resources`
Detailed information about resources with configuration changes.

```json
[
  {
    "address": "azurerm_monitor_metric_alert.cpu",
    "changes": [
      {
        "attribute": "description",
        "before": "Old description",
        "after": "New description",
        "is_known_after_apply": false
      },
      {
        "attribute": "scopes",
        "before": null,
        "after": "(known after apply)",
        "is_known_after_apply": true
      },
      {
        "attribute": "backend_address_pool_id",
        "before": "/subscriptions/.../BackendPool",
        "after": "${azurerm_lb_backend_address_pool.pool.id}",
        "is_known_after_apply": true
      }
    ]
  }
]
```

#### Change Object Fields:
- **address**: Full resource address (type.name)
- **changes**: Array of attribute changes
  - **attribute**: Name of the changed attribute
  - **before**: Previous value (null if not set)
  - **after**: New value
  - **is_known_after_apply**: Boolean flag indicating:
    - `true` if value is `"(known after apply)"` (computed during apply)
    - `true` if value contains HCL interpolations like `${...}` (resolved from .tf files but contains variable references)
    - `false` if value is a concrete, known value from the plan

### `tag_only_updates`
Array of resources that only have tag changes (no functional configuration changes).

```json
[
  "azurerm_resource_group.rg1",
  "azurerm_storage_account.storage"
]
```

### `deleted_resources`
Array of resources being destroyed.

```json
[
  "azurerm_old_resource.deprecated"
]
```

### `ignored_changes`
Changes that were filtered out based on ignore configuration, grouped by field name.

```json
{
  "action": {
    "reason": "Dynamic block conversion causes inconsequential changes",
    "resources": [
      {
        "address": "azurerm_monitor_metric_alert.cpu",
        "resource_type": "azurerm_monitor_metric_alert"
      },
      {
        "address": "azurerm_monitor_metric_alert.memory",
        "resource_type": "azurerm_monitor_metric_alert"
      }
    ]
  },
  "tags": {
    "reason": "Tags are managed separately",
    "resources": [...]
  }
}
```

- **Key** (e.g., "action", "tags"): The field name that was ignored
- **reason**: Explanation for why this field is ignored (from ignore config)
- **resources**: Array of affected resources
  - **address**: Full resource address
  - **resource_type**: Type of resource (useful for filtering)

## Usage Examples

### Using `jq` to Query the Report

```bash
# Get summary statistics
jq '.summary' report.json

# Count resources by change type
jq '.summary | {created, updated, deleted}' report.json

# List all created resources
jq '.created_resources[]' report.json

# Find resources with specific attribute changes
jq '.updated_resources[] | select(.changes[].attribute == "description")' report.json

# Get all changes that are "known after apply"
jq '.updated_resources[].changes[] | select(.is_known_after_apply == true)' report.json

# Count ignored changes by field
jq '.ignored_changes | to_entries | map({field: .key, count: (.value.resources | length)})' report.json

# Find all resources affected by a specific ignored field
jq '.ignored_changes.action.resources[].address' report.json
```

### Python Script Example

```python
import json

with open('tfplan-test-2.report.json') as f:
    report = json.load(f)

# Check if plan has any destructive changes
if report['summary']['deleted'] > 0:
    print(f"⚠️  Warning: {report['summary']['deleted']} resources will be deleted!")
    for resource in report['deleted_resources']:
        print(f"  - {resource}")

# Find changes that need manual review (known after apply)
manual_review = []
for resource in report['updated_resources']:
    for change in resource['changes']:
        if change['is_known_after_apply']:
            manual_review.append({
                'resource': resource['address'],
                'attribute': change['attribute']
            })

if manual_review:
    print(f"\n📋 {len(manual_review)} attributes require manual review")
```

### CI/CD Pipeline Integration

```bash
#!/bin/bash
# Example CI/CD validation script

REPORT="tfplan.report.json"

# Generate the report
python3 analyze_plan.py tfplan.json --json "$REPORT" --ignore-azure-casing

# Check for destructive changes
DELETED=$(jq '.summary.deleted' "$REPORT")
if [ "$DELETED" -gt 0 ]; then
  echo "❌ Plan contains $DELETED resource deletions - manual approval required"
  exit 1
fi

# Check for too many changes (potential issue)
TOTAL_CHANGES=$(jq '.summary.created + .summary.updated + .summary.deleted' "$REPORT")
if [ "$TOTAL_CHANGES" -gt 100 ]; then
  echo "⚠️  Large change set detected: $TOTAL_CHANGES changes"
  echo "Please review carefully"
fi

# Report on ignored changes
IGNORED=$(jq '.summary.ignored_changes' "$REPORT")
echo "ℹ️  $IGNORED changes were filtered by ignore rules"

echo "✅ Plan validation passed"
```

## Understanding `is_known_after_apply`

This flag helps distinguish between three types of values:

1. **`false` - Concrete values**: The exact value is known from the Terraform plan
   ```json
   {
     "attribute": "enabled",
     "before": false,
     "after": true,
     "is_known_after_apply": false
   }
   ```

2. **`true` - Computed values**: Value will be determined during `terraform apply`
   ```json
   {
     "attribute": "id",
     "before": null,
     "after": "(known after apply)",
     "is_known_after_apply": true
   }
   ```

3. **`true` - HCL-resolved with variables**: Value was resolved from .tf files but contains variable interpolations
   ```json
   {
     "attribute": "subnet_id",
     "before": "/subscriptions/.../old-subnet",
     "after": "${azurerm_subnet.main.id}",
     "is_known_after_apply": true
   }
   ```

## Filtering and Validation Strategies

### Recommended Checks

1. **Destructive Changes**: Always review `deleted_resources` before approving
2. **Unknown Values**: Review resources with `is_known_after_apply: true` for critical attributes
3. **Large Change Sets**: Alert when `summary.updated` exceeds threshold
4. **Ignored Changes**: Monitor `ignored_changes` to ensure ignore rules are appropriate
5. **Type-Specific Rules**: Filter by `resource_type` for environment-specific validation

### Example Validations

```bash
# Ensure no production databases are being deleted
jq -e '.deleted_resources[] | select(contains("azurerm_mssql_database"))' report.json && \
  echo "❌ Database deletion detected!" || echo "✅ No databases being deleted"

# Check for security-sensitive changes
jq '.updated_resources[] | select(.address | contains("azurerm_key_vault"))' report.json

# Validate that certain fields are always ignored
jq -e '.ignored_changes.tags' report.json && \
  echo "✅ Tags are being ignored as expected" || echo "⚠️  Tag changes not ignored"
```

## Tips for Effective Use

1. **Version Control**: Commit the JSON report alongside your plan for audit trails
2. **Diff Reports**: Compare reports across environments to ensure consistency
3. **Automated Gates**: Use summary counts as quality gates in CI/CD
4. **Change Tracking**: Track `ignored_changes` over time to identify noise patterns
5. **Documentation**: Use `reason` fields in ignored changes to document why fields are ignored

## Integration with Other Tools

- **Slack/Teams**: Post summary statistics to chat channels
- **JIRA**: Create tickets for resources with `is_known_after_apply` flags
- **Monitoring**: Track change metrics over time
- **Policy as Code**: Validate against OPA/Sentinel policies
- **Custom Dashboards**: Visualize plan trends
