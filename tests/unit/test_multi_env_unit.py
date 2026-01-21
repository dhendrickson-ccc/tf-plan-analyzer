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


class TestIgnoreCounts:
    """Unit tests for US3 - Combined Normalization Ignore Tracking."""

    def test_calculate_ignore_counts_both_types(self):
        """Test calculating separate counts for config and normalization ignores."""
        from src.core.multi_env_comparator import _calculate_ignore_counts, AttributeDiff
        
        # Create attribute diffs with mixed ignore types
        attr_diffs = [
            AttributeDiff("name", {"env1": "value1"}, True, "string"),  # Different, not ignored
            AttributeDiff("tags", {"env1": "value1"}, False, "object"),  # Not different
        ]
        
        # Manually set up ignored attributes
        # Simulating 2 config-ignored, 3 normalization-ignored
        config_ignored = {"timeout", "user_data"}
        
        # Add normalization-ignored attributes
        norm_diff1 = AttributeDiff("subscription_id", {"env1": "abc", "env2": "xyz"}, True, "string")
        norm_diff1.ignored_due_to_normalization = True
        norm_diff2 = AttributeDiff("tenant_id", {"env1": "123", "env2": "456"}, True, "string")
        norm_diff2.ignored_due_to_normalization = True
        norm_diff3 = AttributeDiff("resource_group_id", {"env1": "rg1", "env2": "rg2"}, True, "string")
        norm_diff3.ignored_due_to_normalization = True
        
        attr_diffs.extend([norm_diff1, norm_diff2, norm_diff3])
        
        config_count, norm_count = _calculate_ignore_counts(config_ignored, attr_diffs)
        
        assert config_count == 2, "Should count 2 config-ignored attributes"
        assert norm_count == 3, "Should count 3 normalization-ignored attributes"

    def test_calculate_ignore_counts_only_normalization(self):
        """Test calculating counts with only normalization ignores."""
        from src.core.multi_env_comparator import _calculate_ignore_counts, AttributeDiff
        
        attr_diffs = []
        norm_diff1 = AttributeDiff("subscription_id", {"env1": "abc"}, True, "string")
        norm_diff1.ignored_due_to_normalization = True
        attr_diffs.append(norm_diff1)
        
        config_ignored = set()  # No config ignores
        
        config_count, norm_count = _calculate_ignore_counts(config_ignored, attr_diffs)
        
        assert config_count == 0, "Should have no config ignores"
        assert norm_count == 1, "Should count 1 normalization ignore"

    def test_render_ignore_badge_both_types(self):
        """Test badge rendering with both ignore types."""
        from src.core.multi_env_comparator import _render_ignore_badge
        
        config_ignored = {"tags", "timeout"}
        normalized_attrs = ["subscription_id", "tenant_id"]
        
        badge_html = _render_ignore_badge(2, 2, config_ignored, normalized_attrs)
        
        assert "4 attributes ignored" in badge_html, "Should show total count"
        assert "2 config" in badge_html, "Should show config count"
        assert "2 normalized" in badge_html, "Should show normalized count"
        assert "tags" in badge_html, "Should list config-ignored attributes in tooltip"
        assert "subscription_id" in badge_html, "Should list normalized attributes in tooltip"

    def test_render_ignore_badge_only_normalization(self):
        """Test badge rendering with only normalization ignores."""
        from src.core.multi_env_comparator import _render_ignore_badge
        
        config_ignored = set()
        normalized_attrs = ["subscription_id", "tenant_id"]
        
        badge_html = _render_ignore_badge(0, 2, config_ignored, normalized_attrs)
        
        assert "2 attributes ignored" in badge_html or "2 normalized" in badge_html, "Should show normalized count"
        assert "subscription_id" in badge_html, "Should list normalized attributes"
        assert "tenant_id" in badge_html, "Should list normalized attributes"
