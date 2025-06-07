"""
Vibe Coding Digest Script: fetch, summarize, and email daily digests.
"""

import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict

import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

from src.feeds import fetch_all_feed_items_concurrently
from src.config_loader import load_feed_configuration
from src.models import DigestItem
from src.summarize import summarize, summarize_concurrent, batch_summarize
from src.email_utils import send_email
from src.config import get_config, SummarizationRequest

# Optionally import fetch_aws_blog_posts for testability
try:
    from src.aws_blog_search import fetch_aws_blog_posts  # type: ignore
except ImportError:
    logging.warning("aws_blog_search.py not found—skipping AWS Blog items.")
    fetch_aws_blog_posts = None  # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def fetch_single_feed(url):
    """Fetches and parses a single RSS/Atom feed."""
    logging.info(f"Fetching feed: {url}")
    digest_items = []
    feed = feedparser.parse(url)

    if feed.bozo and isinstance(feed.bozo_exception, feedparser.http.FeedHttpError):
        logging.warning(f"Retriable parse error for {url}: {feed.bozo_exception}")
        raise Exception("Retriable feed parse error")

    # Get source mapping from configuration
    _, source_mapping = load_feed_configuration()
    source_name = source_mapping.get(url, "Unknown Source")
    for entry in feed.entries[:3]:
        link = getattr(entry, "link", None) or entry.get("feedburner_origlink")
        if not link:
            logging.warning(f"Skipping {source_name} entry with no link: {entry}")
            continue

        title = getattr(entry, "title", "No Title")
        summary = entry.get("summary") or entry.get("description", "")
        published = getattr(entry, "published_parsed", None)
        author = getattr(entry, "author", None)

        digest_items.append(
            DigestItem(
                title=title,
                link=link,
                summary=summary,
                source_name=source_name,
                source_url=url,
                published_date=published,
                author=author,
            )
        )

    logging.info(f"Fetched {len(digest_items)} items from {source_name}")
    return digest_items


def fetch_claude_release_notes_scraper():
    """
    A placeholder scraper for Claude Release Notes.
    In production, replace with BeautifulSoup-based parsing, rate-limit handling, etc.
    """
    url = "https://docs.anthropic.com/claude/docs/claude-release-notes"
    logging.info(f"Scraping Claude Release Notes from: {url}")
    # TODO: real scraping logic here
    return []


def format_digest(summaries_by_source):
    """Format the digest into HTML and Markdown, grouped by source."""
    now_et = datetime.now(tz=ZoneInfo("America/New_York"))
    now_str = now_et.strftime("%B %d, %Y %-I:%M %p %Z")
    html = f"<h2>🧠 Vibe Coding Digest – {now_str}</h2>"
    md = f"## 🧠 Vibe Coding Digest – {now_str}\n"

    for source, items in summaries_by_source.items():
        html += f"<h3>{source}</h3><ul>"
        md += f"\n### {source}\n"
        for summary in items:
            html += f"<li>{summary}</li>"
            md += f"- {summary}\n"
        html += "</ul>"

    return html, md


def validate_environment():
    required = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "EMAIL_TO": os.getenv("EMAIL_TO"),
        "EMAIL_FROM": os.getenv("EMAIL_FROM"),
        "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY"),
    }
    for var, val in required.items():
        if not val:
            logging.error(f"Missing required environment variable: {var}")
            sys.exit(1)


def gather_feed_items():
    """Load feeds from external configuration and fetch items."""
    feed_urls, _ = load_feed_configuration()
    logging.info(f"Loading {len(feed_urls)} feeds from configuration")
    return fetch_all_feed_items_concurrently(feed_urls)


def add_aws_blog_posts(all_items):
    if fetch_aws_blog_posts:
        try:
            aws_posts = fetch_aws_blog_posts()
            if aws_posts:
                for post in aws_posts:
                    all_items.append(
                        DigestItem(
                            title=post["title"],
                            link=post["link"],
                            summary=post["summary"],
                            source_name="AWS Blog",
                            source_url="https://aws.amazon.com/blogs/aws/",
                            published_date=None,
                            author=None,
                        )
                    )
                logging.info(f"Added {len(aws_posts)} AWS Blog items.")
        except Exception as exc:
            logging.error(f"AWS Blog fetch failed: {exc}")


def add_claude_release_notes(all_items):
    for item in fetch_claude_release_notes_scraper():
        all_items.append(item)


def dedupe_and_sort_items(all_items):
    unique_items = list(dict.fromkeys(all_items))
    unique_items.sort(
        key=lambda x: x.published_date or datetime.min.timetuple(),
        reverse=True,
    )
    return unique_items


def _prepare_summarization_requests(items: List[DigestItem]) -> List[SummarizationRequest]:
    """
    Convert DigestItem objects to SummarizationRequest objects.
    
    Refactoring: Extract Method to reduce complexity in summarize_items.
    """
    config = get_config()
    items_to_process = items[:config.max_items]
    
    requests = []
    for item in items_to_process:
        text = (
            f"Title: {item.title}\n"
            f"Link: {item.link}\n"
            f"Source: {item.source_name}\n"
            f"Published: {item.published_date or 'N/A'}\n"
            f"Author: {item.author or 'N/A'}\n"
            f"Content: {item.summary}"
        )
        try:
            request = SummarizationRequest(text, item.source_name, item.link)
            requests.append(request)
        except ValueError as e:
            logging.warning(f"Skipping invalid item: {e}")
            continue
    
    return requests


def _try_batch_summarization(requests: List[SummarizationRequest], api_key: str) -> Dict[str, List[str]]:
    """
    Attempt batch summarization strategy.
    
    Refactoring: Extract Method to reduce duplicate error handling.
    """
    config = get_config()
    summaries = {}
    
    if len(requests) < config.openai_batch_size:
        raise ValueError(f"Not enough items for batching (need {config.openai_batch_size})")
    
    logging.info(f"Using batch summarization for {len(requests)} items")
    
    # Convert requests back to tuples for existing batch_summarize function
    items_for_batch = [(req.text, req.source_name, req.source_url) for req in requests]
    batch_results = batch_summarize(items_for_batch, api_key, batch_size=config.openai_batch_size)
    
    # Group results by source
    for idx, request in enumerate(requests):
        if idx < len(batch_results):
            summary = batch_results[idx]
            summaries.setdefault(request.source_name, []).append(summary)
        else:
            summaries.setdefault(request.source_name, []).append(f"[Summary unavailable for {request.source_name}]")
    
    return summaries


def _try_concurrent_summarization(requests: List[SummarizationRequest], api_key: str) -> Dict[str, List[str]]:
    """
    Attempt concurrent summarization strategy.
    
    Refactoring: Extract Method to reduce duplicate error handling.
    """
    config = get_config()
    summaries = {}
    
    logging.info(f"Using concurrent summarization for {len(requests)} items")
    
    # Convert requests back to tuples for existing summarize_concurrent function
    items_for_concurrent = [(req.text, req.source_name, req.source_url) for req in requests]
    concurrent_results = summarize_concurrent(
        items_for_concurrent,
        api_key,
        max_workers=config.openai_max_concurrent
    )
    
    # Group results by source
    for summary, source_name, source_url in concurrent_results:
        summaries.setdefault(source_name, []).append(summary)
    
    return summaries


def _fallback_sequential_summarization(requests: List[SummarizationRequest], api_key: str) -> Dict[str, List[str]]:
    """
    Fallback sequential summarization strategy.
    
    Refactoring: Extract Method to isolate fallback logic.
    """
    config = get_config()
    summaries = {}
    
    logging.info(f"Using sequential summarization for {len(requests)} items")
    
    for request in requests:
        try:
            summary = summarize(request.text, request.source_name, request.source_url, api_key)
            summaries.setdefault(request.source_name, []).append(summary)
        except Exception as exc:
            logging.error(f"Summarize failed for {request.source_name}: {exc}")
            summaries.setdefault(request.source_name, []).append(f"[Summary unavailable for {request.source_name}]")
        
        # Rate limiting for sequential processing
        if len(summaries) >= config.max_sources:
            logging.info(f"Reached source limit of {config.max_sources}, stopping sequential processing")
            break
    
    return summaries


def summarize_items(unique_items: List[DigestItem], use_concurrent: bool = True, use_batching: bool = False) -> Dict[str, List[str]]:
    """
    Summarize items using optimized OpenAI processing with configurable strategies.
    
    Refactoring: Simplified main method that delegates to extracted strategy methods.
    This addresses the Long Method code smell by breaking down a 77-line function
    into focused, single-responsibility methods.

    Args:
        unique_items: List of DigestItem objects
        use_concurrent: Use concurrent processing (recommended)
        use_batching: Use batch processing (experimental)

    Returns:
        Dictionary of summaries grouped by source
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logging.error("OPENAI_API_KEY not found")
        return {}
    
    requests = _prepare_summarization_requests(unique_items)
    if not requests:
        logging.warning("No valid items to summarize")
        return {}
    
    summaries = {}
    
    # Try batch summarization first if requested
    if use_batching:
        try:
            summaries = _try_batch_summarization(requests, openai_api_key)
            logging.info(f"Completed batch summarization for {len(summaries)} sources")
            return summaries
        except Exception as e:
            logging.error(f"Batch summarization failed: {e}, falling back to concurrent")
            use_concurrent = True
    
    # Try concurrent summarization
    if use_concurrent:
        try:
            summaries = _try_concurrent_summarization(requests, openai_api_key)
            logging.info(f"Completed concurrent summarization for {len(summaries)} sources")
            return summaries
        except Exception as e:
            logging.error(f"Concurrent summarization failed: {e}, falling back to sequential")
    
    # Fallback to sequential processing
    summaries = _fallback_sequential_summarization(requests, openai_api_key)
    logging.info(f"Completed sequential summarization for {len(summaries)} sources")
    return summaries


def generate_and_send_digest(summaries):
    html, md = format_digest(summaries)
    logging.info("\n--- Generated Markdown Digest ---\n%s\n--- End ---", md)
    try:
        send_email(html)
    except Exception as exc:
        logging.error(f"Email send failed: {exc}")
        sys.exit(1)


def main():
    """Main entry point: fetch, summarize, and send the digest."""
    validate_environment()
    all_items = gather_feed_items()
    add_aws_blog_posts(all_items)
    add_claude_release_notes(all_items)
    unique_items = dedupe_and_sort_items(all_items)
    summaries = summarize_items(unique_items)
    generate_and_send_digest(summaries)


if __name__ == "__main__":
    main()
