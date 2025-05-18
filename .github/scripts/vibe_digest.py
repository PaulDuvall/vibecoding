"""
Vibe Coding Digest Script: fetch, summarize, and email daily digests.
"""

import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

from feeds import FEED_SOURCES, FEEDS, fetch_all_feed_items_concurrently
from models import DigestItem
from summarize import summarize
from email_utils import send_email

# Optionally import fetch_aws_blog_posts for testability
try:
    from aws_blog_search import fetch_aws_blog_posts  # type: ignore
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

    source_name = FEED_SOURCES.get(url, "Unknown Source")
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


def main():
    """Main entry point: fetch, summarize, and send the digest."""
    # Validate environment
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

    # Fetch feeds
    all_items = fetch_all_feed_items_concurrently(FEEDS)

    # Optionally add AWS Blog posts
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

    # Add scraped Claude notes
    for item in fetch_claude_release_notes_scraper():
        all_items.append(item)

    # Dedupe & sort
    unique_items = list(dict.fromkeys(all_items))
    unique_items.sort(
        key=lambda x: x.published_date or datetime.min.timetuple(),
        reverse=True,
    )

    # Summarize
    summaries = {}
    for item in unique_items:
        text = (
            f"Title: {item.title}\n"
            f"Link: {item.link}\n"
            f"Source: {item.source_name}\n"
            f"Published: {item.published_date or 'N/A'}\n"
            f"Author: {item.author or 'N/A'}\n"
            f"Content: {item.summary}"
        )
        try:
            summary = summarize(
                text,
                item.source_name,
                item.link,
                os.getenv("OPENAI_API_KEY"),
            )  # pylint: disable=duplicate-code
            summaries.setdefault(item.source_name, []).append(summary)
        except Exception as exc:
            logging.error(
                f"Summarize failed for {item.title}: {exc}"
            )
            summaries.setdefault(item.source_name, []).append(
                f"[Summary unavailable for {item.title}]"
            )
        # Limit to first 10 sources
        if len(summaries) >= 10:
            break

    # Generate & send
    html, md = format_digest(summaries)
    logging.info("\n--- Generated Markdown Digest ---\n%s\n--- End ---", md)

    try:
        send_email(html)
    except Exception as exc:
        logging.error(f"Email send failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
