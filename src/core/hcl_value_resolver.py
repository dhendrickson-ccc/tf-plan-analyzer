#!/usr/bin/env python3
"""
HCL Value Resolver for Terraform configurations.

Parses .tf files to extract resource definitions and resolves variables
from variables.tf and .tfvars files.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Set


class HCLValueResolver:
    """Resolves Terraform HCL values with variable substitution."""

    def __init__(self, tf_dir: str):
        """
        Initialize the resolver with a directory containing .tf files.

        Args:
            tf_dir: Path to directory containing Terraform files
        """
        self.tf_dir = Path(tf_dir)
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.variables: Dict[str, Any] = {}
        self.locals: Dict[str, Any] = {}

        # Load all definitions
        self._load_variables()
        self._load_locals()
        self._load_resources()

    def _load_variables(self) -> None:
        """Load variable definitions and values from variables.tf and .tfvars files."""
        # First, load defaults from variables.tf
        for tf_file in self.tf_dir.glob("variables.tf"):
            content = tf_file.read_text()
            self._parse_variable_definitions(content)

        # Then, override with .tfvars values (higher priority)
        for tfvars_file in self.tf_dir.glob("*.tfvars"):
            content = tfvars_file.read_text()
            self._parse_tfvars(content)

        # Also check for terraform.tfvars specifically
        terraform_tfvars = self.tf_dir / "terraform.tfvars"
        if terraform_tfvars.exists():
            content = terraform_tfvars.read_text()
            self._parse_tfvars(content)

    def _parse_variable_definitions(self, content: str) -> None:
        """Parse variable blocks to extract default values."""
        # Pattern: variable "name" { default = "value" }
        var_pattern = re.compile(
            r'variable\s+"([^"]+)"\s*\{([^}]*)\}', re.MULTILINE | re.DOTALL
        )

        for match in var_pattern.finditer(content):
            var_name = match.group(1)
            var_block = match.group(2)

            # Extract default value
            default_match = re.search(
                r"default\s*=\s*(.+?)(?:\n|$)", var_block, re.MULTILINE
            )
            if default_match:
                default_value = self._parse_value(default_match.group(1).strip())
                if (
                    var_name not in self.variables
                ):  # Only set if not already set by tfvars
                    self.variables[var_name] = default_value

    def _parse_tfvars(self, content: str) -> None:
        """Parse .tfvars file for variable assignments."""
        # Pattern: variable_name = "value"
        assignment_pattern = re.compile(r"(\w+)\s*=\s*(.+?)(?:\n|$)", re.MULTILINE)

        for match in assignment_pattern.finditer(content):
            var_name = match.group(1)
            value_str = match.group(2).strip()
            self.variables[var_name] = self._parse_value(value_str)

    def _load_locals(self) -> None:
        """Load local values from all .tf files."""
        for tf_file in self.tf_dir.glob("*.tf"):
            content = tf_file.read_text()
            self._parse_locals(content)

    def _parse_locals(self, content: str) -> None:
        """Parse locals blocks."""
        # Pattern: locals { name = value }
        locals_pattern = re.compile(r"locals\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL)

        for match in locals_pattern.finditer(content):
            locals_block = match.group(1)

            # Parse each assignment in the locals block
            assignment_pattern = re.compile(
                r"(\w+)\s*=\s*(.+?)(?=\n\s*\w+\s*=|\n\s*\}|$)", re.MULTILINE | re.DOTALL
            )

            for assign_match in assignment_pattern.finditer(locals_block):
                local_name = assign_match.group(1)
                value_str = assign_match.group(2).strip()
                self.locals[local_name] = self._parse_value(value_str)

    def _load_resources(self) -> None:
        """Load resource definitions from all .tf files."""
        for tf_file in self.tf_dir.glob("*.tf"):
            content = tf_file.read_text()
            self._parse_resources(content)

    def _parse_resources(self, content: str) -> None:
        """Parse resource blocks and extract attributes."""
        # Pattern: resource "type" "name" { ... }
        resource_pattern = re.compile(
            r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE
        )

        matches = list(resource_pattern.finditer(content))

        for i, match in enumerate(matches):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_address = f"{resource_type}.{resource_name}"

            # Find the closing brace for this resource block
            start_pos = match.end()
            resource_body = self._extract_block_content(content, start_pos)

            # Parse the resource body into a dictionary
            attributes = self._parse_resource_body(resource_body)

            self.resources[resource_address] = attributes

    def _extract_block_content(self, content: str, start_pos: int) -> str:
        """Extract content between matching braces."""
        brace_count = 1
        pos = start_pos

        while pos < len(content) and brace_count > 0:
            char = content[pos]
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            pos += 1

        return content[start_pos : pos - 1]  # Exclude the closing brace

    def _parse_resource_body(self, body: str) -> Dict[str, Any]:
        """Parse resource body into a dictionary of attributes."""
        attributes = {}

        # Remove comments
        body = re.sub(r"#[^\n]*", "", body)
        body = re.sub(r"//[^\n]*", "", body)

        # Pattern for assignments with map values: key = { ... }
        map_assignment_pattern = re.compile(r"^\s*(\w+)\s*=\s*\{", re.MULTILINE)

        # Pattern for nested blocks (no equals): key { ... }
        block_pattern = re.compile(r"^\s*(\w+)\s*\{", re.MULTILINE)

        # Track positions we've already processed
        processed_positions: Set[int] = set()

        # First, find all map assignments (key = { ... })
        for match in map_assignment_pattern.finditer(body):
            if match.start() in processed_positions:
                continue

            attr_name = match.group(1)
            start_pos = match.end()
            map_content = self._extract_block_content(body, start_pos)

            # Mark this entire assignment as processed
            for pos in range(match.start(), start_pos + len(map_content) + 1):
                processed_positions.add(pos)

            # Parse as a map/object
            attributes[attr_name] = self._parse_map(map_content)

        # Then, find nested blocks (key { ... } without =)
        for match in block_pattern.finditer(body):
            if match.start() in processed_positions:
                continue

            # Check if this is actually a map assignment (has = before {)
            # Look backwards from match start to see if there's an =
            before_match = body[max(0, match.start() - 50) : match.start()]
            if "=" in before_match.split("\n")[-1]:
                # This is a map assignment, already handled
                continue

            attr_name = match.group(1)
            start_pos = match.end()
            block_content = self._extract_block_content(body, start_pos)

            # Mark this entire block as processed
            for pos in range(match.start(), start_pos + len(block_content) + 1):
                processed_positions.add(pos)

            # Check if it's a list (multiple blocks with same name) or a map
            if attr_name in attributes:
                # Convert to list if not already
                if not isinstance(attributes[attr_name], list):
                    attributes[attr_name] = [attributes[attr_name]]
                attributes[attr_name].append(self._parse_resource_body(block_content))
            else:
                # Parse as nested object
                attributes[attr_name] = self._parse_resource_body(block_content)

        # Finally, find simple assignments (key = value, not maps)
        simple_pattern = re.compile(
            r"^\s*(\w+)\s*=\s*(.+?)(?=\n\s*\w+\s*=|\n\s*\}|\n\s*$|$)",
            re.MULTILINE | re.DOTALL,
        )

        for match in simple_pattern.finditer(body):
            if match.start() in processed_positions:
                continue

            attr_name = match.group(1)
            value_str = match.group(2).strip()

            # Skip if this looks like a block opening
            if value_str.endswith("{"):
                continue

            attributes[attr_name] = self._parse_value(value_str)

        return attributes

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string into Python types.
        Returns resolved value if possible, or string representation for interpolations.
        """
        value_str = value_str.strip()

        # Remove trailing commas
        if value_str.endswith(","):
            value_str = value_str[:-1].strip()

        # Quoted string
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]

        # Boolean
        if value_str == "true":
            return True
        if value_str == "false":
            return False

        # Null
        if value_str == "null":
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # List [...]
        if value_str.startswith("[") and value_str.endswith("]"):
            return self._parse_list(value_str[1:-1])

        # Map {...}
        if value_str.startswith("{") and value_str.endswith("}"):
            return self._parse_map(value_str[1:-1])

        # Variable reference: var.name
        var_match = re.match(r"var\.(\w+)", value_str)
        if var_match:
            var_name = var_match.group(1)
            if var_name in self.variables:
                return self.variables[var_name]
            else:
                return f"${{{value_str}}}"  # Keep as interpolation syntax

        # Local reference: local.name
        local_match = re.match(r"local\.(\w+)", value_str)
        if local_match:
            local_name = local_match.group(1)
            if local_name in self.locals:
                return self.locals[local_name]
            else:
                return f"${{{value_str}}}"

        # Resource/data reference (keep as-is, can't resolve without state)
        if "." in value_str and not value_str.startswith('"'):
            return f"${{{value_str}}}"

        # Function calls or complex expressions - keep as string representation
        if "(" in value_str or value_str.startswith("${"):
            return f"${{{value_str}}}"

        # Default: return as string
        return value_str

    def _parse_list(self, content: str) -> List[Any]:
        """Parse list content."""
        if not content.strip():
            return []

        items = []
        # Simple split by comma (doesn't handle nested structures perfectly)
        # For now, use a simple approach
        parts = content.split(",")
        for part in parts:
            part = part.strip()
            if part:
                items.append(self._parse_value(part))

        return items

    def _parse_map(self, content: str) -> Dict[str, Any]:
        """Parse map/object content."""
        result = {}

        # Pattern: key = value
        assignment_pattern = re.compile(
            r'(\w+|"[^"]+")\s*=\s*(.+?)(?=\n\s*\w+\s*=|\n\s*"[^"]+"\s*=|$)',
            re.MULTILINE | re.DOTALL,
        )

        for match in assignment_pattern.finditer(content):
            key = match.group(1).strip().strip('"')
            value_str = match.group(2).strip()

            # Remove trailing comma
            if value_str.endswith(","):
                value_str = value_str[:-1].strip()

            result[key] = self._parse_value(value_str)

        return result

    def get_resource_attribute(
        self, resource_address: str, attribute_path: str
    ) -> Optional[Any]:
        """
        Get a specific attribute value for a resource.

        Args:
            resource_address: Full resource address (e.g., "azurerm_windows_web_app.admin")
            attribute_path: Dot-separated path to attribute (e.g., "app_settings")

        Returns:
            The resolved attribute value, or None if not found
        """
        if resource_address not in self.resources:
            return None

        resource = self.resources[resource_address]

        # Navigate the path
        current = resource
        for part in attribute_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def get_all_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get all parsed resources."""
        return self.resources


if __name__ == "__main__":
    # Test the resolver
    import sys

    if len(sys.argv) > 1:
        resolver = HCLValueResolver(sys.argv[1])
        print(f"Loaded {len(resolver.resources)} resources")
        print(f"Loaded {len(resolver.variables)} variables")
        print(f"Loaded {len(resolver.locals)} locals")

        # Print a sample resource
        if resolver.resources:
            sample_addr = list(resolver.resources.keys())[0]
            print(f"\nSample resource: {sample_addr}")
            print(json.dumps(resolver.resources[sample_addr], indent=2, default=str))
