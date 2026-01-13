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
