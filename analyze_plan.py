#!/usr/bin/env python3
"""
Terraform Plan Analyzer
Analyzes terraform plan JSON files to categorize resource changes.
"""

import argparse
import html
import json
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional

try:
    from hcl_value_resolver import HCLValueResolver
except ImportError:
    HCLValueResolver = None  # Optional dependency


class TerraformPlanAnalyzer:
    """Analyzes terraform plan JSON files."""
    
    # Default fields to ignore when detecting changes (computed values)
    DEFAULT_IGNORE_FIELDS = {
        'id', 'etag', 'default_hostname', 
        'outbound_ip_addresses', 'outbound_ip_address_list',
        'possible_outbound_ip_addresses', 'possible_outbound_ip_address_list'
    }
    
    def __init__(self, plan_file: str, custom_ignore_fields: Set[str] = None, 
                 resource_specific_ignores: Dict[str, Set[str]] = None,
                 global_ignore_reasons: Dict[str, str] = None,
                 resource_ignore_reasons: Dict[str, Dict[str, str]] = None,
                 hcl_resolver: Optional['HCLValueResolver'] = None,
                 ignore_azure_casing: bool = False):
        self.plan_file = Path(plan_file)
        self.plan_data = None
        self.resource_changes = []
        
        # Combine default and custom ignore fields (global)
        self.ignore_fields = self.DEFAULT_IGNORE_FIELDS.copy()
        if custom_ignore_fields:
            self.ignore_fields.update(custom_ignore_fields)
        
        # Resource-type-specific ignores
        self.resource_specific_ignores = resource_specific_ignores or {}
        
        # Reasons for ignores
        self.global_ignore_reasons = global_ignore_reasons or {}
        self.resource_ignore_reasons = resource_ignore_reasons or {}
        
        # Track what was actually ignored during analysis
        self.ignored_changes = {}
        
        # HCL resolver for "known after apply" values
        self.hcl_resolver = hcl_resolver
        
        # Whether to ignore casing differences in Azure resource IDs
        self.ignore_azure_casing = ignore_azure_casing

        
    def load_plan(self) -> None:
        """Load the terraform plan JSON file."""
        with open(self.plan_file, 'r') as f:
            self.plan_data = json.load(f)
        self.resource_changes = self.plan_data.get('resource_changes', [])
        
    def analyze(self) -> Dict[str, List]:
        """
        Analyze the plan and categorize all resources.
        
        Returns:
            Dict with keys: created, imported, tag_only, config_changes, deleted
        """
        results = {
            'created': [],
            'imported': [],
            'tag_only': [],
            'config_changes': [],
            'deleted': []
        }
        
        for rc in self.resource_changes:
            addr = rc.get('address', '')
            change = rc.get('change', {})
            actions = change.get('actions', [])
            
            if 'create' in actions and 'delete' not in actions:
                if rc.get('action_reason') == 'import':
                    results['imported'].append(addr)
                else:
                    results['created'].append(addr)
                    
            elif 'update' in actions:
                changed_attrs = self._get_changed_attributes(change, addr)
                
                # Only count as an update if there are real (non-ignored) changes
                if changed_attrs:
                    if set(changed_attrs.keys()) == {'tags'}:
                        results['tag_only'].append(addr)
                    else:
                        results['config_changes'].append({
                            'address': addr,
                            'changed_attributes': changed_attrs  # Store the full dict with before/after values
                        })
                # If no real changes after filtering, don't count as an update
                    
            elif 'delete' in actions and 'create' not in actions:
                results['deleted'].append(addr)
                
        return results
    
    def _get_changed_attributes(self, change: Dict, resource_address: str) -> Dict:
        """
        Determine which attributes actually changed.
        
        Args:
            change: The change object from resource_changes
            resource_address: Full resource address (e.g., azurerm_monitor_metric_alert.example)
            
        Returns:
            Dict of changed attributes (excluding computed/ignored fields)
        """
        before = change.get('before', {})
        after = change.get('after', {})
        after_unknown = change.get('after_unknown', {})
        
        # Find all changed keys
        changes_dict = {}
        for key in set(list(before.keys()) + list(after.keys())):
            before_val = before.get(key)
            after_val = after.get(key)
            
            # Check if the value is unknown (will be computed during apply)
            if after_unknown.get(key) is True:
                # Try to resolve from HCL if available
                if self.hcl_resolver:
                    hcl_value = self.hcl_resolver.get_resource_attribute(resource_address, key)
                    if hcl_value is not None:
                        after_val = hcl_value
                    else:
                        after_val = '(known after apply)'
                else:
                    after_val = '(known after apply)'
            
            if not self._values_equal(before_val, after_val):
                changes_dict[key] = (before_val, after_val)
        
        # Extract resource type from address (e.g., "azurerm_monitor_metric_alert.example" -> "azurerm_monitor_metric_alert")
        resource_type = resource_address.split('.')[0] if '.' in resource_address else ''
        
        # Build combined ignore set (global + resource-specific)
        ignore_set = self.ignore_fields.copy()
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
                # This is a real change (including fields that will be "known after apply")
                real_changes[k] = v
        
        return real_changes
    
    def _format_value(self, value) -> str:
        """Format a value for display."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, dict)):
            # For complex structures, show a formatted representation
            return json.dumps(value, indent=2, separators=(',', ': '))
        else:
            return str(value)
    
    @staticmethod
    def _is_azure_resource_id(value: Any) -> bool:
        """Check if a value is an Azure resource ID."""
        if not isinstance(value, str):
            return False
        # Azure resource IDs contain these path segments
        return any(segment in value for segment in ['/subscriptions/', '/providers/', '/resourceGroups/'])
    
    @staticmethod
    def _normalize_for_comparison_static(value: Any, ignore_azure_casing: bool = False) -> Any:
        """Static version of normalize for use in static methods."""
        if isinstance(value, str):
            if ignore_azure_casing and TerraformPlanAnalyzer._is_azure_resource_id(value):
                return value.lower()
            return value
        elif isinstance(value, list):
            return [TerraformPlanAnalyzer._normalize_for_comparison_static(item, ignore_azure_casing) for item in value]
        elif isinstance(value, dict):
            return {k: TerraformPlanAnalyzer._normalize_for_comparison_static(v, ignore_azure_casing) for k, v in value.items()}
        else:
            return value
    
    def _normalize_for_comparison(self, value: Any) -> Any:
        """Recursively normalize Azure resource IDs to lowercase for comparison."""
        if isinstance(value, str):
            # Normalize Azure resource IDs to lowercase if flag is set
            if self.ignore_azure_casing and self._is_azure_resource_id(value):
                return value.lower()
            return value
        elif isinstance(value, list):
            # Recursively normalize list elements
            return [self._normalize_for_comparison(item) for item in value]
        elif isinstance(value, dict):
            # Recursively normalize dict values (keep keys as-is)
            return {k: self._normalize_for_comparison(v) for k, v in value.items()}
        else:
            return value
    
    def _values_equal(self, before_val: Any, after_val: Any) -> bool:
        """Check if two values are equal with case-insensitive comparison for Azure resource IDs."""
        # Normalize both values and compare
        normalized_before = self._normalize_for_comparison(before_val)
        normalized_after = self._normalize_for_comparison(after_val)
        return normalized_before == normalized_after
    
    def print_summary(self, results: Dict[str, List]) -> None:
        """Print a formatted summary of the analysis."""
        created_count = len(results['created'])
        imported_count = len(results['imported'])
        tag_only_count = len(results['tag_only'])
        config_count = len(results['config_changes'])
        deleted_count = len(results['deleted'])
        total = len(self.resource_changes)
        
        print("=" * 60)
        print("TERRAFORM PLAN ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Resources: {total}")
        print(f"  Created:       {created_count}")
        print(f"  Imported:      {imported_count}")
        print(f"  Updated:       {tag_only_count + config_count}")
        print(f"    - Tag-only:      {tag_only_count}")
        print(f"    - Config changes: {config_count}")
        print(f"  Deleted:       {deleted_count}")
        print("=" * 60)
        
    def print_details(self, results: Dict[str, List], verbose: bool = False) -> None:
        """Print detailed breakdown of all changes."""
        
        if results['created']:
            print(f"\nCREATED ({len(results['created'])})")
            print("-" * 60)
            for r in sorted(results['created']):
                print(f"  {r}")
        
        if results['imported']:
            print(f"\nIMPORTED ({len(results['imported'])})")
            print("-" * 60)
            for r in sorted(results['imported']):
                print(f"  {r}")
        
        if results['config_changes']:
            print(f"\nUPDATED - CONFIG CHANGES ({len(results['config_changes'])})")
            print("-" * 60)
            for item in sorted(results['config_changes'], key=lambda x: x['address']):
                changed_attrs = item['changed_attributes']
                
                if verbose:
                    # Show full before/after values
                    print(f"\n  {item['address']}")
                    for attr_name in sorted(changed_attrs.keys()):
                        before_val, after_val = changed_attrs[attr_name]
                        # Format values for display
                        before_str = self._format_value(before_val)
                        after_str = self._format_value(after_val)
                        
                        print(f"    • {attr_name}:")
                        # Indent multi-line values
                        for line in before_str.split('\n'):
                            print(f"        - {line}")
                        for line in after_str.split('\n'):
                            print(f"        + {line}")
                else:
                    # Just show attribute names
                    attrs = ', '.join(sorted(changed_attrs.keys()))
                    print(f"  {item['address']}")
                    print(f"    → {attrs}")
        
        if results['tag_only']:
            print(f"\nUPDATED - TAG-ONLY CHANGES ({len(results['tag_only'])})")
            print("-" * 60)
            for r in sorted(results['tag_only']):
                print(f"  {r}")
        
        if results['deleted']:
            print(f"\nDELETED ({len(results['deleted'])})")
            print("-" * 60)
            for r in sorted(results['deleted']):
                print(f"  {r}")
    
    def print_ignore_report(self) -> None:
        """Print a report of what was ignored during analysis."""
        if not self.ignored_changes:
            return
        
        print("\n" + "=" * 60)
        print("IGNORED CHANGES REPORT")
        print("=" * 60)
        
        total_ignored = sum(len(resources) for fields in self.ignored_changes.values() for resources in fields.values())
        print(f"\nTotal ignored changes: {total_ignored}\n")
        
        for resource_type in sorted(self.ignored_changes.keys()):
            fields = self.ignored_changes[resource_type]
            total_for_type = sum(len(resources) for resources in fields.values())
            
            print(f"\n{resource_type} ({total_for_type} ignored changes)")
            print("-" * 60)
            
            for field in sorted(fields.keys()):
                resources = fields[field]
                count = len(resources)
                
                # Get reason if available
                reason = None
                if resource_type in self.resource_ignore_reasons:
                    reason = self.resource_ignore_reasons[resource_type].get(field)
                if not reason and field in self.global_ignore_reasons:
                    reason = self.global_ignore_reasons[field]
                
                reason_str = f" - {reason}" if reason else ""
                print(f"  {field}: {count} resource(s){reason_str}")
                
                # Show first few examples
                max_examples = 3
                for i, res in enumerate(sorted(resources)[:max_examples]):
                    print(f"    • {res}")
                if len(resources) > max_examples:
                    print(f"    ... and {len(resources) - max_examples} more")
        
        print("\n" + "=" * 60)
    
    @staticmethod
    def _highlight_char_diff(before_str: str, after_str: str, is_known_after_apply: bool = False) -> Tuple[str, str]:
        """
        Highlight character-level differences between two similar strings.
        Returns HTML with character-level highlighting.
        """
        matcher = SequenceMatcher(None, before_str, after_str)
        before_parts = []
        after_parts = []
        
        # Choose the CSS class based on whether it's known after apply
        char_added_class = 'char-known-after-apply' if is_known_after_apply else 'char-added'
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Characters are the same
                text = html.escape(before_str[i1:i2])
                before_parts.append(text)
                after_parts.append(text)
            elif tag == 'delete':
                # Characters only in before
                before_parts.append(f'<span class="char-removed">{html.escape(before_str[i1:i2])}</span>')
            elif tag == 'insert':
                # Characters only in after
                after_parts.append(f'<span class="{char_added_class}">{html.escape(after_str[j1:j2])}</span>')
            elif tag == 'replace':
                # Characters differ
                before_parts.append(f'<span class="char-removed">{html.escape(before_str[i1:i2])}</span>')
                after_parts.append(f'<span class="{char_added_class}">{html.escape(after_str[j1:j2])}</span>')
        
        return ''.join(before_parts), ''.join(after_parts)
    
    def _highlight_json_diff(self, before: Any, after: Any) -> Tuple[str, str, bool]:
        """
        Highlight differences between two JSON structures.
        Returns HTML for before and after with differences highlighted, and a flag for known_after_apply.
        Only highlights lines that are actually different.
        """
        # Check if after is "(known after apply)" or contains HCL values
        is_known_after_apply = after == "(known after apply)"
        
        # Check if value is from HCL (contains interpolations like ${...})
        # This applies when we resolved from HCL but it has variable references
        is_from_hcl = False
        if isinstance(after, (dict, list, str)):
            after_json = json.dumps(after, indent=2, sort_keys=True) if not isinstance(after, str) else after
            is_from_hcl = '${' in after_json
        
        # If it's from HCL, treat like known_after_apply for styling purposes
        if is_from_hcl:
            is_known_after_apply = True
        
        # Normalize values to handle case-insensitive Azure resource IDs
        # This ensures resource ID casing differences don't show in the diff
        normalized_before = TerraformPlanAnalyzer._normalize_for_comparison_static(before, self.ignore_azure_casing)
        normalized_after = TerraformPlanAnalyzer._normalize_for_comparison_static(after, self.ignore_azure_casing)
        
        # Convert normalized values to formatted JSON strings for display
        before_str = json.dumps(normalized_before, indent=2, sort_keys=True) if normalized_before is not None else "null"
        after_str = json.dumps(normalized_after, indent=2, sort_keys=True) if normalized_after is not None else "null"
        
        # If strings are identical after normalization, return without highlighting
        if before_str == after_str:
            before_html = f'<pre class="json-content">{html.escape(before_str)}</pre>'
            after_html = f'<pre class="json-content">{html.escape(after_str)}</pre>'
            return before_html, after_html, is_known_after_apply
        
        # Split into lines for comparison
        before_lines = before_str.split('\n')
        after_lines = after_str.split('\n')
        
        # Use SequenceMatcher to find differences
        matcher = SequenceMatcher(None, before_lines, after_lines)
        
        before_html_lines = []
        after_html_lines = []
        
        # Choose the CSS class based on whether it's known after apply
        added_class = 'known-after-apply' if is_known_after_apply else 'added'
        char_added_class = 'char-known-after-apply' if is_known_after_apply else 'char-added'
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                for line in before_lines[i1:i2]:
                    before_html_lines.append(f'<span class="unchanged">{html.escape(line)}</span>')
                for line in after_lines[j1:j2]:
                    after_html_lines.append(f'<span class="unchanged">{html.escape(line)}</span>')
            elif tag == 'delete':
                # Lines only in before
                for line in before_lines[i1:i2]:
                    before_html_lines.append(f'<span class="removed">{html.escape(line)}</span>')
                # Add empty lines to after to maintain alignment
                empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
                for _ in range(i2 - i1):
                    after_html_lines.append(empty_line)
            elif tag == 'insert':
                # Lines only in after
                # Add empty lines to before to maintain alignment
                empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
                for _ in range(j2 - j1):
                    before_html_lines.append(empty_line)
                for line in after_lines[j1:j2]:
                    after_html_lines.append(f'<span class="{added_class}">{html.escape(line)}</span>')
            elif tag == 'replace':
                # Lines differ - do character-level comparison for similar lines
                before_chunk = before_lines[i1:i2]
                after_chunk = after_lines[j1:j2]
                
                # For each pair of lines, check if they're similar (e.g., only value differs)
                max_len = max(len(before_chunk), len(after_chunk))
                empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
                for idx in range(max_len):
                    if idx < len(before_chunk) and idx < len(after_chunk):
                        before_line = before_chunk[idx]
                        after_line = after_chunk[idx]
                        
                        # Check if lines are similar enough for character-level diff
                        similarity = SequenceMatcher(None, before_line, after_line).ratio()
                        if similarity > 0.5:  # If more than 50% similar, show character diff
                            before_highlighted, after_highlighted = TerraformPlanAnalyzer._highlight_char_diff(before_line, after_line, is_known_after_apply)
                            before_html_lines.append(f'<span class="removed">{before_highlighted}</span>')
                            after_html_lines.append(f'<span class="{added_class}">{after_highlighted}</span>')
                        else:
                            # Lines are too different, show as full line changes
                            if before_line in after_chunk:
                                before_html_lines.append(f'<span class="unchanged">{html.escape(before_line)}</span>')
                            else:
                                before_html_lines.append(f'<span class="removed">{html.escape(before_line)}</span>')
                            
                            if after_line in before_chunk:
                                after_html_lines.append(f'<span class="unchanged">{html.escape(after_line)}</span>')
                            else:
                                after_html_lines.append(f'<span class="{added_class}">{html.escape(after_line)}</span>')
                    elif idx < len(before_chunk):
                        before_line = before_chunk[idx]
                        if before_line in after_chunk:
                            before_html_lines.append(f'<span class="unchanged">{html.escape(before_line)}</span>')
                        else:
                            before_html_lines.append(f'<span class="removed">{html.escape(before_line)}</span>')
                        after_html_lines.append(empty_line)
                    else:
                        before_html_lines.append(empty_line)
                        after_line = after_chunk[idx]
                        if after_line in before_chunk:
                            after_html_lines.append(f'<span class="unchanged">{html.escape(after_line)}</span>')
                        else:
                            after_html_lines.append(f'<span class="{added_class}">{html.escape(after_line)}</span>')
        
        before_html = f'<pre class="json-content">{"<br>".join(before_html_lines)}</pre>'
        after_html = f'<pre class="json-content">{"<br>".join(after_html_lines)}</pre>'
        
        return before_html, after_html, is_known_after_apply
        
        return before_html, after_html
    
    def _transform_results_for_html(self, results: Dict) -> Dict[str, Any]:
        """Transform results dict from analyze() format to HTML-friendly format."""
        transformed = {
            'summary': {
                'total': len(self.resource_changes),
                'created': len(results['created']),
                'imported': len(results['imported']),
                'updated': len(results['tag_only']) + len(results['config_changes']),
                'tag_only': len(results['tag_only']),
                'config_changes': len(results['config_changes']),
                'deleted': len(results['deleted'])
            },
            'created': results['created'],
            'updated': []
        }
        
        # Transform config_changes from tuple format to list-of-dicts format
        for item in results['config_changes']:
            changes_list = []
            for attr_name, (before_val, after_val) in item['changed_attributes'].items():
                changes_list.append({
                    'attribute': attr_name,
                    'before': before_val,
                    'after': after_val
                })
            
            transformed['updated'].append({
                'name': item['address'],
                'changes': changes_list
            })
        
        return transformed
    
    def generate_html_report(self, results: Dict, output_path: str) -> None:
        """Generate an HTML report from the analysis results."""
        data = self._transform_results_for_html(results)
        current_date = datetime.now().strftime('%B %d, %Y')
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Plan Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }}
        
        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .summary-card.total .number {{ color: #667eea; }}
        .summary-card.created .number {{ color: #51cf66; }}
        .summary-card.updated .number {{ color: #ffa94d; }}
        .summary-card.deleted .number {{ color: #ff6b6b; }}
        
        .section {{
            padding: 30px;
        }}
        
        .section-header {{
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }}
        
        .resource-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .resource-item {{
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 4px solid #51cf66;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-all;
        }}
        
        .resource-change {{
            background: #fff;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            overflow: hidden;
        }}
        
        .resource-change-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 1.1em;
            color: #495057;
            border-bottom: 2px solid #ffa94d;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .resource-change-header:hover {{
            background: #e9ecef;
        }}
        
        .toggle-icon {{
            cursor: pointer;
            user-select: none;
            flex-shrink: 0;
            width: 20px;
            transition: transform 0.3s;
            font-size: 0.9em;
        }}
        
        .toggle-icon.collapsed {{
            transform: rotate(-90deg);
        }}
        
        .resource-name {{
            user-select: text;
            cursor: text;
            flex: 1;
        }}
        
        .resource-change-content {{
            padding: 20px;
        }}
        
        .resource-change-content.hidden {{
            display: none;
        }}
        
        .change-item {{
            margin-bottom: 25px;
            border-left: 3px solid #ffa94d;
            padding-left: 15px;
        }}
        
        .change-attribute {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
            font-size: 1.05em;
        }}
        
        .change-diff {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 10px;
        }}
        
        .diff-column {{
            background: #f8f9fa;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        .diff-header {{
            padding: 8px 12px;
            font-weight: bold;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        
        .diff-header.before {{
            background: #ffe0e0;
            color: #c92a2a;
        }}
        
        .diff-header.after {{
            background: #d3f9d8;
            color: #2b8a3e;
        }}
        
        .diff-header.after-unknown {{
            background: #fff4e6;
            color: #e67700;
        }}
        
        .json-content {{
            padding: 12px;
            margin: 0;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .unchanged {{
            color: #666;
        }}
        
        .opacity-50 {{
            opacity: 0.3;
        }}
        
        .removed {{
            background-color: #ffe0e0;
            color: #c92a2a;
            display: block;
        }}
        
        .added {{
            background-color: #d3f9d8;
            color: #2b8a3e;
            display: block;
        }}
        
        .known-after-apply {{
            background-color: #fff4e6;
            color: #e67700;
            display: block;
        }}
        
        .char-removed {{
            background-color: #ff9999;
            color: #7d0000;
        }}
        
        .char-added {{
            background-color: #99ff99;
            color: #006600;
        }}
        
        .char-known-after-apply {{
            background-color: #ffe8a1;
            color: #995700;
        }}
        
        .simple-change {{
            font-family: 'Courier New', monospace;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .simple-change .before {{
            color: #c92a2a;
            text-decoration: line-through;
        }}
        
        .simple-change .after {{
            color: #2b8a3e;
            font-weight: bold;
        }}
        
        .simple-change .after.known-after-apply {{
            color: #e67700;
            background-color: #fff4e6;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .toggle-all {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }}
        
        .toggle-all:hover {{
            background: #5568d3;
        }}
        
        .resource-type-section {{
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }}
        
        .resource-type-section h3 {{
            color: #667eea;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .ignored-field {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #868e96;
        }}
        
        .ignored-field-header {{
            margin-bottom: 10px;
            color: #495057;
        }}
        
        .ignored-resources-list {{
            list-style-type: none;
            padding-left: 0;
            margin: 0;
        }}
        
        .ignored-resources-list li {{
            padding: 5px 10px;
            margin: 3px 0;
            background: #f1f3f5;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .ignored-resources-list .more-indicator {{
            background: #e9ecef;
            color: #868e96;
            font-style: italic;
            font-family: inherit;
        }}
        
        .legend {{
            background: #f8f9fa;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .legend h2 {{
            margin-top: 0;
            color: #667eea;
            font-size: 1.3em;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-content {{
            margin-top: 15px;
        }}
        
        .legend-content.hidden {{
            display: none;
        }}
        
        .resource-list.hidden {{
            display: none;
        }}
        
        .legend-section {{
            margin-bottom: 20px;
        }}
        
        .legend-section h3 {{
            color: #495057;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 8px;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }}
        
        .legend-symbol {{
            font-weight: bold;
            min-width: 30px;
        }}
        
        .legend-description {{
            flex: 1;
        }}
        
        @media (max-width: 768px) {{
            .change-diff {{
                grid-template-columns: 1fr;
            }}
            
            .summary {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Terraform Plan Analysis Report</h1>
            <p>Generated on {current_date}</p>
        </header>
        
        <div class="legend">
            <h2 onclick="toggleLegend()"><span id="legend-icon">▶</span> Report Guide</h2>
            <div class="legend-content hidden" id="legend-content">
                <div class="legend-section">
                    <h3>📊 Value Indicators</h3>
                    <div class="legend-item">
                        <span class="legend-symbol">⚙️</span>
                        <span class="legend-description"><strong>From Terraform config</strong> - Value resolved from .tf files, not from plan. May contain unresolved variable references like <code>${{...}}</code>. Shows yellow background.</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol">⚠️</span>
                        <span class="legend-description"><strong>Computed at apply</strong> - Value will only be known when Terraform applies the changes. No HCL definition found. Shows yellow background.</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol" style="color: #2b8a3e;">●</span>
                        <span class="legend-description"><strong>Known value</strong> - Value is known from the plan. Shows green background for additions.</span>
                    </div>
                </div>
                
                <div class="legend-section">
                    <h3>ℹ️ Comparison Rules</h3>
                    <div class="legend-item">
                        <span class="legend-symbol">🔗</span>
                        <span class="legend-description"><strong>Resource IDs are case-insensitive</strong> - Azure resource IDs like <code>/providers/Microsoft.IotHub</code> are compared without case sensitivity, so changes only in casing (e.g., <code>IotHub</code> vs <code>Iothub</code>) are filtered out as noise.</span>
                    </div>
                </div>
                
                <div class="legend-section">
                    <h3>🎨 Color Coding</h3>
                    <div class="legend-item">
                        <span class="legend-symbol" style="background: #d3f9d8; padding: 4px 8px; border-radius: 3px;">Green</span>
                        <span class="legend-description">Added values or normal changes from the plan</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol" style="background: #ffe0e0; padding: 4px 8px; border-radius: 3px;">Red</span>
                        <span class="legend-description">Removed values</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol" style="background: #fff4e6; padding: 4px 8px; border-radius: 3px;">Yellow</span>
                        <span class="legend-description">Values from Terraform config or computed at apply (not final)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol" style="color: #666;">Gray</span>
                        <span class="legend-description">Unchanged values (shown for context)</span>
                    </div>
                </div>
                
                <div class="legend-section">
                    <h3>📑 Report Sections</h3>
                    <div class="legend-item">
                        <span class="legend-symbol">📝</span>
                        <span class="legend-description"><strong>Created Resources</strong> - New resources being added to your infrastructure</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol">🔄</span>
                        <span class="legend-description"><strong>Updated Resources</strong> - Existing resources with configuration changes (click to expand/collapse)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol">🏷️</span>
                        <span class="legend-description"><strong>Tag-Only Updates</strong> - Resources with only tag changes</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-symbol">🔽</span>
                        <span class="legend-description"><strong>Ignored Changes</strong> - Changes filtered out based on ignore configuration (at bottom)</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="number">{data['summary'].get('total', 0)}</div>
                <div class="label">Total Resources</div>
            </div>
            <div class="summary-card created">
                <div class="number">{data['summary'].get('created', 0)}</div>
                <div class="label">Created</div>
            </div>
            <div class="summary-card updated">
                <div class="number">{data['summary'].get('config_changes', 0)}</div>
                <div class="label">Updated</div>
            </div>
            <div class="summary-card deleted">
                <div class="number">{data['summary'].get('deleted', 0)}</div>
                <div class="label">Deleted</div>
            </div>
        </div>
"""
        
        # Created resources section
        if data['created']:
            html_content += """
        <div class="section">
            <h2 class="section-header" onclick="toggleCreatedResources()" style="cursor: pointer;">
                <span id="created-icon">▶</span> 📦 Created Resources
            </h2>
            <div class="resource-list hidden" id="created-resources">
"""
            for resource in sorted(data['created']):
                html_content += f'                <div class="resource-item">{html.escape(resource)}</div>\n'
            
            html_content += """            </div>
        </div>
"""
        
        # Updated resources section
        if data['updated']:
            html_content += """
        <div class="section">
            <h2 class="section-header">🔄 Updated Resources</h2>
            <button class="toggle-all" onclick="toggleAll()">Expand/Collapse All</button>
"""
            
            for resource in sorted(data['updated'], key=lambda x: x['name']):
                resource_name = html.escape(resource['name'])
                html_content += f"""
            <div class="resource-change">
                <div class="resource-change-header">
                    <span class="toggle-icon" onclick="toggleResource(this)">▼</span>
                    <span class="resource-name">{resource_name}</span>
                </div>
                <div class="resource-change-content">
"""
                
                for change in sorted(resource['changes'], key=lambda x: x['attribute']):
                    attr_name = html.escape(change['attribute'])
                    html_content += f"""
                    <div class="change-item">
                        <div class="change-attribute">{attr_name}</div>
"""
                    
                    before = change.get('before')
                    after = change.get('after')
                    
                    # Check if it's a simple value or complex structure
                    if isinstance(before, (dict, list)) or isinstance(after, (dict, list)):
                        # Complex structure - use diff highlighting
                        before_html, after_html, is_known_after_apply = self._highlight_json_diff(before, after)
                        # Use ⚙️ for HCL-resolved values, ⚠️ for truly unknown
                        if is_known_after_apply and after != "(known after apply)":
                            after_header = "After ⚙️ (from Terraform config, not plan)"
                            after_class = "after-unknown"
                        elif is_known_after_apply:
                            after_header = "After ⚠️ (computed at apply)"
                            after_class = "after-unknown"
                        else:
                            after_header = "After"
                            after_class = "after"
                        html_content += f"""
                        <div class="change-diff">
                            <div class="diff-column">
                                <div class="diff-header before">Before</div>
                                {before_html}
                            </div>
                            <div class="diff-column">
                                <div class="diff-header {after_class}">{after_header}</div>
                                {after_html}
                            </div>
                        </div>
"""
                    else:
                        # Simple value change
                        before_str = html.escape(str(before) if before is not None else 'null')
                        after_str = html.escape(str(after) if after is not None else 'null')
                        # Check if from HCL or truly unknown
                        is_from_hcl = '${' in str(after)
                        is_known_after_apply = after == "(known after apply)" or is_from_hcl
                        
                        if is_from_hcl:
                            emoji = '<span title="Value from Terraform config, not plan">⚙️</span>'
                        elif after == "(known after apply)":
                            emoji = '<span title="Computed at apply time">⚠️</span>'
                        else:
                            emoji = ""
                        
                        after_class = "after known-after-apply" if is_known_after_apply else "after"
                        html_content += f"""
                        <div class="simple-change">
                            <span class="before">{before_str}</span> → <span class="{after_class}">{after_str} {emoji}</span>
                        </div>
"""
                    
                    html_content += """
                    </div>
"""
                
                html_content += """
                </div>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        # Add Ignored Changes section
        if self.ignored_changes:
            total_ignored = sum(len(resources) for fields in self.ignored_changes.values() for resources in fields.values())
            
            # Group by field instead of resource type
            by_field = {}
            for resource_type, fields in self.ignored_changes.items():
                for field, resources in fields.items():
                    if field not in by_field:
                        by_field[field] = []
                    # Add resources with their type
                    for resource in resources:
                        by_field[field].append((resource, resource_type))
            
            html_content += f"""
        <div class="section">
            <h2>Ignored Changes ({total_ignored} total)</h2>
"""
            
            for field in sorted(by_field.keys()):
                resources_with_types = by_field[field]
                count = len(resources_with_types)
                
                # Get reason if available - check all resource types for this field
                reason = None
                if field in self.global_ignore_reasons:
                    reason = self.global_ignore_reasons[field]
                else:
                    # Check resource-specific reasons
                    for resource_type in self.resource_ignore_reasons:
                        if field in self.resource_ignore_reasons[resource_type]:
                            reason = self.resource_ignore_reasons[resource_type][field]
                            break
                
                reason_str = f" - {html.escape(reason)}" if reason else ""
                
                html_content += f"""
            <div class="ignored-field">
                <div class="ignored-field-header">
                    <strong>{html.escape(field)}</strong>: {count} resource(s){reason_str}
                </div>
                <ul class="ignored-resources-list">
"""
                
                # Show all resources with their types
                for resource, resource_type in sorted(resources_with_types):
                    html_content += f"""
                    <li>{html.escape(resource)} <span style="color: #868e96;">({html.escape(resource_type)})</span></li>
"""
                
                html_content += """
                </ul>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        # JavaScript for toggling
        html_content += """
    </div>
    
    <script>
        function toggleLegend() {
            const content = document.getElementById('legend-content');
            const icon = document.getElementById('legend-icon');
            content.classList.toggle('hidden');
            icon.textContent = content.classList.contains('hidden') ? '▶' : '▼';
        }
        
        function toggleCreatedResources() {
            const content = document.getElementById('created-resources');
            const icon = document.getElementById('created-icon');
            content.classList.toggle('hidden');
            icon.textContent = content.classList.contains('hidden') ? '▶' : '▼';
        }
        
        function toggleResource(icon) {
            icon.classList.toggle('collapsed');
            const header = icon.parentElement;
            const content = header.nextElementSibling;
            content.classList.toggle('hidden');
        }
        
        function toggleAll() {
            const icons = document.querySelectorAll('.toggle-icon');
            const firstIcon = icons[0];
            const shouldExpand = firstIcon.classList.contains('collapsed');
            
            icons.forEach(icon => {
                const header = icon.parentElement;
                const content = header.nextElementSibling;
                if (shouldExpand) {
                    icon.classList.remove('collapsed');
                    content.classList.remove('hidden');
                } else {
                    icon.classList.add('collapsed');
                    content.classList.add('hidden');
                }
            });
        }
    </script>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)

    def generate_json_report(self, results: Dict, output_path: str) -> None:
        """Generate a JSON report from the analysis results."""
        from datetime import datetime
        
        # Build summary statistics
        summary = {
            'total': len(self.resource_changes),
            'created': len(results['created']),
            'imported': len(results['imported']),
            'updated': len(results['tag_only']) + len(results['config_changes']),
            'tag_only': len(results['tag_only']),
            'config_changes': len(results['config_changes']),
            'deleted': len(results['deleted']),
            'ignored_changes': sum(len(resources) for fields in self.ignored_changes.values() for resources in fields.values())
        }
        
        # Transform updated resources with full change details
        updated_resources = []
        for item in results['config_changes']:
            changes = []
            for attr_name, (before_val, after_val) in item['changed_attributes'].items():
                # Determine if this is "known after apply"
                is_known_after_apply = after_val == "(known after apply)"
                
                # Check if value is from HCL (contains interpolations)
                is_from_hcl = False
                if isinstance(after_val, (dict, list, str)):
                    after_json = json.dumps(after_val, indent=2, sort_keys=True) if not isinstance(after_val, str) else after_val
                    is_from_hcl = '${' in after_json
                
                if is_from_hcl:
                    is_known_after_apply = True
                
                changes.append({
                    'attribute': attr_name,
                    'before': before_val,
                    'after': after_val,
                    'is_known_after_apply': is_known_after_apply
                })
            
            updated_resources.append({
                'address': item['address'],
                'changes': changes
            })
        
        # Transform ignored changes - group by field
        ignored_changes_by_field = {}
        for resource_type, fields in self.ignored_changes.items():
            for field, resources in fields.items():
                if field not in ignored_changes_by_field:
                    # Get reason if available
                    reason = None
                    if field in self.global_ignore_reasons:
                        reason = self.global_ignore_reasons[field]
                    else:
                        # Check resource-specific reasons
                        for rt in self.resource_ignore_reasons:
                            if field in self.resource_ignore_reasons[rt]:
                                reason = self.resource_ignore_reasons[rt][field]
                                break
                    
                    ignored_changes_by_field[field] = {
                        'reason': reason,
                        'resources': []
                    }
                
                # Add resources with their type
                for resource in resources:
                    ignored_changes_by_field[field]['resources'].append({
                        'address': resource,
                        'resource_type': resource_type
                    })
        
        # Build the complete report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'plan_file': str(self.plan_file),
                'analyzer_version': '1.0',
                'ignore_azure_casing': self.ignore_azure_casing
            },
            'summary': summary,
            'created_resources': sorted(results['created']),
            'imported_resources': sorted(results['imported']),
            'updated_resources': sorted(updated_resources, key=lambda x: x['address']),
            'tag_only_updates': sorted(results['tag_only']),
            'deleted_resources': sorted(results['deleted']),
            'ignored_changes': ignored_changes_by_field
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, sort_keys=False)


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze Terraform plan JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python analyze_plan.py tfplan.json
  
  # Use a config file
  python analyze_plan.py tfplan.json --config ignore_config.json
  
  # Ignore specific fields
  python analyze_plan.py tfplan.json --ignore description
  
  # Ignore multiple fields globally
  python analyze_plan.py tfplan.json --ignore description --ignore severity
  python analyze_plan.py tfplan.json --ignore description,severity,scopes
  
  # Ignore fields for specific resource types
  python analyze_plan.py tfplan.json --ignore-for azurerm_monitor_metric_alert:tags,action,description
  python analyze_plan.py tfplan.json --ignore-for azurerm_storage_account:min_tls_version,cross_tenant_replication_enabled
  
  # Combine config file with CLI args (CLI args are additive)
  python analyze_plan.py tfplan.json --config ignore_config.json --ignore extra_field
  
  # Generate HTML report
  python analyze_plan.py tfplan.json --html
  python analyze_plan.py tfplan.json --html custom_report.html
  
  # Generate JSON report for programmatic analysis
  python analyze_plan.py tfplan.json --json
  python analyze_plan.py tfplan.json --json custom_report.json
  
  # Ignore Azure resource ID casing differences
  python analyze_plan.py tfplan.json --ignore-azure-casing
  
  # Show currently ignored fields
  python analyze_plan.py tfplan.json --show-ignores
  
Config file format (JSON):
  # Simple format (list):
  {
    "global_ignores": ["field1", "field2"],
    "resource_ignores": {
      "azurerm_monitor_metric_alert": ["tags", "action"]
    }
  }
  
  # With reasons (dict):
  {
    "global_ignores": {
      "tags": "Tags are managed separately"
    },
    "resource_ignores": {
      "azurerm_monitor_metric_alert": {
        "action": "Action groups are non-impacting changes",
        "description": "Description updates don't affect functionality"
      }
    }
  }
        """
    )
    
    parser.add_argument('plan_file', help='Path to the terraform plan JSON file')
    parser.add_argument(
        '--config', '-c',
        dest='config_file',
        help='Path to JSON config file with ignore settings'
    )
    parser.add_argument(
        '--ignore', '-i',
        action='append',
        dest='ignore_fields',
        help='Additional field(s) to ignore globally when detecting changes (can be used multiple times or comma-separated)'
    )
    parser.add_argument(
        '--ignore-for',
        action='append',
        dest='resource_ignores',
        help='Ignore specific fields for a resource type. Format: resource_type:field1,field2 (e.g., azurerm_monitor_metric_alert:tags,action,description)'
    )
    parser.add_argument(
        '--show-ignores',
        action='store_true',
        help='Display all fields being ignored'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show full before/after values for changed attributes'
    )
    parser.add_argument(
        '--html',
        nargs='?',
        const=True,
        default=None,
        metavar='OUTPUT',
        help='Generate HTML report instead of text output. Optionally specify output path (default: <plan_file>.html)'
    )
    parser.add_argument(
        '--json',
        nargs='?',
        const=True,
        default=None,
        metavar='OUTPUT',
        help='Generate JSON report for programmatic analysis. Optionally specify output path (default: <plan_file>.report.json)'
    )
    parser.add_argument(
        '--tf-dir',
        type=str,
        default=None,
        metavar='DIR',
        help='Directory containing Terraform .tf files for resolving "known after apply" values (default: same directory as plan file)'
    )
    parser.add_argument(
        '--ignore-azure-casing',
        action='store_true',
        help='Ignore casing differences in Azure resource IDs (e.g., /providers/Microsoft.IotHub vs /providers/Microsoft.Iothub)'
    )
    
    args = parser.parse_args()
    
    if not Path(args.plan_file).exists():
        print(f"Error: File not found: {args.plan_file}")
        sys.exit(1)
    
    # Load config file if specified
    custom_ignore_fields = set()
    resource_specific_ignores = {}
    global_ignore_reasons = {}
    resource_ignore_reasons = {}
    
    if args.config_file:
        config = load_config(args.config_file)
        
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
    
    # Parse custom ignore fields from CLI (additive to config)
    if args.ignore_fields:
        for field_arg in args.ignore_fields:
            # Support comma-separated values
            fields = [f.strip() for f in field_arg.split(',')]
            custom_ignore_fields.update(fields)
    
    # Parse resource-specific ignores from CLI (additive to config)
    if args.resource_ignores:
        for resource_ignore in args.resource_ignores:
            if ':' not in resource_ignore:
                print(f"Warning: Invalid format for --ignore-for: {resource_ignore}")
                print("Expected format: resource_type:field1,field2")
                continue
            
            resource_type, fields_str = resource_ignore.split(':', 1)
            resource_type = resource_type.strip()
            fields = {f.strip() for f in fields_str.split(',')}
            
            if resource_type in resource_specific_ignores:
                resource_specific_ignores[resource_type].update(fields)
            else:
                resource_specific_ignores[resource_type] = fields
    
    # Initialize HCL resolver if tf_dir specified or use default
    hcl_resolver = None
    if HCLValueResolver:
        tf_dir = args.tf_dir
        if tf_dir is None:
            # Default to same directory as plan file
            tf_dir = Path(args.plan_file).parent
        
        if Path(tf_dir).exists():
            try:
                print(f"Loading Terraform files from: {tf_dir}")
                hcl_resolver = HCLValueResolver(str(tf_dir))
                print(f"✅ Loaded {len(hcl_resolver.resources)} resources from HCL")
            except Exception as e:
                print(f"Warning: Failed to load HCL files: {e}")
                hcl_resolver = None
    
    # Analyze the plan
    analyzer = TerraformPlanAnalyzer(args.plan_file, custom_ignore_fields, resource_specific_ignores,
                                    global_ignore_reasons, resource_ignore_reasons, hcl_resolver,
                                    args.ignore_azure_casing)
    
    # Show ignored fields if requested
    if args.show_ignores:
        print("=" * 60)
        print("IGNORED FIELDS")
        print("=" * 60)
        print("\nDefault ignored fields (global):")
        for field in sorted(TerraformPlanAnalyzer.DEFAULT_IGNORE_FIELDS):
            print(f"  - {field}")
        if custom_ignore_fields:
            print("\nCustom ignored fields (global):")
            for field in sorted(custom_ignore_fields):
                print(f"  - {field}")
        if resource_specific_ignores:
            print("\nResource-specific ignored fields:")
            for resource_type in sorted(resource_specific_ignores.keys()):
                fields = sorted(resource_specific_ignores[resource_type])
                print(f"  {resource_type}:")
                for field in fields:
                    print(f"    - {field}")
        print("=" * 60)
        print()
    
    analyzer.load_plan()
    results = analyzer.analyze()
    
    # Check if HTML output is requested
    if args.html is not None:
        # Determine output path
        if args.html is True:
            # Default: replace .json extension with .html
            plan_path = Path(args.plan_file)
            if plan_path.suffix == '.json':
                html_output = str(plan_path.with_suffix('.html'))
            else:
                html_output = str(plan_path) + '.html'
        else:
            # User specified a path
            html_output = args.html
        
        # Generate HTML report
        analyzer.generate_html_report(results, html_output)
        print(f"✅ HTML report generated: {html_output}")
    elif args.json is not None:
        # Determine output path
        if args.json is True:
            # Default: <plan_file>.report.json
            plan_path = Path(args.plan_file)
            if plan_path.suffix == '.json':
                # Remove .json and add .report.json
                json_output = str(plan_path.with_suffix('')) + '.report.json'
            else:
                json_output = str(plan_path) + '.report.json'
        else:
            # User specified a path
            json_output = args.json
        
        # Generate JSON report
        analyzer.generate_json_report(results, json_output)
        print(f"✅ JSON report generated: {json_output}")
    else:
        # Print text results to stdout
        analyzer.print_summary(results)
        analyzer.print_details(results, verbose=args.verbose)
        analyzer.print_ignore_report()


if __name__ == '__main__':
    import signal
    # Ignore SIGPIPE to prevent BrokenPipeError when piping to head, less, etc.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        sys.exit(0)
