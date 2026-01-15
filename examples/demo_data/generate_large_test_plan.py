#!/usr/bin/env python3
"""Generate a large Terraform plan JSON for performance testing."""

import json
import sys

def generate_large_plan(num_resources=1000):
    """Generate a Terraform plan with the specified number of resources."""
    resource_changes = []
    
    for i in range(num_resources):
        resource = {
            "address": f"aws_db_instance.database_{i}",
            "mode": "managed",
            "type": "aws_db_instance",
            "name": f"database_{i}",
            "provider_name": "registry.terraform.io/hashicorp/aws",
            "change": {
                "actions": ["create"],
                "before": None,
                "after": {
                    "allocated_storage": 20,
                    "auto_minor_version_upgrade": True,
                    "backup_retention_period": 7,
                    "db_name": f"mydb_{i}",
                    "engine": "postgres",
                    "engine_version": "13.7",
                    "identifier": f"prod-db-{i}",
                    "instance_class": "db.t3.micro",
                    "username": f"admin_{i}",
                    "password": f"SecurePassword{i}!@#",
                    "multi_az": False,
                    "publicly_accessible": False,
                    "storage_encrypted": True,
                    "storage_type": "gp2",
                    "tags": {
                        "Environment": "production",
                        "Terraform": "true",
                        "Index": str(i)
                    },
                    "vpc_security_group_ids": [
                        f"sg-{i:08x}"
                    ]
                },
                "after_unknown": {
                    "arn": True,
                    "endpoint": True,
                    "id": True
                },
                "before_sensitive": False,
                "after_sensitive": {
                    "password": True,
                    "tags": {},
                    "vpc_security_group_ids": [False]
                }
            }
        }
        resource_changes.append(resource)
    
    plan = {
        "format_version": "1.0",
        "terraform_version": "1.3.0",
        "planned_values": {
            "root_module": {
                "resources": []
            }
        },
        "resource_changes": resource_changes,
        "configuration": {
            "root_module": {}
        }
    }
    
    return plan

if __name__ == "__main__":
    num_resources = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"test_data/large-plan-{num_resources}.json"
    
    plan = generate_large_plan(num_resources)
    
    with open(output_file, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"Generated {output_file} with {num_resources} resources")
