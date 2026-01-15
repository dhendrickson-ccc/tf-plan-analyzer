#!/usr/bin/env python3
"""
Multi-Environment Terraform Plan Comparator

Compares Terraform plan "before" states across multiple environments
to identify configuration drift and ensure parity.
"""

import html
import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from ignore_utils import apply_ignore_config, get_ignored_attributes


def _highlight_char_diff(before_str: str, after_str: str) -> Tuple[str, str]:
    """
    Highlight character-level differences between two similar strings.
    Returns HTML with character-level highlighting.
    
    Based on the implementation from analyze_plan.py TerraformPlanAnalyzer._highlight_char_diff()
    """
    matcher = SequenceMatcher(None, before_str, after_str)
    before_parts = []
    after_parts = []
    
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
            after_parts.append(f'<span class="char-added">{html.escape(after_str[j1:j2])}</span>')
        elif tag == 'replace':
            # Characters differ
            before_parts.append(f'<span class="char-removed">{html.escape(before_str[i1:i2])}</span>')
            after_parts.append(f'<span class="char-added">{html.escape(after_str[j1:j2])}</span>')
    
    return ''.join(before_parts), ''.join(after_parts)


def _highlight_json_diff(before: Any, after: Any) -> Tuple[str, str]:
    """
    Highlight differences between two JSON structures.
    Returns HTML for before and after with differences highlighted.
    Only highlights lines that are actually different.
    
    Based on the implementation from analyze_plan.py TerraformPlanAnalyzer._highlight_json_diff()
    Simplified for multi-environment comparison (no known-after-apply, no sensitive redaction).
    """
    # Convert to formatted JSON strings
    before_str = json.dumps(before, indent=2, sort_keys=True) if before is not None else "null"
    after_str = json.dumps(after, indent=2, sort_keys=True) if after is not None else "null"
    
    # If strings are identical, return without highlighting
    if before_str == after_str:
        before_html = f'<pre class="json-content">{html.escape(before_str)}</pre>'
        after_html = f'<pre class="json-content">{html.escape(after_str)}</pre>'
        return before_html, after_html
    
    # Split into lines for comparison
    before_lines = before_str.split('\n')
    after_lines = after_str.split('\n')
    
    # Use SequenceMatcher to find differences
    matcher = SequenceMatcher(None, before_lines, after_lines)
    
    before_html_lines = []
    after_html_lines = []
    
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
                after_html_lines.append(f'<span class="added">{html.escape(line)}</span>')
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
                        before_highlighted, after_highlighted = _highlight_char_diff(before_line, after_line)
                        before_html_lines.append(f'<span class="removed">{before_highlighted}</span>')
                        after_html_lines.append(f'<span class="added">{after_highlighted}</span>')
                    else:
                        # Lines are too different, show as full line changes
                        if before_line in after_chunk:
                            before_html_lines.append(f'<span class="unchanged">{html.escape(before_line)}</span>')
                        else:
                            before_html_lines.append(f'<span class="removed">{html.escape(before_line)}</span>')
                        
                        if after_line in before_chunk:
                            after_html_lines.append(f'<span class="unchanged">{html.escape(after_line)}</span>')
                        else:
                            after_html_lines.append(f'<span class="added">{html.escape(after_line)}</span>')
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
                        after_html_lines.append(f'<span class="added">{html.escape(after_line)}</span>')
    
    before_html = f'<pre class="json-content">{"<br>".join(before_html_lines)}</pre>'
    after_html = f'<pre class="json-content">{"<br>".join(after_html_lines)}</pre>'
    
    return before_html, after_html


class EnvironmentPlan:
    """Represents a single environment's Terraform plan with extracted before state."""
    
    def __init__(self, label: str, plan_file_path: Path, 
                 tf_dir: Optional[str] = None, 
                 tfvars_file: Optional[str] = None,
                 show_sensitive: bool = False):
        """
        Initialize an environment plan.
        
        Args:
            label: Human-readable environment name (e.g., "Development", "Production")
            plan_file_path: Path to the plan JSON file
            tf_dir: Optional directory containing Terraform .tf files for HCL resolution
            tfvars_file: Optional environment-specific tfvars file
            show_sensitive: Whether to show actual sensitive values (default: False to mask)
        """
        self.label = label
        self.plan_file_path = plan_file_path
        self.tf_dir = tf_dir
        self.tfvars_file = tfvars_file
        self.show_sensitive = show_sensitive
        self.plan_data: Optional[Dict[str, Any]] = None
        self.before_values: Dict[str, Dict] = {}
        self.before_values_raw: Dict[str, Dict] = {}  # Store unmasked versions for comparison
        self.hcl_resolver = None
    
    def load(self) -> None:
        """Load and parse the plan JSON file, extract before values."""
        with open(self.plan_file_path, 'r') as f:
            self.plan_data = json.load(f)
        
        # Initialize HCL resolver if tf_dir provided
        if self.tf_dir:
            try:
                from hcl_value_resolver import HCLValueResolver
                self.hcl_resolver = HCLValueResolver(
                    tf_dir=self.tf_dir,
                    tfvars_file=self.tfvars_file
                )
            except ImportError:
                # HCL resolver not available, continue without it
                pass
        
        # Extract before values from resource_changes
        resource_changes = self.plan_data.get('resource_changes', [])
        for rc in resource_changes:
            address = rc.get('address', '')
            change = rc.get('change', {})
            before = change.get('before')
            
            if address and before is not None:
                # Apply HCL resolution if available
                if self.hcl_resolver:
                    before = self._resolve_hcl_values(address, before)
                
                # Store raw version (before masking) for comparison
                import copy
                before_raw = copy.deepcopy(before)
                self.before_values_raw[address] = before_raw
                
                # Handle sensitive values (masks them)
                before = self._process_sensitive_values(before, rc)
                
                self.before_values[address] = before
    
    def _resolve_hcl_values(self, address: str, config: Dict) -> Dict:
        """
        Resolve HCL references in configuration values.
        
        Args:
            address: Resource address
            config: Resource configuration
            
        Returns:
            Configuration with resolved HCL values
        """
        if not self.hcl_resolver:
            return config
        
        # Deep copy to avoid modifying original
        import copy
        resolved_config = copy.deepcopy(config)
        
        # Recursively resolve values
        def resolve_recursive(obj):
            if isinstance(obj, dict):
                return {k: resolve_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_recursive(item) for item in obj]
            elif isinstance(obj, str):
                # Check if this looks like an HCL reference or "known after apply"
                if obj == "(known after apply)" or "${" in obj:
                    # Try to resolve from HCL
                    resolved = self.hcl_resolver.resolve_value(obj, address)
                    return resolved if resolved != obj else obj
                return obj
            else:
                return obj
        
        return resolve_recursive(resolved_config)
    
    def _process_sensitive_values(self, config: Dict, resource_change: Dict) -> Dict:
        """
        Process sensitive values in configuration.
        
        Args:
            config: Resource configuration
            resource_change: Full resource change object (contains sensitive markers)
            
        Returns:
            Configuration with sensitive values masked if show_sensitive=False
        """
        if self.show_sensitive:
            return config
        
        # Get sensitive value paths from change metadata
        change = resource_change.get('change', {})
        before_sensitive = change.get('before_sensitive', {})
        
        if not before_sensitive:
            return config
        
        # Deep copy to avoid modifying original
        import copy
        processed_config = copy.deepcopy(config)
        
        # Recursively mask sensitive values
        def mask_sensitive(obj, sensitive_map):
            if isinstance(sensitive_map, bool) and sensitive_map:
                return "[SENSITIVE]"
            elif isinstance(sensitive_map, dict) and isinstance(obj, dict):
                return {k: mask_sensitive(obj.get(k), sensitive_map.get(k, False)) 
                       for k in obj.keys()}
            elif isinstance(sensitive_map, list) and isinstance(obj, list):
                return [mask_sensitive(obj[i] if i < len(obj) else None, 
                                      sensitive_map[i] if i < len(sensitive_map) else False)
                       for i in range(max(len(obj), len(sensitive_map)))]
            else:
                return obj
        
        return mask_sensitive(processed_config, before_sensitive)


class ResourceComparison:
    """Represents a single resource address with configuration across all environments."""
    
    def __init__(self, resource_address: str, resource_type: str):
        """
        Initialize a resource comparison.
        
        Args:
            resource_address: Terraform resource address (e.g., "aws_instance.web[0]")
            resource_type: Terraform resource type (e.g., "aws_instance")
        """
        self.resource_address = resource_address
        self.resource_type = resource_type
        self.env_configs: Dict[str, Optional[Dict]] = {}
        self.env_configs_raw: Dict[str, Optional[Dict]] = {}  # Store unmasked configs for comparison
        self.is_present_in: Set[str] = set()
        self.has_differences = False
        self.ignored_attributes: Set[str] = set()  # Track which attributes were ignored
    
    def add_environment_config(self, env_label: str, config: Optional[Dict], config_raw: Optional[Dict] = None) -> None:
        """
        Add configuration for an environment.
        
        Args:
            env_label: Environment label
            config: Configuration dict (possibly with masked sensitive values) or None if resource doesn't exist
            config_raw: Unmasked configuration for comparison purposes
        """
        self.env_configs[env_label] = config
        self.env_configs_raw[env_label] = config_raw if config_raw is not None else config
        if config is not None:
            self.is_present_in.add(env_label)
    
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
    
    def mark_changed_sensitive_values(self) -> None:
        """
        Mark sensitive values that changed between environments with (changed) indicator.
        Compares RAW configs to detect changes, then updates masked configs.
        """
        if not self.has_differences:
            return
        
        # Get baseline (first environment)
        env_labels = list(self.env_configs.keys())
        if len(env_labels) < 2:
            return
        
        baseline_label = env_labels[0]
        baseline_raw = self.env_configs_raw.get(baseline_label)
        baseline_masked = self.env_configs.get(baseline_label)
        
        if not baseline_raw or not baseline_masked:
            return
        
        # For each other environment, detect which sensitive fields changed
        for env_label in env_labels[1:]:
            other_raw = self.env_configs_raw.get(env_label)
            other_masked = self.env_configs.get(env_label)
            
            if not other_raw or not other_masked:
                continue
            
            # Recursively mark changed sensitive values
            self.env_configs[env_label] = self._mark_changed_recursive(
                baseline_raw, other_raw, baseline_masked, other_masked
            )
    
    def _mark_changed_recursive(self, baseline_raw: Any, other_raw: Any, 
                                baseline_masked: Any, other_masked: Any) -> Any:
        """
        Recursively compare raw and masked values, marking changed sensitive fields.
        
        Args:
            baseline_raw: Unmasked baseline value
            other_raw: Unmasked comparison value
            baseline_masked: Masked baseline value
            other_masked: Masked comparison value
            
        Returns:
            Updated masked value with (changed) indicators
        """
        # If the masked value is [SENSITIVE] and raw values differ, mark as changed
        if isinstance(other_masked, str) and other_masked == "[SENSITIVE]":
            if baseline_raw != other_raw:
                return "[SENSITIVE] (changed)"
            return other_masked
        
        # Recursively process dictionaries
        if isinstance(other_masked, dict) and isinstance(baseline_masked, dict):
            result = {}
            for key in other_masked.keys():
                baseline_raw_val = baseline_raw.get(key) if isinstance(baseline_raw, dict) else None
                other_raw_val = other_raw.get(key) if isinstance(other_raw, dict) else None
                baseline_masked_val = baseline_masked.get(key)
                other_masked_val = other_masked.get(key)
                
                result[key] = self._mark_changed_recursive(
                    baseline_raw_val, other_raw_val, 
                    baseline_masked_val, other_masked_val
                )
            return result
        
        # Recursively process lists
        if isinstance(other_masked, list) and isinstance(baseline_masked, list):
            result = []
            for i in range(len(other_masked)):
                baseline_raw_val = baseline_raw[i] if isinstance(baseline_raw, list) and i < len(baseline_raw) else None
                other_raw_val = other_raw[i] if isinstance(other_raw, list) and i < len(other_raw) else None
                baseline_masked_val = baseline_masked[i] if i < len(baseline_masked) else None
                other_masked_val = other_masked[i]
                
                result.append(self._mark_changed_recursive(
                    baseline_raw_val, other_raw_val,
                    baseline_masked_val, other_masked_val
                ))
            return result
        
        return other_masked
    
    def has_sensitive_differences(self) -> bool:
        """
        Check if any configs contain [SENSITIVE] markers that differ.
        
        Returns:
            True if sensitive values differ across environments
        """
        def contains_sensitive(obj):
            """Recursively check if object contains [SENSITIVE] marker."""
            if isinstance(obj, str):
                return obj == "[SENSITIVE]"
            elif isinstance(obj, dict):
                return any(contains_sensitive(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(contains_sensitive(item) for item in obj)
            return False
        
        # Check if any config has sensitive values
        has_any_sensitive = any(
            contains_sensitive(cfg) for cfg in self.env_configs.values() if cfg is not None
        )
        
        return has_any_sensitive and self.has_differences


class MultiEnvReport:
    """Orchestrates multi-environment comparison and report generation."""
    
    def __init__(self, environments: List[EnvironmentPlan], 
                 show_sensitive: bool = False, diff_only: bool = False,
                 ignore_config: Optional[Dict] = None):
        """
        Initialize the multi-environment report.
        
        Args:
            environments: List of EnvironmentPlan objects to compare
            show_sensitive: Whether to reveal sensitive values
            diff_only: Whether to filter out identical resources
            ignore_config: Optional ignore configuration dict
        """
        self.environments = environments
        self.show_sensitive = show_sensitive
        self.diff_only = diff_only
        self.ignore_config = ignore_config
        self.resource_comparisons: List[ResourceComparison] = []
        self.summary_stats: Dict[str, int] = {}
        self.ignore_statistics: Dict[str, Any] = {
            'total_ignored_attributes': 0,
            'resources_with_ignores': 0,
            'all_changes_ignored': 0,
            'ignore_breakdown': {}  # Map attribute name -> count
        }
    
    def load_environments(self) -> None:
        """Load all environment plan files."""
        for env in self.environments:
            env.load()
    
    def build_comparisons(self) -> None:
        """Build ResourceComparison objects for each unique resource address."""
        # Extract all unique resource addresses
        all_addresses: Set[str] = set()
        for env in self.environments:
            all_addresses.update(env.before_values.keys())
        
        # Build comparison for each address
        for address in sorted(all_addresses):
            # Extract resource type from address (e.g., "aws_instance.web" -> "aws_instance")
            resource_type = address.split('.')[0] if '.' in address else address
            
            comparison = ResourceComparison(address, resource_type)
            
            # Track which attributes were actually ignored for this resource
            ignored_for_resource: Set[str] = set()
            
            # Add config from each environment (with ignore config applied)
            for env in self.environments:
                config = env.before_values.get(address)
                config_raw = env.before_values_raw.get(address)
                
                # Apply ignore filtering if config exists
                if config is not None and self.ignore_config:
                    # Track what gets ignored before filtering
                    ignored_attrs = get_ignored_attributes(config, self.ignore_config, resource_type)
                    ignored_for_resource.update(ignored_attrs)
                    
                    # Apply filtering
                    config = apply_ignore_config(config, self.ignore_config, resource_type)
                    
                if config_raw is not None and self.ignore_config:
                    config_raw = apply_ignore_config(config_raw, self.ignore_config, resource_type)
                    
                comparison.add_environment_config(env.label, config, config_raw)
            
            # Store ignored attributes for this resource
            comparison.ignored_attributes = ignored_for_resource
            
            # Detect differences (uses raw values AFTER ignore filtering)
            comparison.detect_differences()
            
            # Mark changed sensitive values with (changed) indicator
            comparison.mark_changed_sensitive_values()
            
            # Update ignore statistics
            if ignored_for_resource:
                self.ignore_statistics['resources_with_ignores'] += 1
                self.ignore_statistics['total_ignored_attributes'] += len(ignored_for_resource)
                
                # Track breakdown by attribute name
                for attr in ignored_for_resource:
                    self.ignore_statistics['ignore_breakdown'][attr] = \
                        self.ignore_statistics['ignore_breakdown'].get(attr, 0) + 1
                
                # Check if ALL changes were ignored (resource became identical after filtering)
                if not comparison.has_differences:
                    self.ignore_statistics['all_changes_ignored'] += 1
            
            self.resource_comparisons.append(comparison)
    
    def calculate_summary(self) -> None:
        """Calculate summary statistics for the report."""
        self.summary_stats = {
            'total_environments': len(self.environments),
            'total_unique_resources': len(self.resource_comparisons),
            'resources_with_differences': sum(1 for rc in self.resource_comparisons if rc.has_differences),
            'resources_consistent': sum(1 for rc in self.resource_comparisons if not rc.has_differences),
            'resources_missing_from_some': sum(1 for rc in self.resource_comparisons 
                                               if len(rc.is_present_in) < len(self.environments))
        }
    
    def generate_html(self, output_path: str) -> None:
        """Generate HTML comparison report.
        
        Args:
            output_path: Path to write the HTML report
        """
        # Build environment labels list
        env_labels = [env.label for env in self.environments]
        
        # Build HTML content
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('    <title>Multi-Environment Terraform Comparison Report</title>')
        html_parts.append('    <style>')
        html_parts.append('        * { margin: 0; padding: 0; box-sizing: border-box; }')
        html_parts.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }')
        html_parts.append('        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }')
        html_parts.append('        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }')
        html_parts.append('        h1 { font-size: 2em; margin-bottom: 10px; }')
        html_parts.append('        header p { font-size: 1em; opacity: 0.9; }')
        html_parts.append('        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }')
        html_parts.append('        .summary-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }')
        html_parts.append('        .summary-card .number { font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }')
        html_parts.append('        .summary-card .label { color: #666; font-size: 0.9em; }')
        html_parts.append('        .summary-card.total .number { color: #667eea; }')
        html_parts.append('        .summary-card.updated .number { color: #ffa94d; }')
        html_parts.append('        .summary-card.created .number { color: #51cf66; }')
        html_parts.append('        .section { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }')
        html_parts.append('        .section h2 { font-size: 1.5em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }')
        html_parts.append('        .toggle-all { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px; margin-bottom: 20px; }')
        html_parts.append('        .toggle-all:hover { background: #5568d3; }')
        html_parts.append('        .resource-change { background: white; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }')
        html_parts.append('        .resource-change-header { padding: 15px 20px; cursor: pointer; background: #f7fafc; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; gap: 10px; }')
        html_parts.append('        .resource-change-header:hover { background: #edf2f7; }')
        html_parts.append('        .toggle-icon { transition: transform 0.2s; font-weight: bold; color: #667eea; }')
        html_parts.append('        .toggle-icon.collapsed { transform: rotate(-90deg); }')
        html_parts.append('        .resource-name { font-weight: 600; color: #2d3748; flex: 1; font-family: "Monaco", "Menlo", monospace; font-size: 0.95em; }')
        html_parts.append('        .resource-status { font-size: 13px; padding: 4px 10px; border-radius: 4px; font-weight: 500; }')
        html_parts.append('        .resource-status.identical { background: #d3f9d8; color: #2b8a3e; }')
        html_parts.append('        .resource-status.different { background: #fff4e6; color: #d97706; }')
        html_parts.append('        .resource-change-content { padding: 20px; display: none; background: #fafafa; }')
        html_parts.append('        .resource-change-content.expanded { display: block; }')
        html_parts.append('        .change-diff { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }')
        html_parts.append('        .diff-column { background: white; border-radius: 4px; overflow: hidden; border: 1px solid #e2e8f0; }')
        html_parts.append('        .diff-header { padding: 10px 15px; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; background: #e3f2fd; color: #1976d2; }')
        html_parts.append('        .env-content { padding: 15px; }')
        html_parts.append('        .env-action { font-weight: 600; padding: 4px 10px; border-radius: 3px; display: inline-block; margin-bottom: 10px; font-size: 12px; }')
        html_parts.append('        .env-action.create { background: #d3f9d8; color: #2b8a3e; }')
        html_parts.append('        .env-action.update { background: #fff4e6; color: #d97706; }')
        html_parts.append('        .env-action.delete { background: #ffe0e0; color: #c92a2a; }')
        html_parts.append('        .env-action.no-op { background: #e9ecef; color: #495057; }')
        html_parts.append('        .env-action.missing { background: #f1f3f5; color: #868e96; }')
        html_parts.append('        .config-json { font-family: "Monaco", "Menlo", monospace; font-size: 0.85em; white-space: pre-wrap; background: #f8f9fa; padding: 12px; border-radius: 5px; line-height: 1.5; word-break: break-word; margin-top: 10px; border: 1px solid #e2e8f0; }')
        html_parts.append('        .json-content { font-family: "Monaco", "Menlo", monospace; font-size: 0.85em; white-space: pre-wrap; background: #f8f9fa; padding: 12px; border-radius: 5px; line-height: 1.5; word-break: break-word; margin: 0; border: none; }')
        html_parts.append('        .unchanged { color: #495057; }')
        html_parts.append('        .removed { background-color: #ffe0e0; color: #c92a2a; display: block; }')
        html_parts.append('        .added { background-color: #d3f9d8; color: #2b8a3e; display: block; }')
        html_parts.append('        .baseline-removed { background-color: #bbdefb; color: #0d47a1; display: block; }')
        html_parts.append('        .baseline-added { background-color: #e3f2fd; color: #1565c0; display: block; }')
        html_parts.append('        .char-removed { background-color: #ffc9c9; color: #c92a2a; }')
        html_parts.append('        .char-added { background-color: #b2f2bb; color: #2b8a3e; }')
        html_parts.append('        .baseline-char-removed { background-color: #90caf9; color: #01579b; }')
        html_parts.append('        .baseline-char-added { background-color: #e3f2fd; color: #1565c0; }')
        html_parts.append('        .opacity-50 { opacity: 0.5; }')
        html_parts.append('        .sensitive-indicator { background: #fff4e6; color: #d97706; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-left: 8px; }')
        html_parts.append('        .hcl-resolved { background: #e7f5ff; color: #1971c2; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-left: 8px; }')
        html_parts.append('    </style>')
        html_parts.append('    <script>')
        html_parts.append('        function toggleAll() {')
        html_parts.append('            const contents = document.querySelectorAll(".resource-change-content");')
        html_parts.append('            const icons = document.querySelectorAll(".toggle-icon");')
        html_parts.append('            const anyExpanded = Array.from(contents).some(c => c.classList.contains("expanded"));')
        html_parts.append('            contents.forEach(content => {')
        html_parts.append('                if (anyExpanded) { content.classList.remove("expanded"); }')
        html_parts.append('                else { content.classList.add("expanded"); }')
        html_parts.append('            });')
        html_parts.append('            icons.forEach(icon => {')
        html_parts.append('                if (anyExpanded) { icon.classList.add("collapsed"); }')
        html_parts.append('                else { icon.classList.remove("collapsed"); }')
        html_parts.append('            });')
        html_parts.append('        }')
        html_parts.append('        function toggleResource(element) {')
        html_parts.append('            const header = element.closest(".resource-change-header");')
        html_parts.append('            const content = header.nextElementSibling;')
        html_parts.append('            const icon = header.querySelector(".toggle-icon");')
        html_parts.append('            content.classList.toggle("expanded");')
        html_parts.append('            icon.classList.toggle("collapsed");')
        html_parts.append('        }')
        html_parts.append('    </script>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('    <div class="container">')
        html_parts.append('        <header>')
        html_parts.append('            <h1>Multi-Environment Terraform Plan Comparison</h1>')
        html_parts.append(f'            <p>Comparing {len(env_labels)} environments: {", ".join(env_labels)}</p>')
        html_parts.append('        </header>')
        
        # Summary cards
        html_parts.append('        <div class="summary">')
        html_parts.append('            <div class="summary-card total">')
        html_parts.append(f'                <div class="number">{self.summary_stats["total_unique_resources"]}</div>')
        html_parts.append('                <div class="label">Total Resources</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card total">')
        html_parts.append(f'                <div class="number">{self.summary_stats["total_environments"]}</div>')
        html_parts.append('                <div class="label">Environments</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card updated">')
        html_parts.append(f'                <div class="number">{self.summary_stats["resources_with_differences"]}</div>')
        html_parts.append('                <div class="label">With Differences</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card created">')
        html_parts.append(f'                <div class="number">{self.summary_stats["resources_consistent"]}</div>')
        html_parts.append('                <div class="label">Consistent</div>')
        html_parts.append('            </div>')
        
        # Show ignore statistics if any ignoring was applied
        if self.ignore_config and self.ignore_statistics['total_ignored_attributes'] > 0:
            html_parts.append('            <div class="summary-card total" style="background: #fff4e6; border-left: 4px solid #f59e0b;">')
            html_parts.append(f'                <div class="number">{self.ignore_statistics["total_ignored_attributes"]}</div>')
            html_parts.append('                <div class="label">Attributes Ignored</div>')
            html_parts.append('            </div>')
            html_parts.append('            <div class="summary-card created" style="background: #ecfdf5; border-left: 4px solid #10b981;">')
            html_parts.append(f'                <div class="number">{self.ignore_statistics["all_changes_ignored"]}</div>')
            html_parts.append('                <div class="label">All Changes Ignored</div>')
            html_parts.append('            </div>')
        
        html_parts.append('        </div>')
        
        # Comparison section with collapsible resource blocks
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>Resource Comparison</h2>')
        html_parts.append('            <button class="toggle-all" onclick="toggleAll()">Expand/Collapse All</button>')
        
        # Filter if diff_only is enabled
        comparisons_to_show = self.resource_comparisons
        if self.diff_only:
            comparisons_to_show = [rc for rc in self.resource_comparisons if rc.has_differences]
        
        for rc in comparisons_to_show:
            is_identical = not rc.has_differences
            status_class = 'identical' if is_identical else 'different'
            status_text = '✓ Identical' if is_identical else '⚠ Different'
            
            # Check for sensitive value differences
            has_sensitive_diff = rc.has_sensitive_differences()
            
            html_parts.append('            <div class="resource-change">')
            html_parts.append('                <div class="resource-change-header" onclick="toggleResource(this)">')
            html_parts.append('                    <span class="toggle-icon collapsed">▼</span>')
            html_parts.append(f'                    <span class="resource-name">{rc.resource_address}</span>')
            html_parts.append(f'                    <span class="resource-status {status_class}">{status_text}</span>')
            
            # Show ignored attributes indicator
            if rc.ignored_attributes:
                ignored_count = len(rc.ignored_attributes)
                ignored_list = ', '.join(sorted(rc.ignored_attributes))
                html_parts.append(f'                    <span class="badge" style="background: #fbbf24; color: #78350f;" title="Ignored: {ignored_list}">{ignored_count} attributes ignored</span>')
            
            if has_sensitive_diff:
                html_parts.append('                    <span class="sensitive-indicator">⚠️ SENSITIVE DIFF</span>')
            
            html_parts.append('                </div>')
            html_parts.append('                <div class="resource-change-content">')
            html_parts.append('                    <div class="change-diff">')
            
            # Get baseline environment (first in the list)
            baseline_label = env_labels[0]
            baseline_config = rc.env_configs.get(baseline_label)
            
            # Show each environment's configuration
            for idx, env_label in enumerate(env_labels):
                config = rc.env_configs.get(env_label)
                html_parts.append('                        <div class="diff-column">')
                html_parts.append(f'                            <div class="diff-header">{env_label}</div>')
                html_parts.append('                            <div class="env-content">')
                
                if config is None:
                    html_parts.append('                                <div class="env-action missing">NOT PRESENT</div>')
                    html_parts.append('                                <p style="color: #868e96; font-size: 0.9em;">Resource not found in this environment</p>')
                else:
                    # Determine action type (for multi-env we don't have before/after, just config)
                    html_parts.append('                                <div class="env-action no-op">PRESENT</div>')
                    
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
                            # Replace red/green classes with blue for baseline (both line and character level)
                            baseline_html = (before_html
                                .replace('class="removed"', 'class="baseline-removed"')
                                .replace('class="added"', 'class="baseline-added"')
                                .replace('char-added', 'baseline-char-added')
                                .replace('char-removed', 'baseline-char-removed'))
                            html_parts.append(f'                                {baseline_html}')
                        else:
                            # No other environment to compare to, show plain JSON
                            config_json = json.dumps(config, indent=2, sort_keys=True)
                            html_parts.append(f'                                <pre class="config-json">{config_json}</pre>')
                    else:
                        # Non-baseline environments: show character-level diff against baseline
                        if baseline_config is None:
                            # Baseline doesn't have this resource, show as added
                            config_json = json.dumps(config, indent=2, sort_keys=True)
                            html_parts.append('                                <div style="background: #fff4e6; color: #d97706; padding: 8px; border-radius: 4px; margin-bottom: 10px; font-size: 0.85em;">')
                            html_parts.append('                                    ⚠️ BASELINE MISSING - Resource not present in baseline environment')
                            html_parts.append('                                </div>')
                            # Show highlighted as all "added"
                            lines = config_json.split('\n')
                            highlighted_lines = [f'<span class="added">{html.escape(line)}</span>' for line in lines]
                            html_parts.append(f'                                <pre class="json-content">{"<br>".join(highlighted_lines)}</pre>')
                        else:
                            # Generate character-level diff HTML
                            _, after_html = _highlight_json_diff(baseline_config, config)
                            html_parts.append(f'                                {after_html}')
                
                html_parts.append('                            </div>')
                html_parts.append('                        </div>')
            
            html_parts.append('                    </div>')
            html_parts.append('                </div>')
            html_parts.append('            </div>')
        
        html_parts.append('        </div>')
        html_parts.append('    </div>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        # Write HTML file
        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))
    
    def generate_text(self, verbose: bool = False) -> str:
        """Generate text comparison report for terminal output.
        
        Args:
            verbose: Whether to include full configuration details
            
        Returns:
            Formatted text report
        """
        import shutil
        
        # Get terminal width, default to 100 if not available
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 100
        
        # Build environment labels list
        env_labels = [env.label for env in self.environments]
        
        lines = []
        
        # Header
        lines.append("=" * terminal_width)
        lines.append("Multi-Environment Terraform Comparison Report")
        lines.append("=" * terminal_width)
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * terminal_width)
        lines.append(f"Total Environments: {self.summary_stats['total_environments']}")
        lines.append(f"Total Unique Resources: {self.summary_stats['total_unique_resources']}")
        lines.append(f"Resources with Differences: {self.summary_stats['resources_with_differences']}")
        lines.append(f"Resources Consistent: {self.summary_stats['resources_consistent']}")
        lines.append(f"Resources Missing from Some: {self.summary_stats['resources_missing_from_some']}")
        
        # Show ignore statistics if any ignoring was applied
        if self.ignore_config and self.ignore_statistics['total_ignored_attributes'] > 0:
            lines.append("")
            lines.append("IGNORE STATISTICS")
            lines.append(f"Total Ignored Attributes: {self.ignore_statistics['total_ignored_attributes']}")
            lines.append(f"Resources with Ignores: {self.ignore_statistics['resources_with_ignores']}")
            lines.append(f"Resources with All Changes Ignored: {self.ignore_statistics['all_changes_ignored']}")
            if self.ignore_statistics['ignore_breakdown']:
                lines.append("Breakdown by Attribute:")
                for attr, count in sorted(self.ignore_statistics['ignore_breakdown'].items()):
                    lines.append(f"  - {attr}: {count} resource(s)")
        
        lines.append("")
        
        # Resource comparison section
        lines.append("RESOURCE COMPARISON")
        lines.append("-" * terminal_width)
        lines.append("")
        
        # Filter if diff_only is enabled
        comparisons_to_show = self.resource_comparisons
        if self.diff_only:
            comparisons_to_show = [rc for rc in self.resource_comparisons if rc.has_differences]
        
        for rc in comparisons_to_show:
            status = "✓ IDENTICAL" if not rc.has_differences else "⚠ DIFFERENT"
            
            # Resource header
            lines.append(f"Resource: {rc.resource_address}")
            lines.append(f"Status: {status}")
            
            # Show ignored attributes count if any
            if rc.ignored_attributes:
                lines.append(f"Ignored Attributes: {len(rc.ignored_attributes)} ({', '.join(sorted(rc.ignored_attributes))})")
            
            # Check for sensitive differences
            if rc.has_sensitive_differences():
                lines.append("⚠️  SENSITIVE VALUE DIFFERENCES DETECTED")
            
            # Environment presence
            present_envs = ', '.join(sorted(rc.is_present_in))
            missing_envs = ', '.join(sorted(set(env_labels) - rc.is_present_in))
            
            if len(rc.is_present_in) < len(env_labels):
                lines.append(f"Present in: {present_envs}")
                lines.append(f"Missing from: {missing_envs}")
            else:
                lines.append(f"Present in all environments: {present_envs}")
            
            # Verbose mode: show configs
            if verbose:
                lines.append("")
                lines.append("Configurations:")
                for env_label in env_labels:
                    config = rc.env_configs.get(env_label)
                    lines.append(f"  [{env_label}]")
                    if config is None:
                        lines.append("    NOT PRESENT")
                    else:
                        config_json = json.dumps(config, indent=4, sort_keys=True)
                        # Indent each line
                        for line in config_json.split('\n'):
                            lines.append(f"    {line}")
                    lines.append("")
            
            lines.append("-" * terminal_width)
            lines.append("")
        
        return '\n'.join(lines)
