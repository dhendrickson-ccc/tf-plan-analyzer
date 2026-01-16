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


# The diff highlighting functions now use shared utilities from src.lib.diff_utils
# Kept as module-level wrappers for backward compatibility
def _highlight_char_diff(before_str: str, after_str: str, is_baseline: bool = True) -> Tuple[str, str]:
    """Wrapper for shared highlight_char_diff utility with baseline comparison styling."""
    return highlight_char_diff(before_str, after_str, is_known_after_apply=False, is_baseline_comparison=is_baseline)


def _highlight_json_diff(before: Any, after: Any, is_baseline: bool = True) -> Tuple[str, str]:
    """Wrapper for shared highlight_json_diff utility with baseline comparison styling."""
    return highlight_json_diff(before, after, is_known_after_apply=False, is_baseline_comparison=is_baseline)


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

    def add_environment_config(
        self, env_label: str, config: Optional[Dict], config_raw: Optional[Dict] = None
    ) -> None:
        """
        Add configuration for an environment.

        Args:
            env_label: Environment label
            config: Configuration dict (possibly with masked sensitive values) or None if resource doesn't exist
            config_raw: Unmasked configuration for comparison purposes
        """
        self.env_configs[env_label] = config
        self.env_configs_raw[env_label] = (
            config_raw if config_raw is not None else config
        )
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

    def compute_attribute_diffs(self) -> None:
        """
        Compute attribute-level diffs for rendering in HTML reports.

        Extracts top-level attributes from each environment's config and
        creates AttributeDiff objects that can be rendered as table rows.
        Skips attributes that are in the ignored_attributes set.
        """
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
            baseline_value = None
            is_different = False

            # Collect values from each environment
            for env_label in env_labels:
                config = self.env_configs.get(env_label)
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

            # Determine attribute type
            attr_type = "primitive"
            if baseline_value is not None:
                if isinstance(baseline_value, dict):
                    attr_type = "object"
                elif isinstance(baseline_value, list):
                    attr_type = "array"

            # Create AttributeDiff
            attr_diff = AttributeDiff(attr_name, env_values, is_different, attr_type)
            self.attribute_diffs.append(attr_diff)

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
    ):
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
            "total_ignored_attributes": 0,
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

            # Track which attributes were actually ignored for this resource
            ignored_for_resource: Set[str] = set()

            # Add config from each environment (with ignore config applied)
            for env in self.environments:
                config = env.before_values.get(address)
                config_raw = env.before_values_raw.get(address)

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

                comparison.add_environment_config(env.label, config, config_raw)

            # Store ignored attributes for this resource
            comparison.ignored_attributes = ignored_for_resource

            # Detect differences (uses raw values AFTER ignore filtering)
            comparison.detect_differences()

            # Compute attribute-level diffs for HTML rendering
            comparison.compute_attribute_diffs()

            # Mark changed sensitive values with (changed) indicator
            comparison.mark_changed_sensitive_values()

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
            and self.ignore_statistics["total_ignored_attributes"] > 0
        ):
            html_parts.append(
                '            <div class="summary-card total" style="background: #fff4e6; border-left: 4px solid #f59e0b;">'
            )
            html_parts.append(
                f'                <div class="number">{self.ignore_statistics["total_ignored_attributes"]}</div>'
            )
            html_parts.append(
                '                <div class="label">Attributes Ignored</div>'
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
        
        for rc in comparisons_to_show:
            # Resources present in all environments are "regular"
            if len(rc.is_present_in) == len(env_labels):
                regular_resources.append(rc)
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

            # Show ignored attributes indicator
            if rc.ignored_attributes:
                ignored_count = len(rc.ignored_attributes)
                ignored_list = ", ".join(sorted(rc.ignored_attributes))
                html_parts.append(
                    f'                    <span class="badge" style="background: #fbbf24; color: #78350f;" title="Ignored: {ignored_list}">{ignored_count} attributes ignored</span>'
                )

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
                
                if rc.ignored_attributes:
                    ignored_count = len(rc.ignored_attributes)
                    ignored_list = ", ".join(sorted(rc.ignored_attributes))
                    html_parts.append(
                        f'                            <span class="badge" style="background: #fbbf24; color: #78350f;" title="Ignored: {ignored_list}">{ignored_count} attributes ignored</span>'
                    )
                
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

                parts.append("                            </h3>")

                # Attribute values container (flexbox)
                parts.append(
                    '                            <div class="attribute-values">'
                )

                # Value columns for each environment
                for env_label in env_labels:
                    value = attr_diff.env_values.get(env_label)
                    value_html = self._render_attribute_value(
                        value, attr_diff, env_labels, env_label
                    )
                    
                    parts.append(
                        '                                <div class="env-value-column">'
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
                # Get baseline value (first non-None value)
                baseline_val = None
                baseline_env = None
                for env in env_labels:
                    if attr_diff.env_values.get(env) is not None:
                        baseline_val = attr_diff.env_values[env]
                        baseline_env = env
                        break

                # If this IS the baseline environment, we need to compare against other envs
                if current_env == baseline_env and baseline_val is not None:
                    # Find any different value to compare against
                    other_val = None
                    for env in env_labels:
                        if env != baseline_env:
                            other_val = attr_diff.env_values.get(env)
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
                # Get baseline value
                baseline_val = None
                baseline_env = None
                for env in env_labels:
                    if attr_diff.env_values.get(env) is not None:
                        baseline_val = attr_diff.env_values[env]
                        baseline_env = env
                        break
                
                # If this IS the baseline environment, compare against other envs
                if current_env == baseline_env and baseline_val is not None:
                    # Find any different value to compare against
                    other_val = None
                    for env in env_labels:
                        if env != baseline_env:
                            other_val = attr_diff.env_values.get(env)
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
            # Truncate if too long
            if len(value_json) > 500:
                value_json = value_json[:500] + "\n  ...(truncated)...\n}"
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
            and self.ignore_statistics["total_ignored_attributes"] > 0
        ):
            lines.append("")
            lines.append("IGNORE STATISTICS")
            lines.append(
                f"Total Ignored Attributes: {self.ignore_statistics['total_ignored_attributes']}"
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
