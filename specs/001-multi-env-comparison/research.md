# Phase 0: Research & Technical Decisions

**Feature**: Multi-Environment Terraform Plan Comparison
**Date**: 2026-01-13

## Overview

This document captures research findings and technical decisions for implementing multi-environment comparison functionality. Research focused on CLI architecture patterns, multi-column HTML layouts, and integration with existing codebase.

## Research Areas

### 1. Python Subcommand CLI Architecture

**Question**: How to implement AWS CLI-style subcommands in Python with argparse?

**Decision**: Use argparse subparsers with isolated argument definitions per subcommand

**Rationale**:
- argparse natively supports subcommands via `add_subparsers()` method
- Provides clean separation: each subcommand gets its own parser with distinct arguments
- Maintains backward compatibility by preserving existing argument structure
- Standard pattern used by git, aws-cli, kubectl, and other professional CLI tools

**Implementation Pattern**:
```python
def main():
    parser = argparse.ArgumentParser(description='Terraform Plan Analyzer')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # report subcommand (existing single-plan behavior)
    report_parser = subparsers.add_parser('report', help='Analyze single plan')
    report_parser.add_argument('plan_file', help='Plan JSON file')
    report_parser.add_argument('--html', help='Generate HTML report')
    # ... all existing flags
    
    # compare subcommand (new multi-env behavior) 
    compare_parser = subparsers.add_parser('compare', help='Compare multiple environments')
    compare_parser.add_argument('plan_files', nargs='+', help='2+ plan files')
    compare_parser.add_argument('--html', help='Generate HTML report')
    compare_parser.add_argument('--env-names', help='Environment labels')
    # ... multi-env specific flags
```

**Alternatives Considered**:
- Flag-based mode switching (`--compare`): Rejected - less clear separation, harder to validate incompatible flag combinations
- Separate scripts (compare_plans.py): Rejected - code duplication, harder to maintain shared logic
- Click library: Rejected - adds external dependency, argparse sufficient for requirements

### 2. Multi-Column HTML Table Layout

**Question**: How to display 2-5 environment columns side-by-side with nested JSON structures?

**Decision**: Use responsive HTML table with expand/collapse controls for nested structures

**Rationale**:
- Tables provide natural columnar alignment for comparison
- CSS Grid considered but tables better for variable column count
- Existing generate_html_report.py uses tables - consistency important
- Nested structures collapsed by default prevents horizontal overflow
- JavaScript for expand/collapse already in existing HTML reports

**Implementation Approach**:
```html
<table class="comparison-table">
  <thead>
    <tr>
      <th>Resource</th>
      <th>Dev</th>
      <th>Staging</th>
      <th>Prod</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>aws_instance.web</td>
      <td><div class="collapsible">...</div></td>
      <td><div class="collapsible">...</div></td>
      <td><div class="collapsible">...</div></td>
    </tr>
  </tbody>
</table>
```

**Alternatives Considered**:
- CSS Grid: More modern but harder to implement responsive variable columns
- Horizontal scrolling cards: Less scannable for comparison, harder to align
- Vertical stacking: Defeats purpose of side-by-side comparison

### 3. Reusing Existing Diff Highlighting Logic

**Question**: Can existing diff highlighting from generate_html_report.py be reused for multi-environment comparison?

**Decision**: Yes, with minor adaptation for multi-way comparison

**Rationale**:
- Existing `highlight_json_diff(before, after)` works for 2-way comparison
- For N-way comparison, need to identify which environments differ
- Can apply pairwise comparison logic: compare each env to "baseline" (first env)
- Reuse existing character-level diff highlighting CSS classes
- Same visual language users are familiar with

**Implementation Strategy**:
1. Extract baseline configuration (first environment or designated reference)
2. For each other environment, run pairwise diff against baseline  
3. Highlight cells where configuration differs from baseline
4. Use existing highlight_json_diff() function - no reinvention

**Alternatives Considered**:
- Complete rewrite of diff logic: Rejected - code duplication, unnecessary
- Show all pairwise diffs: Rejected - too complex, N² comparisons for N environments
- No highlighting: Rejected - defeats purpose of quick visual identification

### 4. HCL Resolution for Multi-Environment

**Question**: How to handle HCL variable resolution when comparing multiple environments?

**Decision**: Single --tf-dir with per-environment .tfvars files via --tfvars-files flag

**Rationale**:
- Common pattern: same Terraform code with different tfvars per environment
- Clarification confirmed this is the expected workflow (not separate directories)
- Existing HCLValueResolver supports tfvars file input
- Order-based matching: tfvars files provided in same order as plan files

**Implementation Pattern**:
```bash
python analyze_plan.py compare dev.json staging.json prod.json \
  --tf-dir ./terraform \
  --tfvars-files dev.tfvars staging.tfvars prod.tfvars \
  --html
```

**Alternatives Considered**:
- Multiple --tf-dir flags: Rejected - less common pattern, clarification ruled it out
- Auto-detect tfvars: Rejected - too magical, explicit is better
- No HCL resolution for compare: Rejected - users expect consistent feature set

### 5. Resource Matching Across Environments

**Question**: How to match resources across environments when addresses might differ?

**Decision**: Strict resource address matching only - no fuzzy matching

**Rationale**:
- Clarification confirmed: renamed resources treated as separate (one missing, one new)
- Terraform resource address is canonical identifier
- Fuzzy matching based on configuration is error-prone and computationally expensive
- Users expect deterministic behavior based on resource addresses
- Edge case of renamed resources is rare and intentional when it occurs

**Algorithm**:
1. Collect all unique resource addresses across all environments
2. For each address, gather configuration from each environment (or None if missing)
3. Display in table row with N/A for missing environments
4. Highlight differences where configs don't match

**Alternatives Considered**:
- Configuration similarity matching: Rejected per clarification, too complex
- User-provided mapping file: Rejected - over-engineering for rare edge case
- Ignore resources missing from any environment: Rejected - hides important drift information

### 6. Sensitive Value Handling

**Question**: How to display sensitive values in multi-environment comparison?

**Decision**: Respect --show-sensitive flag; highlight differences even when masked

**Rationale**:
- Clarification confirmed: use existing flag behavior for consistency
- Critical insight: knowing *that* sensitive values differ is operationally important
- Example: different DB passwords between dev/prod is expected and good
- Example: different passwords between prod replicas might indicate misconfiguration
- Visual indicator: highlight masked values that differ (e.g., "[SENSITIVE] ⚠️" in yellow)

**Implementation**:
- Default: mask sensitive values as "[SENSITIVE]"
- When comparing: check if underlying values differ (even if masked)
- Apply diff highlighting to masked values if they differ
- If --show-sensitive: reveal actual values but maintain highlighting

**Alternatives Considered**:
- Always hide differences in sensitive values: Rejected - loses critical operational insight
- Always show sensitive values: Rejected - security risk, inconsistent with existing behavior
- No sensitive value support: Rejected - regression from existing functionality

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| CLI Architecture | argparse subparsers (report/compare) | Clean separation, standard pattern, backward compatible |
| HTML Layout | Responsive table with collapsible nested structures | Consistent with existing reports, handles variable columns |
| Diff Highlighting | Reuse existing highlight_json_diff() | No code duplication, familiar visual language |
| HCL Resolution | Single --tf-dir + --tfvars-files | Matches common workflow, per clarification |
| Resource Matching | Strict address matching, no fuzzy logic | Deterministic, per clarification |
| Sensitive Values | Respect --show-sensitive, highlight masked diffs | Operational insight without security compromise |

## Open Questions

None - all clarifications obtained during spec clarification phase.
