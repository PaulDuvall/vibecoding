Feature: Daily Digest Generation and Delivery
  As a content consumer interested in AI and developer tools
  I want to receive a daily email digest with curated, summarized content
  So that I can stay updated on the latest developments efficiently

  Background:
    Given the system has valid API keys for OpenAI and SendGrid
    And the recipient email is configured
    And RSS feeds are accessible

  Scenario: US-001 US-003 - Complete daily digest workflow execution
    Given multiple RSS feeds are available with recent content
    And the OpenAI API is responding normally
    And SendGrid email service is operational
    When the daily digest generation process is executed
    Then content should be fetched from all configured RSS feeds
    And articles should be summarized using OpenAI with Paul Duvall's voice
    And a properly formatted HTML email should be generated
    And the email should be sent successfully via SendGrid
    And the email subject should include the current date in Eastern Time
    And the email should contain content from multiple sources
    And each article should include source attribution and links

  Scenario: US-007 - Digest generation with some feed failures
    Given some RSS feeds are temporarily unavailable
    And other RSS feeds are accessible with content
    And the OpenAI API is responding normally
    And SendGrid email service is operational
    When the daily digest generation process is executed
    Then available feeds should be processed successfully
    And failed feeds should be logged but not stop the process
    And a digest should be generated with available content
    And the email should be sent successfully
    And the digest should indicate if some sources were unavailable

  Scenario: US-002 US-007 - OpenAI API rate limiting scenario
    Given RSS feeds are accessible with content
    And the OpenAI API returns rate limiting errors
    And SendGrid email service is operational
    When the daily digest generation process is executed
    Then the system should retry with exponential backoff
    And if retries fail, articles should use fallback summaries
    And the digest should still be generated and sent
    And the rate limiting should be logged appropriately

  Scenario: US-003 US-007 - Email delivery failure handling
    Given RSS feeds are accessible with content
    And articles are successfully summarized
    And SendGrid API returns delivery errors
    When the daily digest generation process is executed
    Then the digest content should be generated successfully
    And the email delivery failure should be logged
    And the system should attempt retry with exponential backoff
    And if delivery ultimately fails, the error should be properly reported

  Scenario: US-001 - Content deduplication across sources
    Given multiple RSS feeds contain the same article
    And the OpenAI API is responding normally
    And SendGrid email service is operational
    When the daily digest generation process is executed
    Then duplicate articles should be identified and removed
    And only unique content should be included in the digest
    And the most complete version of duplicate articles should be preserved
    And source attribution should reflect the primary source

  Scenario: US-001 - AWS blog search integration
    Given AWS blog search is configured with relevant queries
    And AWS RSS feeds are accessible
    And regular RSS feeds are also accessible
    And the OpenAI API is responding normally
    When the daily digest generation process is executed
    Then AWS-specific content should be fetched and included
    And AWS content should be properly integrated with other sources
    And duplicate content between AWS search and regular feeds should be removed
    And AWS content should be clearly labeled as such

  Scenario: US-003 - Mobile-optimized email formatting
    Given content has been successfully aggregated and summarized
    And the email generation process is executed
    When the HTML email is generated
    Then the email should have a responsive design for mobile devices
    And images should be properly sized for mobile viewing
    And links should be easily clickable on touch devices
    And the font size should be readable on small screens
    And the email structure should be compatible with major email clients

  Scenario: US-002 US-012 - Performance requirements for digest generation
    Given all RSS feeds are accessible (25+ sources)
    And the OpenAI API is responding normally
    And SendGrid email service is operational
    When the daily digest generation process is executed
    Then the entire process should complete within 5 minutes
    And feed fetching should be performed concurrently
    And the system should handle network timeouts gracefully
    And memory usage should remain within reasonable limits

  Scenario: US-002 - Digest content quality validation
    Given RSS feeds contain technical content about AI and developer tools
    And the OpenAI API is responding normally
    When articles are summarized
    Then summaries should preserve key technical information
    And summaries should maintain Paul Duvall's voice and style
    And summaries should include relevant emojis for categorization
    And summaries should be concise but informative (around 300 tokens)
    And links to original articles should be preserved and functional