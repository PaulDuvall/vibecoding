Feature: US-004 Daily Task Implementation
  As a developer
  I want to complete data persistence tasks incrementally
  So that I can deliver value continuously and manage complexity

  # Day 1: Foundation & Setup Tasks
  
  Scenario: US-004-001 - Deploy DynamoDB table via CloudFormation
    Given I have a CloudFormation template for the VibeDigest table
    And AWS credentials are configured for the dev environment
    When I deploy the CloudFormation stack
    Then a DynamoDB table named "VibeDigest-dev" should be created
    And the table should have partition key "digest_date" of type String
    And the table should have sort key "item_id" of type String
    And the table should use PAY_PER_REQUEST billing mode
    And the table status should be "ACTIVE" within 2 minutes

  Scenario: US-004-002 - Database package structure exists and imports correctly
    Given the src/database directory exists
    And the __init__.py file exists in src/database
    And the client.py module exists with DynamoDBClient class skeleton
    When I run "python -c 'from src.database.client import DynamoDBClient'"
    Then no import errors should occur
    And the DynamoDBClient class should be importable
    And boto3 should be added to requirements.txt

  Scenario: US-004-003 - Basic DynamoDB connection works
    Given AWS credentials are configured correctly
    And the DynamoDB table "VibeDigest-dev" exists
    When I create a DynamoDBClient instance
    And I call the test_connection method
    Then the connection should succeed
    And the table description should be retrievable
    And connection logs should be generated

  # Day 2: Basic Write Operations

  Scenario: US-004-004 - Single item write operation
    Given a DynamoDBClient is connected to the test table
    And I have a DigestItem with title "Test Article"
    When I call put_item with the digest item and date "2024-06-08"
    Then the item should be stored successfully in DynamoDB
    And no exceptions should be raised
    And the stored item should have all required fields

  Scenario: US-004-005 - Unique ID generation for digest items
    Given I have two DigestItems with different URLs
    When I generate item IDs for both items using the same date
    Then the generated IDs should be different
    And each ID should follow the format "date#source#hash"
    And the same item should always generate the same ID

  Scenario: US-004-006 - Main workflow includes persistence
    Given persistence is enabled via configuration
    And the DynamoDB table is accessible
    When the digest generation workflow runs
    Then digest items should be persisted to the database
    And the email should still be sent successfully
    And persistence logs should be generated

  # Day 3: Error Handling & Reliability

  Scenario: US-004-007 - Graceful handling of database failures
    Given the digest generation process is running
    And the DynamoDB service is unavailable
    When the persistence operation is attempted
    Then an error should be logged with appropriate context
    But the email digest should still be sent
    And the system should remain stable

  Scenario: US-004-008 - Retry logic for transient failures
    Given the DynamoDB service fails twice then succeeds
    When I attempt to store a digest item
    Then the operation should retry up to 3 times
    And the final attempt should succeed
    And all retry attempts should be logged
    And exponential backoff should be applied

  Scenario: US-004-009 - Feature flag controls persistence
    Given the ENABLE_PERSISTENCE environment variable is set to "false"
    When the digest generation process runs
    Then no database operations should be attempted
    And a skip message should be logged
    And the email should still be sent normally

  # Day 4: Batch Operations

  Scenario: US-004-010 - Batch write operations for multiple items
    Given I have 30 digest items to store
    When I call batch_write_items with all items
    Then all 30 items should be stored successfully
    And the operation should use 2 batch requests (25 item limit)
    And no items should be lost during batching
    And batch operation metrics should be recorded

  Scenario: US-004-011 - Main workflow uses batch operations
    Given a digest contains 40 items
    And persistence is enabled
    When the digest generation process runs
    Then batch_write_items should be called instead of individual puts
    And all 40 items should be stored successfully
    And performance should be measurably improved

  # Day 5: Basic Retrieval

  Scenario: US-004-012 - Query digest items by date
    Given digest items exist in the database for date "2024-06-08"
    When I query for items with that date
    Then all items for that date should be returned
    And each item should have all required fields
    And the query should complete within 5 seconds

  Scenario: US-004-013 - CLI command for digest retrieval
    Given digest items exist for date "2024-06-08"
    When I run "python -m src.vibe_digest --retrieve-date 2024-06-08"
    Then the stored items should be printed to console
    And the output should be human-readable
    And invalid date formats should be handled gracefully

  # Day 6: Monitoring & Observability

  Scenario: US-004-014 - CloudWatch metrics are published
    Given a persistence operation succeeds
    When the operation completes
    Then a "PersistenceSuccess" metric should be published to CloudWatch
    And the operation latency should be recorded
    And the metric should include appropriate dimensions

  Scenario: US-004-015 - Structured logging for operations
    Given persistence operations are running
    When any database operation occurs
    Then logs should be output in JSON format
    And logs should include operation type, date, and item count
    And correlation IDs should be present for request tracking