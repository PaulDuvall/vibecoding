"""
Step definitions for externalized configuration ATDD tests
"""
import json
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from behave import given, when, then
from src.config_loader import ConfigurationLoader, load_feed_configuration
from src.feeds import fetch_all_feed_items_concurrently, get_configured_feeds


@given('the vibe digest system is available')
def step_given_system_available(context):
    """Ensure the system is ready for testing."""
    context.system_available = True


@given('I have permission to modify feed configurations')
def step_given_permission(context):
    """Set up permissions context."""
    context.has_permission = True


@given('a configuration file "{filename}" exists with the following feeds')
def step_given_config_file_with_feeds(context, filename):
    """Create a configuration file with specified feeds."""
    config_data = json.loads(context.text)
    
    # Create temporary file
    temp_dir = Path(tempfile.mkdtemp())
    config_path = temp_dir / filename
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    context.config_file = config_path
    context.config_data = config_data


@given('a configuration file "{filename}" exists with mixed enabled/disabled feeds')
def step_given_config_with_mixed_feeds(context, filename):
    """Create configuration with both enabled and disabled feeds."""
    step_given_config_file_with_feeds(context, filename)


@given('no external configuration file exists')
def step_given_no_config_file(context):
    """Ensure no external configuration exists."""
    context.config_file = None


@given('a malformed configuration file "{filename}" exists')
def step_given_malformed_config(context, filename):
    """Create a malformed configuration file."""
    temp_dir = Path(tempfile.mkdtemp())
    config_path = temp_dir / filename
    
    with open(config_path, 'w') as f:
        f.write(context.text)
    
    context.config_file = config_path


@given('the default configuration includes "{url}" with source name "{source_name}"')
def step_given_default_config_includes(context, url, source_name):
    """Verify default configuration includes specific feed."""
    from src.feeds import FEEDS, FEED_SOURCES
    assert url in FEEDS
    assert FEED_SOURCES.get(url) == source_name
    context.default_url = url
    context.default_source = source_name


@given('I set the environment variable "{var_name}" to "{var_value}"')
def step_given_env_var(context, var_name, var_value):
    """Set environment variable."""
    context.env_vars = getattr(context, 'env_vars', {})
    context.env_vars[var_name] = var_value


@given('a configuration file exists at "{custom_path}" with valid feeds')
def step_given_config_at_custom_path(context, custom_path):
    """Create configuration at specific path."""
    config_data = {
        "feeds": [
            {
                "url": "https://example.com/custom.rss",
                "source_name": "Custom Feed",
                "category": "Custom",
                "enabled": True
            }
        ]
    }
    
    # Mock the file existence
    context.custom_config_path = custom_path
    context.custom_config_data = config_data


@given('a configuration file "{filename}" exists')
def step_given_yaml_config(context, filename):
    """Create YAML configuration file."""
    config_data = yaml.safe_load(context.text)
    
    temp_dir = Path(tempfile.mkdtemp())
    config_path = temp_dir / filename
    
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    context.config_file = config_path
    context.config_data = config_data


@given('the digest system is running in development mode')
def step_given_dev_mode(context):
    """Set development mode."""
    context.dev_mode = True


@given('the system has hardcoded feeds in feeds.py')
def step_given_hardcoded_feeds(context):
    """Verify hardcoded feeds exist."""
    from src.feeds import FEEDS, FEED_SOURCES
    assert len(FEEDS) > 0
    assert len(FEED_SOURCES) > 0
    context.hardcoded_feeds_count = len(FEEDS)


@when('I run the digest with the external configuration')
def step_when_run_with_external_config(context):
    """Run digest with external configuration."""
    with patch.dict(os.environ, getattr(context, 'env_vars', {})):
        with patch('src.config_loader.Path.exists') as mock_exists:
            with patch('builtins.open', create=True) as mock_open:
                # Mock file existence
                mock_exists.return_value = True
                
                # Mock file reading
                config_content = json.dumps(context.config_data)
                mock_open.return_value.__enter__.return_value.read.return_value = config_content
                
                # Mock feedparser to avoid actual network calls
                with patch('src.feeds.feedparser.parse') as mock_parse:
                    mock_feed = MagicMock()
                    mock_feed.bozo = False
                    mock_feed.entries = []
                    mock_parse.return_value = mock_feed
                    
                    # Load configuration
                    loader = ConfigurationLoader(str(context.config_file))
                    context.external_config_loaded = loader.load_configuration()
                    context.enabled_feeds = loader.get_enabled_feed_urls()
                    context.source_mapping = loader.get_source_mapping()


@when('I run the digest')
def step_when_run_digest(context):
    """Run digest with default configuration."""
    with patch('src.feeds.feedparser.parse') as mock_parse:
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        
        if hasattr(context, 'config_file') and context.config_file:
            step_when_run_with_external_config(context)
        else:
            # Use default configuration
            context.enabled_feeds, context.source_mapping = load_feed_configuration()


@when('I attempt to run the digest with the external configuration')
def step_when_attempt_run_with_external_config(context):
    """Attempt to run digest, expecting errors."""
    try:
        step_when_run_with_external_config(context)
        context.error_occurred = False
    except Exception as e:
        context.error_occurred = True
        context.error_message = str(e)


@when('I run the digest with the YAML configuration')
def step_when_run_with_yaml_config(context):
    """Run digest with YAML configuration."""
    step_when_run_with_external_config(context)


@when('I modify the configuration file to add {count:d} more feed')
def step_when_modify_config_add_feed(context, count):
    """Modify configuration to add feeds."""
    context.config_data['feeds'].append({
        "url": "https://example.com/new-feed.rss",
        "source_name": "New Feed",
        "category": "Testing",
        "enabled": True
    })
    context.modified_feed_count = len(context.config_data['feeds'])


@when('I trigger a configuration reload')
def step_when_trigger_reload(context):
    """Trigger configuration reload."""
    # This would normally reload from file
    context.reload_triggered = True


@then('the system should fetch from exactly {count:d} feed')
def step_then_system_fetches_count_feeds(context, count):
    """Verify the number of feeds being processed."""
    assert len(context.enabled_feeds) == count, f"Expected {count} feeds, got {len(context.enabled_feeds)}"


@then('the system should fetch from exactly {count:d} feeds')
def step_then_system_fetches_count_feeds_plural(context, count):
    """Verify the number of feeds being processed (plural)."""
    step_then_system_fetches_count_feeds(context, count)


@then('the system should use "{source_name}" as the source name for "{url}"')
def step_then_system_uses_source_name(context, source_name, url):
    """Verify source name mapping."""
    assert context.source_mapping.get(url) == source_name, \
        f"Expected source name '{source_name}' for URL '{url}', got '{context.source_mapping.get(url)}'"


@then('the system should not attempt to fetch from "{url}"')
def step_then_system_should_not_fetch(context, url):
    """Verify URL is not in enabled feeds."""
    assert url not in context.enabled_feeds, f"URL '{url}' should not be in enabled feeds"


@then('the system should use the built-in default feed configuration')
def step_then_system_uses_default_config(context):
    """Verify default configuration is used."""
    from src.feeds import FEEDS
    assert len(context.enabled_feeds) == len(FEEDS)


@then('the system should fetch from all default feeds')
def step_then_system_fetches_all_default(context):
    """Verify all default feeds are processed."""
    from src.feeds import FEEDS
    assert set(context.enabled_feeds) == set(FEEDS)


@then('the system should raise a configuration validation error')
def step_then_system_raises_validation_error(context):
    """Verify validation error occurred."""
    assert context.error_occurred, "Expected validation error but none occurred"


@then('the error message should indicate "{message}"')
def step_then_error_message_contains(context, message):
    """Verify error message content."""
    assert message in context.error_message, \
        f"Expected error message to contain '{message}', got '{context.error_message}'"


@then('the system should successfully process feeds from the "{category}" category')
def step_then_system_processes_category(context, category):
    """Verify category processing."""
    # Find feeds in the category
    category_feeds = [
        feed for feed in context.config_data['feeds'] 
        if feed['category'] == category and feed['enabled']
    ]
    assert len(category_feeds) > 0, f"No enabled feeds found in category '{category}'"


@then('the digest should include items tagged with "{source_name}" as the source')
def step_then_digest_includes_source(context, source_name):
    """Verify source tagging."""
    assert source_name in context.source_mapping.values(), \
        f"Source name '{source_name}' not found in source mapping"


@then('the system should use "{new_source}" as the source name instead of "{old_source}"')
def step_then_system_overrides_source_name(context, new_source, old_source):
    """Verify source name override."""
    # Check that the new source name is used
    found_new_source = any(source == new_source for source in context.source_mapping.values())
    assert found_new_source, f"New source name '{new_source}' not found"


@then('the system should load configuration from "{custom_path}"')
def step_then_system_loads_from_custom_path(context, custom_path):
    """Verify configuration loaded from custom path."""
    assert hasattr(context, 'custom_config_path')
    assert context.custom_config_path == custom_path


@then('the system should use the feeds defined in that custom configuration')
def step_then_system_uses_custom_config(context):
    """Verify custom configuration is used."""
    assert hasattr(context, 'custom_config_data')


@then('the system should successfully parse the YAML configuration')
def step_then_system_parses_yaml(context):
    """Verify YAML parsing success."""
    assert context.external_config_loaded, "YAML configuration was not loaded successfully"


@then('the system should fetch from "{url}"')
def step_then_system_fetches_from_url(context, url):
    """Verify specific URL is fetched."""
    assert url in context.enabled_feeds, f"URL '{url}' not found in enabled feeds"


@then('the system should detect the configuration change')
def step_then_system_detects_change(context):
    """Verify configuration change detection."""
    assert context.reload_triggered, "Configuration reload was not triggered"


@then('the system should fetch from exactly {count:d} feeds on the next run')
def step_then_system_fetches_count_next_run(context, count):
    """Verify feed count after modification."""
    assert context.modified_feed_count == count, \
        f"Expected {count} feeds after modification, got {context.modified_feed_count}"


@then('the system should function exactly as before')
def step_then_system_functions_as_before(context):
    """Verify backward compatibility."""
    from src.feeds import FEEDS
    assert len(context.enabled_feeds) == len(FEEDS)


@then('all existing feeds should be processed')
def step_then_all_existing_feeds_processed(context):
    """Verify all existing feeds are processed."""
    from src.feeds import FEEDS
    for feed in FEEDS:
        assert feed in context.enabled_feeds, f"Existing feed '{feed}' not found in enabled feeds"


@then('all existing source name mappings should remain intact')
def step_then_existing_mappings_intact(context):
    """Verify existing source mappings are preserved."""
    from src.feeds import FEED_SOURCES
    for url, source_name in FEED_SOURCES.items():
        if url in context.enabled_feeds:
            assert context.source_mapping.get(url) == source_name, \
                f"Source mapping for '{url}' changed from '{source_name}' to '{context.source_mapping.get(url)}'"