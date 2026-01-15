#!/usr/bin/env python3
"""End-to-end test for sensitive value change detection with HCL references."""

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

print("=" * 80)
print(
    "Test: IoT Hub file_upload.connection_string changing to different storage account"
)
print("=" * 80)
print()

# Simulate the before state (old storage account)
before_val = {
    "authentication_type": "keyBased",
    "connection_string": 'azurerm_storage_account.account["oldfiles"].primary_blob_connection_string',
    "container_name": "inst-files",
}

# Simulate the after state (new storage account)
after_val = {
    "authentication_type": "keyBased",
    "connection_string": 'azurerm_storage_account.account["instfiles"].primary_blob_connection_string',
    "container_name": "inst-files",
}

# Sensitivity map shows connection_string is sensitive
before_sens = [{"connection_string": True}]
after_sens = [{"connection_string": True}]

# Wrap in list as file_upload is a list in the Terraform schema
before_wrapped = [before_val]
after_wrapped = [after_val]

# Test the redaction with change detection
display_before, display_after, values_changed = analyzer._redact_with_change_detection(
    before_wrapped, after_wrapped, before_sens, after_sens
)

print("BEFORE:")
print(f"  {display_before}")
print()
print("AFTER:")
print(f"  {display_after}")
print()
print(f"VALUES CHANGED: {values_changed}")
print()

# Verify the results
print("=" * 80)
print("Verification:")
print("=" * 80)

checks = []

# Check 1: connection_string in before should show <REDACTED (changed)> with HCL reference
before_conn_str = display_before[0]["connection_string"]
has_redacted_changed = "<REDACTED (changed)>" in before_conn_str
has_before_hcl = "oldfiles" in before_conn_str
checks.append(
    (
        "Before shows '<REDACTED (changed)>' with HCL reference",
        has_redacted_changed and has_before_hcl,
        before_conn_str,
    )
)

# Check 2: connection_string in after should show <REDACTED (changed)> with HCL reference
after_conn_str = display_after[0]["connection_string"]
has_redacted_changed = "<REDACTED (changed)>" in after_conn_str
has_after_hcl = "instfiles" in after_conn_str
checks.append(
    (
        "After shows '<REDACTED (changed)>' with HCL reference",
        has_redacted_changed and has_after_hcl,
        after_conn_str,
    )
)

# Check 3: values_changed should be True
checks.append(
    ("values_changed flag is True", values_changed == True, str(values_changed))
)

# Check 4: Non-sensitive fields should not be redacted
checks.append(
    (
        "container_name not redacted",
        display_before[0]["container_name"] == "inst-files",
        display_before[0]["container_name"],
    )
)

# Print results
all_passed = True
for check_name, passed, actual_value in checks:
    status = "✅" if passed else "❌"
    if not passed:
        all_passed = False
    print(f"{status} {check_name}")
    print(f"   Value: {actual_value}")
    print()

if all_passed:
    print("=" * 80)
    print("✅ ALL CHECKS PASSED! Feature is working correctly.")
    print("=" * 80)
    print()
    print("Summary:")
    print("- Sensitive values that change show '<REDACTED (changed)>'")
    print("- HCL references (including direct references) are displayed")
    print("- values_changed flag accurately detects changes")
    print("- Non-sensitive fields remain visible")
else:
    print("=" * 80)
    print("❌ SOME CHECKS FAILED!")
    print("=" * 80)
    sys.exit(1)
