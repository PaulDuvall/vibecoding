Feature: US-004 Day 1 - Database Foundation and Setup
  As a developer implementing data persistence
  I want to establish the database infrastructure and basic connectivity
  So that I can build persistence features incrementally

  # US-004-001: Create DynamoDB Table Infrastructure (2 hours)
  Scenario: US-004-001 - Deploy DynamoDB table via CloudFormation
    Given I have a CloudFormation template for the VibeDigest table
    And AWS credentials are configured for the dev environment
    When I deploy the CloudFormation stack
    Then a DynamoDB table named "VibeDigest-dev" should be created
    And the table should have partition key "digest_date" of type String
    And the table should have sort key "item_id" of type String
    And the table should use PAY_PER_REQUEST billing mode
    And the table status should be "ACTIVE" within 2 minutes

  # US-004-002: Create Database Package Structure (1 hour)
  Scenario: US-004-002 - Database package structure exists and imports correctly
    Given the src/database directory exists
    And the __init__.py file exists in src/database
    And the client.py module exists with DynamoDBClient class skeleton
    When I run "python -c 'from src.database.client import DynamoDBClient'"
    Then no import errors should occur
    And the DynamoDBClient class should be importable
    And boto3 should be added to requirements.txt

  # US-004-003: Implement Basic DynamoDB Connection (2 hours)  
  Scenario: US-004-003 - Connect to DynamoDB table successfully
    Given AWS credentials are configured in environment variables
    And the VibeDigest-dev table exists in DynamoDB
    When I create a DynamoDBClient instance for table "VibeDigest-dev"
    Then the client should connect successfully
    And calling describe_table() should return table metadata
    And the connection should be logged at INFO level
    
  Scenario: US-004-003 - Handle connection with missing table gracefully
    Given AWS credentials are configured
    And a table named "NonExistentTable" does not exist
    When I create a DynamoDBClient instance for table "NonExistentTable"
    Then a ResourceNotFoundException should be raised
    And the error should be logged at ERROR level
    And the error message should mention the missing table name

  Scenario: US-004-003 - Connection with invalid credentials fails cleanly
    Given invalid AWS credentials are configured
    When I attempt to create a DynamoDBClient instance
    Then a NoCredentialsError or ClientError should be raised
    And the error should be logged at ERROR level
    And the error message should indicate authentication failure