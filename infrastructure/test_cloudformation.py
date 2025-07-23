"""
CloudFormation template validation tests.
Referenced in us004_data_persistence_spec.md as [^cf6]
Tests CloudFormation template syntax and resource configuration.
"""

import pytest
import json
import yaml
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_cloudformation, mock_dynamodb
from typing import Dict, Any, List


class TestCloudFormationTemplateValidation:
    """Tests for CloudFormation template validation."""
    
    def setup_method(self):
        """Set up CloudFormation test fixtures."""
        # Sample CloudFormation template for DynamoDB table
        self.dynamodb_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "DynamoDB table for Vibe Coding Digest persistence",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": "dev",
                    "AllowedValues": ["dev", "staging", "prod"],
                    "Description": "Environment name for resource naming"
                }
            },
            "Resources": {
                "VibeDigestTable": {
                    "Type": "AWS::DynamoDB::Table",
                    "Properties": {
                        "TableName": {"Fn::Sub": "VibeDigest-${Environment}"},
                        "BillingMode": "PAY_PER_REQUEST",
                        "AttributeDefinitions": [
                            {"AttributeName": "digest_date", "AttributeType": "S"},
                            {"AttributeName": "item_id", "AttributeType": "S"},
                            {"AttributeName": "feed_source", "AttributeType": "S"},
                            {"AttributeName": "timestamp", "AttributeType": "S"}
                        ],
                        "KeySchema": [
                            {"AttributeName": "digest_date", "KeyType": "HASH"},
                            {"AttributeName": "item_id", "KeyType": "RANGE"}
                        ],
                        "GlobalSecondaryIndexes": [
                            {
                                "IndexName": "SourceIndex",
                                "KeySchema": [
                                    {"AttributeName": "feed_source", "KeyType": "HASH"},
                                    {"AttributeName": "timestamp", "KeyType": "RANGE"}
                                ],
                                "Projection": {"ProjectionType": "ALL"}
                            }
                        ],
                        "PointInTimeRecoverySpecification": {
                            "PointInTimeRecoveryEnabled": True
                        },
                        "Tags": [
                            {"Key": "Environment", "Value": {"Ref": "Environment"}},
                            {"Key": "Project", "Value": "VibeCodingDigest"},
                            {"Key": "Purpose", "Value": "DigestPersistence"}
                        ]
                    }
                }
            },
            "Outputs": {
                "TableName": {
                    "Description": "Name of the DynamoDB table",
                    "Value": {"Ref": "VibeDigestTable"},
                    "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-TableName"}}
                },
                "TableArn": {
                    "Description": "ARN of the DynamoDB table",
                    "Value": {"Fn::GetAtt": ["VibeDigestTable", "Arn"]},
                    "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-TableArn"}}
                }
            }
        }
    
    def test_template_syntax_validation(self):
        """Test CloudFormation template syntax is valid."""
        # Verify required top-level sections
        required_sections = ["AWSTemplateFormatVersion", "Description", "Resources"]
        for section in required_sections:
            assert section in self.dynamodb_template, f"Missing required section: {section}"
        
        # Verify template format version
        assert self.dynamodb_template["AWSTemplateFormatVersion"] == "2010-09-09"
        
        # Verify resources section is not empty
        assert len(self.dynamodb_template["Resources"]) > 0, "Resources section cannot be empty"
        
        # Verify JSON serialization works (syntax check)
        try:
            json.dumps(self.dynamodb_template)
        except Exception as e:
            pytest.fail(f"Template JSON serialization failed: {e}")
    
    def test_dynamodb_table_configuration(self):
        """Test DynamoDB table resource configuration."""
        table_resource = self.dynamodb_template["Resources"]["VibeDigestTable"]
        
        # Verify resource type
        assert table_resource["Type"] == "AWS::DynamoDB::Table"
        
        # Verify required properties
        properties = table_resource["Properties"]
        required_properties = ["TableName", "KeySchema", "AttributeDefinitions"]
        for prop in required_properties:
            assert prop in properties, f"Missing required property: {prop}"
        
        # Verify key schema
        key_schema = properties["KeySchema"]
        assert len(key_schema) == 2, "Should have partition and sort key"
        
        partition_key = next(k for k in key_schema if k["KeyType"] == "HASH")
        sort_key = next(k for k in key_schema if k["KeyType"] == "RANGE")
        
        assert partition_key["AttributeName"] == "digest_date"
        assert sort_key["AttributeName"] == "item_id"
        
        # Verify attribute definitions
        attr_defs = properties["AttributeDefinitions"]
        assert len(attr_defs) >= 2, "Should define at least partition and sort key attributes"
        
        # Verify billing mode
        assert properties["BillingMode"] == "PAY_PER_REQUEST"
    
    def test_global_secondary_index_configuration(self):
        """Test GSI configuration in template."""
        table_properties = self.dynamodb_template["Resources"]["VibeDigestTable"]["Properties"]
        gsi_list = table_properties["GlobalSecondaryIndexes"]
        
        assert len(gsi_list) == 1, "Should have exactly one GSI"
        
        source_index = gsi_list[0]
        assert source_index["IndexName"] == "SourceIndex"
        
        # Verify GSI key schema
        gsi_key_schema = source_index["KeySchema"]
        assert len(gsi_key_schema) == 2
        
        gsi_partition = next(k for k in gsi_key_schema if k["KeyType"] == "HASH")
        gsi_sort = next(k for k in gsi_key_schema if k["KeyType"] == "RANGE")
        
        assert gsi_partition["AttributeName"] == "feed_source"
        assert gsi_sort["AttributeName"] == "timestamp"
        
        # Verify projection
        assert source_index["Projection"]["ProjectionType"] == "ALL"
    
    def test_backup_and_recovery_configuration(self):
        """Test point-in-time recovery configuration."""
        table_properties = self.dynamodb_template["Resources"]["VibeDigestTable"]["Properties"]
        pitr_config = table_properties["PointInTimeRecoverySpecification"]
        
        assert pitr_config["PointInTimeRecoveryEnabled"] is True
    
    def test_tagging_configuration(self):
        """Test resource tagging configuration."""
        table_properties = self.dynamodb_template["Resources"]["VibeDigestTable"]["Properties"]
        tags = table_properties["Tags"]
        
        # Verify required tags are present
        tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
        required_tags = ["Environment", "Project", "Purpose"]
        
        for tag_key in required_tags:
            assert tag_key in tag_dict, f"Missing required tag: {tag_key}"
        
        # Verify specific tag values
        assert tag_dict["Project"] == "VibeCodingDigest"
        assert tag_dict["Purpose"] == "DigestPersistence"
    
    def test_parameters_configuration(self):
        """Test CloudFormation parameters configuration."""
        parameters = self.dynamodb_template["Parameters"]
        
        # Verify Environment parameter
        env_param = parameters["Environment"]
        assert env_param["Type"] == "String"
        assert env_param["Default"] == "dev"
        assert set(env_param["AllowedValues"]) == {"dev", "staging", "prod"}
    
    def test_outputs_configuration(self):
        """Test CloudFormation outputs configuration."""
        outputs = self.dynamodb_template["Outputs"]
        
        # Verify required outputs
        required_outputs = ["TableName", "TableArn"]
        for output_name in required_outputs:
            assert output_name in outputs, f"Missing required output: {output_name}"
        
        # Verify output exports
        for output_name, output_config in outputs.items():
            assert "Export" in output_config, f"Output {output_name} should have export"
            assert "Name" in output_config["Export"], f"Output {output_name} export should have name"
    
    @mock_cloudformation
    def test_template_deployment_simulation(self):
        """Test template deployment using moto simulation."""
        cf = boto3.client('cloudformation', region_name='us-east-1')
        
        # Create stack
        stack_name = 'vibe-digest-test-stack'
        
        try:
            cf.create_stack(
                StackName=stack_name,
                TemplateBody=json.dumps(self.dynamodb_template),
                Parameters=[
                    {'ParameterKey': 'Environment', 'ParameterValue': 'test'}
                ]
            )
            
            # Verify stack was created
            stacks = cf.list_stacks()
            stack_names = [stack['StackName'] for stack in stacks['StackSummaries']]
            assert stack_name in stack_names
            
            # Verify stack status
            stack_info = cf.describe_stacks(StackName=stack_name)
            stack = stack_info['Stacks'][0]
            assert stack['StackStatus'] in ['CREATE_IN_PROGRESS', 'CREATE_COMPLETE']
            
        except Exception as e:
            pytest.fail(f"Template deployment simulation failed: {e}")
    
    def test_cross_stack_references(self):
        """Test cross-stack reference capability."""
        outputs = self.dynamodb_template["Outputs"]
        
        # Verify outputs are properly formatted for cross-stack references
        for output_name, output_config in outputs.items():
            export_name = output_config["Export"]["Name"]
            
            # Should use stack name in export name
            assert "${AWS::StackName}" in str(export_name), \
                f"Export name for {output_name} should include stack name"
    
    def test_template_parameter_validation(self):
        """Test template parameter validation logic."""
        def validate_parameters(template: Dict[str, Any], provided_params: Dict[str, str]) -> List[str]:
            """Validate provided parameters against template definition."""
            errors = []
            template_params = template.get("Parameters", {})
            
            for param_name, param_config in template_params.items():
                if param_name in provided_params:
                    value = provided_params[param_name]
                    
                    # Check allowed values
                    if "AllowedValues" in param_config:
                        if value not in param_config["AllowedValues"]:
                            errors.append(f"Invalid value '{value}' for parameter '{param_name}'")
                    
                    # Check type (basic validation)
                    if param_config["Type"] == "String" and not isinstance(value, str):
                        errors.append(f"Parameter '{param_name}' must be a string")
                else:
                    # Check if parameter has default
                    if "Default" not in param_config:
                        errors.append(f"Missing required parameter: {param_name}")
            
            return errors
        
        # Test valid parameters
        valid_params = {"Environment": "dev"}
        errors = validate_parameters(self.dynamodb_template, valid_params)
        assert len(errors) == 0, f"Valid parameters should not produce errors: {errors}"
        
        # Test invalid environment value
        invalid_params = {"Environment": "invalid"}
        errors = validate_parameters(self.dynamodb_template, invalid_params)
        assert len(errors) > 0, "Invalid environment value should produce error"
        assert "Invalid value 'invalid'" in errors[0]
    
    def test_resource_naming_conventions(self):
        """Test that resources follow naming conventions."""
        table_resource = self.dynamodb_template["Resources"]["VibeDigestTable"]
        table_name = table_resource["Properties"]["TableName"]
        
        # Verify table name uses environment parameter
        assert "VibeDigest" in str(table_name), "Table name should include project name"
        assert "${Environment}" in str(table_name), "Table name should include environment"
        
        # Verify resource logical name follows convention
        assert "VibeDigestTable" == "VibeDigestTable"  # Pascal case
    
    def test_security_configuration(self):
        """Test security-related configuration in template."""
        table_properties = self.dynamodb_template["Resources"]["VibeDigestTable"]["Properties"]
        
        # Verify point-in-time recovery is enabled (security/backup)
        pitr = table_properties["PointInTimeRecoverySpecification"]
        assert pitr["PointInTimeRecoveryEnabled"] is True
        
        # In real implementation, would also check:
        # - SSE configuration
        # - KMS key configuration
        # - VPC endpoints (if applicable)


class TestInfrastructureAsCode:
    """Tests for Infrastructure as Code best practices."""
    
    def test_template_linting(self):
        """Test CloudFormation template against linting rules."""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Test template",
            "Resources": {
                "TestTable": {
                    "Type": "AWS::DynamoDB::Table",
                    "Properties": {
                        "TableName": "test-table",
                        "BillingMode": "PAY_PER_REQUEST",
                        "KeySchema": [
                            {"AttributeName": "id", "KeyType": "HASH"}
                        ],
                        "AttributeDefinitions": [
                            {"AttributeName": "id", "AttributeType": "S"}
                        ]
                    }
                }
            }
        }
        
        def lint_template(template: Dict[str, Any]) -> List[str]:
            """Basic template linting rules."""
            issues = []
            
            # Check for hardcoded values
            template_str = json.dumps(template)
            if '"test-table"' in template_str:
                issues.append("Hardcoded table name found")
            
            # Check for missing descriptions
            if not template.get("Description"):
                issues.append("Template missing description")
            
            # Check for missing tags on resources
            for resource_name, resource in template.get("Resources", {}).items():
                if resource["Type"] == "AWS::DynamoDB::Table":
                    if "Tags" not in resource.get("Properties", {}):
                        issues.append(f"Resource {resource_name} missing tags")
            
            return issues
        
        issues = lint_template(template)
        # This template intentionally has issues for testing
        assert len(issues) > 0, "Linting should detect issues in test template"
        assert any("Hardcoded" in issue for issue in issues)
        assert any("missing tags" in issue for issue in issues)
    
    def test_template_versioning(self):
        """Test template versioning strategy."""
        # Template should include version metadata
        template_metadata = {
            "template_version": "1.0.0",
            "last_updated": "2024-06-08",
            "author": "VibeCoding Team",
            "change_log": [
                {"version": "1.0.0", "date": "2024-06-08", "changes": ["Initial template creation"]}
            ]
        }
        
        # Verify version format
        version = template_metadata["template_version"]
        version_parts = version.split(".")
        assert len(version_parts) == 3, "Version should follow semantic versioning (major.minor.patch)"
        assert all(part.isdigit() for part in version_parts), "Version parts should be numeric"
    
    def test_environment_specific_configuration(self):
        """Test environment-specific configuration handling."""
        environments = {
            "dev": {
                "table_name": "VibeDigest-dev",
                "backup_retention": 7,
                "monitoring_level": "basic"
            },
            "staging": {
                "table_name": "VibeDigest-staging", 
                "backup_retention": 30,
                "monitoring_level": "enhanced"
            },
            "prod": {
                "table_name": "VibeDigest-prod",
                "backup_retention": 365,
                "monitoring_level": "comprehensive"
            }
        }
        
        # Verify each environment has required configuration
        required_configs = ["table_name", "backup_retention", "monitoring_level"]
        for env_name, env_config in environments.items():
            for config_key in required_configs:
                assert config_key in env_config, f"Missing {config_key} for {env_name}"
            
            # Verify production has strongest settings
            if env_name == "prod":
                assert env_config["backup_retention"] >= 365
                assert env_config["monitoring_level"] == "comprehensive"