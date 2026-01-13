#!/usr/bin/env python3
"""Test script to verify HCL reference detection."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from analyze_plan import TerraformPlanAnalyzer

# Create a mock analyzer instance
class MockAnalyzer(TerraformPlanAnalyzer):
    def __init__(self):
        self.show_sensitive = False
        self.ignore_azure_casing = False

analyzer = MockAnalyzer()

# Test cases
test_cases = [
    ("${var.foo}", True, "Variable interpolation"),
    ("azurerm_storage_account.account[\"instfiles\"].primary_blob_connection_string", True, "Direct Azure reference with array index"),
    ("azurerm_storage_account.old.primary_connection_string", True, "Direct Azure reference"),
    ("aws_s3_bucket.mybucket.arn", True, "Direct AWS reference"),
    ("google_storage_bucket.bucket.url", True, "Direct Google reference"),
    ("data.azurerm_storage_account.existing.id", True, "Data source reference"),
    ("var.environment", True, "Variable reference"),
    ("local.connection_string", True, "Local value reference"),
    ("module.storage.connection_string", True, "Module output reference"),
    ("just a regular string", False, "Regular string"),
    ("secret123", False, "Secret value"),
    ("DefaultEndpointsProtocol=https;...", False, "Connection string"),
    (123, False, "Number"),
    (None, False, "None value"),
]

print("Testing HCL reference detection:\n")
all_passed = True

for value, expected, description in test_cases:
    result = analyzer._is_hcl_reference(value)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"{status} {description}")
    print(f"   Value: {repr(value)}")
    print(f"   Expected: {expected}, Got: {result}")
    print()

if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed!")
    sys.exit(1)
