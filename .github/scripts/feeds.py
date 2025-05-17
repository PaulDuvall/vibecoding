"""
feeds.py - Feed configuration and feed-fetching logic for vibe_digest
"""
import logging
import feedparser
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, wait_exponential, stop_after_attempt
from models import DigestItem

# Feed URLs
FEEDS = [
    # --- Core AI/Dev Feeds ---
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714",
    "https://www.google.com/alerts/feeds/11805205268710618137/13681474149755866365",
    "https://www.google.com/alerts/feeds/11805205268710618137/6447382119890310773",
    "https://www.google.com/alerts/feeds/11805205268710618137/13093926530832902642",
    "https://www.google.com/alerts/feeds/11805205268710618137/17153509184522491480",
    "https://www.cursor.sh/blog/rss.xml",
    "https://windsurf.com/blog/rss.xml",
    "https://latent.space/feed",
    "https://hnrss.org/newest?q=cursor+IDE&points=50",
    "https://hnrss.org/newest?q=AI+coding&points=50",
    "https://www.reddit.com/r/vibecoding/.rss",
    "https://github.com/search?q=vibe+coding&type=repositories&format=rss",
    # --- GitHub Copilot related ---
    "https://hnrss.org/newest?q=github+copilot&points=50",
    "https://www.reddit.com/search.rss?q=github+copilot&sort=hot",
    "https://github.blog/feed/",
    # --- Recommended Additional Feeds ---
    # "https://rsshub.app/anthropic/claude/release-notes",
    "https://github-trending-api.now.sh/repositories?language=python&since=daily",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCtzS3R3_eB0JgE-hM8mX8XQ",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCuTaETsuCOh0P_XJg_i0wFQ",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UC6YI7W9_UuP5sF98d7_k5GA",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCP_r0x3Y8S_D_h_FmYqg4Gw",
    # "https://rsshub.app/Youtube/ai%20coding",
    "https://www.producthunt.com/topics/artificial-intelligence.rss",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/programming/.rss",
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/feed.xml",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://github.com/langchain-ai/langchain/releases.atom",
    "https://github.com/microsoft/autogen/releases.atom",
]

# Mapping from feed URL to human-friendly source name
FEED_SOURCES = {
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714": (
        "Google Alerts: Vibe Coding"
    ),
    "https://www.google.com/alerts/feeds/11805205268710618137/13681474149755866365": (
        "Google Alerts: Vibe Coding DevOps"
    ),
    "https://www.google.com/alerts/feeds/11805205268710618137/6447382119890310773": (
        "Google Alerts: Vibe Coding Security"
    ),
    "https://www.google.com/alerts/feeds/11805205268710618137/13093926530832902642": (
        "Google Alerts: Vibe Coding DevSecOps"
    ),
    "https://www.google.com/alerts/feeds/11805205268710618137/17153509184522491480": (
        "Google Alerts: OpenAI"
    ),
    "https://www.cursor.sh/blog/rss.xml": "Cursor Blog",
    "https://windsurf.com/blog/rss.xml": "Windsurf Blog",
    "https://latent.space/feed": "Latent Space (Substack)",
    "https://hnrss.org/newest?q=cursor+IDE&points=50": (
        "Hacker News (Cursor IDE)"
    ),
    "https://hnrss.org/newest?q=AI+coding&points=50": "Hacker News (AI Coding)",
    "https://www.reddit.com/r/vibecoding/.rss": "Reddit /r/vibecoding",
    "https://github.com/search?q=vibe+coding&type=repositories&format=rss": (
        "GitHub Search (Vibe Coding)"
    ),
    "https://hnrss.org/newest?q=github+copilot&points=50": (
        "Hacker News (GitHub Copilot)"
    ),
    "https://www.reddit.com/search.rss?q=github+copilot&sort=hot": (
        "Reddit Search (GitHub Copilot)"
    ),
    "https://github.blog/feed/": "GitHub Blog",
    "https://github-trending-api.now.sh/repositories?language=python&since=daily": (
        "GitHub Trending (Python, daily)"
    ),
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCtzS3R3_eB0JgE-hM8mX8XQ": (
        "YouTube: Yannic Kilcher"
    ),
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCuTaETsuCOh0P_XJg_i0wFQ": (
        "YouTube: Two Minute Papers"
    ),
    "https://www.youtube.com/feeds/videos.xml?channel_id=UC6YI7W9_UuP5sF98d7_k5GA": (
        "YouTube: OpenAI"
    ),
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCP_r0x3Y8S_D_h_FmYqg4Gw": (
        "YouTube: Latent Space Podcast"
    ),
    "https://www.producthunt.com/topics/artificial-intelligence.rss": (
        "Product Hunt: AI"
    ),
    "https://www.reddit.com/r/MachineLearning/.rss": "Reddit: MachineLearning",
    "https://www.reddit.com/r/artificial/.rss": "Reddit: Artificial Intelligence",
    "https://www.reddit.com/r/programming/.rss": "Reddit: Programming",
    "https://openai.com/news/rss.xml": "OpenAI News",
    "https://www.anthropic.com/news/feed.xml": "Anthropic Blog",
    "https://ai.googleblog.com/feeds/posts/default": "Google AI Blog",
    "https://github.com/langchain-ai/langchain/releases.atom": (
        "GitHub Releases: LangChain"
    ),
    "https://github.com/microsoft/autogen/releases.atom": (
        "GitHub Releases: AutoGen"
    ),
    "https://aws.amazon.com/blogs/aws/feed/": "AWS Blog",
    "Claude Release Notes (Scraper)": "Claude Release Notes"
}


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
def fetch_single_feed(url):
    """Fetches and parses a single RSS/Atom feed."""
    digest_items = []
    try:
        logging.info("Fetching feed: {}".format(url))
        feed = feedparser.parse(url)
        if feed.bozo:
            if isinstance(feed.bozo_exception, (feedparser.http.FeedHttpError,)):
                logging.warning(
                    (
                        "Retriable feed parse error for {}: {}"
                    ).format(
                        url, feed.bozo_exception
                    )
                )
                raise Exception("Retriable feed parse error")
        source_name = FEED_SOURCES.get(url, "Unknown Source")
        for entry in feed.entries[:3]:
            link = (
                entry.get("feedburner_origlink", entry.link)
                if hasattr(entry, "link")
                else None
            )
            summary = (
                entry.get("summary", "")
                or entry.get("description", "")
            )
            title = (
                entry.title
                if hasattr(entry, "title")
                else "No Title"
            )
            published_date = getattr(entry, "published_parsed", None)
            author = getattr(entry, "author", None)
            if not link:
                logging.warning(
                    (
                        "Skipping entry from {} due to missing link: {}"
                    ).format(
                        source_name, title
                    )
                )
                continue
            digest_items.append(
                DigestItem(
                    title, link, summary, source_name, url, published_date, author
                )
            )
        logging.info(
            (
                "Successfully fetched {} items from {} ("
                "{})"
            ).format(
                len(digest_items), source_name, url
            )
        )
    except Exception as e:
        logging.error("Exception fetching or parsing feed {}: {}".format(url, e))
    return digest_items


def fetch_all_feed_items_concurrently(feeds_list):
    """Fetches items from all RSS feeds concurrently."""
    all_items = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_single_feed, feeds_list))
        for items_from_feed in results:
            all_items.extend(items_from_feed)
    return all_items
