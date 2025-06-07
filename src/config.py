"""
Configuration management for Vibe Coding Digest.

This module provides centralized configuration management to address
primitive obsession and hardcoded values throughout the codebase.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DigestConfig:
    """Central configuration for digest processing."""
    
    # Content processing limits
    max_items: int = 15
    max_feed_items_per_source: int = 3
    max_sources: int = 10
    
    # OpenAI configuration
    openai_timeout: int = 30
    openai_max_tokens: int = 300
    openai_temperature: float = 0.7
    openai_model: str = "gpt-4o"
    openai_max_concurrent: int = 5
    openai_batch_size: int = 3
    openai_max_retries: int = 3
    
    # Text processing
    max_text_length: int = 8000
    cache_size_limit: int = 1000
    cache_cleanup_size: int = 100
    
    # Network configuration
    request_timeout: int = 30
    max_feed_workers: int = 10
    
    # Email configuration
    email_timeout: int = 30
    
    @classmethod
    def from_environment(cls) -> 'DigestConfig':
        """Create configuration from environment variables with defaults."""
        return cls(
            max_items=int(os.getenv('DIGEST_MAX_ITEMS', cls.max_items)),
            max_feed_items_per_source=int(os.getenv('DIGEST_MAX_FEED_ITEMS', cls.max_feed_items_per_source)),
            max_sources=int(os.getenv('DIGEST_MAX_SOURCES', cls.max_sources)),
            
            openai_timeout=int(os.getenv('OPENAI_TIMEOUT', cls.openai_timeout)),
            openai_max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', cls.openai_max_tokens)),
            openai_temperature=float(os.getenv('OPENAI_TEMPERATURE', cls.openai_temperature)),
            openai_model=os.getenv('OPENAI_MODEL', cls.openai_model),
            openai_max_concurrent=int(os.getenv('OPENAI_MAX_CONCURRENT', cls.openai_max_concurrent)),
            openai_batch_size=int(os.getenv('OPENAI_BATCH_SIZE', cls.openai_batch_size)),
            openai_max_retries=int(os.getenv('OPENAI_MAX_RETRIES', cls.openai_max_retries)),
            
            max_text_length=int(os.getenv('DIGEST_MAX_TEXT_LENGTH', cls.max_text_length)),
            cache_size_limit=int(os.getenv('OPENAI_CACHE_SIZE_LIMIT', cls.cache_size_limit)),
            cache_cleanup_size=int(os.getenv('OPENAI_CACHE_CLEANUP_SIZE', cls.cache_cleanup_size)),
            
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', cls.request_timeout)),
            max_feed_workers=int(os.getenv('MAX_FEED_WORKERS', cls.max_feed_workers)),
            
            email_timeout=int(os.getenv('EMAIL_TIMEOUT', cls.email_timeout)),
        )


@dataclass
class SummarizationRequest:
    """Data structure for summarization requests to replace tuple-based data clumps."""
    
    text: str
    source_name: str
    source_url: str
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        if not self.source_name.strip():
            raise ValueError("Source name cannot be empty")
        if not self.source_url.strip():
            raise ValueError("Source URL cannot be empty")


# Global configuration instance
_config: Optional[DigestConfig] = None


def get_config() -> DigestConfig:
    """Get the global configuration instance, creating it if necessary."""
    global _config
    if _config is None:
        _config = DigestConfig.from_environment()
    return _config


def set_config(config: DigestConfig) -> None:
    """Set a custom configuration (mainly for testing)."""
    global _config
    _config = config