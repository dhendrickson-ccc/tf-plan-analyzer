#!/usr/bin/env python3
"""
Multi-Environment Terraform Plan Comparator

Compares Terraform plan "before" states across multiple environments
to identify configuration drift and ensure parity.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any


class EnvironmentPlan:
    """Represents a single environment's Terraform plan with extracted before state."""
    
    def __init__(self, label: str, plan_file_path: Path, 
                 hcl_resolver=None, tfvars_file: Optional[Path] = None):
        """
        Initialize an environment plan.
        
        Args:
            label: Human-readable environment name (e.g., "Development", "Production")
            plan_file_path: Path to the plan JSON file
            hcl_resolver: Optional HCLValueResolver for variable resolution
            tfvars_file: Optional environment-specific tfvars file
        """
        self.label = label
        self.plan_file_path = plan_file_path
        self.hcl_resolver = hcl_resolver
        self.tfvars_file = tfvars_file
        self.plan_data: Optional[Dict[str, Any]] = None
        self.before_values: Dict[str, Dict] = {}
    
    def load(self) -> None:
        """Load and parse the plan JSON file, extract before values."""
        with open(self.plan_file_path, 'r') as f:
            self.plan_data = json.load(f)
        
        # Extract before values from resource_changes
        resource_changes = self.plan_data.get('resource_changes', [])
        for rc in resource_changes:
            address = rc.get('address', '')
            change = rc.get('change', {})
            before = change.get('before')
            
            if address and before is not None:
                self.before_values[address] = before


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
        self.is_present_in: Set[str] = set()
        self.has_differences = False
    
    def add_environment_config(self, env_label: str, config: Optional[Dict]) -> None:
        """
        Add configuration for an environment.
        
        Args:
            env_label: Environment label
            config: Configuration dict or None if resource doesn't exist in this environment
        """
        self.env_configs[env_label] = config
        if config is not None:
            self.is_present_in.add(env_label)
    
    def detect_differences(self) -> None:
        """Detect if configurations differ across environments."""
        # Get all non-None configs
        configs = [cfg for cfg in self.env_configs.values() if cfg is not None]
        
        if len(configs) <= 1:
            self.has_differences = False
            return
        
        # Compare first config with all others
        baseline = json.dumps(configs[0], sort_keys=True)
        for cfg in configs[1:]:
            if json.dumps(cfg, sort_keys=True) != baseline:
                self.has_differences = True
                return
        
        self.has_differences = False


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
            
            # Add config from each environment
            for env in self.environments:
                config = env.before_values.get(address)
                comparison.add_environment_config(env.label, config)
            
            # Detect differences
            comparison.detect_differences()
            
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
        html_parts.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }')
        html_parts.append('        .container { max-width: 1600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
        html_parts.append('        h1 { color: #333; margin-bottom: 10px; }')
        html_parts.append('        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }')
        html_parts.append('        .summary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }')
        html_parts.append('        .summary-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }')
        html_parts.append('        .summary-card .value { font-size: 32px; font-weight: bold; }')
        html_parts.append('        table { width: 100%; border-collapse: collapse; margin-top: 20px; }')
        html_parts.append('        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }')
        html_parts.append('        th { background-color: #667eea; color: white; font-weight: 600; }')
        html_parts.append('        tr.has-diff { background-color: #fff3cd; }')
        html_parts.append('        tr.consistent { background-color: #d4edda; }')
        html_parts.append('        .resource-address { font-weight: 600; color: #333; }')
        html_parts.append('        .config-cell { max-width: 400px; overflow-x: auto; }')
        html_parts.append('        .config-json { font-family: "Courier New", monospace; font-size: 12px; white-space: pre-wrap; }')
        html_parts.append('        .not-present { color: #999; font-style: italic; }')
        html_parts.append('    </style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('    <div class="container">')
        html_parts.append('        <h1>🌍 Multi-Environment Terraform Comparison Report</h1>')
        html_parts.append(f'        <p>Comparing {len(env_labels)} environments: {", ".join(env_labels)}</p>')
        
        # Summary cards
        html_parts.append('        <div class="summary">')
        html_parts.append('            <div class="summary-card">')
        html_parts.append('                <h3>Total Environments</h3>')
        html_parts.append(f'                <div class="value">{self.summary_stats["total_environments"]}</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card">')
        html_parts.append('                <h3>Total Resources</h3>')
        html_parts.append(f'                <div class="value">{self.summary_stats["total_unique_resources"]}</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card">')
        html_parts.append('                <h3>Resources with Differences</h3>')
        html_parts.append(f'                <div class="value">{self.summary_stats["resources_with_differences"]}</div>')
        html_parts.append('            </div>')
        html_parts.append('            <div class="summary-card">')
        html_parts.append('                <h3>Consistent Resources</h3>')
        html_parts.append(f'                <div class="value">{self.summary_stats["resources_consistent"]}</div>')
        html_parts.append('            </div>')
        html_parts.append('        </div>')
        
        # Comparison table
        html_parts.append('        <table>')
        html_parts.append('            <thead>')
        html_parts.append('                <tr>')
        html_parts.append('                    <th>Resource Address</th>')
        for env_label in env_labels:
            html_parts.append(f'                    <th>{env_label}</th>')
        html_parts.append('                </tr>')
        html_parts.append('            </thead>')
        html_parts.append('            <tbody>')
        
        # Filter if diff_only is enabled
        comparisons_to_show = self.resource_comparisons
        if self.diff_only:
            comparisons_to_show = [rc for rc in self.resource_comparisons if rc.has_differences]
        
        for rc in comparisons_to_show:
            row_class = 'has-diff' if rc.has_differences else 'consistent'
            html_parts.append(f'                <tr class="{row_class}">')
            html_parts.append(f'                    <td class="resource-address">{rc.resource_address}</td>')
            
            for env_label in env_labels:
                config = rc.env_configs.get(env_label)
                if config is None:
                    html_parts.append('                    <td class="not-present">N/A</td>')
                else:
                    config_json = json.dumps(config, indent=2, sort_keys=True)
                    html_parts.append('                    <td class="config-cell">')
                    html_parts.append(f'                        <pre class="config-json">{config_json}</pre>')
                    html_parts.append('                    </td>')
            
            html_parts.append('                </tr>')
        
        html_parts.append('            </tbody>')
        html_parts.append('        </table>')
        html_parts.append('    </div>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        # Write HTML file
        with open(output_path, 'w') as f:
            f.write('\n'.join(html_parts))
