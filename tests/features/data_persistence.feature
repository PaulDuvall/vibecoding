Feature: US-004 - Data Persistence of Digests
  As a system operator
  I want each day's fetched feed and website summaries to be persisted in an AWS database
  So that historical digests are reliably stored and retrievable

  Background:
    Given the system has valid AWS credentials for database access
    And the DynamoDB table "VibeDigest" exists and is accessible

  Scenario: US-004 - Successfully persist daily digest to database
    Given a daily digest has been generated with multiple articles
    And the digest includes articles from different sources with timestamps
    And the digest contains the following sample data:
      | source      | title              | url                              | summary                          | timestamp             |
      | AWS Blog    | New AI Service     | https://aws.amazon.com/blog/ai   | Revolutionary AI service launched | 2024-06-08T10:00:00Z |
      | OpenAI Blog | GPT Update         | https://openai.com/blog/update   | Latest GPT improvements          | 2024-06-08T11:00:00Z |
    When the digest persistence process is executed for date "2024-06-08"
    Then each digest item should be stored in the database with a date key "2024-06-08"
    And the stored data should include feed source, title, URL, summary, and timestamp
    And the digest should be retrievable using the date key "2024-06-08"
    And the persistence operation should complete within 30 seconds
    And the data should be persisted with at least 99.9% durability

  Scenario: US-004 - Handle database write failures gracefully
    Given the system has generated a valid daily digest
    And the database service is temporarily unavailable
    When the digest persistence process is executed
    Then the system should retry the database write operation up to 3 times
    And failure logs should be generated for monitoring
    And the digest generation should not be blocked by persistence failures
    And the email digest should still be sent successfully
    And an alert should be triggered for the operations team

  Scenario: US-004 - Retrieve historical digest data
    Given historical digest data exists for previous dates:
      | date       | item_count | sources                              |
      | 2024-06-07 | 15         | AWS Blog, OpenAI Blog, GitHub Blog   |
      | 2024-06-06 | 12         | AWS Blog, TechCrunch                 |
    When a request is made to retrieve digest data for date "2024-06-07"
    Then the complete digest for that date should be returned
    And the data should include all required fields (source, title, URL, summary, timestamp)
    And the response should contain exactly 15 digest items
    And the retrieval should complete within 5 seconds

  Scenario: US-004 - Handle duplicate digest items gracefully
    Given a digest item with the same URL already exists for the current date
    When the persistence process encounters the duplicate item
    Then the system should update the existing item with newer timestamp
    And no duplicate entries should be created in the database
    And a log entry should record the duplicate handling

  Scenario: US-004 - Validate data integrity before persistence
    Given a digest contains items with missing required fields:
      | field_missing | item_count |
      | title         | 2          |
      | url           | 1          |
      | summary       | 0          |
    When the digest persistence process is executed
    Then items with missing critical fields should be logged but not stored
    And valid items should be stored successfully
    And a data quality report should be generated
    And the system should continue processing remaining valid items

  Scenario: US-004 - Handle large digest volumes efficiently
    Given a daily digest contains more than 100 articles
    And the total data size exceeds 1MB
    When the digest persistence process is executed
    Then the data should be stored using batch operations
    And the operation should complete within 60 seconds
    And no items should be lost during the batch processing
    And memory usage should remain below 512MB during processing