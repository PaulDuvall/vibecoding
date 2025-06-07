"""
config_loader.py - External configuration loading for feed management
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class FeedConfig:
    """Represents a single feed configuration."""
    
    def __init__(self, url: str, source_name: str, category: str = "General", enabled: bool = True):
        self.url = url
        self.source_name = source_name
        self.category = category
        self.enabled = enabled
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FeedConfig':
        """Create FeedConfig from dictionary."""
        return cls(
            url=data['url'],
            source_name=data['source_name'],
            category=data.get('category', 'General'),
            enabled=data.get('enabled', True)
        )
    
    def to_dict(self) -> Dict:
        """Convert FeedConfig to dictionary."""
        return {
            'url': self.url,
            'source_name': self.source_name,
            'category': self.category,
            'enabled': self.enabled
        }


class ConfigurationLoader:
    """Handles loading and validation of externalized feed configurations."""
    
    DEFAULT_CONFIG_PATHS = [
        'feeds_config.json',
        'feeds_config.yaml',
        'feeds_config.yml',
        'config/feeds.json',
        'config/feeds.yaml'
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._feeds: List[FeedConfig] = []
        self._source_mapping: Dict[str, str] = {}
    
    def load_configuration(self) -> bool:
        """
        Load configuration from external file or environment variable.
        Returns True if external config was loaded, False if using defaults.
        """
        config_file = self._find_config_file()
        
        if not config_file:
            logging.info("No external configuration found, using built-in defaults")
            return False
        
        try:
            config_data = self._parse_config_file(config_file)
            self._validate_configuration(config_data)
            self._load_feeds_from_config(config_data)
            logging.info(f"Successfully loaded configuration from {config_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to load configuration from {config_file}: {e}")
            raise ValueError(f"Invalid configuration format: {e}")
    
    def _find_config_file(self) -> Optional[Path]:
        """Find the configuration file to use."""
        # Check environment variable first
        env_path = os.getenv('VIBE_CONFIG_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Check explicit config path
        if self.config_path and Path(self.config_path).exists():
            return Path(self.config_path)
        
        # Check default paths
        for default_path in self.DEFAULT_CONFIG_PATHS:
            path = Path(default_path)
            if path.exists():
                return path
        
        return None
    
    def _parse_config_file(self, config_file: Path) -> Dict:
        """Parse configuration file based on extension."""
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_file.suffix.lower() == '.json':
                return json.load(f)
            else:
                # Try JSON first, then YAML
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return yaml.safe_load(content)
    
    def _validate_configuration(self, config_data: Dict) -> None:
        """Validate the configuration structure."""
        if not isinstance(config_data, dict):
            raise ValueError("Configuration must be a dictionary")
        
        if 'feeds' not in config_data:
            raise ValueError("Configuration must contain 'feeds' key")
        
        if not isinstance(config_data['feeds'], list):
            raise ValueError("'feeds' must be a list")
        
        for i, feed in enumerate(config_data['feeds']):
            if not isinstance(feed, dict):
                raise ValueError(f"Feed {i} must be a dictionary")
            
            required_fields = ['url', 'source_name']
            for field in required_fields:
                if field not in feed:
                    raise ValueError(f"Feed {i} missing required field: {field}")
            
            if not isinstance(feed['url'], str) or not feed['url'].strip():
                raise ValueError(f"Feed {i} has invalid URL")
            
            if not isinstance(feed['source_name'], str) or not feed['source_name'].strip():
                raise ValueError(f"Feed {i} has invalid source_name")
    
    def _load_feeds_from_config(self, config_data: Dict) -> None:
        """Load feeds from validated configuration data."""
        self._feeds = []
        self._source_mapping = {}
        
        for feed_data in config_data['feeds']:
            feed_config = FeedConfig.from_dict(feed_data)
            if feed_config.enabled:
                self._feeds.append(feed_config)
                self._source_mapping[feed_config.url] = feed_config.source_name
    
    def get_enabled_feed_urls(self) -> List[str]:
        """Get list of enabled feed URLs."""
        return [feed.url for feed in self._feeds if feed.enabled]
    
    def get_source_mapping(self) -> Dict[str, str]:
        """Get mapping from feed URL to source name."""
        return self._source_mapping.copy()
    
    def get_feeds_by_category(self, category: str) -> List[FeedConfig]:
        """Get feeds filtered by category."""
        return [feed for feed in self._feeds if feed.category == category and feed.enabled]
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories."""
        return list(set(feed.category for feed in self._feeds))
    
    def reload_configuration(self) -> bool:
        """Reload configuration from file (useful for development)."""
        return self.load_configuration()
    
    def export_default_config(self, output_path: str) -> None:
        """Export current hardcoded configuration to external file for migration."""
        from src.feeds import FEEDS, FEED_SOURCES
        
        default_feeds = []
        for url in FEEDS:
            source_name = FEED_SOURCES.get(url, "Unknown Source")
            # Categorize based on URL patterns
            category = self._categorize_url(url)
            default_feeds.append({
                'url': url,
                'source_name': source_name,
                'category': category,
                'enabled': True
            })
        
        config = {'feeds': default_feeds}
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            if output_file.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            else:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Default configuration exported to {output_path}")
    
    def _categorize_url(self, url: str) -> str:
        """Categorize a feed URL based on patterns."""
        url_lower = url.lower()
        
        if any(term in url_lower for term in ['openai', 'anthropic', 'ai', 'machine', 'artificial']):
            return 'AI'
        elif any(term in url_lower for term in ['github', 'programming', 'dev', 'coding']):
            return 'DevTools'
        elif 'youtube' in url_lower:
            return 'YouTube'
        elif any(term in url_lower for term in ['reddit', 'hn', 'hacker']):
            return 'Community'
        elif 'blog' in url_lower:
            return 'Blogs'
        else:
            return 'General'


def load_feed_configuration(config_path: Optional[str] = None) -> tuple[List[str], Dict[str, str]]:
    """
    Convenience function to load feed configuration.
    Returns (feed_urls, source_mapping) tuple.
    """
    loader = ConfigurationLoader(config_path)
    has_external_config = loader.load_configuration()
    
    if has_external_config:
        return loader.get_enabled_feed_urls(), loader.get_source_mapping()
    else:
        # Fallback to hardcoded configuration
        from src.feeds import FEEDS, FEED_SOURCES
        return FEEDS, FEED_SOURCES