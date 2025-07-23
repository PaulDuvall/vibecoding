"""
DynamoDB client for digest persistence.
US-004-003: Implement Basic DynamoDB Connection
"""

import logging
import os
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for interacting with DynamoDB table."""
    
    def __init__(self, table_name: str, region: str = None):
        """Initialize DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table
            region: AWS region (defaults to AWS_DEFAULT_REGION or us-east-1)
        """
        self.table_name = table_name
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self._table = None
        self._resource = None
        
        logger.info(f"Initializing DynamoDBClient for table: {table_name} in region: {self.region}")
        
        # Validate connection on initialization
        try:
            self._initialize_connection()
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB connection: {e}")
            raise
    
    def _initialize_connection(self):
        """Initialize connection to DynamoDB."""
        try:
            self._resource = boto3.resource('dynamodb', region_name=self.region)
            self._table = self._resource.Table(self.table_name)
            
            # Verify table exists by describing it
            self.describe_table()
            logger.info(f"Successfully connected to table: {self.table_name}")
            
        except NoCredentialsError:
            logger.error("No AWS credentials found. Please configure AWS credentials.")
            raise
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Table '{self.table_name}' does not exist in region {self.region}")
            else:
                logger.error(f"AWS Client Error: {error_code} - {e}")
            raise
    
    @property
    def table(self):
        """Get the DynamoDB table resource."""
        if self._table is None:
            raise RuntimeError("DynamoDB connection not initialized")
        return self._table
    
    def describe_table(self) -> Dict[str, Any]:
        """Get table description.
        
        Returns:
            Dictionary containing table metadata
            
        Raises:
            ClientError: If table doesn't exist or access denied
        """
        try:
            response = self._table.meta.client.describe_table(TableName=self.table_name)
            return response['Table']
        except ClientError as e:
            logger.error(f"Failed to describe table {self.table_name}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test the connection to DynamoDB table.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.describe_table()
            return True
        except Exception:
            return False