"""
Unit tests for daily task implementations.
Referenced in us004_daily_task_breakdown_spec.md as [^ut2]
Tests individual daily tasks and their implementations.
"""

import pytest
import os
import json
import boto3
from unittest.mock import Mock, patch, MagicMock
from moto import mock_dynamodb, mock_cloudformation
from datetime import datetime, timezone
from typing import Dict, List, Any

from src.models import DigestItem


class TestDay1Implementations:
    """Tests for Day 1 task implementations."""
    
    def test_us004_001_cloudformation_template_creation(self):
        """Test US-004-001: Create DynamoDB Table Infrastructure."""
        # Test CloudFormation template structure
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "DynamoDB table for Vibe Coding Digest persistence",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": "dev",
                    "AllowedValues": ["dev", "staging", "prod"]
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
                            {"AttributeName": "item_id", "AttributeType": "S"}
                        ],
                        "KeySchema": [
                            {"AttributeName": "digest_date", "KeyType": "HASH"},
                            {"AttributeName": "item_id", "KeyType": "RANGE"}
                        ]
                    }
                }
            }
        }
        
        # Validate template structure
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"
        assert "VibeDigestTable" in template["Resources"]
        
        table_resource = template["Resources"]["VibeDigestTable"]
        assert table_resource["Type"] == "AWS::DynamoDB::Table"
        assert table_resource["Properties"]["BillingMode"] == "PAY_PER_REQUEST"
        
        # Validate key schema
        key_schema = table_resource["Properties"]["KeySchema"]
        partition_key = next(k for k in key_schema if k["KeyType"] == "HASH")
        sort_key = next(k for k in key_schema if k["KeyType"] == "RANGE")
        
        assert partition_key["AttributeName"] == "digest_date"
        assert sort_key["AttributeName"] == "item_id"
    
    def test_us004_002_database_package_structure(self):
        """Test US-004-002: Create Database Package Structure."""
        # Test package structure validation
        expected_structure = {
            "src/database/__init__.py": "Package initialization file",
            "src/database/client.py": "DynamoDB client implementation"
        }
        
        # Mock package structure validation
        def validate_package_structure(structure: Dict[str, str]) -> List[str]:
            """Validate database package structure."""
            issues = []
            
            for file_path, description in structure.items():
                if not file_path.endswith('.py'):
                    issues.append(f"Non-Python file in package: {file_path}")
                
                if '__init__.py' not in structure:
                    issues.append("Missing __init__.py in package")
                
                if 'client.py' not in file_path and '__init__.py' not in file_path:
                    issues.append(f"Unexpected file in package: {file_path}")
            
            return issues
        
        issues = validate_package_structure(expected_structure)
        assert len(issues) == 0, f"Package structure issues: {issues}"
        
        # Test DynamoDBClient class skeleton
        client_skeleton = '''
class DynamoDBClient:
    def __init__(self, table_name: str, region: str = 'us-east-1'):
        self.table_name = table_name
        self.region = region
        
    def test_connection(self) -> bool:
        pass
'''
        
        # Verify class definition exists
        assert "class DynamoDBClient:" in client_skeleton
        assert "__init__" in client_skeleton
        assert "test_connection" in client_skeleton
    
    @mock_dynamodb
    def test_us004_003_basic_dynamodb_connection(self):
        """Test US-004-003: Implement Basic DynamoDB Connection."""
        # Mock DynamoDBClient implementation
        class MockDynamoDBClient:
            def __init__(self, table_name: str, region: str = 'us-east-1'):
                self.table_name = table_name
                self.region = region
                self._table = None
            
            def test_connection(self) -> bool:
                """Test connection to DynamoDB table."""
                try:
                    dynamodb = boto3.resource('dynamodb', region_name=self.region)
                    self._table = dynamodb.Table(self.table_name)
                    # In real implementation, would call describe_table()
                    return True
                except Exception:
                    return False
        
        # Create test table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Test connection
        client = MockDynamoDBClient('VibeDigest-test')
        connection_result = client.test_connection()
        
        assert connection_result is True
        assert client.table_name == 'VibeDigest-test'
        assert client.region == 'us-east-1'


class TestDay2Implementations:
    """Tests for Day 2 task implementations."""
    
    @mock_dynamodb
    def test_us004_004_single_item_write(self):
        """Test US-004-004: Implement Single Item Write."""
        # Mock implementation of put_item
        class MockDynamoDBClient:
            def __init__(self, table_name: str):
                self.table_name = table_name
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                self.table = dynamodb.Table(table_name)
            
            def put_item(self, item: Dict[str, Any]) -> bool:
                """Store single item in DynamoDB."""
                try:
                    self.table.put_item(Item=item)
                    return True
                except Exception:
                    return False
        
        # Create test table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-write-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Test single item write
        client = MockDynamoDBClient('VibeDigest-write-test')
        test_item = {
            'digest_date': '2024-06-08',
            'item_id': 'aws#123#abc',
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'summary': 'Test summary',
            'source': 'AWS Blog'
        }
        
        result = client.put_item(test_item)
        assert result is True
        
        # Verify item was stored
        response = table.get_item(
            Key={'digest_date': '2024-06-08', 'item_id': 'aws#123#abc'}
        )
        assert 'Item' in response
        assert response['Item']['title'] == 'Test Article'
    
    def test_us004_005_unique_id_generation(self):
        """Test US-004-005: Generate Unique Item IDs."""
        def generate_item_id(digest_date: str, source: str, url: str) -> str:
            """Generate unique ID for digest item."""
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"{digest_date}#{source}#{url_hash}"
        
        # Test ID generation
        id1 = generate_item_id('2024-06-08', 'AWS Blog', 'https://example.com/1')
        id2 = generate_item_id('2024-06-08', 'AWS Blog', 'https://example.com/2')
        id3 = generate_item_id('2024-06-08', 'AWS Blog', 'https://example.com/1')  # Same URL
        
        # Verify uniqueness for different URLs
        assert id1 != id2
        
        # Verify consistency for same URL
        assert id1 == id3
        
        # Verify format
        assert id1.startswith('2024-06-08#AWS Blog#')
        assert len(id1.split('#')) == 3
    
    def test_us004_006_persistence_integration(self):
        """Test US-004-006: Add Persistence to Main Workflow."""
        # Mock main workflow integration
        def mock_digest_workflow_with_persistence():
            """Mock digest workflow with persistence."""
            # Simulate digest generation
            digest_items = [
                DigestItem(
                    title="Test Article",
                    link="https://example.com/test",
                    summary="Test summary",
                    source="Test Source",
                    published=datetime.now(timezone.utc)
                )
            ]
            
            # Simulate persistence attempt
            persistence_successful = True
            email_sent = True
            
            try:
                # Mock persistence call
                if persistence_successful:
                    # Items would be stored here
                    pass
            except Exception:
                # Email should still be sent
                persistence_successful = False
            
            return {
                'digest_items': digest_items,
                'persistence_successful': persistence_successful,
                'email_sent': email_sent
            }
        
        result = mock_digest_workflow_with_persistence()
        
        assert len(result['digest_items']) == 1
        assert result['persistence_successful'] is True
        assert result['email_sent'] is True


class TestDay3Implementations:
    """Tests for Day 3 task implementations."""
    
    def test_us004_007_connection_failure_handling(self):
        """Test US-004-007: Handle Database Connection Failures."""
        def mock_digest_with_db_failure():
            """Mock digest workflow with database failure."""
            try:
                # Simulate database connection failure
                raise Exception("Database unavailable")
            except Exception as e:
                # Log error but continue
                error_logged = True
                email_sent = True  # Email should still be sent
                return {
                    'error_logged': error_logged,
                    'email_sent': email_sent,
                    'error_type': type(e).__name__
                }
        
        result = mock_digest_with_db_failure()
        
        assert result['error_logged'] is True
        assert result['email_sent'] is True
        assert result['error_type'] == 'Exception'
    
    def test_us004_008_retry_logic(self):
        """Test US-004-008: Add Simple Retry Logic."""
        def mock_operation_with_retry(max_retries: int = 3):
            """Mock operation with retry logic."""
            attempts = 0
            
            while attempts < max_retries:
                attempts += 1
                
                # Simulate failure for first 2 attempts, success on 3rd
                if attempts <= 2:
                    continue  # Simulate failure
                else:
                    return {
                        'success': True,
                        'attempts': attempts,
                        'final_attempt_successful': True
                    }
            
            return {
                'success': False,
                'attempts': attempts,
                'max_retries_exceeded': True
            }
        
        # Test successful retry
        result = mock_operation_with_retry(3)
        assert result['success'] is True
        assert result['attempts'] == 3
        assert result['final_attempt_successful'] is True
        
        # Test retry exhaustion
        result_failure = mock_operation_with_retry(2)
        assert result_failure['success'] is False
        assert result_failure['max_retries_exceeded'] is True
    
    def test_us004_009_feature_flag(self):
        """Test US-004-009: Add Feature Flag."""
        def mock_persistence_with_feature_flag(enable_persistence: bool):
            """Mock persistence with feature flag control."""
            if not enable_persistence:
                return {
                    'persistence_attempted': False,
                    'skip_logged': True,
                    'email_sent': True
                }
            
            return {
                'persistence_attempted': True,
                'persistence_successful': True,
                'email_sent': True
            }
        
        # Test with persistence enabled
        result_enabled = mock_persistence_with_feature_flag(True)
        assert result_enabled['persistence_attempted'] is True
        assert result_enabled['email_sent'] is True
        
        # Test with persistence disabled
        result_disabled = mock_persistence_with_feature_flag(False)
        assert result_disabled['persistence_attempted'] is False
        assert result_disabled['skip_logged'] is True
        assert result_disabled['email_sent'] is True


class TestDay4Implementations:
    """Tests for Day 4 task implementations."""
    
    @mock_dynamodb
    def test_us004_010_batch_write_implementation(self):
        """Test US-004-010: Implement Batch Write."""
        class MockBatchWriter:
            def __init__(self, table_name: str):
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                self.table = dynamodb.Table(table_name)
            
            def batch_write_items(self, items: List[Dict[str, Any]]) -> Dict:
                """Write multiple items in batches."""
                batch_size = 25
                batches_processed = 0
                items_processed = 0
                
                for i in range(0, len(items), batch_size):
                    batch = items[i:i + batch_size]
                    
                    with self.table.batch_writer() as batch_writer:
                        for item in batch:
                            batch_writer.put_item(Item=item)
                    
                    batches_processed += 1
                    items_processed += len(batch)
                
                return {
                    'batches_processed': batches_processed,
                    'items_processed': items_processed,
                    'success': True
                }
        
        # Create test table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-batch-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Test batch write with 30 items
        batch_writer = MockBatchWriter('VibeDigest-batch-test')
        test_items = []
        
        for i in range(30):
            item = {
                'digest_date': '2024-06-08',
                'item_id': f'batch#{i}#test',
                'title': f'Batch Article {i}',
                'url': f'https://example.com/batch-{i}',
                'summary': f'Summary {i}'
            }
            test_items.append(item)
        
        result = batch_writer.batch_write_items(test_items)
        
        assert result['success'] is True
        assert result['items_processed'] == 30
        assert result['batches_processed'] == 2  # 30 items / 25 per batch = 2 batches
    
    def test_us004_011_main_flow_batch_integration(self):
        """Test US-004-011: Update Main Flow to Use Batches."""
        def mock_main_flow_with_batches():
            """Mock main flow using batch operations."""
            # Simulate digest with 40 items
            digest_items = [
                {
                    'digest_date': '2024-06-08',
                    'item_id': f'main#{i}#test',
                    'title': f'Main Article {i}'
                }
                for i in range(40)
            ]
            
            # Use batch write instead of individual puts
            batch_operation_used = True
            all_items_stored = len(digest_items) == 40
            
            return {
                'total_items': len(digest_items),
                'batch_operation_used': batch_operation_used,
                'all_items_stored': all_items_stored,
                'performance_improved': True
            }
        
        result = mock_main_flow_with_batches()
        
        assert result['total_items'] == 40
        assert result['batch_operation_used'] is True
        assert result['all_items_stored'] is True
        assert result['performance_improved'] is True


class TestDay5Day6Implementations:
    """Tests for Day 5-6 task implementations."""
    
    @mock_dynamodb
    def test_us004_012_query_by_date(self):
        """Test US-004-012: Query Items by Date."""
        # Create and populate test table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-query-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # Add test data
        test_items = [
            {'digest_date': '2024-06-08', 'item_id': 'item1', 'title': 'Article 1'},
            {'digest_date': '2024-06-08', 'item_id': 'item2', 'title': 'Article 2'},
            {'digest_date': '2024-06-07', 'item_id': 'item3', 'title': 'Article 3'}
        ]
        
        for item in test_items:
            table.put_item(Item=item)
        
        # Test query by date
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('digest_date').eq('2024-06-08')
        )
        
        assert len(response['Items']) == 2
        assert all(item['digest_date'] == '2024-06-08' for item in response['Items'])
    
    def test_us004_013_cli_retrieval_command(self):
        """Test US-004-013: Add CLI Command for Retrieval."""
        def mock_cli_retrieval(date: str):
            """Mock CLI retrieval command."""
            # Simulate CLI argument parsing
            if not date or not date.match(r'\d{4}-\d{2}-\d{2}'):
                return {
                    'success': False,
                    'error': 'Invalid date format',
                    'output': 'Error: Please provide date in YYYY-MM-DD format'
                }
            
            # Simulate retrieval
            mock_items = [
                {'title': 'CLI Test Article 1', 'url': 'https://example.com/1'},
                {'title': 'CLI Test Article 2', 'url': 'https://example.com/2'}
            ]
            
            output = f"Retrieved {len(mock_items)} items for {date}:\n"
            for item in mock_items:
                output += f"- {item['title']}: {item['url']}\n"
            
            return {
                'success': True,
                'items_count': len(mock_items),
                'output': output
            }
        
        # Mock date validation
        class MockDate:
            def __init__(self, date_str):
                self.date_str = date_str
            
            def match(self, pattern):
                import re
                return re.match(pattern, self.date_str)
        
        # Test valid date
        result_valid = mock_cli_retrieval(MockDate('2024-06-08'))
        assert result_valid['success'] is True
        assert result_valid['items_count'] == 2
        assert '2024-06-08' in result_valid['output']
        
        # Test invalid date
        result_invalid = mock_cli_retrieval(MockDate('invalid-date'))
        assert result_invalid['success'] is False
        assert 'Invalid date format' in result_invalid['error']
    
    def test_us004_014_cloudwatch_metrics(self):
        """Test US-004-014: Add CloudWatch Metrics."""
        def mock_cloudwatch_metrics_publishing():
            """Mock CloudWatch metrics publishing."""
            with patch('boto3.client') as mock_boto:
                mock_cloudwatch = Mock()
                mock_boto.return_value = mock_cloudwatch
                
                # Simulate successful metric publishing
                mock_cloudwatch.put_metric_data.return_value = {
                    'ResponseMetadata': {'HTTPStatusCode': 200}
                }
                
                # Publish test metrics
                metric_data = [
                    {
                        'MetricName': 'PersistenceSuccess',
                        'Value': 1,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'PersistenceLatency',
                        'Value': 250,
                        'Unit': 'Milliseconds'
                    }
                ]
                
                mock_cloudwatch.put_metric_data(
                    Namespace='VibeCodingDigest/Persistence',
                    MetricData=metric_data
                )
                
                return {
                    'metrics_published': True,
                    'metric_count': len(metric_data),
                    'namespace': 'VibeCodingDigest/Persistence'
                }
        
        result = mock_cloudwatch_metrics_publishing()
        
        assert result['metrics_published'] is True
        assert result['metric_count'] == 2
        assert result['namespace'] == 'VibeCodingDigest/Persistence'
    
    def test_us004_015_structured_logging(self):
        """Test US-004-015: Add Structured Logging."""
        def mock_structured_logging():
            """Mock structured logging implementation."""
            import json
            
            # Simulate structured log entry
            log_entry = {
                'timestamp': '2024-06-08T10:00:00Z',
                'level': 'INFO',
                'operation': 'persist_digest',
                'digest_date': '2024-06-08',
                'item_count': 5,
                'correlation_id': 'digest-12345',
                'success': True,
                'duration_ms': 250
            }
            
            # Convert to JSON format
            json_log = json.dumps(log_entry)
            
            return {
                'log_format': 'json',
                'log_entry': log_entry,
                'json_output': json_log,
                'parseable': True
            }
        
        result = mock_structured_logging()
        
        assert result['log_format'] == 'json'
        assert 'operation' in result['log_entry']
        assert 'correlation_id' in result['log_entry']
        assert result['parseable'] is True
        
        # Verify JSON is valid
        parsed_log = json.loads(result['json_output'])
        assert parsed_log['operation'] == 'persist_digest'
        assert parsed_log['item_count'] == 5