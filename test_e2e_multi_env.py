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
        assert 'COMPARISON SUMMARY' in result.stdout
        assert 'Total unique resources: 2' in result.stdout
        assert 'Resources with differences: 2' in result.stdout
    
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
        assert 'Total unique resources: 3' in result.stdout
        assert 'Resources with differences' in result.stdout
    
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

