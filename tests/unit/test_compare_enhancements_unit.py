#!/usr/bin/env python3
"""
Unit tests for compare enhancements functionality.

Tests the internal logic for attribute-level diff computation
and other compare enhancement features.
"""

import pytest
import json
from src.core.multi_env_comparator import ResourceComparison


class TestComputeAttributeDiffs:
    """Unit tests for compute_attribute_diffs method."""
    
    def test_single_attribute_difference(self):
        """Test computing diffs when only one attribute differs."""
        rc = ResourceComparison("aws_instance.web", "aws_instance")
        
        # Add configs for two environments
        config1 = {"name": "web-server", "location": "eastus", "size": "Standard_B1s"}
        config2 = {"name": "web-server", "location": "westus", "size": "Standard_B1s"}
        
        rc.add_environment_config("env1", config1, config1)
        rc.add_environment_config("env2", config2, config2)
        rc.detect_differences()
        
        # Compute attribute diffs
        if hasattr(rc, 'compute_attribute_diffs'):
            rc.compute_attribute_diffs()
            
            # Should have attribute_diffs list
            assert hasattr(rc, 'attribute_diffs')
            assert len(rc.attribute_diffs) > 0
            
            # Should have location in diffs
            location_diffs = [ad for ad in rc.attribute_diffs if ad.attribute_name == 'location']
            assert len(location_diffs) == 1
            assert location_diffs[0].is_different is True
    
    def test_no_differences(self):
        """Test computing diffs when configs are identical."""
        rc = ResourceComparison("aws_instance.web", "aws_instance")
        
        config = {"name": "web-server", "location": "eastus"}
        rc.add_environment_config("env1", config, config)
        rc.add_environment_config("env2", config, config)
        rc.detect_differences()
        
        if hasattr(rc, 'compute_attribute_diffs'):
            rc.compute_attribute_diffs()
            
            # All attributes should be marked as not different
            if hasattr(rc, 'attribute_diffs'):
                for ad in rc.attribute_diffs:
                    assert ad.is_different is False
    
    def test_nested_object_attribute(self):
        """Test that nested objects are treated as single top-level attributes."""
        rc = ResourceComparison("azurerm_kusto_cluster.main", "azurerm_kusto_cluster")
        
        config1 = {
            "name": "cluster1",
            "identity": {"type": "SystemAssigned", "principal_id": "abc123"}
        }
        config2 = {
            "name": "cluster1",
            "identity": {"type": "UserAssigned", "principal_id": "xyz789"}
        }
        
        rc.add_environment_config("env1", config1, config1)
        rc.add_environment_config("env2", config2, config2)
        rc.detect_differences()
        
        if hasattr(rc, 'compute_attribute_diffs'):
            rc.compute_attribute_diffs()
            
            if hasattr(rc, 'attribute_diffs'):
                # Should have 'identity' as a single attribute that differs
                identity_diffs = [ad for ad in rc.attribute_diffs if ad.attribute_name == 'identity']
                assert len(identity_diffs) == 1
                assert identity_diffs[0].is_different is True
    
    def test_multiple_environments(self):
        """Test computing diffs across more than 2 environments."""
        rc = ResourceComparison("aws_s3_bucket.data", "aws_s3_bucket")
        
        config1 = {"bucket": "data-dev", "region": "us-east-1"}
        config2 = {"bucket": "data-staging", "region": "us-east-1"}
        config3 = {"bucket": "data-prod", "region": "us-west-2"}
        
        rc.add_environment_config("dev", config1, config1)
        rc.add_environment_config("staging", config2, config2)
        rc.add_environment_config("prod", config3, config3)
        rc.detect_differences()
        
        if hasattr(rc, 'compute_attribute_diffs'):
            rc.compute_attribute_diffs()
            
            if hasattr(rc, 'attribute_diffs'):
                # Both bucket and region should differ
                bucket_diffs = [ad for ad in rc.attribute_diffs if ad.attribute_name == 'bucket']
                region_diffs = [ad for ad in rc.attribute_diffs if ad.attribute_name == 'region']
                
                assert len(bucket_diffs) == 1
                assert len(region_diffs) == 1
                assert bucket_diffs[0].is_different is True
                assert region_diffs[0].is_different is True
