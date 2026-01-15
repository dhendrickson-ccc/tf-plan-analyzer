#!/usr/bin/env python3
"""Test script to verify sensitive value change detection."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.cli.analyze_plan import TerraformPlanAnalyzer


# Create a mock analyzer instance
class MockAnalyzer(TerraformPlanAnalyzer):
    def __init__(self):
        self.show_sensitive = False
        self.ignore_azure_casing = False


analyzer = MockAnalyzer()

# Test case 1: Both values sensitive and different
print("Test 1: Different sensitive values")
before_val = "secret123"
after_val = "secret456"
before_sens = True
after_sens = True

display_before, display_after, changed = analyzer._redact_with_change_detection(
    before_val, after_val, before_sens, after_sens
)
print(f"  Before: {display_before}")
print(f"  After: {display_after}")
print(f"  Changed: {changed}")
print(f"  Expected: Both show '<REDACTED (changed)>', changed=True")
print()

# Test case 2: Both values sensitive and same
print("Test 2: Same sensitive values")
before_val = "secret123"
after_val = "secret123"
before_sens = True
after_sens = True

display_before, display_after, changed = analyzer._redact_with_change_detection(
    before_val, after_val, before_sens, after_sens
)
print(f"  Before: {display_before}")
print(f"  After: {display_after}")
print(f"  Changed: {changed}")
print(f"  Expected: Both show '<REDACTED>', changed=False")
print()

# Test case 3: Sensitive value with HCL reference that changed
print("Test 3: Sensitive HCL references that differ")
before_val = "azurerm_storage_account.old.primary_connection_string"
after_val = "azurerm_storage_account.new.primary_connection_string"
before_sens = True
after_sens = True

display_before, display_after, changed = analyzer._redact_with_change_detection(
    before_val, after_val, before_sens, after_sens
)
print(f"  Before: {display_before}")
print(f"  After: {display_after}")
print(f"  Changed: {changed}")
print(f"  Expected: Both show '<REDACTED (changed)> (resolves to: ...)', changed=True")
print()

# Test case 4: Nested dict with sensitive field that changed
print("Test 4: Nested dict with changed sensitive field")
before_val = {
    "authentication_type": "keyBased",
    "connection_string": "old_secret",
    "container_name": "files",
}
after_val = {
    "authentication_type": "keyBased",
    "connection_string": "new_secret",
    "container_name": "files",
}
before_sens = {"connection_string": True}
after_sens = {"connection_string": True}

display_before, display_after, changed = analyzer._redact_with_change_detection(
    before_val, after_val, before_sens, after_sens
)
print(f"  Before: {display_before}")
print(f"  After: {display_after}")
print(f"  Changed: {changed}")
print(f"  Expected: connection_string shows '<REDACTED (changed)>', changed=True")
print()

# Test case 5: List with sensitive value that changed
print("Test 5: List with changed sensitive value")
before_val = [{"connection_string": "old_secret"}]
after_val = [{"connection_string": "new_secret"}]
before_sens = [{"connection_string": True}]
after_sens = [{"connection_string": True}]

display_before, display_after, changed = analyzer._redact_with_change_detection(
    before_val, after_val, before_sens, after_sens
)
print(f"  Before: {display_before}")
print(f"  After: {display_after}")
print(f"  Changed: {changed}")
print(f"  Expected: connection_string shows '<REDACTED (changed)>', changed=True")
