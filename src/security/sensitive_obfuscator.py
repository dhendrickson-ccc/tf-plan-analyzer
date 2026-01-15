#!/usr/bin/env python3
"""
Sensitive Value Obfuscator for Terraform Plans

Handles traversal of Terraform plan JSON structures and obfuscation of
sensitive values marked by Terraform's after_sensitive structure.

Uses SHA-256 hashing with salt inserted at variable positions for
irreversible but deterministic obfuscation.
"""

import hashlib
import json
import secrets
from typing import Union, Any, List, Dict


def get_salt_position(value_bytes: bytes, position_seed: bytes, max_length: int) -> int:
    """
    Determine salt insertion position using deterministic PRNG.

    Uses a hash of the value and position seed to generate a deterministic
    but unpredictable insertion position.

    Args:
        value_bytes: Value as bytes
        position_seed: Seed for position randomization (32 bytes)
        max_length: Maximum valid position (length of value)

    Returns:
        Position index (0 to max_length inclusive)
    """
    # Use SHA-256 to create deterministic but unpredictable position
    # Combine value_bytes and position_seed for the hash input
    position_hash = hashlib.sha256(value_bytes + position_seed).digest()

    # Convert first 8 bytes of hash to integer
    position_int = int.from_bytes(position_hash[:8], byteorder="big")

    # Modulo to get position within valid range (0 to max_length inclusive)
    # +1 because we can insert at any position including after the last byte
    return position_int % (max_length + 1)


def obfuscate_value(
    value: Union[str, int, float, bool, None], salt: bytes, position_seed: bytes
) -> str:
    """
    Hash a value with salt inserted at deterministic position.

    Converts the value to JSON representation, inserts salt at a position
    determined by the position seed, and hashes with SHA-256.

    Args:
        value: The sensitive value to obfuscate
        salt: Cryptographic salt (32 bytes)
        position_seed: Seed for position randomization (32 bytes)

    Returns:
        Obfuscated hash with "obf_" prefix (e.g., "obf_a1b2c3...")
    """
    # Convert value to bytes using JSON serialization to handle all types consistently
    value_json = json.dumps(value, sort_keys=True, ensure_ascii=False)
    value_bytes = value_json.encode("utf-8")

    # Determine salt insertion position
    position = get_salt_position(value_bytes, position_seed, len(value_bytes))

    # Insert salt at the determined position
    combined = value_bytes[:position] + salt + value_bytes[position:]

    # Hash the combined value
    hash_hex = hashlib.sha256(combined).hexdigest()

    # Return with "obf_" prefix
    return f"obf_{hash_hex}"


def traverse_and_obfuscate(
    data: Any,
    sensitive_marker: Any,
    salt: bytes,
    position_seed: bytes,
    path: List[str] = None,
) -> Any:
    """
    Recursively traverse JSON structure and obfuscate sensitive values.

    Walks the data structure in parallel with the sensitive_marker structure.
    When a field is marked as True in sensitive_marker, the corresponding
    value in data is replaced with its obfuscated hash.

    Args:
        data: The actual data structure (from resource.change.after)
        sensitive_marker: The sensitive marker structure (from resource.change.after_sensitive)
        salt: Cryptographic salt for hashing
        position_seed: Position seed for hash randomization
        path: Current JSON path (for error messages)

    Returns:
        Modified data structure with sensitive values obfuscated

    Raises:
        ValueError: If sensitive_marker structure is malformed
    """
    if path is None:
        path = []

    # If marker is True, obfuscate the entire value
    if sensitive_marker is True:
        return obfuscate_value(data, salt, position_seed)

    # If marker is False or None, return data unchanged
    if sensitive_marker is False or sensitive_marker is None:
        return data

    # If marker is a dict, traverse recursively
    if isinstance(sensitive_marker, dict):
        if not isinstance(data, dict):
            # Mismatch between marker and data structure
            path_str = ".".join(path) if path else "root"
            raise ValueError(
                f"Malformed sensitive_values structure at {path_str}: "
                f"marker is dict but data is {type(data).__name__}"
            )

        # Create new dict with obfuscated values
        result = {}
        for key, value in data.items():
            marker_value = sensitive_marker.get(key, False)

            # Check if marker is a valid type
            if marker_value is not None and not isinstance(
                marker_value, (bool, dict, list)
            ):
                path_str = ".".join(path + [key]) if path else key
                raise ValueError(
                    f"Malformed sensitive_values structure at {path_str}: "
                    f"expected boolean or nested object, got {type(marker_value).__name__}"
                )

            result[key] = traverse_and_obfuscate(
                value, marker_value, salt, position_seed, path + [key]
            )
        return result

    # If marker is a list, traverse recursively
    if isinstance(sensitive_marker, list):
        if not isinstance(data, list):
            path_str = ".".join(path) if path else "root"
            raise ValueError(
                f"Malformed sensitive_values structure at {path_str}: "
                f"marker is list but data is {type(data).__name__}"
            )

        # Lists must be same length
        if len(sensitive_marker) != len(data):
            path_str = ".".join(path) if path else "root"
            raise ValueError(
                f"Malformed sensitive_values structure at {path_str}: "
                f"marker list length ({len(sensitive_marker)}) != data list length ({len(data)})"
            )

        # Create new list with obfuscated values
        result = []
        for i, (item_data, item_marker) in enumerate(zip(data, sensitive_marker)):
            result.append(
                traverse_and_obfuscate(
                    item_data, item_marker, salt, position_seed, path + [f"[{i}]"]
                )
            )
        return result

    # If we get here, marker type is invalid
    path_str = ".".join(path) if path else "root"
    raise ValueError(
        f"Malformed sensitive_values structure at {path_str}: "
        f"marker has invalid type {type(sensitive_marker).__name__}, "
        f"expected boolean, dict, or list"
    )
