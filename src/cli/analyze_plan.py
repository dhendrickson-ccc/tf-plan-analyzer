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

# Import shared HTML/CSS generation utilities
import src.lib.html_generation
from src.lib.diff_utils import (
    highlight_char_diff,
    highlight_json_diff as highlight_json_diff_util,
)

try:
    from src.core.hcl_value_resolver import HCLValueResolver
except ImportError:
    HCLValueResolver = None  # Optional dependency

try:
    from src.security.salt_manager import (
        generate_salt,
        generate_position_seed,
        store_salt,
        load_salt,
    )
    from src.security.sensitive_obfuscator import traverse_and_obfuscate
except ImportError as e:
    print(
        f"Warning: Obfuscate subcommand dependencies not available: {e}",
        file=sys.stderr,
    )
    generate_salt = None
    generate_position_seed = None
    store_salt = None
    load_salt = None
    traverse_and_obfuscate = None


class TerraformPlanAnalyzer:
    """Analyzes terraform plan JSON files."""

    # Default fields to ignore when detecting changes (computed values)
    DEFAULT_IGNORE_FIELDS = {
        "id",
        "etag",
        "default_hostname",
        "outbound_ip_addresses",
        "outbound_ip_address_list",
        "possible_outbound_ip_addresses",
        "possible_outbound_ip_address_list",
    }

    def __init__(
        self,
        plan_file: str,
        custom_ignore_fields: Set[str] = None,
        resource_specific_ignores: Dict[str, Set[str]] = None,
        global_ignore_reasons: Dict[str, str] = None,
        resource_ignore_reasons: Dict[str, Dict[str, str]] = None,
        hcl_resolver: Optional["HCLValueResolver"] = None,
        ignore_azure_casing: bool = False,
        show_sensitive: bool = False,
    ):
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

        # Whether to show sensitive values (default: redact them)
        self.show_sensitive = show_sensitive

    def load_plan(self) -> None:
        """Load the terraform plan JSON file."""
        with open(self.plan_file, "r") as f:
            self.plan_data = json.load(f)
        self.resource_changes = self.plan_data.get("resource_changes", [])

    def analyze(self) -> Dict[str, List]:
        """
        Analyze the plan and categorize all resources.

        Returns:
            Dict with keys: created, imported, tag_only, config_changes, deleted
        """
        results = {
            "created": [],
            "imported": [],
            "tag_only": [],
            "config_changes": [],
            "deleted": [],
        }

        for rc in self.resource_changes:
            addr = rc.get("address", "")
            change = rc.get("change", {})
            actions = change.get("actions", [])

            if "create" in actions and "delete" not in actions:
                if rc.get("action_reason") == "import":
                    results["imported"].append(addr)
                else:
                    results["created"].append(addr)

            elif "update" in actions:
                changed_attrs = self._get_changed_attributes(change, addr)

                # Only count as an update if there are real (non-ignored) changes
                if changed_attrs:
                    if set(changed_attrs.keys()) == {"tags"}:
                        results["tag_only"].append(addr)
                    else:
                        results["config_changes"].append(
                            {
                                "address": addr,
                                "changed_attributes": changed_attrs,  # Store the full dict with before/after values
                            }
                        )
                # If no real changes after filtering, don't count as an update

            elif "delete" in actions and "create" not in actions:
                results["deleted"].append(addr)

        return results

    def _get_changed_attributes(self, change: Dict, resource_address: str) -> Dict:
        """
        Determine which attributes actually changed.

        Args:
            change: The change object from resource_changes
            resource_address: Full resource address (e.g., azurerm_monitor_metric_alert.example)

        Returns:
            Dict of changed attributes with sensitivity info: {attr: (before, after, is_sensitive_before, is_sensitive_after)}
        """
        before = change.get("before", {})
        after = change.get("after", {})
        after_unknown = change.get("after_unknown", {})
        before_sensitive = change.get("before_sensitive", {})
        after_sensitive = change.get("after_sensitive", {})

        # Find all changed keys
        changes_dict = {}
        for key in set(list(before.keys()) + list(after.keys())):
            before_val = before.get(key)
            after_val = after.get(key)

            # Get sensitivity maps for this field
            before_sens = (
                before_sensitive.get(key)
                if isinstance(before_sensitive, dict)
                else None
            )
            after_sens = (
                after_sensitive.get(key) if isinstance(after_sensitive, dict) else None
            )

            # Get the after_unknown metadata for this field
            key_unknown = (
                after_unknown.get(key) if isinstance(after_unknown, dict) else None
            )

            # Recursively resolve HCL values for nested structures
            if key_unknown is not None:
                after_val = self._resolve_nested_hcl(
                    after_val, key_unknown, resource_address, [key]
                )

            if not self._values_equal(before_val, after_val):
                # Store with sensitivity information (pass the sensitivity maps, not booleans)
                changes_dict[key] = (before_val, after_val, before_sens, after_sens)

        # Extract resource type from address (e.g., "azurerm_monitor_metric_alert.example" -> "azurerm_monitor_metric_alert")
        resource_type = (
            resource_address.split(".")[0] if "." in resource_address else ""
        )

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
            return json.dumps(value, indent=2, separators=(",", ": "))
        else:
            return str(value)

    @staticmethod
    def _is_azure_resource_id(value: Any) -> bool:
        """Check if a value is an Azure resource ID."""
        if not isinstance(value, str):
            return False
        # Azure resource IDs contain these path segments
        return any(
            segment in value
            for segment in ["/subscriptions/", "/providers/", "/resourceGroups/"]
        )

    @staticmethod
    def _normalize_for_comparison_static(
        value: Any, ignore_azure_casing: bool = False
    ) -> Any:
        """Static version of normalize for use in static methods."""
        if isinstance(value, str):
            if ignore_azure_casing and TerraformPlanAnalyzer._is_azure_resource_id(
                value
            ):
                return value.lower()
            return value
        elif isinstance(value, list):
            return [
                TerraformPlanAnalyzer._normalize_for_comparison_static(
                    item, ignore_azure_casing
                )
                for item in value
            ]
        elif isinstance(value, dict):
            return {
                k: TerraformPlanAnalyzer._normalize_for_comparison_static(
                    v, ignore_azure_casing
                )
                for k, v in value.items()
            }
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

    def _resolve_nested_hcl(
        self,
        value: Any,
        after_unknown: Any,
        resource_address: str,
        path: List[str] = None,
    ) -> Any:
        """Recursively resolve HCL values for nested structures that are 'known after apply'.

        Args:
            value: The value to potentially resolve (may be null for computed values)
            after_unknown: The after_unknown metadata for this value
            resource_address: The resource address (e.g., azurerm_linux_function_app.python_analysis)
            path: The current path within the structure (e.g., ['site_config', 'application_insights_connection_string'])

        Returns:
            The value with nested HCL references resolved where possible
        """
        if path is None:
            path = []

        # If this specific value is marked as unknown, try to resolve it
        if after_unknown is True:
            if self.hcl_resolver and path:
                # Build the full attribute path, skipping numeric indices for blocks
                # (e.g., "site_config.application_insights_connection_string" not "site_config.0.application_insights_connection_string")
                attr_path = ".".join(str(p) for p in path if not p.isdigit())
                hcl_value = self.hcl_resolver.get_resource_attribute(
                    resource_address, attr_path
                )
                if hcl_value is not None:
                    return hcl_value
            return "(known after apply)"

        # If value is null but not marked as unknown, keep it as null
        if value is None:
            return None

        # If it's a dict, recursively resolve nested fields
        if isinstance(value, dict):
            resolved = {}
            unknown_map = after_unknown if isinstance(after_unknown, dict) else {}
            for key, val in value.items():
                nested_unknown = unknown_map.get(key)
                resolved[key] = self._resolve_nested_hcl(
                    val, nested_unknown, resource_address, path + [key]
                )
            # Also check for fields that are in unknown_map but not in value (they'd be null)
            if isinstance(after_unknown, dict):
                for key in after_unknown:
                    if key not in resolved:
                        nested_unknown = after_unknown[key]
                        resolved[key] = self._resolve_nested_hcl(
                            None, nested_unknown, resource_address, path + [key]
                        )
            return resolved

        # If it's a list, recursively resolve each element
        if isinstance(value, list) and isinstance(after_unknown, list):
            resolved = []
            for i, val in enumerate(value):
                elem_unknown = after_unknown[i] if i < len(after_unknown) else None
                resolved.append(
                    self._resolve_nested_hcl(
                        val, elem_unknown, resource_address, path + [str(i)]
                    )
                )
            return resolved

        # Otherwise return as-is
        return value

    def _get_sensitivity_for_path(self, sensitive_map: Any, path: List[str]) -> Any:
        """Navigate through a nested sensitivity map following a path.

        Returns the sensitivity value at the given path, which could be:
        - True/False for leaf values
        - A dict/list for nested structures
        - None if path doesn't exist
        """
        if not sensitive_map:
            return None

        current = sensitive_map
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            elif isinstance(current, list):
                # For lists in sensitivity maps, typically the entire list is marked
                # or each element has its own sensitivity
                try:
                    idx = int(key)
                    if idx < len(current):
                        current = current[idx]
                    else:
                        return None
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current

    def _is_value_sensitive(self, sensitive_indicator: Any) -> bool:
        """Check if a sensitivity indicator means the value is sensitive.

        Args:
            sensitive_indicator: Could be True, False, {}, [], or a nested structure

        Returns:
            True if this indicates a sensitive value, False otherwise
        """
        if sensitive_indicator is True:
            return True
        if sensitive_indicator is False or sensitive_indicator is None:
            return False
        # Empty dict/list in sensitivity map means structure exists but no fields are sensitive
        if (
            isinstance(sensitive_indicator, (dict, list))
            and len(sensitive_indicator) == 0
        ):
            return False
        # Non-empty dict/list means some nested fields might be sensitive
        return False

    def _is_hcl_reference(self, value: Any) -> bool:
        """Check if a value is an HCL reference (interpolation or direct reference).

        Args:
            value: The value to check

        Returns:
            True if the value appears to be an HCL reference
        """
        if not isinstance(value, str):
            return False

        # ${...} interpolation
        if "${" in value and "}" in value:
            return True

        # Direct reference patterns: azurerm_resource.name.attribute or resource["key"].attribute
        # Common Terraform provider prefixes
        provider_prefixes = [
            "azurerm_",
            "aws_",
            "google_",
            "azuread_",
            "data.",
            "var.",
            "local.",
            "module.",
        ]
        if any(value.startswith(prefix) for prefix in provider_prefixes):
            # Must have dots or brackets to be a reference
            if "." in value or "[" in value:
                return True

        return False

    def _redact_sensitive_fields(
        self, value: Any, sensitivity_map: Any
    ) -> Tuple[Any, Any]:
        """Recursively redact sensitive fields in a value.

        Args:
            value: The actual value to potentially redact
            sensitivity_map: The sensitivity metadata for this value

        Returns:
            Tuple of (redacted_value, sensitivity_info) where sensitivity_info
            indicates which parts are sensitive
        """
        # If the entire value is sensitive, redact it
        if self._is_value_sensitive(sensitivity_map):
            if self.show_sensitive:
                return value, True
            else:
                # Build the redacted display string
                display_value = "<REDACTED>"

                # If the value is an HCL reference, show it
                if isinstance(value, str) and self._is_hcl_reference(value):
                    display_value += f" (resolves to: {value})"
                elif value == "(known after apply)":
                    display_value = "<REDACTED> (resolves to: (known after apply))"

                return display_value, True

        # If it's a dict, recursively check each field
        if isinstance(value, dict) and isinstance(sensitivity_map, dict):
            redacted = {}
            sensitivity_info = {}
            for key, val in value.items():
                field_sensitivity = sensitivity_map.get(key)
                redacted_val, is_sensitive = self._redact_sensitive_fields(
                    val, field_sensitivity
                )
                redacted[key] = redacted_val
                if is_sensitive:
                    sensitivity_info[key] = is_sensitive

            # Return the dict with sensitive fields redacted
            return redacted, sensitivity_info if sensitivity_info else False

        # If it's a list, recursively check each element
        if isinstance(value, list) and isinstance(sensitivity_map, list):
            redacted = []
            sensitivity_info = []
            for i, val in enumerate(value):
                elem_sensitivity = (
                    sensitivity_map[i] if i < len(sensitivity_map) else None
                )
                redacted_val, is_sensitive = self._redact_sensitive_fields(
                    val, elem_sensitivity
                )
                redacted.append(redacted_val)
                sensitivity_info.append(is_sensitive if is_sensitive else False)

            return redacted, sensitivity_info if any(sensitivity_info) else False

        # Not sensitive
        return value, False

    def _redact_with_change_detection(
        self,
        before_value: Any,
        after_value: Any,
        before_sensitivity: Any,
        after_sensitivity: Any,
    ) -> Tuple[Any, Any, bool]:
        """Redact sensitive fields while detecting if values changed.

        Args:
            before_value: The before value
            after_value: The after value
            before_sensitivity: Sensitivity map for before value
            after_sensitivity: Sensitivity map for after value

        Returns:
            Tuple of (redacted_before, redacted_after, values_changed)
        """
        # Check if before value is sensitive
        before_is_sensitive = self._is_value_sensitive(before_sensitivity)
        after_is_sensitive = self._is_value_sensitive(after_sensitivity)

        # Compare the actual values BEFORE redaction
        values_changed = before_value != after_value

        # Now handle redaction
        if before_is_sensitive or after_is_sensitive:
            if self.show_sensitive:
                return before_value, after_value, values_changed
            else:
                # Build display strings
                before_display = "<REDACTED>"
                after_display = "<REDACTED>"

                # Add "(changed)" indicator if values differ
                if values_changed:
                    before_display = "<REDACTED (changed)>"
                    after_display = "<REDACTED (changed)>"

                # Show HCL references if available
                if isinstance(before_value, str) and self._is_hcl_reference(
                    before_value
                ):
                    before_display += f" (resolves to: {before_value})"
                elif before_value == "(known after apply)":
                    before_display = "<REDACTED> (resolves to: (known after apply))"

                if isinstance(after_value, str) and self._is_hcl_reference(after_value):
                    after_display += f" (resolves to: {after_value})"
                elif after_value == "(known after apply)":
                    after_display = "<REDACTED> (resolves to: (known after apply))"

                return before_display, after_display, values_changed

        # If it's a dict, recursively check each field
        if isinstance(before_value, dict) and isinstance(after_value, dict):
            redacted_before = {}
            redacted_after = {}
            any_changed = False

            all_keys = set(before_value.keys()) | set(after_value.keys())
            for key in all_keys:
                before_val = before_value.get(key)
                after_val = after_value.get(key)
                before_sens = (
                    before_sensitivity.get(key)
                    if isinstance(before_sensitivity, dict)
                    else None
                )
                after_sens = (
                    after_sensitivity.get(key)
                    if isinstance(after_sensitivity, dict)
                    else None
                )

                r_before, r_after, changed = self._redact_with_change_detection(
                    before_val, after_val, before_sens, after_sens
                )
                redacted_before[key] = r_before
                redacted_after[key] = r_after
                if changed:
                    any_changed = True

            return redacted_before, redacted_after, any_changed

        # If it's a list, recursively check each element
        if isinstance(before_value, list) and isinstance(after_value, list):
            redacted_before = []
            redacted_after = []
            any_changed = False

            max_len = max(len(before_value), len(after_value))
            for i in range(max_len):
                before_val = before_value[i] if i < len(before_value) else None
                after_val = after_value[i] if i < len(after_value) else None
                before_sens = (
                    before_sensitivity[i]
                    if isinstance(before_sensitivity, list)
                    and i < len(before_sensitivity)
                    else None
                )
                after_sens = (
                    after_sensitivity[i]
                    if isinstance(after_sensitivity, list)
                    and i < len(after_sensitivity)
                    else None
                )

                r_before, r_after, changed = self._redact_with_change_detection(
                    before_val, after_val, before_sens, after_sens
                )
                if before_val is not None:
                    redacted_before.append(r_before)
                if after_val is not None:
                    redacted_after.append(r_after)
                if changed:
                    any_changed = True

            return redacted_before, redacted_after, any_changed

        # Not sensitive - return as is
        return before_value, after_value, values_changed

    def print_summary(self, results: Dict[str, List]) -> None:
        """Print a formatted summary of the analysis."""
        created_count = len(results["created"])
        imported_count = len(results["imported"])
        tag_only_count = len(results["tag_only"])
        config_count = len(results["config_changes"])
        deleted_count = len(results["deleted"])
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

        if results["created"]:
            print(f"\nCREATED ({len(results['created'])})")
            print("-" * 60)
            for r in sorted(results["created"]):
                print(f"  {r}")

        if results["imported"]:
            print(f"\nIMPORTED ({len(results['imported'])})")
            print("-" * 60)
            for r in sorted(results["imported"]):
                print(f"  {r}")

        if results["config_changes"]:
            print(f"\nUPDATED - CONFIG CHANGES ({len(results['config_changes'])})")
            print("-" * 60)
            for item in sorted(results["config_changes"], key=lambda x: x["address"]):
                changed_attrs = item["changed_attributes"]

                if verbose:
                    # Show full before/after values
                    print(f"\n  {item['address']}")
                    for attr_name in sorted(changed_attrs.keys()):
                        before_val, after_val, before_sens_map, after_sens_map = (
                            changed_attrs[attr_name]
                        )

                        # Redact sensitive values using granular checking
                        display_before, before_sensitivity = (
                            self._redact_sensitive_fields(before_val, before_sens_map)
                        )
                        display_after, after_sensitivity = (
                            self._redact_sensitive_fields(after_val, after_sens_map)
                        )

                        # Format values for display
                        before_str = self._format_value(display_before)
                        after_str = self._format_value(display_after)

                        # Check if any part is sensitive
                        has_sensitive = before_sensitivity or after_sensitivity
                        sensitivity_marker = " 🔒" if has_sensitive else ""

                        print(f"    • {attr_name}{sensitivity_marker}:")
                        # Indent multi-line values
                        for line in before_str.split("\n"):
                            print(f"        - {line}")
                        for line in after_str.split("\n"):
                            print(f"        + {line}")
                else:
                    # Just show attribute names
                    attrs = ", ".join(sorted(changed_attrs.keys()))
                    print(f"  {item['address']}")
                    print(f"    → {attrs}")

        if results["tag_only"]:
            print(f"\nUPDATED - TAG-ONLY CHANGES ({len(results['tag_only'])})")
            print("-" * 60)
            for r in sorted(results["tag_only"]):
                print(f"  {r}")

        if results["deleted"]:
            print(f"\nDELETED ({len(results['deleted'])})")
            print("-" * 60)
            for r in sorted(results["deleted"]):
                print(f"  {r}")

    def print_ignore_report(self) -> None:
        """Print a report of what was ignored during analysis."""
        if not self.ignored_changes:
            return

        print("\n" + "=" * 60)
        print("IGNORED CHANGES REPORT")
        print("=" * 60)

        total_ignored = sum(
            len(resources)
            for fields in self.ignored_changes.values()
            for resources in fields.values()
        )
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
    def _highlight_char_diff(
        before_str: str, after_str: str, is_known_after_apply: bool = False
    ) -> Tuple[str, str]:
        """
        Highlight character-level differences between two similar strings.
        Returns HTML with character-level highlighting.

        This method delegates to the shared src.lib.diff_utils.highlight_char_diff function.
        """
        return highlight_char_diff(before_str, after_str, is_known_after_apply)

    def _highlight_json_diff(
        self, before: Any, after: Any, values_changed: bool = None
    ) -> Tuple[str, str, bool]:
        """
        Highlight differences between two JSON structures.
        Returns HTML for before and after with differences highlighted, and a flag for known_after_apply.
        Only highlights lines that are actually different.

        Args:
            before: The before value
            after: The after value
            values_changed: Optional metadata flag indicating if the actual values changed
                           (used when both display as identical strings like <REDACTED (changed)>)
        """
        # Check if after is "(known after apply)" or contains HCL values
        is_known_after_apply = after == "(known after apply)"

        # Check if value is from HCL (contains interpolations like ${...})
        # This applies when we resolved from HCL but it has variable references
        is_from_hcl = False
        if isinstance(after, (dict, list, str)):
            after_json = (
                json.dumps(after, indent=2, sort_keys=True)
                if not isinstance(after, str)
                else after
            )
            is_from_hcl = "${" in after_json

        # If it's from HCL, treat like known_after_apply for styling purposes
        if is_from_hcl:
            is_known_after_apply = True

        # Normalize values to handle case-insensitive Azure resource IDs
        # This ensures resource ID casing differences don't show in the diff
        normalized_before = TerraformPlanAnalyzer._normalize_for_comparison_static(
            before, self.ignore_azure_casing
        )
        normalized_after = TerraformPlanAnalyzer._normalize_for_comparison_static(
            after, self.ignore_azure_casing
        )

        # Delegate to shared highlighting utility
        before_html, after_html = highlight_json_diff_util(
            normalized_before,
            normalized_after,
            is_known_after_apply=is_known_after_apply,
            values_changed=values_changed,
        )

        return before_html, after_html, is_known_after_apply

    def _transform_results_for_html(self, results: Dict) -> Dict[str, Any]:
        """Transform results dict from analyze() format to HTML-friendly format."""
        transformed = {
            "summary": {
                "total": len(self.resource_changes),
                "created": len(results["created"]),
                "imported": len(results["imported"]),
                "updated": len(results["tag_only"]) + len(results["config_changes"]),
                "tag_only": len(results["tag_only"]),
                "config_changes": len(results["config_changes"]),
                "deleted": len(results["deleted"]),
            },
            "created": results["created"],
            "updated": [],
        }

        # Transform config_changes from tuple format to list-of-dicts format
        for item in results["config_changes"]:
            changes_list = []
            for attr_name, (
                before_val,
                after_val,
                before_sens_map,
                after_sens_map,
            ) in item["changed_attributes"].items():
                # Use change detection to compare before redacting
                display_before, display_after, values_changed = (
                    self._redact_with_change_detection(
                        before_val, after_val, before_sens_map, after_sens_map
                    )
                )

                # Check if any part is sensitive
                before_sensitivity = self._is_value_sensitive(before_sens_map)
                after_sensitivity = self._is_value_sensitive(after_sens_map)
                has_sensitive = before_sensitivity or after_sensitivity

                # If not sensitive at the top level, check nested sensitivity
                if not has_sensitive:
                    _, before_sensitivity = self._redact_sensitive_fields(
                        before_val, before_sens_map
                    )
                    _, after_sensitivity = self._redact_sensitive_fields(
                        after_val, after_sens_map
                    )
                    has_sensitive = bool(before_sensitivity or after_sensitivity)

                changes_list.append(
                    {
                        "attribute": attr_name,
                        "before": display_before,
                        "after": display_after,
                        "is_sensitive": has_sensitive,
                        "values_changed": values_changed,
                    }
                )

            transformed["updated"].append(
                {"name": item["address"], "changes": changes_list}
            )

        return transformed

    def generate_html_report(self, results: Dict, output_path: str) -> None:
        """Generate an HTML report from the analysis results."""
        data = self._transform_results_for_html(results)
        current_date = datetime.now().strftime("%B %d, %Y")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Plan Analysis Report</title>
    {src.lib.html_generation.generate_full_styles()}
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
                
                <div class="legend-section">
                    <h3>🔒 Security & Privacy</h3>
                    <div class="legend-item">
                        <span class="legend-symbol">🔒</span>
                        <span class="legend-description"><strong>Sensitive Values</strong> - Fields marked as sensitive by Terraform are redacted and shown as <code>&lt;REDACTED&gt;</code>. Use <code>--show-sensitive</code> flag to override (not recommended for shared reports).</span>
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
        if data["created"]:
            html_content += """
        <div class="section">
            <h2 class="section-header" onclick="toggleCreatedResources()" style="cursor: pointer;">
                <span id="created-icon">▶</span> 📦 Created Resources
            </h2>
            <div class="resource-list hidden" id="created-resources">
"""
            for resource in sorted(data["created"]):
                html_content += f'                <div class="resource-item">{html.escape(resource)}</div>\n'

            html_content += """            </div>
        </div>
"""

        # Updated resources section
        if data["updated"]:
            html_content += """
        <div class="section">
            <h2 class="section-header">🔄 Updated Resources</h2>
            <button class="toggle-all" onclick="toggleAll()">Expand/Collapse All</button>
"""

            for resource in sorted(data["updated"], key=lambda x: x["name"]):
                resource_name = html.escape(resource["name"])
                html_content += f"""
            <div class="resource-change">
                <div class="resource-change-header">
                    <span class="toggle-icon" onclick="toggleResource(this)">▼</span>
                    <span class="resource-name">{resource_name}</span>
                </div>
                <div class="resource-change-content">
"""

                for change in sorted(resource["changes"], key=lambda x: x["attribute"]):
                    attr_name = html.escape(change["attribute"])
                    is_sensitive = change.get("is_sensitive", False)
                    sensitivity_badge = (
                        ' <span class="sensitive-badge">🔒 SENSITIVE</span>'
                        if is_sensitive
                        else ""
                    )

                    html_content += f"""
                    <div class="change-item">
                        <div class="change-attribute">{attr_name}{sensitivity_badge}</div>
"""

                    before = change.get("before")
                    after = change.get("after")

                    # Check if it's a simple value or complex structure
                    if isinstance(before, (dict, list)) or isinstance(
                        after, (dict, list)
                    ):
                        # Complex structure - use diff highlighting
                        # Pass values_changed metadata to enable highlighting even when strings are identical
                        values_changed_metadata = change.get("values_changed", None)
                        before_html, after_html, is_known_after_apply = (
                            self._highlight_json_diff(
                                before, after, values_changed_metadata
                            )
                        )
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
                        before_str = html.escape(
                            str(before) if before is not None else "null"
                        )
                        after_str = html.escape(
                            str(after) if after is not None else "null"
                        )
                        # Check if from HCL or truly unknown
                        is_from_hcl = "${" in str(after)
                        is_known_after_apply = (
                            after == "(known after apply)" or is_from_hcl
                        )

                        if is_from_hcl:
                            emoji = '<span title="Value from Terraform config, not plan">⚙️</span>'
                        elif after == "(known after apply)":
                            emoji = '<span title="Computed at apply time">⚠️</span>'
                        else:
                            emoji = ""

                        after_class = (
                            "after known-after-apply"
                            if is_known_after_apply
                            else "after"
                        )
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
            total_ignored = sum(
                len(resources)
                for fields in self.ignored_changes.values()
                for resources in fields.values()
            )

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

        with open(output_path, "w", encoding="utf-8", errors="surrogatepass") as f:
            f.write(html_content)

    def generate_json_report(self, results: Dict, output_path: str) -> None:
        """Generate a JSON report from the analysis results."""
        from datetime import datetime

        # Build summary statistics
        summary = {
            "total": len(self.resource_changes),
            "created": len(results["created"]),
            "imported": len(results["imported"]),
            "updated": len(results["tag_only"]) + len(results["config_changes"]),
            "tag_only": len(results["tag_only"]),
            "config_changes": len(results["config_changes"]),
            "deleted": len(results["deleted"]),
            "ignored_changes": sum(
                len(resources)
                for fields in self.ignored_changes.values()
                for resources in fields.values()
            ),
        }

        # Transform updated resources with full change details
        updated_resources = []
        for item in results["config_changes"]:
            changes = []
            for attr_name, (
                before_val,
                after_val,
                before_sens_map,
                after_sens_map,
            ) in item["changed_attributes"].items():
                # Use change detection to compare before redacting
                display_before, display_after, values_changed = (
                    self._redact_with_change_detection(
                        before_val, after_val, before_sens_map, after_sens_map
                    )
                )

                # Check if any part is sensitive
                before_sensitivity = self._is_value_sensitive(before_sens_map)
                after_sensitivity = self._is_value_sensitive(after_sens_map)
                has_sensitive = before_sensitivity or after_sensitivity

                # If not sensitive at the top level, check nested sensitivity
                if not has_sensitive:
                    _, before_sensitivity = self._redact_sensitive_fields(
                        before_val, before_sens_map
                    )
                    _, after_sensitivity = self._redact_sensitive_fields(
                        after_val, after_sens_map
                    )
                    has_sensitive = bool(before_sensitivity or after_sensitivity)

                # Determine if this is "known after apply"
                is_known_after_apply = after_val == "(known after apply)"

                # Check if value is from HCL (contains interpolations or direct references)
                is_from_hcl = False
                if isinstance(after_val, (dict, list, str)):
                    after_json = (
                        json.dumps(after_val, indent=2, sort_keys=True)
                        if not isinstance(after_val, str)
                        else str(after_val)
                    )
                    is_from_hcl = self._is_hcl_reference(after_json)

                # Also check before value for HCL references
                before_hcl_ref = None
                after_hcl_ref = None
                if isinstance(before_val, str) and self._is_hcl_reference(before_val):
                    before_hcl_ref = before_val
                if isinstance(after_val, str) and self._is_hcl_reference(after_val):
                    after_hcl_ref = after_val

                if is_from_hcl:
                    is_known_after_apply = True

                change_info = {
                    "attribute": attr_name,
                    "before": display_before,
                    "after": display_after,
                    "is_known_after_apply": is_known_after_apply,
                    "is_sensitive": has_sensitive,
                    "value_changed": values_changed,
                }

                # Add HCL reference information if available
                if before_hcl_ref:
                    change_info["before_hcl_reference"] = before_hcl_ref
                if after_hcl_ref:
                    change_info["after_hcl_reference"] = after_hcl_ref

                changes.append(change_info)

            updated_resources.append({"address": item["address"], "changes": changes})

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
                        "reason": reason,
                        "resources": [],
                    }

                # Add resources with their type
                for resource in resources:
                    ignored_changes_by_field[field]["resources"].append(
                        {"address": resource, "resource_type": resource_type}
                    )

        # Build the complete report
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "plan_file": str(self.plan_file),
                "analyzer_version": "1.0",
                "ignore_azure_casing": self.ignore_azure_casing,
                "sensitive_values_shown": self.show_sensitive,
            },
            "summary": summary,
            "created_resources": sorted(results["created"]),
            "imported_resources": sorted(results["imported"]),
            "updated_resources": sorted(updated_resources, key=lambda x: x["address"]),
            "tag_only_updates": sorted(results["tag_only"]),
            "deleted_resources": sorted(results["deleted"]),
            "ignored_changes": ignored_changes_by_field,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, sort_keys=False)


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)


def handle_report_subcommand(args):
    """Handle the 'report' subcommand for single-plan analysis."""
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
        if "global_ignores" in config:
            if isinstance(config["global_ignores"], list):
                custom_ignore_fields.update(config["global_ignores"])
            elif isinstance(config["global_ignores"], dict):
                for field, reason in config["global_ignores"].items():
                    custom_ignore_fields.add(field)
                    global_ignore_reasons[field] = reason
            else:
                print("Warning: 'global_ignores' should be a list or dict")

        # Load resource-specific ignores from config (supports both list and dict formats)
        if "resource_ignores" in config:
            if isinstance(config["resource_ignores"], dict):
                for resource_type, fields in config["resource_ignores"].items():
                    if isinstance(fields, list):
                        resource_specific_ignores[resource_type] = set(fields)
                    elif isinstance(fields, dict):
                        resource_specific_ignores[resource_type] = set(fields.keys())
                        resource_ignore_reasons[resource_type] = fields
                    else:
                        print(
                            f"Warning: Fields for '{resource_type}' should be a list or dict"
                        )
            else:
                print("Warning: 'resource_ignores' should be a dict")

    # Parse custom ignore fields from CLI (additive to config)
    if args.ignore_fields:
        for field_arg in args.ignore_fields:
            # Support comma-separated values
            fields = [f.strip() for f in field_arg.split(",")]
            custom_ignore_fields.update(fields)

    # Parse resource-specific ignores from CLI (additive to config)
    if args.resource_ignores:
        for resource_ignore in args.resource_ignores:
            if ":" not in resource_ignore:
                print(f"Warning: Invalid format for --ignore-for: {resource_ignore}")
                print("Expected format: resource_type:field1,field2")
                continue

            resource_type, fields_str = resource_ignore.split(":", 1)
            resource_type = resource_type.strip()
            fields = {f.strip() for f in fields_str.split(",")}

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
    analyzer = TerraformPlanAnalyzer(
        args.plan_file,
        custom_ignore_fields,
        resource_specific_ignores,
        global_ignore_reasons,
        resource_ignore_reasons,
        hcl_resolver,
        args.ignore_azure_casing,
        args.show_sensitive,
    )

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
            if plan_path.suffix == ".json":
                html_output = str(plan_path.with_suffix(".html"))
            else:
                html_output = str(plan_path) + ".html"
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
            if plan_path.suffix == ".json":
                # Remove .json and add .report.json
                json_output = str(plan_path.with_suffix("")) + ".report.json"
            else:
                json_output = str(plan_path) + ".report.json"
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


def handle_compare_subcommand(args):
    """Handle the 'compare' subcommand for multi-environment comparison."""
    from src.core.multi_env_comparator import EnvironmentPlan, MultiEnvReport
    from pathlib import Path
    from src.lib.ignore_utils import load_ignore_config

    # Validate at least 2 plan files
    if len(args.plan_files) < 2:
        print("Error: The 'compare' subcommand requires at least 2 plan files.")
        print("Tip: For single plan analysis, use the 'report' subcommand instead:")
        print(
            f"  python analyze_plan.py report {args.plan_files[0] if args.plan_files else 'plan.json'}"
        )
        sys.exit(1)

    # Check all files exist
    for plan_file in args.plan_files:
        if not Path(plan_file).exists():
            print(f"Error: File not found: {plan_file}")
            sys.exit(1)

    # Parse and validate tfvars files if provided
    tfvars_files = None
    if args.tfvars_files:
        tfvars_files = [f.strip() for f in args.tfvars_files.split(",")]

        # Validate count matches plan files
        if len(tfvars_files) != len(args.plan_files):
            print(
                f"Error: Number of tfvars files ({len(tfvars_files)}) must match number of plan files ({len(args.plan_files)})"
            )
            print(f"Provided tfvars: {', '.join(tfvars_files)}")
            print(f"Provided plan files: {len(args.plan_files)}")
            sys.exit(1)

        # Check tfvars files exist
        for tfvars_file in tfvars_files:
            if not Path(tfvars_file).exists():
                print(f"Error: Tfvars file not found: {tfvars_file}")
                sys.exit(1)

    # Create environment names
    if args.env_names:
        # Parse comma-separated names
        env_names = [name.strip() for name in args.env_names.split(",")]

        # Validate count matches
        if len(env_names) != len(args.plan_files):
            print(
                f"Error: Number of environment names ({len(env_names)}) must match number of plan files ({len(args.plan_files)})"
            )
            print(f"Provided names: {', '.join(env_names)}")
            print(f"Provided files: {len(args.plan_files)}")
            sys.exit(1)
    else:
        # Derive names from filenames by default
        env_names = []
        for plan_file in args.plan_files:
            # Derive name from filename: "dev-plan.json" -> "dev-plan"
            name = Path(plan_file).stem
            env_names.append(name)

    # Validate for duplicate environment names
    if len(env_names) != len(set(env_names)):
        duplicates = [name for name in env_names if env_names.count(name) > 1]
        print(
            f"Error: Duplicate environment names detected: {', '.join(set(duplicates))}"
        )
        print(
            "Each environment must have a unique name. Use --env-names to specify custom names."
        )
        sys.exit(1)

    # Create EnvironmentPlan objects
    environments = []
    for idx, (name, plan_file) in enumerate(zip(env_names, args.plan_files)):
        # Get corresponding tfvars file if provided
        tfvars_file = tfvars_files[idx] if tfvars_files else None

        env_plan = EnvironmentPlan(
            label=name,
            plan_file_path=Path(plan_file),
            tf_dir=args.tf_dir,
            tfvars_file=tfvars_file,
            show_sensitive=args.show_sensitive,
        )
        environments.append(env_plan)

    print(f"Comparing {len(args.plan_files)} environments: {', '.join(env_names)}")

    # Load ignore configuration if provided
    ignore_config = None
    if args.config:
        try:
            ignore_config = load_ignore_config(Path(args.config))
        except FileNotFoundError:
            print(f"Error: Ignore config file not found: {args.config}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Malformed JSON in config file: {e}")
            sys.exit(2)
        except ValueError as e:
            print(f"Error: Invalid config file structure: {e}")
            sys.exit(2)

    # Create MultiEnvReport and perform comparison
    diff_only = getattr(args, "diff_only", False)
    verbose_normalization = getattr(args, "verbose_normalization", False)
    report = MultiEnvReport(
        environments=environments, 
        diff_only=diff_only, 
        ignore_config=ignore_config,
        verbose_normalization=verbose_normalization
    )

    # Load environments with error handling
    try:
        report.load_environments()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in plan file: {e}")
        print("Ensure all plan files are valid Terraform JSON plan outputs.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading plan files: {e}")
        sys.exit(1)

    # Build comparisons and calculate summary
    try:
        report.build_comparisons()
        report.calculate_summary()
    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(1)

    # Generate output
    if args.html:
        # Determine output path
        if args.html is True:
            html_output = "comparison_report.html"
        else:
            html_output = args.html

        # Generate HTML report
        report.generate_html(html_output)
        print(f"✅ HTML comparison report generated: {html_output}")
        print(
            f"📊 Summary: {report.summary_stats['total_unique_resources']} resources, "
            + f"{report.summary_stats['resources_with_differences']} with differences"
        )
    else:
        # Text output with verbose support
        verbose = getattr(args, "verbose", False)
        text_output = report.generate_text(verbose=verbose)
        print(text_output)


def handle_obfuscate_subcommand(args):
    """Handle the 'obfuscate' subcommand for sensitive data obfuscation."""
    import time

    # Check dependencies
    if not all(
        [
            generate_salt,
            generate_position_seed,
            store_salt,
            load_salt,
            traverse_and_obfuscate,
        ]
    ):
        print(
            "Error: Obfuscate subcommand requires salt_manager and sensitive_obfuscator modules",
            file=sys.stderr,
        )
        print(
            "  Install cryptography: pip install 'cryptography>=41.0.0'",
            file=sys.stderr,
        )
        sys.exit(8)

    start_time = time.time()

    # Validate input file exists
    input_path = Path(args.plan_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.plan_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default: <input_stem>-obfuscated.json
        output_path = input_path.parent / f"{input_path.stem}-obfuscated.json"

    # Check if output file exists (unless --force)
    if output_path.exists() and not args.force:
        print(f"Error: Output file already exists: {output_path}", file=sys.stderr)
        print(
            f"  Use --force to overwrite, or specify different output with --output",
            file=sys.stderr,
        )
        sys.exit(4)

    # Load input plan
    try:
        with open(input_path, "r") as f:
            plan_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON from {input_path}", file=sys.stderr)
        print(f"  {str(e)}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: Failed to read input file: {input_path}", file=sys.stderr)
        print(f"  {str(e)}", file=sys.stderr)
        sys.exit(8)

    # Validate Terraform plan structure
    if "resource_changes" not in plan_data:
        print(f"Error: Input file is not a valid Terraform plan", file=sys.stderr)
        print(f"  Missing required field: resource_changes", file=sys.stderr)
        sys.exit(3)

    # Load or generate salt
    if args.salt_file:
        # Load existing salt
        salt, position_seed = load_salt(args.salt_file)
        salt_file_path = Path(args.salt_file)
    else:
        # Generate new salt
        salt = generate_salt()
        position_seed = generate_position_seed()
        salt_file_path = Path(str(output_path) + ".salt")

    # Obfuscate resource changes
    resource_count = 0
    values_obfuscated = 0

    try:
        for rc in plan_data.get("resource_changes", []):
            resource_count += 1
            address = rc.get("address", f"resource_{resource_count}")
            change = rc.get("change", {})

            # Get before and after data with sensitive markers
            before_data = change.get("before")
            after_data = change.get("after")
            before_sensitive = change.get("before_sensitive")
            after_sensitive = change.get("after_sensitive")

            try:
                # Obfuscate before values if present
                if (
                    before_data is not None
                    and before_sensitive is not None
                    and before_sensitive is not False
                ):
                    obfuscated_before = traverse_and_obfuscate(
                        before_data,
                        before_sensitive,
                        salt,
                        position_seed,
                        path=[address, "before"],
                    )
                    change["before"] = obfuscated_before

                    # Count obfuscated values
                    def count_sensitive(marker):
                        if marker is True:
                            return 1
                        elif isinstance(marker, dict):
                            return sum(count_sensitive(v) for v in marker.values())
                        elif isinstance(marker, list):
                            return sum(count_sensitive(v) for v in marker)
                        return 0

                    values_obfuscated += count_sensitive(before_sensitive)

                # Obfuscate after values if present
                if (
                    after_data is not None
                    and after_sensitive is not None
                    and after_sensitive is not False
                ):
                    obfuscated_after = traverse_and_obfuscate(
                        after_data,
                        after_sensitive,
                        salt,
                        position_seed,
                        path=[address, "after"],
                    )
                    change["after"] = obfuscated_after

                    # Count obfuscated values
                    def count_sensitive(marker):
                        if marker is True:
                            return 1
                        elif isinstance(marker, dict):
                            return sum(count_sensitive(v) for v in marker.values())
                        elif isinstance(marker, list):
                            return sum(count_sensitive(v) for v in marker)
                        return 0

                    values_obfuscated += count_sensitive(after_sensitive)

            except ValueError as e:
                print(f"Error: Malformed sensitive_values structure", file=sys.stderr)
                print(f"  Resource: {address}", file=sys.stderr)
                print(f"  {str(e)}", file=sys.stderr)
                sys.exit(7)
            except Exception as e:
                print(
                    f"Error: Failed to obfuscate resource: {address}", file=sys.stderr
                )
                print(f"  {str(e)}", file=sys.stderr)
                sys.exit(8)

        # Write obfuscated plan to output file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to write output file: {output_path}", file=sys.stderr)
            print(f"  {str(e)}", file=sys.stderr)
            sys.exit(8)

        # Save salt file (if we generated it)
        if not args.salt_file:
            store_salt(salt, position_seed, str(salt_file_path))

        # Report success
        execution_time = time.time() - start_time
        print(f"✅ Obfuscated plan saved to: {output_path}")
        if not args.salt_file:
            print(f"🔐 Salt saved to: {salt_file_path}")

        if args.show_stats:
            print()
            print("Statistics:")
            print(f"  Resources processed: {resource_count}")
            print(f"  Values obfuscated: {values_obfuscated}")
            print(f"  Execution time: {execution_time:.1f}s")

    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Error: Unexpected error during obfuscation", file=sys.stderr)
        print(f"  {str(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(8)


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Analyze Terraform plan JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  report    Analyze a single Terraform plan file (default mode)
  compare   Compare multiple Terraform plan files across environments

Examples:
  # Single plan analysis (report subcommand)
  python analyze_plan.py report tfplan.json
  python analyze_plan.py report tfplan.json --config ignore_config.json
  # Single plan analysis (report subcommand)
  python analyze_plan.py report tfplan.json
  python analyze_plan.py report tfplan.json --config ignore_config.json
  python analyze_plan.py report tfplan.json --html
  python analyze_plan.py report tfplan.json --ignore description
  
  # Multi-environment comparison (compare subcommand)
  python analyze_plan.py compare dev.json staging.json prod.json --html
  python analyze_plan.py compare dev.json prod.json --env-names "Development,Production"
        """,
    )

    # Create subparsers for subcommands
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # ========== REPORT SUBCOMMAND (single plan analysis) ==========
    report_parser = subparsers.add_parser(
        "report",
        help="Analyze a single Terraform plan file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python analyze_plan.py report tfplan.json
  
  # Use a config file
  python analyze_plan.py report tfplan.json --config ignore_config.json
  
  # Ignore specific fields
  python analyze_plan.py report tfplan.json --ignore description
  
  # Ignore multiple fields globally
  python analyze_plan.py report tfplan.json --ignore description --ignore severity
  python analyze_plan.py report tfplan.json --ignore description,severity,scopes
  
  # Ignore fields for specific resource types
  python analyze_plan.py report tfplan.json --ignore-for azurerm_monitor_metric_alert:tags,action,description
  python analyze_plan.py report tfplan.json --ignore-for azurerm_storage_account:min_tls_version,cross_tenant_replication_enabled
  
  # Combine config file with CLI args (CLI args are additive)
  python analyze_plan.py report tfplan.json --config ignore_config.json --ignore extra_field
  
  # Generate HTML report
  python analyze_plan.py report tfplan.json --html
  python analyze_plan.py report tfplan.json --html custom_report.html
  
  # Generate JSON report for programmatic analysis
  python analyze_plan.py report tfplan.json --json
  python analyze_plan.py report tfplan.json --json custom_report.json
  
  # Ignore Azure resource ID casing differences
  python analyze_plan.py report tfplan.json --ignore-azure-casing
  
  # Show currently ignored fields
  python analyze_plan.py report tfplan.json --show-ignores
  
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
        """,
    )

    report_parser.add_argument("plan_file", help="Path to the terraform plan JSON file")
    report_parser.add_argument(
        "--config",
        "-c",
        dest="config_file",
        help="Path to JSON config file with ignore settings",
    )
    report_parser.add_argument(
        "--ignore",
        "-i",
        action="append",
        dest="ignore_fields",
        help="Additional field(s) to ignore globally when detecting changes (can be used multiple times or comma-separated)",
    )
    report_parser.add_argument(
        "--ignore-for",
        action="append",
        dest="resource_ignores",
        help="Ignore specific fields for a resource type. Format: resource_type:field1,field2 (e.g., azurerm_monitor_metric_alert:tags,action,description)",
    )
    report_parser.add_argument(
        "--show-ignores", action="store_true", help="Display all fields being ignored"
    )
    report_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show full before/after values for changed attributes",
    )
    report_parser.add_argument(
        "--html",
        nargs="?",
        const=True,
        default=None,
        metavar="OUTPUT",
        help="Generate HTML report instead of text output. Optionally specify output path (default: <plan_file>.html)",
    )
    report_parser.add_argument(
        "--json",
        nargs="?",
        const=True,
        default=None,
        metavar="OUTPUT",
        help="Generate JSON report for programmatic analysis. Optionally specify output path (default: <plan_file>.report.json)",
    )
    report_parser.add_argument(
        "--tf-dir",
        type=str,
        default=None,
        metavar="DIR",
        help='Directory containing Terraform .tf files for resolving "known after apply" values (default: same directory as plan file)',
    )
    report_parser.add_argument(
        "--ignore-azure-casing",
        action="store_true",
        help="Ignore casing differences in Azure resource IDs (e.g., /providers/Microsoft.IotHub vs /providers/Microsoft.Iothub)",
    )
    report_parser.add_argument(
        "--show-sensitive",
        action="store_true",
        help="Show sensitive values in reports instead of redacting them (use with caution)",
    )

    # ========== COMPARE SUBCOMMAND (multi-environment comparison) ==========
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare multiple Terraform plan files across environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare three environments
  python analyze_plan.py compare dev.json staging.json prod.json --html
  
  # Compare with custom environment names
  python analyze_plan.py compare dev.json prod.json --env-names "Development,Production"
  
  # Show only resources with differences
  python analyze_plan.py compare dev.json staging.json prod.json --diff-only --html
        """,
    )

    compare_parser.add_argument(
        "plan_files",
        nargs="+",
        help="Paths to Terraform plan JSON files (minimum 2 required)",
    )
    compare_parser.add_argument(
        "--html",
        nargs="?",
        const=True,
        default=None,
        metavar="OUTPUT",
        help="Generate HTML report. Optionally specify output path (default: comparison_report.html)",
    )
    compare_parser.add_argument(
        "--env-names",
        type=str,
        default=None,
        metavar="NAMES",
        help='Comma-separated list of environment names (e.g., "dev,staging,prod"). If not provided, names are derived from filenames.',
    )
    compare_parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Show only resources with differences (hide identical resources)",
    )
    compare_parser.add_argument(
        "--tf-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="Directory containing Terraform .tf files for HCL value resolution",
    )
    compare_parser.add_argument(
        "--tfvars-files",
        type=str,
        default=None,
        metavar="FILES",
        help="Comma-separated list of .tfvars files (one per environment, in same order as plan files)",
    )
    compare_parser.add_argument(
        "--show-sensitive",
        action="store_true",
        help="Show actual sensitive values instead of masking them (not recommended for shared reports)",
    )
    compare_parser.add_argument(
        "--config",
        type=str,
        default=None,
        metavar="FILE",
        help="Path to ignore configuration JSON file (same format as single-plan report)",
    )
    compare_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed configuration for each resource in text output",
    )
    compare_parser.add_argument(
        "--verbose-normalization",
        action="store_true",
        help="Log normalization transformations (before/after values) for debugging",
    )

    # ========== OBFUSCATE SUBCOMMAND (sensitive data obfuscation) ==========
    obfuscate_parser = subparsers.add_parser(
        "obfuscate",
        help="Obfuscate sensitive values in Terraform plan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic obfuscation (generates new salt)
  python analyze_plan.py obfuscate plan.json
  
  # Custom output path
  python analyze_plan.py obfuscate plan.json --output sanitized/plan.json
  
  # Reuse salt for drift detection across files
  python analyze_plan.py obfuscate dev.json -o dev-obf.json
  python analyze_plan.py obfuscate prod.json -o prod-obf.json -s dev-obf.json.salt
  
  # Force overwrite existing output
  python analyze_plan.py obfuscate plan.json --force
  
  # Show statistics
  python analyze_plan.py obfuscate plan.json --show-stats
        """,
    )

    obfuscate_parser.add_argument("plan_file", help="Path to Terraform plan JSON file")
    obfuscate_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        metavar="OUTPUT",
        help="Output file path (default: <input>-obfuscated.json)",
    )
    obfuscate_parser.add_argument(
        "--salt-file",
        "-s",
        type=str,
        default=None,
        metavar="SALT",
        help="Existing salt file for deterministic hashing",
    )
    obfuscate_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing output file"
    )
    obfuscate_parser.add_argument(
        "--show-stats", action="store_true", help="Display obfuscation statistics"
    )

    args = parser.parse_args()

    # If no subcommand provided, show help
    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate handler
    if args.subcommand == "report":
        handle_report_subcommand(args)
    elif args.subcommand == "compare":
        handle_compare_subcommand(args)
    elif args.subcommand == "obfuscate":
        handle_obfuscate_subcommand(args)


if __name__ == "__main__":
    import signal

    # Ignore SIGPIPE to prevent BrokenPipeError when piping to head, less, etc.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        sys.exit(0)
