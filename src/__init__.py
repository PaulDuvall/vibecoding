"""
Vibe Coding Digest Package

An automated content aggregation and summarization tool that delivers
curated, daily email digests of the most relevant developments in AI,
developer tools, and emerging technology.
"""

from src.vibe_digest import main as run_digest, validate_environment
from src.models import DigestItem
from src.feeds import FEEDS, FEED_SOURCES, fetch_all_feed_items_concurrently
from src.summarize import summarize
from src.email_utils import send_email
from src.aws_blog_search import fetch_aws_blog_posts
from src.config import DigestConfig, SummarizationRequest, get_config, set_config

__version__ = "1.0.0"
__author__ = "Paul Duvall"

__all__ = [
    "run_digest",
    "validate_environment",
    "DigestItem",
    "FEEDS",
    "FEED_SOURCES",
    "fetch_all_feed_items_concurrently",
    "summarize",
    "send_email",
    "fetch_aws_blog_posts",
    "DigestConfig",
    "SummarizationRequest",
    "get_config",
    "set_config"
]