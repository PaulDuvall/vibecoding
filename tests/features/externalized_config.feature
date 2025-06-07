Feature: US-301 US-302 US-303 US-304 US-305 - Externalized Feed Configuration
  As a content curator
  I want to externalize the feed configuration to a separate file
  So that I can easily modify, add, or remove feeds without changing the source code

  Background:
    Given the vibe digest system is available
    And I have permission to modify feed configurations

  Scenario: US-301 - Load feed configuration from external JSON file
    Given a configuration file "feeds_config.json" exists with the following feeds:
      """
      {
        "feeds": [
          {
            "url": "https://example.com/feed1.rss",
            "source_name": "Example Feed 1",
            "category": "AI",
            "enabled": true
          },
          {
            "url": "https://example.com/feed2.rss", 
            "source_name": "Example Feed 2",
            "category": "DevTools",
            "enabled": true
          }
        ]
      }
      """
    When I run the digest with the external configuration
    Then the system should fetch from exactly 2 feeds
    And the system should use "Example Feed 1" as the source name for "https://example.com/feed1.rss"
    And the system should use "Example Feed 2" as the source name for "https://example.com/feed2.rss"

  Scenario: US-303 - Handle disabled feeds in configuration
    Given a configuration file "feeds_config.json" exists with mixed enabled/disabled feeds:
      """
      {
        "feeds": [
          {
            "url": "https://example.com/enabled.rss",
            "source_name": "Enabled Feed",
            "category": "AI", 
            "enabled": true
          },
          {
            "url": "https://example.com/disabled.rss",
            "source_name": "Disabled Feed", 
            "category": "AI",
            "enabled": false
          }
        ]
      }
      """
    When I run the digest with the external configuration
    Then the system should fetch from exactly 1 feed
    And the system should not attempt to fetch from "https://example.com/disabled.rss"

  Scenario: US-301 - Fallback to default configuration when external config is missing
    Given no external configuration file exists
    When I run the digest
    Then the system should use the built-in default feed configuration
    And the system should fetch from all default feeds

  Scenario: US-305 - Validate configuration file format
    Given a malformed configuration file "feeds_config.json" exists:
      """
      {
        "invalid": "format"
      }
      """
    When I attempt to run the digest with the external configuration
    Then the system should raise a configuration validation error
    And the error message should indicate "Invalid configuration format"

  Scenario: US-303 - Add new feed category via external configuration
    Given a configuration file "feeds_config.json" exists with a new category:
      """
      {
        "feeds": [
          {
            "url": "https://blockchain.example.com/feed.rss",
            "source_name": "Blockchain News",
            "category": "Blockchain",
            "enabled": true
          }
        ]
      }
      """
    When I run the digest with the external configuration
    Then the system should successfully process feeds from the "Blockchain" category
    And the digest should include items tagged with "Blockchain News" as the source

  Scenario: US-301 - Override feed source names via configuration
    Given the default configuration includes "https://github.blog/feed/" with source name "GitHub Blog"
    And a configuration file "feeds_config.json" exists with an override:
      """
      {
        "feeds": [
          {
            "url": "https://github.blog/feed/",
            "source_name": "GitHub Official Blog",
            "category": "DevTools",
            "enabled": true
          }
        ]
      }
      """
    When I run the digest with the external configuration
    Then the system should use "GitHub Official Blog" as the source name instead of "GitHub Blog"

  Scenario: US-302 - Load configuration from environment variable path
    Given I set the environment variable "VIBE_CONFIG_PATH" to "/custom/path/feeds.json"
    And a configuration file exists at "/custom/path/feeds.json" with valid feeds
    When I run the digest
    Then the system should load configuration from "/custom/path/feeds.json"
    And the system should use the feeds defined in that custom configuration

  Scenario: US-301 - Support YAML configuration format
    Given a configuration file "feeds_config.yaml" exists:
      """
      feeds:
        - url: "https://example.com/yaml-feed.rss"
          source_name: "YAML Test Feed"
          category: "Testing"
          enabled: true
      """
    When I run the digest with the YAML configuration
    Then the system should successfully parse the YAML configuration
    And the system should fetch from "https://example.com/yaml-feed.rss"

  Scenario: US-305 - Configuration file hot-reload during development
    Given a configuration file "feeds_config.json" exists with 2 feeds
    And the digest system is running in development mode
    When I modify the configuration file to add 1 more feed
    And I trigger a configuration reload
    Then the system should detect the configuration change
    And the system should fetch from exactly 3 feeds on the next run

  Scenario: US-304 - Preserve backward compatibility with hardcoded feeds
    Given the system has hardcoded feeds in feeds.py
    And no external configuration file is provided
    When I run the digest
    Then the system should function exactly as before
    And all existing feeds should be processed
    And all existing source name mappings should remain intact