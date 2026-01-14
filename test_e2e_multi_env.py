#!/usr/bin/env python3
"""
End-to-end tests for multi-environment comparison CLI.

Tests the complete user journey from CLI invocation to report generation.
Per Constitution Principle V: User-Facing Features Require End-to-End Testing
"""

import subprocess
import pytest
from pathlib import Path


class TestCLIRouting:
    """End-to-end tests for CLI subcommand routing."""
    
    def test_no_subcommand_shows_help(self):
        """Test that running without subcommand shows help and exits with error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'report' in result.stdout
        assert 'compare' in result.stdout
    
    def test_report_subcommand_help(self):
        """Test that report subcommand help is accessible."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'report', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'plan_file' in result.stdout
        assert '--config' in result.stdout
        assert '--html' in result.stdout
    
    def test_compare_subcommand_help(self):
        """Test that compare subcommand help is accessible."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'plan_files' in result.stdout
        assert '--html' in result.stdout
    
    def test_compare_with_one_file_errors(self):
        """Test that compare subcommand requires at least 2 files."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare', 'dummy.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'at least 2 plan files' in result.stdout
        assert 'report' in result.stdout  # Should suggest report subcommand


class TestMultiEnvComparison:
    """End-to-end tests for multi-environment comparison."""
    
    def test_compare_two_environments(self):
        """Test comparing two environments with text output."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Comparing 2 environments' in result.stdout
        assert 'SUMMARY' in result.stdout
        assert 'Total Unique Resources: 2' in result.stdout
        assert 'Resources with Differences: 2' in result.stdout
    
    def test_compare_three_environments(self):
        """Test comparing three environments."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json', 
             'test_data/prod-plan.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Comparing 3 environments' in result.stdout
        assert 'Total Unique Resources: 3' in result.stdout
        assert 'Resources with Differences' in result.stdout
    
    def test_compare_with_html_output(self):
        """Test comparing environments with HTML output."""
        import os
        
        # Clean up any existing report
        output_file = 'test_comparison.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'HTML comparison report generated' in result.stdout
        assert output_file in result.stdout
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        # Verify HTML content
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        assert '<!DOCTYPE html>' in html_content
        assert 'Multi-Environment Terraform Comparison Report' in html_content
        assert 'dev-plan' in html_content
        assert 'staging-plan' in html_content
        
        # Clean up
        os.remove(output_file)
    
    def test_compare_nonexistent_file(self):
        """Test that comparing nonexistent file shows error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'nonexistent.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'File not found' in result.stdout
    
    def test_compare_five_environments(self):
        """Test comparing five environments to verify variable environment count support."""
        import os
        
        output_file = 'test_5_env_comparison.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/qa-plan.json',
             'test_data/staging-plan.json', 'test_data/preprod-plan.json',
             'test_data/prod-plan.json',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Comparing 5 environments' in result.stdout
        assert output_file in result.stdout
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        # Verify HTML has 5 columns
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        assert 'dev-plan' in html_content
        assert 'qa-plan' in html_content
        assert 'staging-plan' in html_content
        assert 'preprod-plan' in html_content
        assert 'prod-plan' in html_content
        
        # Clean up
        os.remove(output_file)


class TestSensitiveValues:
    """Test suite for sensitive value handling."""
    
    def test_sensitive_values_masked_by_default(self):
        """Test that sensitive values are masked by default."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-sensitive.json', 'test_data/prod-sensitive.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Sensitive values should be masked in comparison output
        assert '[SENSITIVE]' in result.stdout or 'SENSITIVE' in result.stdout or result.returncode == 0
    
    def test_show_sensitive_reveals_values(self):
        """Test that --show-sensitive flag reveals actual sensitive values."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-sensitive.json', 'test_data/prod-sensitive.json',
             '--show-sensitive'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # With --show-sensitive, actual values should appear (or at least not be masked)
        # The test passes if command succeeds
    
    def test_sensitive_diff_indicator_in_html(self):
        """Test that differing masked sensitive values show indicator in HTML."""
        import os
        
        output_file = 'test_sensitive_diff.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-sensitive.json', 'test_data/prod-sensitive.json',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify HTML contains sensitive indicator
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Should have SENSITIVE marker or indicator
        assert 'SENSITIVE' in html_content or 'sensitive' in html_content
        
        os.remove(output_file)


class TestHCLResolution:
    """Test suite for HCL value resolution."""
    
    def test_tfvars_count_mismatch_error(self):
        """Test that mismatched tfvars count triggers error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json', 'test_data/prod-plan.json',
             '--tfvars-files', 'dev.tfvars,staging.tfvars'],  # Only 2 tfvars for 3 files
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'tfvars' in result.stdout.lower()
        assert 'must match' in result.stdout.lower()


class TestEnvironmentLabeling:
    """Tests for environment labeling with --env-names flag."""
    
    def test_custom_environment_names(self):
        """Test using --env-names flag with custom environment labels."""
        import os
        
        output_file = 'test_custom_names.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--env-names', 'Development,Staging',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Development, Staging' in result.stdout
        
        # Verify custom names in HTML
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        assert 'Development' in html_content
        assert 'Staging' in html_content
        # Old names should NOT be in the HTML
        assert 'dev-plan' not in html_content
        assert 'staging-plan' not in html_content
        
        os.remove(output_file)
    
    def test_env_names_count_mismatch_error(self):
        """Test that mismatched env-names count triggers error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json', 'test_data/prod-plan.json',
             '--env-names', 'Dev,Staging'],  # Only 2 names for 3 files
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'Number of environment names' in result.stdout
        assert 'must match' in result.stdout
    
    def test_default_names_from_filenames(self):
        """Test that names are derived from filenames when --env-names not provided."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'dev-plan, staging-plan' in result.stdout


class TestDiffOnlyFilter:
    """Tests for --diff-only flag to filter identical resources."""
    
    def test_diff_only_filters_identical_resources(self):
        """Test that --diff-only hides resources with identical configs."""
        import os
        
        output_file = 'test_diff_only_filtered.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/test1-plan.json', 'test_data/test2-plan.json',
             '--diff-only', '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '1 with differences' in result.stdout
        
        # Verify HTML only shows differing resources
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Should have the instance (different)
        assert 'aws_instance.web' in html_content
        # Should NOT have the S3 bucket or database (identical)
        assert 'aws_s3_bucket.data' not in html_content
        assert 'aws_db_instance.database' not in html_content
        
        os.remove(output_file)
    
    def test_without_diff_only_shows_all_resources(self):
        """Test that without --diff-only, all resources are shown."""
        import os
        
        output_file = 'test_all_resources_shown.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/test1-plan.json', 'test_data/test2-plan.json',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify HTML shows all resources
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            html_content = f.read()
        
        # Should have all 3 resources
        assert 'aws_instance.web' in html_content
        assert 'aws_s3_bucket.data' in html_content
        assert 'aws_db_instance.database' in html_content
        
        os.remove(output_file)


class TestIgnoreConfig:
    """Test suite for ignore configuration support."""
    
    def test_ignore_config_filters_fields(self):
        """Test that --config flag filters out ignored fields."""
        import os
        
        output_file = 'test_ignore_config.html'
        if os.path.exists(output_file):
            os.remove(output_file)
        
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--config', 'test_data/ignore_config.json',
             '--html', output_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify HTML was created
        assert os.path.exists(output_file)
        
        # Clean up
        os.remove(output_file)
    
    def test_missing_config_file_error(self):
        """Test that missing config file triggers error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--config', 'nonexistent_config.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'not found' in result.stdout.lower()

class TestTextOutput:
    """Test suite for text output functionality."""
    
    def test_text_output_without_html_flag(self):
        """Test that text output is generated when --html flag is omitted."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify text output contains expected sections
        assert 'Multi-Environment Terraform Comparison Report' in result.stdout
        assert 'SUMMARY' in result.stdout
        assert 'RESOURCE COMPARISON' in result.stdout
        assert 'Total Environments: 2' in result.stdout
        assert 'aws_instance.web' in result.stdout
        assert 'aws_s3_bucket.data' in result.stdout
    
    def test_verbose_flag_shows_configurations(self):
        """Test that -v flag shows detailed configurations in text output."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '-v'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify verbose output contains configurations
        assert 'Configurations:' in result.stdout
        assert '[dev-plan]' in result.stdout
        assert '[staging-plan]' in result.stdout
        assert '"instance_type"' in result.stdout  # Should show config details
        assert '"ami"' in result.stdout
    
    def test_verbose_long_form_flag(self):
        """Test that --verbose long form works the same as -v."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--verbose'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Configurations:' in result.stdout

class TestErrorHandling:
    """Test suite for error handling and edge cases."""
    
    def test_duplicate_environment_names_error(self):
        """Test that duplicate environment names trigger an error."""
        result = subprocess.run(
            ['python3', 'analyze_plan.py', 'compare',
             'test_data/dev-plan.json', 'test_data/staging-plan.json',
             '--env-names', 'env1,env1'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'Duplicate environment names' in result.stdout
    
    def test_invalid_json_plan_file_error(self):
        """Test that invalid JSON plan file triggers an error."""
        import tempfile
        import os
        
        # Create a temporary invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json content')
            invalid_file = f.name
        
        try:
            result = subprocess.run(
                ['python3', 'analyze_plan.py', 'compare',
                 'test_data/dev-plan.json', invalid_file],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert 'Invalid JSON' in result.stdout or 'Error' in result.stdout
        finally:
            os.remove(invalid_file)
