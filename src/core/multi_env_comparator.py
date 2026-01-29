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
from src.lib.ignore_utils import apply_ignore_config, get_ignored_attributes

# Import shared HTML/CSS generation utilities
import src.lib.html_generation
from src.lib.diff_utils import highlight_char_diff, highlight_json_diff


class AttributeDiff:
    """Represents a single attribute's values across environments."""

    def __init__(
        self,
        attribute_name: str,
        env_values: Dict[str, Any],
        is_different: bool,
        attribute_type: str,
    ):
        """
        Initialize an attribute diff.

        Args:
            attribute_name: The name of the attribute (e.g., 'location', 'tags')
            env_values: Map of environment label -> attribute value
            is_different: Whether the attribute differs across environments
            attribute_type: Type of the attribute ('primitive', 'object', 'array')
        """
        self.attribute_name = attribute_name
        self.env_values = env_values
        self.is_different = is_different
        self.attribute_type = attribute_type
        # Normalization tracking (feature 007)
        self.ignored_due_to_normalization = False
        self.normalized_values: Dict[str, Any] = {}
        # Raw unmasked values for applying merged sensitive metadata
        self.env_values_raw: Dict[str, Any] = {}


# The diff highlighting functions now use shared utilities from src.lib.diff_utils
# Kept as module-level wrappers for backward compatibility
def _highlight_char_diff(before_str: str, after_str: str, is_baseline: bool = True) -> Tuple[str, str]:
    """Wrapper for shared highlight_char_diff utility with baseline comparison styling."""
    return highlight_char_diff(before_str, after_str, is_known_after_apply=False, is_baseline_comparison=is_baseline)


def _highlight_json_diff(before: Any, after: Any, is_baseline: bool = True) -> Tuple[str, str]:
    """Wrapper for shared highlight_json_diff utility with baseline comparison styling."""
    return highlight_json_diff(before, after, is_known_after_apply=False, is_baseline_comparison=is_baseline)


def _calculate_ignore_counts(
    config_ignored: Set[str], attr_diffs: List[AttributeDiff]
) -> Tuple[int, int]:
    """
    Calculate separate counts for config-ignored and normalization-ignored attributes.
    
    Args:
        config_ignored: Set of attribute names ignored via config
        attr_diffs: List of attribute diffs
        
    Returns:
        Tuple of (config_count, normalization_count)
    """
    config_count = len(config_ignored)
    
    # Count attributes ignored due to normalization
    norm_count = sum(1 for diff in attr_diffs if diff.ignored_due_to_normalization)
    
    return config_count, norm_count


def _render_ignore_badge(
    config_count: int,
    norm_count: int,
    config_ignored: Set[str],
    normalized_attrs: List[str]
) -> str:
    """
    Render the ignore badge with separate counts and tooltip breakdown.
    
    Args:
        config_count: Number of config-ignored attributes
        norm_count: Number of normalization-ignored attributes
        config_ignored: Set of config-ignored attribute names
        normalized_attrs: List of normalization-ignored attribute names
        
    Returns:
        HTML string for the badge
    """
    total_count = config_count + norm_count
    
    if total_count == 0:
        return ""
    
    # Build tooltip content with sections (using newlines for better readability)
    tooltip_parts = []
    
    if config_count > 0:
        config_items = "\n• ".join(sorted(config_ignored))
        tooltip_parts.append(f"Config:\n• {config_items}")
    
    if norm_count > 0:
        norm_items = "\n• ".join(sorted(normalized_attrs))
        tooltip_parts.append(f"Normalized:\n• {norm_items}")
    
    tooltip_text = "\n\n".join(tooltip_parts)
    
    # Build badge text
    if config_count > 0 and norm_count > 0:
        badge_text = f"{total_count} attributes ignored ({config_count} config, {norm_count} normalized)"
    elif norm_count > 0:
        badge_text = f"{norm_count} attributes ignored (normalized)"
    else:
        badge_text = f"{config_count} attributes ignored (config)"
    
    return f'<span class="badge" style="background: #fbbf24; color: #78350f;" data-tooltip="{html.escape(tooltip_text)}">{badge_text}</span>'


class EnvironmentPlan:
    """Represents a single environment's Terraform plan with extracted before state."""

    def __init__(
        self,
        label: str,
        plan_file_path: Path,
        tf_dir: Optional[str] = None,
        tfvars_file: Optional[str] = None,
        show_sensitive: bool = False,
    ):
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
        self.before_values_raw: Dict[str, Dict] = (
            {}
        )  # Store unmasked versions for comparison
        self.before_sensitive_metadata: Dict[str, Any] = {}  # Store sensitive metadata for cross-env merging
        self.hcl_resolver = None

    def load(self) -> None:
        """Load and parse the plan JSON file, extract before values."""
        with open(self.plan_file_path, "r") as f:
            self.plan_data = json.load(f)

        # Initialize HCL resolver if tf_dir provided
        if self.tf_dir:
            try:
                from hcl_value_resolver import HCLValueResolver

                self.hcl_resolver = HCLValueResolver(
                    tf_dir=self.tf_dir, tfvars_file=self.tfvars_file
                )
            except ImportError:
                # HCL resolver not available, continue without it
                pass

        # Extract before values from resource_changes
        resource_changes = self.plan_data.get("resource_changes", [])
        for rc in resource_changes:
            address = rc.get("address", "")
            change = rc.get("change", {})
            before = change.get("before")

            if address and before is not None:
                # Apply HCL resolution if available
                if self.hcl_resolver:
                    before = self._resolve_hcl_values(address, before)

                # Store raw version (before masking) for comparison
                import copy

                before_raw = copy.deepcopy(before)
                self.before_values_raw[address] = before_raw

                # Store sensitive metadata for cross-environment merging
                change = rc.get("change", {})
                before_sensitive = change.get("before_sensitive", {})
                self.before_sensitive_metadata[address] = before_sensitive

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
        change = resource_change.get("change", {})
        before_sensitive = change.get("before_sensitive", {})

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
                return {
                    k: mask_sensitive(obj.get(k), sensitive_map.get(k, False))
                    for k in obj.keys()
                }
            elif isinstance(sensitive_map, list) and isinstance(obj, list):
                return [
                    mask_sensitive(
                        obj[i] if i < len(obj) else None,
                        sensitive_map[i] if i < len(sensitive_map) else False,
                    )
                    for i in range(max(len(obj), len(sensitive_map)))
                ]
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
        self.env_configs_raw: Dict[str, Optional[Dict]] = (
            {}
        )  # Store unmasked configs for comparison
        self.is_present_in: Set[str] = set()
        self.has_differences = False
        self.ignored_attributes: Set[str] = set()  # Track which attributes were ignored
        self.attribute_diffs: List[AttributeDiff] = (
            []
        )  # Attribute-level diffs for HTML rendering
        # Normalization config (feature 007)
        self.normalization_config = None
        self.verbose_normalization = False  # For verbose logging (T058)
        # Merged sensitive metadata from all environments
        self.merged_sensitive_metadata: Dict[str, Any] = {}

    def add_environment_config(
        self, env_label: str, config: Optional[Dict], config_raw: Optional[Dict] = None, sensitive_metadata: Optional[Dict] = None
    ) -> None:
        """
        Add configuration for an environment.

        Args:
            env_label: Environment label
            config: Configuration dict (possibly with masked sensitive values) or None if resource doesn't exist
            config_raw: Unmasked configuration for comparison purposes
            sensitive_metadata: Sensitive field metadata from this environment's plan
        """
        self.env_configs[env_label] = config
        self.env_configs[env_label]['open'] = 'open'  # Default expanded
        self.env_configs_raw[env_label] = (
            config_raw if config_raw is not None else config
        )
        if config is not None:
            self.is_present_in.add(env_label)
        
        # Merge sensitive metadata from this environment
        if sensitive_metadata:
            self.merged_sensitive_metadata = self._merge_sensitive_metadata(
                self.merged_sensitive_metadata, sensitive_metadata
            )

    def _merge_sensitive_metadata(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge sensitive metadata from multiple environments.
        If ANY environment marks a field as sensitive, the merged result marks it sensitive.
        
        Args:
            base: Base sensitive metadata dict
            new: New sensitive metadata to merge in
            
        Returns:
            Merged metadata dict with OR logic for sensitive markers
        """
        if not new:
            return base
        if not base:
            return new
            
        result = {}
        all_keys = set(base.keys()) | set(new.keys())
        
        for key in all_keys:
            base_val = base.get(key)
            new_val = new.get(key)
            
            # If either is True (sensitive), mark as sensitive
            if base_val is True or new_val is True:
                result[key] = True
            # If both are dicts, recurse
            elif isinstance(base_val, dict) and isinstance(new_val, dict):
                result[key] = self._merge_sensitive_metadata(base_val, new_val)
            # If one is a dict, keep it
            elif isinstance(base_val, dict):
                result[key] = base_val
            elif isinstance(new_val, dict):
                result[key] = new_val
            # Otherwise take the new value
            else:
                result[key] = new_val or base_val
                
        return result

    def _mask_sensitive_value(self, value: Any, sensitive: Any) -> Any:
        """
        Recursively mask sensitive values based on merged metadata.
        
        Args:
            value: The value to potentially mask
            sensitive: Sensitive metadata (True, dict, or False)
            
        Returns:
            Masked value or original value
        """
        if sensitive is True:
            return "[SENSITIVE]"
        elif isinstance(sensitive, dict) and isinstance(value, dict):
            # Recursively mask nested values
            result = {}
            for key, val in value.items():
                if key in sensitive:
                    result[key] = self._mask_sensitive_value(val, sensitive[key])
                else:
                    result[key] = val
            return result
        elif isinstance(sensitive, list) and isinstance(value, list):
            # For lists, apply to all elements if sensitive is True, or per-element
            return [self._mask_sensitive_value(v, sensitive[0] if sensitive else False) for v in value]
        else:
            return value

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

    def compute_attribute_diffs(self) -> None:
        """
        Compute attribute-level diffs for rendering in HTML reports.

        Extracts top-level attributes from each environment's config and
        creates AttributeDiff objects that can be rendered as table rows.
        Skips attributes that are in the ignored_attributes set.
        
        Applies normalization if normalization_config is set (feature 007).
        Performance measurement included to ensure ≤10% overhead (SC-007).
        """
        import time  # For performance measurement (T060)
        
        start_time = time.perf_counter()
        normalization_start_time = 0.0
        normalization_total_time = 0.0
        
        self.attribute_diffs = []

        # Get all non-None configs
        env_labels = list(self.env_configs.keys())
        present_configs = {
            label: cfg for label, cfg in self.env_configs.items() if cfg is not None
        }

        if not present_configs:
            return

        # Extract all unique top-level attribute names across all environments
        all_attributes: Set[str] = set()
        for config in present_configs.values():
            if isinstance(config, dict):
                all_attributes.update(config.keys())

        # Remove ignored attributes
        all_attributes = all_attributes - self.ignored_attributes

        # Build AttributeDiff for each attribute
        for attr_name in sorted(all_attributes):
            env_values: Dict[str, Any] = {}
            env_values_raw: Dict[str, Any] = {}
            baseline_value = None
            is_different = False

            # Collect values from each environment (both masked and raw)
            for env_label in env_labels:
                config = self.env_configs.get(env_label)
                config_raw = self.env_configs_raw.get(env_label)
                
                if config is not None and isinstance(config, dict):
                    value = config.get(attr_name, None)
                    env_values[env_label] = value

                    # Check if this attribute differs from baseline
                    if baseline_value is None and value is not None:
                        baseline_value = value
                    elif value is not None and baseline_value is not None:
                        # Compare serialized versions for deep equality
                        if json.dumps(value, sort_keys=True) != json.dumps(
                            baseline_value, sort_keys=True
                        ):
                            is_different = True
                else:
                    env_values[env_label] = None
                
                # Also collect raw unmasked values
                if config_raw is not None and isinstance(config_raw, dict):
                    value_raw = config_raw.get(attr_name, None)
                    env_values_raw[env_label] = value_raw
                else:
                    env_values_raw[env_label] = None

            # Determine attribute type
            attr_type = "primitive"
            if baseline_value is not None:
                if isinstance(baseline_value, dict):
                    attr_type = "object"
                elif isinstance(baseline_value, list):
                    attr_type = "array"

            # Create AttributeDiff
            attr_diff = AttributeDiff(attr_name, env_values, is_different, attr_type)
            # Store raw unmasked values for applying merged sensitive metadata
            attr_diff.env_values_raw = env_values_raw
            
            # Apply normalization if config exists and attribute differs (US1)
            if is_different and self.normalization_config is not None:
                norm_start = time.perf_counter()
                
                from src.lib.normalization_utils import normalize_attribute_value
                
                # Normalize all environment values
                normalized_values = {}
                for env_label, value in env_values.items():
                    if value is not None:
                        normalized_values[env_label] = normalize_attribute_value(
                            attr_name, value, self.normalization_config, self.verbose_normalization
                        )
                    else:
                        normalized_values[env_label] = None
                
                # Always store normalized values for rendering
                attr_diff.normalized_values = normalized_values
                
                # Check if normalized values are all equal
                # Get first non-None normalized value as baseline
                normalized_baseline = None
                all_normalized_equal = True
                
                for norm_value in normalized_values.values():
                    if norm_value is not None:
                        if normalized_baseline is None:
                            normalized_baseline = norm_value
                        else:
                            # Compare normalized values
                            if json.dumps(norm_value, sort_keys=True) != json.dumps(
                                normalized_baseline, sort_keys=True
                            ):
                                all_normalized_equal = False
                                break
                
                # If all normalized values match, mark as ignored (hide from display)
                if all_normalized_equal and normalized_baseline is not None:
                    attr_diff.ignored_due_to_normalization = True
                
                normalization_total_time += time.perf_counter() - norm_start
            
            self.attribute_diffs.append(attr_diff)
        
        # Performance measurement logging (T060 - SC-007)
        total_time = time.perf_counter() - start_time
        if self.normalization_config is not None and total_time > 0:
            overhead_pct = (normalization_total_time / total_time) * 100
            if self.verbose_normalization:
                print(f"  [PERF] Normalization overhead: {normalization_total_time:.4f}s / {total_time:.4f}s ({overhead_pct:.1f}%)")
        
        # Update has_differences based on remaining non-normalized differences
        # After normalization filtering, check if any attribute diffs remain
        has_any_unignored_diff = any(
            diff.is_different and not diff.ignored_due_to_normalization
            for diff in self.attribute_diffs
        )
        
        # If all differences were normalized away, update has_differences
        if not has_any_unignored_diff and self.has_differences:
            # Only update if we actually had normalization applied
            if any(diff.ignored_due_to_normalization for diff in self.attribute_diffs):
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

    def _mark_changed_recursive(
        self, baseline_raw: Any, other_raw: Any, baseline_masked: Any, other_masked: Any
    ) -> Any:
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
                baseline_raw_val = (
                    baseline_raw.get(key) if isinstance(baseline_raw, dict) else None
                )
                other_raw_val = (
                    other_raw.get(key) if isinstance(other_raw, dict) else None
                )
                baseline_masked_val = baseline_masked.get(key)
                other_masked_val = other_masked.get(key)

                result[key] = self._mark_changed_recursive(
                    baseline_raw_val,
                    other_raw_val,
                    baseline_masked_val,
                    other_masked_val,
                )
            return result

        # Recursively process lists
        if isinstance(other_masked, list) and isinstance(baseline_masked, list):
            result = []
            for i in range(len(other_masked)):
                baseline_raw_val = (
                    baseline_raw[i]
                    if isinstance(baseline_raw, list) and i < len(baseline_raw)
                    else None
                )
                other_raw_val = (
                    other_raw[i]
                    if isinstance(other_raw, list) and i < len(other_raw)
                    else None
                )
                baseline_masked_val = (
                    baseline_masked[i] if i < len(baseline_masked) else None
                )
                other_masked_val = other_masked[i]

                result.append(
                    self._mark_changed_recursive(
                        baseline_raw_val,
                        other_raw_val,
                        baseline_masked_val,
                        other_masked_val,
                    )
                )
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
            contains_sensitive(cfg)
            for cfg in self.env_configs.values()
            if cfg is not None
        )

        return has_any_sensitive and self.has_differences


class MultiEnvReport:
    """Orchestrates multi-environment comparison and report generation."""

    def __init__(
        self,
        environments: List[EnvironmentPlan],
        show_sensitive: bool = False,
        diff_only: bool = False,
        ignore_config: Optional[Dict] = None,
        verbose_normalization: bool = False,
    ):
        """
        Initialize the multi-environment report.

        Args:
            environments: List of EnvironmentPlan objects to compare
            show_sensitive: Whether to reveal sensitive values
            diff_only: Whether to filter out identical resources
            ignore_config: Optional ignore configuration dict
            verbose_normalization: Whether to log normalization transformations (FR-015)
        """
        self.environments = environments
        self.show_sensitive = show_sensitive
        self.diff_only = diff_only
        self.ignore_config = ignore_config
        self.verbose_normalization = verbose_normalization
        self.resource_comparisons: List[ResourceComparison] = []
        self.summary_stats: Dict[str, int] = {}
        self.ignore_statistics: Dict[str, Any] = {
            "total_ignored_attributes": 0,
            "normalization_ignored_attributes": 0,  # Feature 007 US3
            "resources_with_ignores": 0,
            "all_changes_ignored": 0,
            "ignore_breakdown": {},  # Map attribute name -> count
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
            resource_type = address.split(".")[0] if "." in address else address

            comparison = ResourceComparison(address, resource_type)
            
            # Pass normalization config if available (feature 007)
            if self.ignore_config and "normalization_config" in self.ignore_config:
                comparison.normalization_config = self.ignore_config["normalization_config"]
                comparison.verbose_normalization = self.verbose_normalization

            # Track which attributes were actually ignored for this resource
            ignored_for_resource: Set[str] = set()

            # Add config from each environment (with ignore config applied)
            for env in self.environments:
                config = env.before_values.get(address)
                config_raw = env.before_values_raw.get(address)
                sensitive_metadata = env.before_sensitive_metadata.get(address)

                # Apply ignore filtering if config exists
                if config is not None and self.ignore_config:
                    # Track what gets ignored before filtering
                    ignored_attrs = get_ignored_attributes(
                        config, self.ignore_config, resource_type
                    )
                    ignored_for_resource.update(ignored_attrs)

                    # Apply filtering
                    config = apply_ignore_config(
                        config, self.ignore_config, resource_type
                    )

                if config_raw is not None and self.ignore_config:
                    config_raw = apply_ignore_config(
                        config_raw, self.ignore_config, resource_type
                    )

                comparison.add_environment_config(env.label, config, config_raw, sensitive_metadata)

            # Store ignored attributes for this resource
            comparison.ignored_attributes = ignored_for_resource

            # Detect differences (uses raw values AFTER ignore filtering)
            comparison.detect_differences()

            # Compute attribute-level diffs for HTML rendering
            comparison.compute_attribute_diffs()

            # Mark changed sensitive values with (changed) indicator
            comparison.mark_changed_sensitive_values()
            
            # Track normalization ignores (feature 007 US3)
            norm_ignored_count = sum(
                1 for diff in comparison.attribute_diffs 
                if diff.ignored_due_to_normalization
            )
            if norm_ignored_count > 0:
                self.ignore_statistics["normalization_ignored_attributes"] += norm_ignored_count

            # Update ignore statistics
            if ignored_for_resource:
                self.ignore_statistics["resources_with_ignores"] += 1
                self.ignore_statistics["total_ignored_attributes"] += len(
                    ignored_for_resource
                )

                # Track breakdown by attribute name
                for attr in ignored_for_resource:
                    self.ignore_statistics["ignore_breakdown"][attr] = (
                        self.ignore_statistics["ignore_breakdown"].get(attr, 0) + 1
                    )

                # Check if ALL changes were ignored (resource became identical after filtering)
                if not comparison.has_differences:
                    self.ignore_statistics["all_changes_ignored"] += 1

            self.resource_comparisons.append(comparison)

    def _detect_sortable_fields(self, attr_diff) -> List[str]:
        """
        Detect common fields across array-of-object values for field-based sorting.
        
        Returns intersection of field names present in ALL environments to ensure
        consistent sorting across environments.
        
        Args:
            attr_diff: AttributeDiff object containing env values
            
        Returns:
            Sorted list of common field names, empty if not applicable
        """
        values = attr_diff.normalized_values.values() if attr_diff.normalized_values else attr_diff.env_values_raw.values()
        
        # Filter to only array-of-object values
        array_values = [
            val for val in values
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict)
        ]
        
        if not array_values:
            return []
        
        # Get field sets from each environment's first object
        field_sets = [set(arr[0].keys()) for arr in array_values]
        
        # Intersection: only fields present in ALL environments
        if field_sets:
            common_fields = set.intersection(*field_sets)
            return sorted(common_fields)
        
        return []

    def calculate_summary(self) -> None:
        """Calculate summary statistics for the report."""
        self.summary_stats = {
            "total_environments": len(self.environments),
            "total_unique_resources": len(self.resource_comparisons),
            "resources_with_differences": sum(
                1 for rc in self.resource_comparisons if rc.has_differences
            ),
            "resources_consistent": sum(
                1 for rc in self.resource_comparisons if not rc.has_differences
            ),
            "resources_missing_from_some": sum(
                1
                for rc in self.resource_comparisons
                if len(rc.is_present_in) < len(self.environments)
            ),
        }

    @staticmethod
    def _sanitize_for_html_id(text: str) -> str:
        """
        Sanitize text for use as HTML ID by replacing special characters.

        Replaces characters that are invalid or problematic in HTML IDs:
        . [ ] : / with hyphens (-)

        Args:
            text: Text to sanitize (e.g., resource address or attribute name)

        Returns:
            Sanitized text safe for use in HTML id attributes

        Examples:
            >>> MultiEnvReport._sanitize_for_html_id("aws_instance.web")
            'aws_instance-web'
            >>> MultiEnvReport._sanitize_for_html_id("sku.0.tier")
            'sku-0-tier'
            >>> MultiEnvReport._sanitize_for_html_id("tags[\"Environment\"]")
            'tags--Environment--'
        """
        return text.replace(".", "-").replace("[", "-").replace("]", "-").replace(":", "-").replace("/", "-")

    def generate_html(self, output_path: str) -> None:
        """Generate HTML comparison report.

        Args:
            output_path: Path to write the HTML report
        """
        # Build environment labels list
        env_labels = [env.label for env in self.environments]

        # Build HTML content
        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append('<html lang="en">')
        html_parts.append("<head>")
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append(
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
        html_parts.append(
            "    <title>Multi-Environment Terraform Comparison Report</title>"
        )
        html_parts.append(f"    {src.lib.html_generation.generate_full_styles()}")
        html_parts.append("    <style>")
        html_parts.append("        /* Additional multi-env specific styles */")
        html_parts.append(
            "        .hcl-resolved { background: #e7f5ff; color: #1971c2; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-left: 8px; }"
        )
        html_parts.append("    </style>")
        html_parts.append("    <script>")
        html_parts.append("        function toggleAll() {")
        html_parts.append(
            '            const contents = document.querySelectorAll(".resource-change-content");'
        )
        html_parts.append(
            '            const icons = document.querySelectorAll(".toggle-icon");'
        )
        html_parts.append(
            '            const anyHidden = Array.from(contents).some(c => c.classList.contains("hidden"));'
        )
        html_parts.append("            contents.forEach(content => {")
        html_parts.append(
            '                if (anyHidden) { content.classList.remove("hidden"); }'
        )
        html_parts.append('                else { content.classList.add("hidden"); }')
        html_parts.append("            });")
        html_parts.append("            icons.forEach(icon => {")
        html_parts.append(
            '                if (anyHidden) { icon.classList.remove("collapsed"); }'
        )
        html_parts.append(
            '                else { icon.classList.add("collapsed"); }'
        )
        html_parts.append("            });")
        html_parts.append("        }")
        html_parts.append("        function toggleResource(element) {")
        html_parts.append(
            '            const header = element.closest(".resource-change-header");'
        )
        html_parts.append("            const content = header.nextElementSibling;")
        html_parts.append(
            '            const icon = header.querySelector(".toggle-icon");'
        )
        html_parts.append('            content.classList.toggle("hidden");')
        html_parts.append('            icon.classList.toggle("collapsed");')
        html_parts.append("        }")
        html_parts.append("        // Synchronized horizontal scrolling for value containers")
        html_parts.append("        document.addEventListener('DOMContentLoaded', function() {")
        html_parts.append("            document.querySelectorAll('.attribute-section').forEach(section => {")
        html_parts.append("                const containers = section.querySelectorAll('.value-container');")
        html_parts.append("                if (containers.length < 2) return;")
        html_parts.append("                let isScrolling = false;")
        html_parts.append("                containers.forEach(container => {")
        html_parts.append("                    container.addEventListener('scroll', function() {")
        html_parts.append("                        if (isScrolling) return;")
        html_parts.append("                        isScrolling = true;")
        html_parts.append("                        const scrollLeft = this.scrollLeft;")
        html_parts.append("                        containers.forEach(otherContainer => {")
        html_parts.append("                            if (otherContainer !== this) {")
        html_parts.append("                                otherContainer.scrollLeft = scrollLeft;")
        html_parts.append("                            }")
        html_parts.append("                        });")
        html_parts.append("                        setTimeout(() => { isScrolling = false; }, 10);")
        html_parts.append("                    });")
        html_parts.append("                });")
        html_parts.append("            });")
        html_parts.append("        });")
        html_parts.append("")
        html_parts.append("        // JSON sorting and diff re-rendering")
        html_parts.append("        function handleSortChange(selectElement) {")
        html_parts.append("            const attributeSection = selectElement.closest('.attribute-section');")
        html_parts.append("            const envColumns = attributeSection.querySelectorAll('.env-value-column[data-json-value]');")
        html_parts.append("            const sortOption = selectElement.value;  // Full option: 'sorted', 'unsorted', or 'field:xxx'")
        html_parts.append("")
        html_parts.append("            // Parse JSON data from all environments")
        html_parts.append("            const envData = [];")
        html_parts.append("            envColumns.forEach(column => {")
        html_parts.append("                try {")
        html_parts.append("                    const jsonValue = JSON.parse(column.getAttribute('data-json-value'));")
        html_parts.append("                    const envLabel = column.getAttribute('data-env');")
        html_parts.append("                    const isBaseline = column.getAttribute('data-is-baseline') === 'true';")
        html_parts.append("                    envData.push({ column, jsonValue, envLabel, isBaseline });")
        html_parts.append("                } catch (e) {")
        html_parts.append("                    console.error('Failed to parse JSON for re-sorting:', e);")
        html_parts.append("                }")
        html_parts.append("            });")
        html_parts.append("")
        html_parts.append("            if (envData.length === 0) return;")
        html_parts.append("")
        html_parts.append("            // Find baseline environment")
        html_parts.append("            const baseline = envData.find(e => e.isBaseline);")
        html_parts.append("            if (!baseline) return;")
        html_parts.append("")
        html_parts.append("            // Re-render each environment's value with new sort order")
        html_parts.append("            envData.forEach(env => {")
        html_parts.append("                const valueContainer = env.column.querySelector('.value-container');")
        html_parts.append("                if (!valueContainer) return;")
        html_parts.append("")
        html_parts.append("                if (env.isBaseline) {")
        html_parts.append("                    // For baseline, compare against first different env")
        html_parts.append("                    const otherEnv = envData.find(e => !e.isBaseline && jsonStringify(sortJson(e.jsonValue, sortOption)) !== jsonStringify(sortJson(baseline.jsonValue, sortOption)));")
        html_parts.append("                    if (otherEnv) {")
        html_parts.append("                        const [beforeHtml, _] = highlightJsonDiff(env.jsonValue, otherEnv.jsonValue, sortOption, true);")
        html_parts.append("                        valueContainer.innerHTML = beforeHtml;")
        html_parts.append("                    } else {")
        html_parts.append("                        // No differences, show plain JSON")
        html_parts.append('                        valueContainer.innerHTML = \'<pre class="json-content">\' + escapeHtml(jsonStringify(sortJson(env.jsonValue, sortOption))) + \'</pre>\';')
        html_parts.append("                    }")
        html_parts.append("                } else {")
        html_parts.append("                    // For non-baseline, compare against baseline")
        html_parts.append("                    const [_, afterHtml] = highlightJsonDiff(baseline.jsonValue, env.jsonValue, sortOption, true);")
        html_parts.append("                    valueContainer.innerHTML = afterHtml;")
        html_parts.append("                }")
        html_parts.append("            });")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        function sortJson(obj, sortOption) {")
        html_parts.append("            if (!sortOption || sortOption === 'unsorted') return obj;")
        html_parts.append("            if (obj === null || obj === undefined) return obj;")
        html_parts.append("            if (typeof obj !== 'object') return obj;")
        html_parts.append("            ")
        html_parts.append("            // Handle arrays")
        html_parts.append("            if (Array.isArray(obj)) {")
        html_parts.append("                let sorted = [...obj];  // Clone array")
        html_parts.append("                ")
        html_parts.append("                // Check if sorting by field")
        html_parts.append("                if (typeof sortOption === 'string' && sortOption.startsWith('field:')) {")
        html_parts.append("                    const fieldName = sortOption.substring(6);  // Remove 'field:' prefix")
        html_parts.append("                    // Only sort if array contains objects with the field")
        html_parts.append("                    if (sorted.length > 0 && typeof sorted[0] === 'object' && sorted[0] !== null && fieldName in sorted[0]) {")
        html_parts.append("                        sorted.sort((a, b) => {")
        html_parts.append("                            const aVal = a[fieldName];")
        html_parts.append("                            const bVal = b[fieldName];")
        html_parts.append("                            ")
        html_parts.append("                            // Handle null/undefined (sort to end)")
        html_parts.append("                            if (aVal == null && bVal == null) return 0;")
        html_parts.append("                            if (aVal == null) return 1;")
        html_parts.append("                            if (bVal == null) return -1;")
        html_parts.append("                            ")
        html_parts.append("                            // Type-safe comparison")
        html_parts.append("                            if (typeof aVal === 'number' && typeof bVal === 'number') {")
        html_parts.append("                                return aVal - bVal;")
        html_parts.append("                            }")
        html_parts.append("                            ")
        html_parts.append("                            // String comparison (convert to string if needed)")
        html_parts.append("                            const aStr = String(aVal);")
        html_parts.append("                            const bStr = String(bVal);")
        html_parts.append("                            return aStr.localeCompare(bStr);")
        html_parts.append("                        });")
        html_parts.append("                    }")
        html_parts.append("                }")
        html_parts.append("                ")
        html_parts.append("                // Recursively process nested structures")
        html_parts.append("                return sorted.map(item => sortJson(item, sortOption));")
        html_parts.append("            }")
        html_parts.append("            ")
        html_parts.append("            // Handle objects - always sort keys to match Python's sort_keys=True")
        html_parts.append("            const sorted = {};")
        html_parts.append("            Object.keys(obj).sort().forEach(key => {")
        html_parts.append("                sorted[key] = sortJson(obj[key], sortOption);")
        html_parts.append("            });")
        html_parts.append("            return sorted;")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        function escapeHtml(text) {")
        html_parts.append("            const div = document.createElement('div');")
        html_parts.append("            div.textContent = text;")
        html_parts.append("            return div.innerHTML;")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        // Custom JSON stringifier to match Python's json.dumps(indent=2, sort_keys=True)")
        html_parts.append("        function jsonStringify(obj) {")
        html_parts.append("            if (obj === null || obj === undefined) return 'null';")
        html_parts.append("            return JSON.stringify(obj, null, 2);")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        function highlightJsonDiff(before, after, sortOption, isBaselineComparison) {")
        html_parts.append("            const beforeStr = jsonStringify(sortJson(before, sortOption));")
        html_parts.append("            const afterStr = jsonStringify(sortJson(after, sortOption));")
        html_parts.append("")
        html_parts.append("            const removedClass = isBaselineComparison ? 'baseline-removed' : 'removed';")
        html_parts.append("            const addedClass = isBaselineComparison ? 'baseline-added' : 'added';")
        html_parts.append("")
        html_parts.append("            if (beforeStr === afterStr) {")
        html_parts.append('                const plain = \'<pre class="json-content">\' + escapeHtml(beforeStr) + \'</pre>\';')
        html_parts.append("                return [plain, plain];")
        html_parts.append("            }")
        html_parts.append("")
        html_parts.append("            const beforeLines = beforeStr.split('\\n');")
        html_parts.append("            const afterLines = afterStr.split('\\n');")
        html_parts.append("            const placeholderLine = '<span class=\"placeholder\">&nbsp;</span>';")
        html_parts.append("")
        html_parts.append("            // Simple line-based diff using LCS algorithm")
        html_parts.append("            const diff = computeDiff(beforeLines, afterLines);")
        html_parts.append("")
        html_parts.append("            const beforeHtmlLines = [];")
        html_parts.append("            const afterHtmlLines = [];")
        html_parts.append("")
        html_parts.append("            diff.forEach(op => {")
        html_parts.append("                if (op.type === 'equal') {")
        html_parts.append("                    op.lines.forEach(line => {")
        html_parts.append('                        beforeHtmlLines.push(\'<span class="unchanged">\' + escapeHtml(line) + \'</span>\');')
        html_parts.append('                        afterHtmlLines.push(\'<span class="unchanged">\' + escapeHtml(line) + \'</span>\');')
        html_parts.append("                    });")
        html_parts.append("                } else if (op.type === 'delete') {")
        html_parts.append("                    op.lines.forEach(line => {")
        html_parts.append('                        beforeHtmlLines.push(\'<span class="\' + removedClass + \'">\' + escapeHtml(line) + \'</span>\');')
        html_parts.append("                        afterHtmlLines.push(placeholderLine);")
        html_parts.append("                    });")
        html_parts.append("                } else if (op.type === 'insert') {")
        html_parts.append("                    op.lines.forEach(line => {")
        html_parts.append("                        beforeHtmlLines.push(placeholderLine);")
        html_parts.append('                        afterHtmlLines.push(\'<span class="\' + addedClass + \'">\' + escapeHtml(line) + \'</span>\');')
        html_parts.append("                    });")
        html_parts.append("                } else if (op.type === 'replace') {")
        html_parts.append("                    // Character-level diff for similar lines")
        html_parts.append("                    for (let i = 0; i < Math.max(op.beforeLines.length, op.afterLines.length); i++) {")
        html_parts.append("                        const beforeLine = op.beforeLines[i];")
        html_parts.append("                        const afterLine = op.afterLines[i];")
        html_parts.append("                        ")
        html_parts.append("                        if (beforeLine !== undefined && afterLine !== undefined) {")
        html_parts.append("                            const [beforeHighlight, afterHighlight] = highlightCharDiff(beforeLine, afterLine, isBaselineComparison);")
        html_parts.append('                            beforeHtmlLines.push(\'<span class="\' + removedClass + \'" style="background-color: rgba(187, 222, 251, 0.3);">\' + beforeHighlight + \'</span>\');')
        html_parts.append('                            afterHtmlLines.push(\'<span class="\' + addedClass + \'" style="background-color: rgba(200, 230, 201, 0.3);">\' + afterHighlight + \'</span>\');')
        html_parts.append("                        } else if (beforeLine !== undefined) {")
        html_parts.append('                            beforeHtmlLines.push(\'<span class="\' + removedClass + \'">\' + escapeHtml(beforeLine) + \'</span>\');')
        html_parts.append("                            afterHtmlLines.push(placeholderLine);")
        html_parts.append("                        } else if (afterLine !== undefined) {")
        html_parts.append("                            beforeHtmlLines.push(placeholderLine);")
        html_parts.append('                            afterHtmlLines.push(\'<span class="\' + addedClass + \'">\' + escapeHtml(afterLine) + \'</span>\');')
        html_parts.append("                        }")
        html_parts.append("                    }")
        html_parts.append("                }")
        html_parts.append("            });")
        html_parts.append("")
        html_parts.append('            const beforeHtml = \'<pre class="json-content">\' + beforeHtmlLines.join(\'<br>\') + \'</pre>\';')
        html_parts.append('            const afterHtml = \'<pre class="json-content">\' + afterHtmlLines.join(\'<br>\') + \'</pre>\';')
        html_parts.append("")
        html_parts.append("            return [beforeHtml, afterHtml];")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        // Simple LCS-based diff algorithm")
        html_parts.append("        function computeDiff(before, after) {")
        html_parts.append("            const n = before.length;")
        html_parts.append("            const m = after.length;")
        html_parts.append("            const lcs = Array(n + 1).fill(null).map(() => Array(m + 1).fill(0));")
        html_parts.append("")
        html_parts.append("            // Build LCS table")
        html_parts.append("            for (let i = 1; i <= n; i++) {")
        html_parts.append("                for (let j = 1; j <= m; j++) {")
        html_parts.append("                    if (before[i - 1] === after[j - 1]) {")
        html_parts.append("                        lcs[i][j] = lcs[i - 1][j - 1] + 1;")
        html_parts.append("                    } else {")
        html_parts.append("                        lcs[i][j] = Math.max(lcs[i - 1][j], lcs[i][j - 1]);")
        html_parts.append("                    }")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("")
        html_parts.append("            // Backtrack to build diff operations")
        html_parts.append("            const result = [];")
        html_parts.append("            let i = n, j = m;")
        html_parts.append("            while (i > 0 || j > 0) {")
        html_parts.append("                if (i > 0 && j > 0 && before[i - 1] === after[j - 1]) {")
        html_parts.append("                    if (result.length === 0 || result[0].type !== 'equal') {")
        html_parts.append("                        result.unshift({ type: 'equal', lines: [] });")
        html_parts.append("                    }")
        html_parts.append("                    result[0].lines.unshift(before[i - 1]);")
        html_parts.append("                    i--; j--;")
        html_parts.append("                } else if (j > 0 && (i === 0 || lcs[i][j - 1] >= lcs[i - 1][j])) {")
        html_parts.append("                    if (result.length === 0 || result[0].type !== 'insert') {")
        html_parts.append("                        result.unshift({ type: 'insert', lines: [] });")
        html_parts.append("                    }")
        html_parts.append("                    result[0].lines.unshift(after[j - 1]);")
        html_parts.append("                    j--;")
        html_parts.append("                } else if (i > 0 && (j === 0 || lcs[i][j - 1] < lcs[i - 1][j])) {")
        html_parts.append("                    if (result.length === 0 || result[0].type !== 'delete') {")
        html_parts.append("                        result.unshift({ type: 'delete', lines: [] });")
        html_parts.append("                    }")
        html_parts.append("                    result[0].lines.unshift(before[i - 1]);")
        html_parts.append("                    i--;")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("            ")
        html_parts.append("            // Post-process: merge adjacent delete+insert into replace if lines are similar")
        html_parts.append("            const merged = [];")
        html_parts.append("            for (let k = 0; k < result.length; k++) {")
        html_parts.append("                const curr = result[k];")
        html_parts.append("                const next = result[k + 1];")
        html_parts.append("                ")
        html_parts.append("                if (curr.type === 'delete' && next && next.type === 'insert') {")
        html_parts.append("                    // Check if lines are similar enough for char-level diff")
        html_parts.append("                    const maxLen = Math.max(curr.lines.length, next.lines.length);")
        html_parts.append("                    const beforeLines = curr.lines;")
        html_parts.append("                    const afterLines = next.lines;")
        html_parts.append("                    ")
        html_parts.append("                    let shouldMerge = false;")
        html_parts.append("                    if (maxLen === 1 || (beforeLines.length === afterLines.length && beforeLines.length <= 3)) {")
        html_parts.append("                        // Check similarity of first pair")
        html_parts.append("                        if (beforeLines.length > 0 && afterLines.length > 0) {")
        html_parts.append("                            const similarity = computeSimilarity(beforeLines[0], afterLines[0]);")
        html_parts.append("                            shouldMerge = similarity > 0.5;")
        html_parts.append("                        }")
        html_parts.append("                    }")
        html_parts.append("                    ")
        html_parts.append("                    if (shouldMerge) {")
        html_parts.append("                        merged.push({ type: 'replace', beforeLines, afterLines });")
        html_parts.append("                        k++; // Skip next")
        html_parts.append("                    } else {")
        html_parts.append("                        merged.push(curr);")
        html_parts.append("                    }")
        html_parts.append("                } else {")
        html_parts.append("                    merged.push(curr);")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("            ")
        html_parts.append("            return merged;")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        function computeSimilarity(str1, str2) {")
        html_parts.append("            const len1 = str1.length;")
        html_parts.append("            const len2 = str2.length;")
        html_parts.append("            if (len1 === 0 || len2 === 0) return 0;")
        html_parts.append("            ")
        html_parts.append("            const lcs = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));")
        html_parts.append("            for (let i = 1; i <= len1; i++) {")
        html_parts.append("                for (let j = 1; j <= len2; j++) {")
        html_parts.append("                    if (str1[i - 1] === str2[j - 1]) {")
        html_parts.append("                        lcs[i][j] = lcs[i - 1][j - 1] + 1;")
        html_parts.append("                    } else {")
        html_parts.append("                        lcs[i][j] = Math.max(lcs[i - 1][j], lcs[i][j - 1]);")
        html_parts.append("                    }")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("            return (2.0 * lcs[len1][len2]) / (len1 + len2);")
        html_parts.append("        }")
        html_parts.append("")
        html_parts.append("        function highlightCharDiff(beforeStr, afterStr, isBaselineComparison) {")
        html_parts.append("            const charRemovedClass = isBaselineComparison ? 'baseline-char-removed' : 'char-removed';")
        html_parts.append("            const charAddedClass = isBaselineComparison ? 'baseline-char-added' : 'char-added';")
        html_parts.append("            ")
        html_parts.append("            const len1 = beforeStr.length;")
        html_parts.append("            const len2 = afterStr.length;")
        html_parts.append("            const lcs = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));")
        html_parts.append("            ")
        html_parts.append("            for (let i = 1; i <= len1; i++) {")
        html_parts.append("                for (let j = 1; j <= len2; j++) {")
        html_parts.append("                    if (beforeStr[i - 1] === afterStr[j - 1]) {")
        html_parts.append("                        lcs[i][j] = lcs[i - 1][j - 1] + 1;")
        html_parts.append("                    } else {")
        html_parts.append("                        lcs[i][j] = Math.max(lcs[i - 1][j], lcs[i][j - 1]);")
        html_parts.append("                    }")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("            ")
        html_parts.append("            const beforeParts = [];")
        html_parts.append("            const afterParts = [];")
        html_parts.append("            let i = len1, j = len2;")
        html_parts.append("            ")
        html_parts.append("            while (i > 0 || j > 0) {")
        html_parts.append("                if (i > 0 && j > 0 && beforeStr[i - 1] === afterStr[j - 1]) {")
        html_parts.append("                    beforeParts.unshift(escapeHtml(beforeStr[i - 1]));")
        html_parts.append("                    afterParts.unshift(escapeHtml(afterStr[j - 1]));")
        html_parts.append("                    i--; j--;")
        html_parts.append("                } else if (j > 0 && (i === 0 || lcs[i][j - 1] >= lcs[i - 1][j])) {")
        html_parts.append('                    afterParts.unshift(\'<span class="\' + charAddedClass + \'">\' + escapeHtml(afterStr[j - 1]) + \'</span>\');')
        html_parts.append("                    j--;")
        html_parts.append("                } else if (i > 0) {")
        html_parts.append('                    beforeParts.unshift(\'<span class="\' + charRemovedClass + \'">\' + escapeHtml(beforeStr[i - 1]) + \'</span>\');')
        html_parts.append("                    i--;")
        html_parts.append("                }")
        html_parts.append("            }")
        html_parts.append("            ")
        html_parts.append("            return [beforeParts.join(''), afterParts.join('')];")
        html_parts.append("        }")
        html_parts.append("    </script>")
        html_parts.append("    <script>")
        html_parts.append(f"    {src.lib.html_generation.get_notes_javascript()}")
        html_parts.append("    </script>")
        # Ensure client-side markdown libraries are available via CDN when viewing the report
        html_parts.append('    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>')
        html_parts.append('    <script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>')
        html_parts.append("    <script>")
        html_parts.append(f"    {src.lib.html_generation.get_notes_markdown_javascript()}")
        html_parts.append("        document.addEventListener('DOMContentLoaded', function() {")
        html_parts.append("            document.querySelectorAll('.notes-container').forEach(function(container) {")
        html_parts.append("                var resource = container.getAttribute('data-resource');")
        html_parts.append("                var attribute = container.getAttribute('data-attribute');")
        html_parts.append("                if (resource && attribute && typeof initializeNoteMode === 'function') {")
        html_parts.append("                    initializeNoteMode(window.getReportId ? window.getReportId() : 'unknown-report', resource, attribute);")
        html_parts.append("                }")
        html_parts.append("            });")
        html_parts.append("        });")
        html_parts.append("    </script>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append('    <div class="container">')
        html_parts.append("        <header>")
        html_parts.append(
            "            <h1>Multi-Environment Terraform Plan Comparison</h1>"
        )
        html_parts.append(
            f'            <p>Comparing {len(env_labels)} environments: {", ".join(env_labels)}</p>'
        )
        html_parts.append("        </header>")

        # Summary cards
        html_parts.append('        <div class="summary">')
        html_parts.append('            <div class="summary-card total">')
        html_parts.append(
            f'                <div class="number">{self.summary_stats["total_unique_resources"]}</div>'
        )
        html_parts.append('                <div class="label">Total Resources</div>')
        html_parts.append("            </div>")
        html_parts.append('            <div class="summary-card total">')
        html_parts.append(
            f'                <div class="number">{self.summary_stats["total_environments"]}</div>'
        )
        html_parts.append('                <div class="label">Environments</div>')
        html_parts.append("            </div>")
        html_parts.append('            <div class="summary-card updated">')
        html_parts.append(
            f'                <div class="number">{self.summary_stats["resources_with_differences"]}</div>'
        )
        html_parts.append('                <div class="label">With Differences</div>')
        html_parts.append("            </div>")
        html_parts.append('            <div class="summary-card created">')
        html_parts.append(
            f'                <div class="number">{self.summary_stats["resources_consistent"]}</div>'
        )
        html_parts.append('                <div class="label">Consistent</div>')
        html_parts.append("            </div>")

        # Show ignore statistics if any ignoring was applied
        if (
            self.ignore_config
            and (self.ignore_statistics["total_ignored_attributes"] > 0 
                 or self.ignore_statistics["normalization_ignored_attributes"] > 0)
        ):
            # Config-ignored attributes
            if self.ignore_statistics["total_ignored_attributes"] > 0:
                html_parts.append(
                    '            <div class="summary-card total" style="background: #fff4e6; border-left: 4px solid #f59e0b;">'
                )
                html_parts.append(
                    f'                <div class="number">{self.ignore_statistics["total_ignored_attributes"]}</div>'
                )
                html_parts.append(
                    '                <div class="label">Config Ignored</div>'
                )
                html_parts.append("            </div>")
            
            # Normalization-ignored attributes (US3 - feature 007)
            if self.ignore_statistics["normalization_ignored_attributes"] > 0:
                html_parts.append(
                    '            <div class="summary-card total" style="background: #e0f2fe; border-left: 4px solid #0284c7;">'
                )
                html_parts.append(
                    f'                <div class="number">{self.ignore_statistics["normalization_ignored_attributes"]}</div>'
                )
                html_parts.append(
                    '                <div class="label">Normalized</div>'
                )
                html_parts.append("            </div>")
            
            html_parts.append(
                '            <div class="summary-card created" style="background: #ecfdf5; border-left: 4px solid #10b981;">'
            )
            html_parts.append(
                f'                <div class="number">{self.ignore_statistics["all_changes_ignored"]}</div>'
            )
            html_parts.append(
                '                <div class="label">All Changes Ignored</div>'
            )
            html_parts.append("            </div>")

        html_parts.append("        </div>")

        # Comparison section with collapsible resource blocks
        html_parts.append('        <div class="section">')
        html_parts.append("            <h2>Resource Comparison</h2>")
        html_parts.append(
            '            <button class="toggle-all" onclick="toggleAll()">Expand/Collapse All</button>'
        )

        # Filter if diff_only is enabled
        comparisons_to_show = self.resource_comparisons
        if self.diff_only:
            comparisons_to_show = [
                rc for rc in self.resource_comparisons if rc.has_differences
            ]

        # Separate regular resources from environment-specific resources (v2.0 feature)
        regular_resources = []
        env_specific_resources = []
        first_env_only_resources = []
        
        # Get the first environment label (baseline)
        first_env = env_labels[0] if env_labels else None
        
        for rc in comparisons_to_show:
            # Resources present in all environments are "regular"
            if len(rc.is_present_in) == len(env_labels):
                regular_resources.append(rc)
            else:
                # Check if resource only exists in first environment (will be created in others)
                if first_env and rc.is_present_in == {first_env}:
                    first_env_only_resources.append(rc)
                else:
                    # Resources missing from one or more environments are "env-specific"
                    env_specific_resources.append(rc)

        # Render regular resources first
        for rc in regular_resources:
            is_identical = not rc.has_differences
            status_class = "identical" if is_identical else "different"
            status_text = "✓ Identical" if is_identical else "⚠ Different"

            # Check for sensitive value differences
            has_sensitive_diff = rc.has_sensitive_differences()

            html_parts.append('            <div class="resource-change">')
            html_parts.append(
                '                <div class="resource-change-header" onclick="toggleResource(this)">'
            )
            html_parts.append(
                '                    <span class="toggle-icon collapsed">▼</span>'
            )
            html_parts.append(
                f'                    <span class="resource-name">{rc.resource_address}</span>'
            )
            html_parts.append(
                f'                    <span class="resource-status {status_class}">{status_text}</span>'
            )

            # Show combined ignore badge (US3 - feature 007)
            if rc.ignored_attributes or any(diff.ignored_due_to_normalization for diff in rc.attribute_diffs):
                # Collect normalized attribute names
                normalized_attrs = [
                    diff.attribute_name 
                    for diff in rc.attribute_diffs 
                    if diff.ignored_due_to_normalization
                ]
                
                # Calculate separate counts
                config_count, norm_count = _calculate_ignore_counts(rc.ignored_attributes, rc.attribute_diffs)
                
                # Render badge with breakdown
                badge_html = _render_ignore_badge(config_count, norm_count, rc.ignored_attributes, normalized_attrs)
                if badge_html:
                    html_parts.append(f'                    {badge_html}')
            

            if has_sensitive_diff:
                html_parts.append(
                    '                    <span class="sensitive-indicator">⚠️ SENSITIVE DIFF</span>'
                )

            html_parts.append("                </div>")
            html_parts.append('                <div class="resource-change-content">')

            # Render attribute table instead of full JSON
            attribute_table_html = self._render_attribute_table(rc, env_labels)
            html_parts.append(attribute_table_html)

            html_parts.append("                </div>")
            html_parts.append("            </div>")

        # Render environment-specific resources in collapsible section (v2.0 feature)
        if env_specific_resources:
            env_count = len(env_specific_resources)
            html_parts.append(
                '            <details open class="env-specific-section">'
            )
            html_parts.append(
                '                <summary class="env-specific-header">'
            )
            html_parts.append(
                f'                    <span>⚠️ Environment-Specific Resources</span>'
            )
            html_parts.append(
                f'                    <span class="resource-count">{env_count}</span>'
            )
            html_parts.append("                </summary>")
            html_parts.append('                <div class="env-specific-content">')
            
            for rc in env_specific_resources:
                is_identical = not rc.has_differences
                status_class = "identical" if is_identical else "different"
                status_text = "✓ Identical" if is_identical else "⚠ Different"
                has_sensitive_diff = rc.has_sensitive_differences()
                
                # Determine which environments have this resource
                present_envs = sorted(rc.is_present_in)
                missing_envs = sorted(set(env_labels) - rc.is_present_in)
                
                html_parts.append('                    <div class="resource-change">')
                html_parts.append(
                    '                        <div class="resource-change-header" onclick="toggleResource(this)">'
                )
                html_parts.append(
                    '                            <span class="toggle-icon collapsed">▼</span>'
                )
                html_parts.append(
                    f'                            <span class="resource-name">{rc.resource_address}</span>'
                )
                
                # Add environment-specific badge
                if len(present_envs) == 1:
                    html_parts.append(
                        f'                            <span class="env-specific-badge">{present_envs[0]} only</span>'
                    )
                else:
                    env_list = ", ".join(present_envs)
                    html_parts.append(
                        f'                            <span class="env-specific-badge">Present in: {env_list}</span>'
                    )
                
                html_parts.append(
                    f'                            <span class="resource-status {status_class}">{status_text}</span>'
                )
                
                # Render combined ignore badge (US3 - feature 007)
                if rc.ignored_attributes or any(diff.ignored_due_to_normalization for diff in rc.attribute_diffs):
                    # Collect normalized attribute names
                    normalized_attrs = [
                        diff.attribute_name 
                        for diff in rc.attribute_diffs 
                        if diff.ignored_due_to_normalization
                    ]
                    
                    # Calculate separate counts
                    config_count, norm_count = _calculate_ignore_counts(rc.ignored_attributes, rc.attribute_diffs)
                    
                    # Render badge with breakdown
                    badge_html = _render_ignore_badge(config_count, norm_count, rc.ignored_attributes, normalized_attrs)
                    if badge_html:
                        html_parts.append(f'                            {badge_html}')
                
                
                if has_sensitive_diff:
                    html_parts.append(
                        '                            <span class="sensitive-indicator">⚠️ SENSITIVE DIFF</span>'
                    )
                
                html_parts.append("                        </div>")
                html_parts.append(
                    '                        <div class="resource-change-content">'
                )
                
                # Add presence info box
                html_parts.append('                            <div class="presence-info">')
                html_parts.append(
                    f'                                <strong>Present in:</strong> {", ".join(present_envs)}'
                )
                html_parts.append("<br>")
                html_parts.append(
                    f'                                <strong>Missing from:</strong> {", ".join(missing_envs)}'
                )
                html_parts.append("                            </div>")
                
                # Render attribute table with ALL environments (show empty for missing)
                attribute_table_html = self._render_attribute_table(rc, env_labels)
                html_parts.append(attribute_table_html)
                
                html_parts.append("                        </div>")
                html_parts.append("                    </div>")
            
            html_parts.append("                </div>")
            html_parts.append("            </details>")

        # Render first-env-only resources in green collapsible section (new resources to be created) - at the bottom
        if first_env_only_resources:
            resource_count = len(first_env_only_resources)
            missing_envs = [env for env in env_labels if env != first_env]
            missing_envs_str = ", ".join(missing_envs)
            
            html_parts.append(
                '            <details class="first-env-only-section">'
            )
            html_parts.append(
                '                <summary class="first-env-only-header">'
            )
            html_parts.append(
                f'                    <span>🆕 Resources in {first_env} ({resource_count} will be created in {missing_envs_str})</span>'
            )
            html_parts.append("                </summary>")
            html_parts.append('                <div class="first-env-only-content">')
            
            for rc in first_env_only_resources:
                is_identical = not rc.has_differences
                status_class = "identical" if is_identical else "different"
                status_text = "✓ Identical" if is_identical else "⚠ Different"
                has_sensitive_diff = rc.has_sensitive_differences()
                
                html_parts.append('                    <div class="resource-change">')
                html_parts.append(
                    '                        <div class="resource-change-header" onclick="toggleResource(this)">'
                )
                html_parts.append(
                    '                            <span class="toggle-icon collapsed">▼</span>'
                )
                html_parts.append(
                    f'                            <span class="resource-name">{rc.resource_address}</span>'
                )
                html_parts.append(
                    f'                            <span class="first-env-badge">Will be created in: {missing_envs_str}</span>'
                )
                
                # Render combined ignore badge
                if rc.ignored_attributes or any(diff.ignored_due_to_normalization for diff in rc.attribute_diffs):
                    normalized_attrs = [
                        diff.attribute_name 
                        for diff in rc.attribute_diffs 
                        if diff.ignored_due_to_normalization
                    ]
                    config_count, norm_count = _calculate_ignore_counts(rc.ignored_attributes, rc.attribute_diffs)
                    badge_html = _render_ignore_badge(config_count, norm_count, rc.ignored_attributes, normalized_attrs)
                    if badge_html:
                        html_parts.append(f'                            {badge_html}')
                
                if has_sensitive_diff:
                    html_parts.append(
                        '                            <span class="sensitive-indicator">⚠️ SENSITIVE DIFF</span>'
                    )
                
                html_parts.append("                        </div>")
                html_parts.append(
                    '                        <div class="resource-change-content">'
                )
                
                # Render attribute table
                attribute_table_html = self._render_attribute_table(rc, env_labels)
                html_parts.append(attribute_table_html)
                
                html_parts.append("                        </div>")
                html_parts.append("                    </div>")
            
            html_parts.append("                </div>")
            html_parts.append("            </details>")

        html_parts.append("        </div>")
        html_parts.append("    </div>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        # Write HTML file
        with open(output_path, "w") as f:
            f.write("\n".join(html_parts))

    def _render_attribute_table(
        self, rc: "ResourceComparison", env_labels: List[str]
    ) -> str:
        """
        Render attribute-level diff sections for a resource (v2.0).

        Uses header-based flexbox layout instead of tables for better readability.
        Each attribute becomes a section with H3 header and horizontally aligned values.

        Args:
            rc: ResourceComparison object with attribute_diffs
            env_labels: List of environment labels

        Returns:
            HTML string for the attribute sections
        """
        parts = []
        parts.append('                    <div class="attribute-table-container">')

        # Check if resource is present in all environments
        if len(rc.is_present_in) < len(env_labels):
            parts.append(
                '                        <div style="padding: 15px; background: #fff4e6; border-left: 4px solid #f59e0b; margin-bottom: 15px;">'
            )
            parts.append(
                "                            <strong>⚠️ Resource Presence Mismatch</strong><br>"
            )
            parts.append(
                f'                            Present in: {", ".join(sorted(rc.is_present_in))}<br>'
            )
            missing = set(env_labels) - rc.is_present_in
            parts.append(
                f'                            Missing from: {", ".join(sorted(missing))}'
            )
            parts.append("                        </div>")

        # If no attribute diffs, show "No differences" message
        if not rc.attribute_diffs:
            parts.append(
                '                        <div style="padding: 20px; text-align: center; color: #10b981; font-size: 1.1em;">'
            )
            parts.append("                            ✓ No differences detected")
            parts.append("                        </div>")
        else:
            # Render attribute sections (v2.0 layout)
            for attr_diff in rc.attribute_diffs:
                # Skip attributes that were normalized and became identical (hide them)
                if attr_diff.ignored_due_to_normalization:
                    continue
                
                # For env-specific resources (not present in all environments), show ALL attributes
                # For resources present in all environments, only show changed attributes
                is_env_specific = len(rc.is_present_in) < len(env_labels)
                if not is_env_specific and not attr_diff.is_different and rc.has_differences:
                    continue

                # Start attribute section
                section_class = "attribute-section"
                if attr_diff.is_different:
                    parts.append(
                        f'                        <div class="{section_class}" style="background: #fff3cd;">'
                    )
                else:
                    parts.append(
                        f'                        <div class="{section_class}">'
                    )

                # Attribute header (H3 with attribute name)
                parts.append(
                    '                            <h3 class="attribute-header">'
                )
                parts.append(
                    f"                                <code>{html.escape(attr_diff.attribute_name)}</code>"
                )

                # Add badge for sensitive attributes
                if any(
                    isinstance(val, str) and "SENSITIVE" in val
                    for val in attr_diff.env_values.values()
                ):
                    parts.append(
                        '                                <span class="sensitive-badge">🔒 SENSITIVE</span>'
                    )

                # Add sort control for JSON objects (dict/list)
                has_json_values = any(
                    isinstance(val, (dict, list)) and val is not None
                    for val in (attr_diff.normalized_values.values() if attr_diff.normalized_values else attr_diff.env_values_raw.values())
                )
                if has_json_values:
                    # Detect sortable fields for array-of-object structures
                    sortable_fields = self._detect_sortable_fields(attr_diff)
                    
                    parts.append(
                        '                                <select class="json-sort-control" onchange="handleSortChange(this)">'
                    )
                    parts.append(
                        '                                    <option value="sorted">Alphabetical (A-Z)</option>'
                    )
                    parts.append(
                        '                                    <option value="unsorted">Insertion Order</option>'
                    )
                    
                    # Add field-based options if sortable fields detected
                    if sortable_fields:
                        parts.append(
                            '                                    <option disabled>──────────</option>'
                        )
                        for field in sortable_fields:
                            parts.append(
                                f'                                    <option value="field:{html.escape(field)}">Sort by: {html.escape(field)}</option>'
                            )
                    
                    parts.append(
                        '                                </select>'
                    )

                parts.append("                            </h3>")

                # Attribute values container (flexbox)
                parts.append(
                    '                            <div class="attribute-values">'
                )

                # Value columns for each environment
                for env_label in env_labels:
                    # Start with raw unmasked value, then apply normalization if available, then merged masking
                    if attr_diff.normalized_values and env_label in attr_diff.normalized_values:
                        # Use normalized value
                        value = attr_diff.normalized_values.get(env_label)
                    else:
                        # Use raw unmasked value
                        value = attr_diff.env_values_raw.get(env_label)
                    
                    # Apply merged sensitive masking to ensure consistency across environments
                    if value is not None and rc.merged_sensitive_metadata:
                        attr_sensitive = rc.merged_sensitive_metadata.get(attr_diff.attribute_name)
                        if attr_sensitive:
                            value = rc._mask_sensitive_value(value, attr_sensitive)
                    
                    value_html = self._render_attribute_value(
                        value, attr_diff, env_labels, env_label
                    )
                    
                    # Build data attributes for JSON objects to enable client-side re-sorting
                    data_attrs = ''
                    if isinstance(value, (dict, list)) and value is not None:
                        # Determine if this is the baseline environment
                        is_baseline = False
                        for env in env_labels:
                            baseline_value = attr_diff.normalized_values.get(env) if attr_diff.normalized_values else attr_diff.env_values_raw.get(env)
                            if baseline_value is not None:
                                is_baseline = (env == env_label)
                                break
                        
                        # Store raw JSON data as data attributes (escape quotes for HTML)
                        json_str = json.dumps(value, ensure_ascii=False)
                        data_attrs = f' data-json-value="{html.escape(json_str, quote=True)}" data-env="{env_label}" data-is-baseline="{str(is_baseline).lower()}"'
                    
                    parts.append(
                        f'                                <div class="env-value-column"{data_attrs}>'
                    )
                    parts.append(
                        f'                                    <div class="env-label">{env_label}</div>'
                    )
                    # Wrap value in scrollable container (v2.0 feature)
                    parts.append(
                        '                                    <div class="value-container">'
                    )
                    parts.append(
                        f'                                        {value_html}'
                    )
                    parts.append(
                        "                                    </div>"
                    )
                    parts.append(
                        "                                </div>"
                    )

                parts.append("                            </div>")  # Close attribute-values
                

                # Add markdown-enabled Q&A notes container (User Story 1)
                sanitized_resource = self._sanitize_for_html_id(rc.resource_address)
                sanitized_attribute = self._sanitize_for_html_id(attr_diff.attribute_name)
                parts.append(f'                            <details class="notes-container" data-resource="{rc.resource_address}" data-attribute="{attr_diff.attribute_name}" data-mode="edit" open>')
                parts.append('                                <summary class="notes-header" data-collapsed="false">')
                parts.append('                                    <span class="notes-title">Notes — Q&amp;A</span>')
                parts.append(f'                                    <button type="button" class="toggle-mode" aria-pressed="true" onclick="toggleNoteMode(event, \'{rc.resource_address}\', \'{attr_diff.attribute_name}\')">Preview</button>')
                parts.append('                                </summary>')
                # Question field (edit + preview share the same visual area) - wrapped so we can hide only question in preview
                parts.append('                                <div class="note-question">')
                parts.append(f'                                    <label class="note-label" for="note-q-{sanitized_resource}-{sanitized_attribute}">Question (optional):</label>')
                parts.append('                                    <div class="notes-content">')
                parts.append(f'                                        <textarea class="note-field note-edit note-question" id="note-q-{sanitized_resource}-{sanitized_attribute}" placeholder="Enter a question (Markdown supported)..." oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'question\', this.value)" onblur="saveNoteWithBlur(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'question\', this)" rows="4"></textarea>')
                parts.append(f'                                        <div class="note-preview" id="note-q-prev-{sanitized_resource}-{sanitized_attribute}"></div>')
                parts.append('                                    </div>')
                parts.append('                                </div>')
                # Answer field
                parts.append('                                <div class="note-answer">')
                parts.append(f'                                    <label class="note-label" for="note-a-{sanitized_resource}-{sanitized_attribute}">Answer (optional):</label>')
                parts.append('                                    <div class="notes-content">')
                parts.append(f'                                        <textarea class="note-field note-edit note-answer" id="note-a-{sanitized_resource}-{sanitized_attribute}" placeholder="Enter an answer (Markdown supported)..." oninput="debouncedSaveNote(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'answer\', this.value)" onblur="saveNoteWithBlur(\'{rc.resource_address}\', \'{attr_diff.attribute_name}\', \'answer\', this)" rows="4"></textarea>')
                parts.append(f'                                        <div class="note-preview" id="note-a-prev-{sanitized_resource}-{sanitized_attribute}"></div>')
                parts.append('                                    </div>')
                parts.append('                                </div>')
                parts.append('                            </details>')
                
                parts.append("                        </div>")  # Close attribute-section

        parts.append("                    </div>")
        return "\n".join(parts)

    def _render_attribute_value(
        self,
        value: Any,
        attr_diff: AttributeDiff,
        env_labels: List[str],
        current_env: str,
    ) -> str:
        """
        Render a single attribute value with appropriate formatting and highlighting.

        Args:
            value: The attribute value to render
            attr_diff: The AttributeDiff object containing all environment values
            env_labels: List of all environment labels
            current_env: Current environment being rendered

        Returns:
            HTML string for the value
        """
        if value is None:
            return '<span style="color: #868e96; font-style: italic;">null</span>'

        # Handle primitive values (strings, numbers, booleans)
        if isinstance(value, (str, int, float, bool)):
            # Check if this is a sensitive value
            if isinstance(value, str) and "SENSITIVE" in value:
                return f'<code style="background: #f8d7da; padding: 2px 6px; border-radius: 3px;">{html.escape(str(value))}</code>'

            # For different values, apply character-level diff highlighting
            if attr_diff.is_different and attr_diff.attribute_type == "primitive":
                # Use normalized values for comparison if available, otherwise use original values
                values_for_comparison = attr_diff.normalized_values if attr_diff.normalized_values else attr_diff.env_values
                
                # Get baseline value (first non-None value)
                baseline_val = None
                baseline_env = None
                for env in env_labels:
                    if values_for_comparison.get(env) is not None:
                        baseline_val = values_for_comparison[env]
                        baseline_env = env
                        break

                # If this IS the baseline environment, we need to compare against other envs
                if current_env == baseline_env and baseline_val is not None:
                    # Find any different value to compare against
                    other_val = None
                    for env in env_labels:
                        if env != baseline_env:
                            other_val = values_for_comparison.get(env)
                            if other_val is not None and other_val != baseline_val:
                                break
                    
                    if other_val is not None and isinstance(value, str) and isinstance(other_val, str):
                        baseline_highlighted, _ = _highlight_char_diff(
                            str(value), str(other_val)
                        )
                        return f'<code class="baseline-removed">{baseline_highlighted}</code>'
                
                # For non-baseline environments, compare against baseline
                elif baseline_val is not None and value != baseline_val:
                    if isinstance(value, str) and isinstance(baseline_val, str):
                        _, value_highlighted = _highlight_char_diff(
                            str(baseline_val), str(value)
                        )
                        return f'<code class="baseline-added">{value_highlighted}</code>'

            # Default: show value without highlighting
            return f"<code>{html.escape(str(value))}</code>"

        # Handle complex objects (dict, list)
        if isinstance(value, (dict, list)):
            # For objects/arrays with differences, apply JSON diff highlighting
            if attr_diff.is_different:
                # Use normalized values for comparison if available, otherwise use original values
                values_for_comparison = attr_diff.normalized_values if attr_diff.normalized_values else attr_diff.env_values
                
                # Get baseline value
                baseline_val = None
                baseline_env = None
                for env in env_labels:
                    if values_for_comparison.get(env) is not None:
                        baseline_val = values_for_comparison[env]
                        baseline_env = env
                        break
                
                # If this IS the baseline environment, compare against other envs
                if current_env == baseline_env and baseline_val is not None:
                    # Find any different value to compare against
                    other_val = None
                    for env in env_labels:
                        if env != baseline_env:
                            other_val = values_for_comparison.get(env)
                            if other_val is not None and json.dumps(other_val, sort_keys=True) != json.dumps(baseline_val, sort_keys=True):
                                break
                    
                    if other_val is not None:
                        baseline_highlighted, _ = _highlight_json_diff(value, other_val)
                        return f'<pre class="json-content" style="margin: 0; font-size: 0.85em;">{baseline_highlighted}</pre>'
                
                # For non-baseline environments, compare against baseline
                elif baseline_val is not None and json.dumps(value, sort_keys=True) != json.dumps(baseline_val, sort_keys=True):
                    _, value_highlighted = _highlight_json_diff(baseline_val, value)
                    return f'<pre class="json-content" style="margin: 0; font-size: 0.85em;">{value_highlighted}</pre>'
            
            # No differences - show plain JSON
            value_json = json.dumps(value, indent=2, sort_keys=True)
            return f'<pre style="margin: 0; font-size: 0.85em;">{html.escape(value_json)}</pre>'

        # Fallback
        return f"<code>{html.escape(str(value))}</code>"

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
        lines.append(
            f"Total Unique Resources: {self.summary_stats['total_unique_resources']}"
        )
        lines.append(
            f"Resources with Differences: {self.summary_stats['resources_with_differences']}"
        )
        lines.append(
            f"Resources Consistent: {self.summary_stats['resources_consistent']}"
        )
        lines.append(
            f"Resources Missing from Some: {self.summary_stats['resources_missing_from_some']}"
        )

        # Show ignore statistics if any ignoring was applied
        if (
            self.ignore_config
            and (self.ignore_statistics["total_ignored_attributes"] > 0 
                 or self.ignore_statistics["normalization_ignored_attributes"] > 0)
        ):
            lines.append("")
            lines.append("IGNORE STATISTICS")
            
            # Config-ignored attributes
            if self.ignore_statistics["total_ignored_attributes"] > 0:
                lines.append(
                    f"Config Ignored Attributes: {self.ignore_statistics['total_ignored_attributes']}"
                )
            
            # Normalization-ignored attributes (US3 - feature 007)
            if self.ignore_statistics["normalization_ignored_attributes"] > 0:
                lines.append(
                    f"Normalized Attributes: {self.ignore_statistics['normalization_ignored_attributes']}"
                )
            
            # Verbose normalization logging indicator (T059)
            if self.verbose_normalization:
                lines.append("  (Verbose normalization logging enabled)")
            
            # Verbose normalization notice (T059 - FR-015)
            if self.verbose_normalization:
                lines.append(
                    "⚙️  Verbose normalization logging enabled (see transformations above)"
                )
            
            lines.append(
                f"Resources with Ignores: {self.ignore_statistics['resources_with_ignores']}"
            )
            lines.append(
                f"Resources with All Changes Ignored: {self.ignore_statistics['all_changes_ignored']}"
            )
            if self.ignore_statistics["ignore_breakdown"]:
                lines.append("Breakdown by Attribute:")
                for attr, count in sorted(
                    self.ignore_statistics["ignore_breakdown"].items()
                ):
                    lines.append(f"  - {attr}: {count} resource(s)")

        lines.append("")

        # Resource comparison section
        lines.append("RESOURCE COMPARISON")
        lines.append("-" * terminal_width)
        lines.append("")

        # Filter if diff_only is enabled
        comparisons_to_show = self.resource_comparisons
        if self.diff_only:
            comparisons_to_show = [
                rc for rc in self.resource_comparisons if rc.has_differences
            ]

        for rc in comparisons_to_show:
            status = "✓ IDENTICAL" if not rc.has_differences else "⚠ DIFFERENT"

            # Resource header
            lines.append(f"Resource: {rc.resource_address}")
            lines.append(f"Status: {status}")

            # Show ignored attributes count if any
            if rc.ignored_attributes:
                lines.append(
                    f"Ignored Attributes: {len(rc.ignored_attributes)} ({', '.join(sorted(rc.ignored_attributes))})"
                )

            # Check for sensitive differences
            if rc.has_sensitive_differences():
                lines.append("⚠️  SENSITIVE VALUE DIFFERENCES DETECTED")

            # Environment presence
            present_envs = ", ".join(sorted(rc.is_present_in))
            missing_envs = ", ".join(sorted(set(env_labels) - rc.is_present_in))

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
                        for line in config_json.split("\n"):
                            lines.append(f"    {line}")
                    lines.append("")

            lines.append("-" * terminal_width)
            lines.append("")

        return "\n".join(lines)
