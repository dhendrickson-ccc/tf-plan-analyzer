#!/usr/bin/env python3
"""
Unit tests for multi-environment comparison functionality.
"""

import json
import pytest
from pathlib import Path
from src.core.multi_env_comparator import (
    EnvironmentPlan,
    ResourceComparison,
    MultiEnvReport,
)


class TestEnvironmentPlan:
    """Unit tests for EnvironmentPlan class."""

    def test_init(self):
        """Test EnvironmentPlan initialization."""
        plan = EnvironmentPlan(label="dev", plan_file_path=Path("test.json"))
        assert plan.label == "dev"
        assert plan.plan_file_path == Path("test.json")
        assert plan.before_values == {}

    def test_load_plan_with_resources(self):
        """Test loading a plan file with resources."""
        plan = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        plan.load()

        # Check that resources were loaded
        assert len(plan.before_values) > 0
        assert "aws_instance.web" in plan.before_values
        assert "aws_s3_bucket.data" in plan.before_values

    def test_load_extracts_correct_config(self):
        """Test that load() correctly extracts before values."""
        plan = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        plan.load()

        # Verify instance type is extracted correctly
        web_config = plan.before_values.get("aws_instance.web")
        assert web_config is not None
        assert web_config.get("instance_type") == "t2.micro"


class TestResourceComparison:
    """Unit tests for ResourceComparison class."""

    def test_init(self):
        """Test ResourceComparison initialization."""
        rc = ResourceComparison(
            resource_address="aws_instance.web", resource_type="aws_instance"
        )
        assert rc.resource_address == "aws_instance.web"
        assert rc.resource_type == "aws_instance"
        assert rc.env_configs == {}
        assert rc.has_differences == False

    def test_add_environment_config(self):
        """Test adding environment configurations."""
        rc = ResourceComparison(
            resource_address="aws_instance.web", resource_type="aws_instance"
        )

        config1 = {"instance_type": "t2.micro"}
        config2 = {"instance_type": "t2.small"}

        rc.add_environment_config("dev", config1)
        rc.add_environment_config("prod", config2)

        assert rc.env_configs["dev"] == config1
        assert rc.env_configs["prod"] == config2
        assert "dev" in rc.is_present_in
        assert "prod" in rc.is_present_in

    def test_detect_differences_identical_configs(self):
        """Test difference detection with identical configs."""
        rc = ResourceComparison(
            resource_address="aws_instance.web", resource_type="aws_instance"
        )

        config = {"instance_type": "t2.micro", "ami": "ami-123"}
        rc.add_environment_config("dev", config)
        rc.add_environment_config("staging", config)

        rc.detect_differences()

        assert rc.has_differences == False

    def test_detect_differences_different_configs(self):
        """Test difference detection with different configs."""
        rc = ResourceComparison(
            resource_address="aws_instance.web", resource_type="aws_instance"
        )

        config1 = {"instance_type": "t2.micro"}
        config2 = {"instance_type": "t2.small"}

        rc.add_environment_config("dev", config1)
        rc.add_environment_config("prod", config2)

        rc.detect_differences()

        assert rc.has_differences == True

    def test_detect_differences_missing_in_some_envs(self):
        """Test difference detection when resource is missing in some environments."""
        rc = ResourceComparison(
            resource_address="aws_instance.web", resource_type="aws_instance"
        )

        config = {"instance_type": "t2.micro"}
        rc.add_environment_config("dev", config, config)
        rc.add_environment_config("prod", None, None)  # Not present in prod

        rc.detect_differences()

        # Should have differences if resource is missing in some environments
        assert rc.has_differences == True


class TestMultiEnvReport:
    """Unit tests for MultiEnvReport class."""

    def test_init(self):
        """Test MultiEnvReport initialization."""
        env1 = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        env2 = EnvironmentPlan(
            label="staging", plan_file_path=Path("tests/fixtures/staging-plan.json")
        )

        report = MultiEnvReport(environments=[env1, env2])

        assert len(report.environments) == 2
        assert report.resource_comparisons == []
        assert report.summary_stats == {}

    def test_load_environments(self):
        """Test loading all environment plans."""
        env1 = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        env2 = EnvironmentPlan(
            label="staging", plan_file_path=Path("tests/fixtures/staging-plan.json")
        )

        report = MultiEnvReport(environments=[env1, env2])
        report.load_environments()

        # Verify both environments loaded data
        assert len(env1.before_values) > 0
        assert len(env2.before_values) > 0

    def test_build_comparisons(self):
        """Test building resource comparisons."""
        env1 = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        env2 = EnvironmentPlan(
            label="staging", plan_file_path=Path("tests/fixtures/staging-plan.json")
        )

        report = MultiEnvReport(environments=[env1, env2])
        report.load_environments()
        report.build_comparisons()

        # Should have comparisons for all unique resources
        assert len(report.resource_comparisons) > 0

        # Verify resource addresses are captured
        addresses = [rc.resource_address for rc in report.resource_comparisons]
        assert "aws_instance.web" in addresses
        assert "aws_s3_bucket.data" in addresses

    def test_calculate_summary(self):
        """Test summary statistics calculation."""
        env1 = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        env2 = EnvironmentPlan(
            label="staging", plan_file_path=Path("tests/fixtures/staging-plan.json")
        )

        report = MultiEnvReport(environments=[env1, env2])
        report.load_environments()
        report.build_comparisons()
        report.calculate_summary()

        # Verify summary stats
        assert report.summary_stats["total_environments"] == 2
        assert report.summary_stats["total_unique_resources"] >= 2
        assert "resources_with_differences" in report.summary_stats
        assert "resources_consistent" in report.summary_stats

    def test_generate_html(self, tmp_path):
        """Test HTML report generation."""
        env1 = EnvironmentPlan(
            label="dev", plan_file_path=Path("tests/fixtures/dev-plan.json")
        )
        env2 = EnvironmentPlan(
            label="staging", plan_file_path=Path("tests/fixtures/staging-plan.json")
        )

        report = MultiEnvReport(environments=[env1, env2])
        report.load_environments()
        report.build_comparisons()
        report.calculate_summary()

        # Generate HTML to temp file
        output_file = tmp_path / "test_report.html"
        report.generate_html(str(output_file))

        # Verify file was created
        assert output_file.exists()

        # Verify HTML content
        html_content = output_file.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Multi-Environment Terraform Comparison Report" in html_content
        assert "dev" in html_content
        assert "staging" in html_content
