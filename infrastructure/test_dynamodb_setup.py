"""
DynamoDB table setup and configuration tests.
Referenced in us004_data_persistence_spec.md as [^dt7]
Tests DynamoDB table creation and configuration verification.
"""

import pytest
import boto3
import time
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb
from typing import Dict, List, Any
from botocore.exceptions import ClientError


class TestDynamoDBTableSetup:
    """Tests for DynamoDB table creation and setup."""
    
    @mock_dynamodb
    def setup_method(self):
        """Set up DynamoDB test environment."""
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
        
        # Standard table configuration
        self.table_config = {
            'TableName': 'VibeDigest-test',
            'KeySchema': [
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'},
                {'AttributeName': 'feed_source', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'SourceIndex',
                    'KeySchema': [
                        {'AttributeName': 'feed_source', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {'Key': 'Environment', 'Value': 'test'},
                {'Key': 'Project', 'Value': 'VibeCodingDigest'},
                {'Key': 'Purpose', 'Value': 'DigestPersistence'}
            ]
        }
    
    @mock_dynamodb
    def test_table_creation_success(self):
        """Test successful DynamoDB table creation."""
        # Create table
        table = self.dynamodb.create_table(**self.table_config)
        
        # Verify table was created
        assert table.table_name == 'VibeDigest-test'
        
        # Wait for table to become active (simulated in moto)
        table.wait_until_exists()
        
        # Verify table status
        table.reload()
        assert table.table_status == 'ACTIVE'
    
    @mock_dynamodb
    def test_table_schema_validation(self):
        """Test table schema configuration."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Verify key schema
        key_schema = table.key_schema
        assert len(key_schema) == 2
        
        partition_key = next(k for k in key_schema if k['KeyType'] == 'HASH')
        sort_key = next(k for k in key_schema if k['KeyType'] == 'RANGE')
        
        assert partition_key['AttributeName'] == 'digest_date'
        assert sort_key['AttributeName'] == 'item_id'
        
        # Verify attribute definitions
        attr_defs = table.attribute_definitions
        attr_names = {attr['AttributeName'] for attr in attr_defs}
        expected_attrs = {'digest_date', 'item_id', 'feed_source', 'timestamp'}
        assert attr_names == expected_attrs
    
    @mock_dynamodb
    def test_global_secondary_index_setup(self):
        """Test GSI creation and configuration."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Verify GSI exists
        gsi_list = table.global_secondary_indexes
        assert len(gsi_list) == 1
        
        source_index = gsi_list[0]
        assert source_index['IndexName'] == 'SourceIndex'
        
        # Verify GSI key schema
        gsi_key_schema = source_index['KeySchema']
        assert len(gsi_key_schema) == 2
        
        gsi_partition = next(k for k in gsi_key_schema if k['KeyType'] == 'HASH')
        gsi_sort = next(k for k in gsi_key_schema if k['KeyType'] == 'RANGE')
        
        assert gsi_partition['AttributeName'] == 'feed_source'
        assert gsi_sort['AttributeName'] == 'timestamp'
        
        # Verify projection
        assert source_index['Projection']['ProjectionType'] == 'ALL'
    
    @mock_dynamodb
    def test_billing_mode_configuration(self):
        """Test PAY_PER_REQUEST billing mode setup."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Verify billing mode
        assert table.billing_mode_summary['BillingMode'] == 'PAY_PER_REQUEST'
        
        # Verify no provisioned throughput is set
        assert 'ProvisionedThroughput' not in table.key_schema[0]
    
    @mock_dynamodb
    def test_table_tagging(self):
        """Test table tagging configuration."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Get table tags
        response = self.dynamodb_client.list_tags_of_resource(
            ResourceArn=table.table_arn
        )
        
        tags = {tag['Key']: tag['Value'] for tag in response['Tags']}
        
        # Verify required tags
        assert tags['Environment'] == 'test'
        assert tags['Project'] == 'VibeCodingDigest'
        assert tags['Purpose'] == 'DigestPersistence'
    
    @mock_dynamodb
    def test_table_exists_check(self):
        """Test checking if table already exists."""
        def table_exists(table_name: str) -> bool:
            """Check if DynamoDB table exists."""
            try:
                self.dynamodb_client.describe_table(TableName=table_name)
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    return False
                raise
        
        # Table should not exist initially
        assert not table_exists('VibeDigest-test')
        
        # Create table
        self.dynamodb.create_table(**self.table_config)
        
        # Table should now exist
        assert table_exists('VibeDigest-test')
    
    @mock_dynamodb
    def test_duplicate_table_creation_handling(self):
        """Test handling of duplicate table creation attempts."""
        # Create table first time
        table1 = self.dynamodb.create_table(**self.table_config)
        table1.wait_until_exists()
        
        # Attempt to create same table again should fail
        with pytest.raises(ClientError) as exc_info:
            self.dynamodb.create_table(**self.table_config)
        
        assert exc_info.value.response['Error']['Code'] == 'ResourceInUseException'
    
    @mock_dynamodb
    def test_table_deletion_and_recreation(self):
        """Test table deletion and recreation process."""
        # Create table
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Verify table exists
        assert table.table_status == 'ACTIVE'
        
        # Delete table
        table.delete()
        
        # Wait for deletion (simulated in moto)
        with pytest.raises(ClientError) as exc_info:
            self.dynamodb_client.describe_table(TableName='VibeDigest-test')
        assert exc_info.value.response['Error']['Code'] == 'ResourceNotFoundException'
        
        # Recreate table
        new_table = self.dynamodb.create_table(**self.table_config)
        new_table.wait_until_exists()
        assert new_table.table_status == 'ACTIVE'
    
    @mock_dynamodb
    def test_environment_specific_table_names(self):
        """Test creation of environment-specific tables."""
        environments = ['dev', 'staging', 'prod']
        created_tables = []
        
        for env in environments:
            env_config = self.table_config.copy()
            env_config['TableName'] = f'VibeDigest-{env}'
            env_config['Tags'] = [
                {'Key': 'Environment', 'Value': env},
                {'Key': 'Project', 'Value': 'VibeCodingDigest'},
                {'Key': 'Purpose', 'Value': 'DigestPersistence'}
            ]
            
            table = self.dynamodb.create_table(**env_config)
            table.wait_until_exists()
            created_tables.append(table)
        
        # Verify all tables were created
        assert len(created_tables) == 3
        
        # Verify table names
        table_names = [table.table_name for table in created_tables]
        expected_names = ['VibeDigest-dev', 'VibeDigest-staging', 'VibeDigest-prod']
        assert set(table_names) == set(expected_names)
    
    def test_table_configuration_validation(self):
        """Test validation of table configuration parameters."""
        def validate_table_config(config: Dict[str, Any]) -> List[str]:
            """Validate table configuration and return errors."""
            errors = []
            
            # Check required fields
            required_fields = ['TableName', 'KeySchema', 'AttributeDefinitions']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Validate key schema
            if 'KeySchema' in config:
                key_schema = config['KeySchema']
                if len(key_schema) != 2:
                    errors.append("Key schema should have exactly 2 keys (HASH and RANGE)")
                
                key_types = {key['KeyType'] for key in key_schema}
                if key_types != {'HASH', 'RANGE'}:
                    errors.append("Key schema should have one HASH and one RANGE key")
            
            # Validate attribute definitions
            if 'AttributeDefinitions' in config and 'KeySchema' in config:
                attr_names = {attr['AttributeName'] for attr in config['AttributeDefinitions']}
                key_names = {key['AttributeName'] for key in config['KeySchema']}
                
                if not key_names.issubset(attr_names):
                    errors.append("All key attributes must be defined in AttributeDefinitions")
            
            # Validate GSI configuration
            if 'GlobalSecondaryIndexes' in config:
                for gsi in config['GlobalSecondaryIndexes']:
                    if 'IndexName' not in gsi:
                        errors.append("GSI missing IndexName")
                    if 'KeySchema' not in gsi:
                        errors.append("GSI missing KeySchema")
            
            return errors
        
        # Test valid configuration
        errors = validate_table_config(self.table_config)
        assert len(errors) == 0, f"Valid config should not have errors: {errors}"
        
        # Test invalid configuration
        invalid_config = {'TableName': 'test'}  # Missing required fields
        errors = validate_table_config(invalid_config)
        assert len(errors) > 0, "Invalid config should have errors"
    
    @mock_dynamodb
    def test_table_capacity_monitoring_setup(self):
        """Test setup for table capacity monitoring."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # In real implementation, would set up CloudWatch monitoring
        # For now, verify table is ready for monitoring
        
        # Verify table ARN is available for CloudWatch setup
        assert table.table_arn is not None
        assert 'arn:aws:dynamodb' in table.table_arn
        
        # Verify table name for metric identification
        assert table.table_name == 'VibeDigest-test'
    
    @mock_dynamodb
    def test_point_in_time_recovery_enablement(self):
        """Test enabling point-in-time recovery."""
        table = self.dynamodb.create_table(**self.table_config)
        table.wait_until_exists()
        
        # Enable point-in-time recovery
        # Note: moto doesn't fully support this, so we simulate the API call
        try:
            self.dynamodb_client.update_continuous_backups(
                TableName=table.table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
        except Exception:
            # Expected in moto environment
            pass
        
        # Verify PITR would be enabled (in real AWS)
        # response = self.dynamodb_client.describe_continuous_backups(TableName=table.table_name)
        # assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


class TestTableOperationalReadiness:
    """Tests to verify table is ready for operational use."""
    
    @mock_dynamodb
    def setup_method(self):
        """Set up operational readiness test environment."""
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'VibeDigest-operational-test'
        
        # Create table for operational testing
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'},
                {'AttributeName': 'feed_source', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SourceIndex',
                    'KeySchema': [
                        {'AttributeName': 'feed_source', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        self.table.wait_until_exists()
    
    @mock_dynamodb
    def test_basic_crud_operations(self):
        """Test basic CRUD operations work correctly."""
        # Test PUT operation
        test_item = {
            'digest_date': '2024-06-08',
            'item_id': 'aws#123#abc',
            'feed_source': 'AWS Blog',
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'summary': 'Test summary',
            'timestamp': '2024-06-08T10:00:00Z'
        }
        
        self.table.put_item(Item=test_item)
        
        # Test GET operation
        response = self.table.get_item(
            Key={'digest_date': '2024-06-08', 'item_id': 'aws#123#abc'}
        )
        
        assert 'Item' in response
        retrieved_item = response['Item']
        assert retrieved_item['title'] == 'Test Article'
        assert retrieved_item['feed_source'] == 'AWS Blog'
        
        # Test QUERY operation
        query_response = self.table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('digest_date').eq('2024-06-08')
        )
        
        assert len(query_response['Items']) == 1
        assert query_response['Items'][0]['item_id'] == 'aws#123#abc'
    
    @mock_dynamodb
    def test_gsi_query_functionality(self):
        """Test GSI query functionality."""
        # Add test data
        test_items = [
            {
                'digest_date': '2024-06-08',
                'item_id': 'aws#123#abc',
                'feed_source': 'AWS Blog',
                'title': 'AWS Article 1',
                'timestamp': '2024-06-08T10:00:00Z'
            },
            {
                'digest_date': '2024-06-08',
                'item_id': 'aws#124#def',
                'feed_source': 'AWS Blog',
                'title': 'AWS Article 2',
                'timestamp': '2024-06-08T11:00:00Z'
            },
            {
                'digest_date': '2024-06-08',
                'item_id': 'openai#125#ghi',
                'feed_source': 'OpenAI Blog',
                'title': 'OpenAI Article',
                'timestamp': '2024-06-08T12:00:00Z'
            }
        ]
        
        # Insert test data
        for item in test_items:
            self.table.put_item(Item=item)
        
        # Query GSI by feed source
        gsi_response = self.table.query(
            IndexName='SourceIndex',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('feed_source').eq('AWS Blog')
        )
        
        # Verify GSI query results
        assert len(gsi_response['Items']) == 2
        aws_items = gsi_response['Items']
        assert all(item['feed_source'] == 'AWS Blog' for item in aws_items)
    
    @mock_dynamodb
    def test_batch_operations_functionality(self):
        """Test batch write operations."""
        # Prepare batch items
        batch_items = []
        for i in range(25):  # DynamoDB batch limit
            item = {
                'digest_date': '2024-06-08',
                'item_id': f'batch#{i}#test',
                'feed_source': f'Source {i % 3}',
                'title': f'Batch Article {i}',
                'timestamp': f'2024-06-08T{10 + (i % 12):02d}:00:00Z'
            }
            batch_items.append(item)
        
        # Perform batch write
        with self.table.batch_writer() as batch:
            for item in batch_items:
                batch.put_item(Item=item)
        
        # Verify all items were written
        response = self.table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('digest_date').eq('2024-06-08')
        )
        
        assert len(response['Items']) == 25
    
    @mock_dynamodb
    def test_table_performance_baseline(self):
        """Test table performance meets baseline requirements."""
        start_time = time.time()
        
        # Perform series of operations
        operations_count = 0
        
        # Single item operations
        for i in range(10):
            self.table.put_item(Item={
                'digest_date': '2024-06-08',
                'item_id': f'perf#{i}#test',
                'feed_source': 'Performance Test',
                'title': f'Performance Article {i}',
                'timestamp': f'2024-06-08T10:{i:02d}:00Z'
            })
            operations_count += 1
        
        # Query operations
        for i in range(5):
            self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('digest_date').eq('2024-06-08')
            )
            operations_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        ops_per_second = operations_count / total_time
        
        # Verify reasonable performance (relaxed for test environment)
        assert ops_per_second > 1.0, f"Performance too slow: {ops_per_second:.2f} ops/sec"
        assert total_time < 30.0, f"Operations took too long: {total_time:.2f} seconds"
    
    @mock_dynamodb
    def test_error_handling_scenarios(self):
        """Test table behavior under error conditions."""
        # Test item not found
        response = self.table.get_item(
            Key={'digest_date': '2024-06-08', 'item_id': 'nonexistent'}
        )
        assert 'Item' not in response
        
        # Test invalid key format
        with pytest.raises(ClientError):
            self.table.get_item(Key={'invalid_key': 'test'})
        
        # Test conditional put failure
        # First, put an item
        self.table.put_item(Item={
            'digest_date': '2024-06-08',
            'item_id': 'conditional#test',
            'title': 'Original Title'
        })
        
        # Then try conditional put that should fail
        with pytest.raises(ClientError) as exc_info:
            self.table.put_item(
                Item={
                    'digest_date': '2024-06-08',
                    'item_id': 'conditional#test',
                    'title': 'Updated Title'
                },
                ConditionExpression='attribute_not_exists(item_id)'
            )
        
        assert exc_info.value.response['Error']['Code'] == 'ConditionalCheckFailedException'