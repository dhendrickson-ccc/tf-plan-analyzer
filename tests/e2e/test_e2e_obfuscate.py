#!/usr/bin/env python3
"""
End-to-end tests for the obfuscate subcommand.

Tests complete user journeys from CLI invocation to file output,
covering success cases and error scenarios.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "obfuscate"
CLI_SCRIPT = Path(__file__).parent.parent.parent / "src" / "cli" / "analyze_plan.py"


def run_obfuscate(args, env=None):
    """
    Run the obfuscate subcommand and return result.

    Args:
        args: List of command-line arguments (after 'obfuscate')
        env: Optional environment variables dict

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    cmd = [sys.executable, str(CLI_SCRIPT), "obfuscate"] + args

    # Merge environment variables
    test_env = os.environ.copy()
    if env:
        test_env.update(env)

    result = subprocess.run(cmd, capture_output=True, text=True, env=test_env)

    return result.returncode, result.stdout, result.stderr


def test_basic_obfuscation(tmp_path):
    """T025: Test basic obfuscation with simple resource."""
    input_file = TEST_DATA_DIR / "basic.json"
    output_file = tmp_path / "basic-obf.json"

    # Run obfuscation
    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    # Should succeed
    assert returncode == 0, f"Failed with stderr: {stderr}"
    assert output_file.exists(), "Output file not created"
    assert (
        output_file.parent / f"{output_file.name}.salt"
    ).exists(), "Salt file not created"

    # Verify output structure
    with open(output_file) as f:
        obfuscated = json.load(f)

    # Check structure is preserved
    assert "resource_changes" in obfuscated
    assert len(obfuscated["resource_changes"]) == 1

    # Check sensitive value is obfuscated
    resource = obfuscated["resource_changes"][0]
    password = resource["change"]["after"]["password"]
    assert password.startswith("obf_"), f"Password not obfuscated: {password}"
    assert (
        len(password) == 68
    ), f"Invalid hash length: {len(password)}"  # "obf_" + 64 hex chars

    # Check non-sensitive values are preserved
    assert resource["change"]["after"]["username"] == "admin"
    assert resource["change"]["after"]["engine"] == "postgres"


def test_nested_obfuscation(tmp_path):
    """T026: Test obfuscation with deeply nested sensitive values."""
    input_file = TEST_DATA_DIR / "nested.json"
    output_file = tmp_path / "nested-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    assert returncode == 0

    with open(output_file) as f:
        obfuscated = json.load(f)

    # Check nested sensitive values are obfuscated
    config = obfuscated["resource_changes"][0]["change"]["after"]["config"]
    db_creds = config["secrets"]["database"]["credentials"]

    # Check deeply nested password
    assert db_creds["password"].startswith("obf_")

    # Check API keys at 5 levels deep
    assert db_creds["api_keys"]["primary"].startswith("obf_")
    assert db_creds["api_keys"]["secondary"].startswith("obf_")

    # Check connection string
    assert config["secrets"]["database"]["connection_string"].startswith("obf_")

    # Check non-sensitive value preserved
    assert config["tenant_id"] == "abc123"


def test_multiple_resources(tmp_path):
    """T026: Test obfuscation with multiple resources and overlapping values."""
    input_file = TEST_DATA_DIR / "multiple-resources.json"
    output_file = tmp_path / "multiple-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    assert returncode == 0

    with open(output_file) as f:
        obfuscated = json.load(f)

    # Should have 3 resources
    assert len(obfuscated["resource_changes"]) == 3

    # Check that matching passwords produce matching hashes
    db1_password = obfuscated["resource_changes"][0]["change"]["after"]["password"]
    db2_password = obfuscated["resource_changes"][1]["change"]["after"]["password"]

    assert (
        db1_password == db2_password
    ), "Identical passwords should produce identical hashes"
    assert db1_password.startswith("obf_")

    # Check unique value is different
    api_key = obfuscated["resource_changes"][2]["change"]["after"]["secret_value"]
    assert api_key.startswith("obf_")
    assert api_key != db1_password, "Different values should produce different hashes"


def test_empty_sensitive_value(tmp_path):
    """T026: Test obfuscation of empty string marked as sensitive."""
    input_file = TEST_DATA_DIR / "empty-sensitive.json"
    output_file = tmp_path / "empty-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    assert returncode == 0

    with open(output_file) as f:
        obfuscated = json.load(f)

    # Empty string should be obfuscated to a hash
    secret_value = obfuscated["resource_changes"][0]["change"]["after"]["secret_value"]
    assert secret_value.startswith("obf_")
    assert len(secret_value) == 68


def test_null_sensitive_value(tmp_path):
    """T026: Test obfuscation of null value marked as sensitive."""
    input_file = TEST_DATA_DIR / "null-sensitive.json"
    output_file = tmp_path / "null-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    assert returncode == 0

    with open(output_file) as f:
        obfuscated = json.load(f)

    # Null values should be obfuscated to hashes
    after = obfuscated["resource_changes"][0]["change"]["after"]
    assert after["password"].startswith("obf_")
    assert after["connection_string"].startswith("obf_")


def test_no_sensitive_marker(tmp_path):
    """T027: Test resource without after_sensitive marker."""
    input_file = TEST_DATA_DIR / "no-sensitive-marker.json"
    output_file = tmp_path / "no-marker-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    # Should succeed (no sensitive values to obfuscate)
    assert returncode == 0

    with open(input_file) as f:
        original = json.load(f)

    with open(output_file) as f:
        obfuscated = json.load(f)

    # Output should be identical to input
    assert original == obfuscated


def test_invalid_json(tmp_path):
    """T027: Test with invalid JSON file."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text('{"incomplete": ')
    output_file = tmp_path / "output.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(invalid_file), "--output", str(output_file)]
    )

    # Should fail with exit code 2
    assert returncode == 2
    assert "Failed to parse JSON" in stderr
    assert not output_file.exists(), "Output file should not be created on error"


def test_malformed_sensitive_values(tmp_path):
    """T027: Test with malformed after_sensitive structure."""
    input_file = TEST_DATA_DIR / "malformed-sensitive.json"
    output_file = tmp_path / "malformed-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    # Should fail with exit code 7
    assert returncode == 7
    assert "Malformed sensitive_values structure" in stderr
    assert not output_file.exists(), "Output file should not be created on error"


def test_file_not_found():
    """T027: Test with non-existent input file."""
    returncode, stdout, stderr = run_obfuscate(["nonexistent.json"])

    # Should fail with exit code 1
    assert returncode == 1
    assert "Input file not found" in stderr


def test_not_terraform_plan(tmp_path):
    """T027: Test with JSON that's not a Terraform plan."""
    not_plan = tmp_path / "not-plan.json"
    not_plan.write_text('{"some": "data"}')

    returncode, stdout, stderr = run_obfuscate([str(not_plan)])

    # Should fail with exit code 3
    assert returncode == 3
    assert "not a valid Terraform plan" in stderr
    assert "resource_changes" in stderr


def test_output_file_exists(tmp_path):
    """T027: Test error when output file already exists without --force."""
    input_file = TEST_DATA_DIR / "basic.json"
    output_file = tmp_path / "exists.json"

    # Create existing output file
    output_file.write_text('{"existing": "data"}')

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file)]
    )

    # Should fail with exit code 4
    assert returncode == 4
    assert "Output file already exists" in stderr
    assert "--force" in stderr


def test_force_overwrite(tmp_path):
    """T027: Test --force flag allows overwriting existing file."""
    input_file = TEST_DATA_DIR / "basic.json"
    output_file = tmp_path / "exists.json"

    # Create existing output file
    output_file.write_text('{"existing": "data"}')

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file), "--force"]
    )

    # Should succeed
    assert returncode == 0

    # Verify file was overwritten
    with open(output_file) as f:
        obfuscated = json.load(f)

    assert "resource_changes" in obfuscated
    assert obfuscated != {"existing": "data"}


def test_show_stats_flag(tmp_path):
    """Test --show-stats flag displays statistics."""
    input_file = TEST_DATA_DIR / "multiple-resources.json"
    output_file = tmp_path / "stats-obf.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(input_file), "--output", str(output_file), "--show-stats"]
    )

    assert returncode == 0
    assert "Statistics:" in stdout
    assert "Resources processed:" in stdout
    assert "Values obfuscated:" in stdout
    assert "Execution time:" in stdout


def test_error_behavior(tmp_path):
    """T027b: Test FR-018/019 - error messages to stderr and no output on error."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not json at all")
    output_file = tmp_path / "should-not-exist.json"

    returncode, stdout, stderr = run_obfuscate(
        [str(invalid_file), "--output", str(output_file)]
    )

    # FR-018: Detailed error messages to stderr
    assert returncode != 0
    assert len(stderr) > 0, "Error messages should be written to stderr"
    assert "Error:" in stderr or "error" in stderr.lower()

    # FR-019: No output file created on any error
    assert (
        not output_file.exists()
    ), "Output file should not be created when errors occur"
    assert not (
        output_file.parent / f"{output_file.name}.salt"
    ).exists(), "Salt file should not be created on error"


# ==================== USER STORY 2: DETERMINISTIC OBFUSCATION ====================


def test_deterministic_same_file(tmp_path):
    """T032: Test that obfuscating same file twice with same salt produces identical output."""
    input_file = TEST_DATA_DIR / "basic.json"
    output1 = tmp_path / "obf1.json"
    output2 = tmp_path / "obf2.json"
    salt_file = tmp_path / "test.salt"

    # First obfuscation (generate salt)
    returncode1, stdout1, stderr1 = run_obfuscate(
        [str(input_file), "--output", str(output1)]
    )
    assert returncode1 == 0

    # Move salt file to known location
    generated_salt = output1.parent / f"{output1.name}.salt"
    generated_salt.rename(salt_file)

    # Second obfuscation (reuse salt)
    returncode2, stdout2, stderr2 = run_obfuscate(
        [str(input_file), "--output", str(output2), "--salt-file", str(salt_file)]
    )
    assert returncode2 == 0

    # Read both outputs
    with open(output1) as f:
        data1 = json.load(f)
    with open(output2) as f:
        data2 = json.load(f)

    # SC-002: Outputs must be byte-identical
    assert data1 == data2, "Same file with same salt should produce identical output"

    # Verify the obfuscated values are the same
    password1 = data1["resource_changes"][0]["change"]["after"]["password"]
    password2 = data2["resource_changes"][0]["change"]["after"]["password"]
    assert password1 == password2
    assert password1.startswith("obf_")


def test_deterministic_cross_file(tmp_path):
    """T033: Test that same sensitive value produces same hash across different files."""
    # Create two different plan files with the same password value
    plan1 = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.db1",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"id": "db1", "password": "shared-secret-password"},
                    "after_sensitive": {"password": True},
                },
            }
        ],
    }

    plan2 = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.db2",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "id": "db2",
                        "region": "us-west-2",
                        "password": "shared-secret-password",
                    },
                    "after_sensitive": {"password": True},
                },
            }
        ],
    }

    input1 = tmp_path / "plan1.json"
    input2 = tmp_path / "plan2.json"
    output1 = tmp_path / "obf1.json"
    output2 = tmp_path / "obf2.json"

    input1.write_text(json.dumps(plan1))
    input2.write_text(json.dumps(plan2))

    # Obfuscate both with same salt
    run_obfuscate([str(input1), "--output", str(output1)])
    salt_file = output1.parent / f"{output1.name}.salt"

    run_obfuscate(
        [str(input2), "--output", str(output2), "--salt-file", str(salt_file)]
    )

    # Read outputs
    with open(output1) as f:
        data1 = json.load(f)
    with open(output2) as f:
        data2 = json.load(f)

    # SC-003: Same sensitive value should produce same hash
    password1 = data1["resource_changes"][0]["change"]["after"]["password"]
    password2 = data2["resource_changes"][0]["change"]["after"]["password"]

    assert (
        password1 == password2
    ), "Identical sensitive values should produce identical hashes with same salt"
    assert password1.startswith("obf_")


def test_drift_detection(tmp_path):
    """T034: Test that differences are visible as different hashes."""
    # Create two plans: one with matching password, one with different
    plan_dev = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "password": "dev-password-123",
                        "api_key": "shared-api-key",
                    },
                    "after_sensitive": {"password": True, "api_key": True},
                },
            }
        ],
    }

    plan_prod = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "password": "prod-password-456",  # Different
                        "api_key": "shared-api-key",  # Same
                    },
                    "after_sensitive": {"password": True, "api_key": True},
                },
            }
        ],
    }

    input_dev = tmp_path / "dev.json"
    input_prod = tmp_path / "prod.json"
    output_dev = tmp_path / "dev-obf.json"
    output_prod = tmp_path / "prod-obf.json"

    input_dev.write_text(json.dumps(plan_dev))
    input_prod.write_text(json.dumps(plan_prod))

    # Obfuscate both with same salt
    run_obfuscate([str(input_dev), "--output", str(output_dev)])
    salt_file = output_dev.parent / f"{output_dev.name}.salt"

    run_obfuscate(
        [str(input_prod), "--output", str(output_prod), "--salt-file", str(salt_file)]
    )

    # Read outputs
    with open(output_dev) as f:
        data_dev = json.load(f)
    with open(output_prod) as f:
        data_prod = json.load(f)

    # SC-004: Differences should be visible
    dev_after = data_dev["resource_changes"][0]["change"]["after"]
    prod_after = data_prod["resource_changes"][0]["change"]["after"]

    # Different passwords should have different hashes
    assert (
        dev_after["password"] != prod_after["password"]
    ), "Different values should produce different hashes"

    # Same API key should have same hash
    assert (
        dev_after["api_key"] == prod_after["api_key"]
    ), "Identical values should produce identical hashes"

    # Both should be obfuscated
    assert dev_after["password"].startswith("obf_")
    assert prod_after["password"].startswith("obf_")
    assert dev_after["api_key"].startswith("obf_")


# ==================== USER STORY 3: SALT MANAGEMENT ====================


def test_salt_reuse(tmp_path):
    """T043: Test reusing salt file across multiple obfuscations."""
    plan1 = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.db1",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"password": "secret123"},
                    "after_sensitive": {"password": True},
                },
            }
        ],
    }

    plan2 = {
        "format_version": "1.0",
        "terraform_version": "1.0.0",
        "resource_changes": [
            {
                "address": "aws_db_instance.db2",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"password": "secret123", "region": "us-east-1"},
                    "after_sensitive": {"password": True},
                },
            }
        ],
    }

    input1 = tmp_path / "file1.json"
    input2 = tmp_path / "file2.json"
    output1 = tmp_path / "obf1.json"
    output2 = tmp_path / "obf2.json"

    input1.write_text(json.dumps(plan1))
    input2.write_text(json.dumps(plan2))

    # Obfuscate file1 (generates salt)
    run_obfuscate([str(input1), "--output", str(output1)])
    salt_file = output1.parent / f"{output1.name}.salt"
    assert salt_file.exists()

    # Obfuscate file2 with same salt
    returncode, stdout, stderr = run_obfuscate(
        [str(input2), "--output", str(output2), "--salt-file", str(salt_file)]
    )

    assert returncode == 0
    # Should NOT create a new salt file when --salt-file is provided
    salt_file2 = output2.parent / f"{output2.name}.salt"
    assert (
        not salt_file2.exists()
    ), "Should not create new salt file when reusing existing one"

    # Verify matching passwords produce matching hashes
    with open(output1) as f:
        data1 = json.load(f)
    with open(output2) as f:
        data2 = json.load(f)

    password1 = data1["resource_changes"][0]["change"]["after"]["password"]
    password2 = data2["resource_changes"][0]["change"]["after"]["password"]

    assert (
        password1 == password2
    ), "Same password with same salt should produce same hash"


def test_different_salts(tmp_path):
    """T044: Test that different salts produce different outputs."""
    input_file = TEST_DATA_DIR / "basic.json"
    output1 = tmp_path / "obf1.json"
    output2 = tmp_path / "obf2.json"

    # First obfuscation
    run_obfuscate([str(input_file), "--output", str(output1)])

    # Second obfuscation (different salt)
    run_obfuscate([str(input_file), "--output", str(output2)])

    # Read outputs
    with open(output1) as f:
        data1 = json.load(f)
    with open(output2) as f:
        data2 = json.load(f)

    # Passwords should be different (different salts)
    password1 = data1["resource_changes"][0]["change"]["after"]["password"]
    password2 = data2["resource_changes"][0]["change"]["after"]["password"]

    assert password1 != password2, "Different salts should produce different hashes"
    assert password1.startswith("obf_")
    assert password2.startswith("obf_")


def test_salt_file_not_found(tmp_path):
    """T045: Test exit code 5 when salt file doesn't exist."""
    input_file = TEST_DATA_DIR / "basic.json"
    output_file = tmp_path / "obf.json"
    missing_salt = tmp_path / "missing.salt"

    returncode, stdout, stderr = run_obfuscate(
        [
            str(input_file),
            "--output",
            str(output_file),
            "--salt-file",
            str(missing_salt),
        ]
    )

    # Should fail with exit code 5
    assert returncode == 5
    assert "Salt file not found" in stderr


def test_corrupted_salt_file(tmp_path):
    """T046: Test exit code 6 for corrupted salt file."""
    input_file = TEST_DATA_DIR / "basic.json"
    output_file = tmp_path / "obf.json"
    corrupt_salt = tmp_path / "corrupt.salt"

    # Create corrupted salt file
    corrupt_salt.write_bytes(b"not a valid salt file format")

    returncode, stdout, stderr = run_obfuscate(
        [
            str(input_file),
            "--output",
            str(output_file),
            "--salt-file",
            str(corrupt_salt),
        ]
    )

    # Should fail with exit code 6
    assert returncode == 6
    assert (
        "Failed to" in stderr and "salt" in stderr.lower()
    ) or "decrypt" in stderr.lower()


def test_environment_variable_encryption(tmp_path):
    """T047: Test TF_ANALYZER_SALT_KEY enables salt decryption across different sessions."""
    input_file = TEST_DATA_DIR / "basic.json"
    output1 = tmp_path / "obf1.json"
    output2 = tmp_path / "obf2.json"

    # First run: Generate salt with explicit key (valid Fernet key)
    test_key = "FKNSRhmPlGYip9-IzC4TT5q82A5C-TKjRNlKmXkP5Rc="
    env1 = {"TF_ANALYZER_SALT_KEY": test_key}

    returncode1, stdout1, stderr1 = run_obfuscate(
        [str(input_file), "--output", str(output1)], env=env1
    )

    assert returncode1 == 0
    assert "WARNING: TF_ANALYZER_SALT_KEY environment variable not set!" not in stderr1

    salt_file = output1.parent / f"{output1.name}.salt"
    assert salt_file.exists()

    # Second run: Reuse salt with same key (simulating different CI node)
    env2 = {"TF_ANALYZER_SALT_KEY": test_key}

    returncode2, stdout2, stderr2 = run_obfuscate(
        [str(input_file), "--output", str(output2), "--salt-file", str(salt_file)],
        env=env2,
    )

    assert returncode2 == 0

    # Verify outputs are identical
    with open(output1) as f:
        data1 = json.load(f)
    with open(output2) as f:
        data2 = json.load(f)

    assert (
        data1 == data2
    ), "Same key should enable decryption and produce identical output"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
