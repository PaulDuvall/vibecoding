# .github/scripts/vibe_digest.py
import os
import feedparser
import openai
import requests
from datetime import datetime


# ---
# 📡 Feeds & Sources to Track (see PRD and README for details)
# - Cursor Blog:         https://www.cursor.sh/blog/rss.xml
# - Windsurf Blog:       https://windsurf.com/blog/rss.xml
# - Claude Code/Anthropic: TODO: Custom watcher on https://docs.anthropic.com/claude/docs/claude-release-notes
# - Hacker News:         https://hnrss.org/newest?q=cursor+IDE
# - GitHub Trending:     TODO: Scraper or GitHub Trending API
# - Latent Space:        https://latent.space/feed
# ---
FEEDS = [
    "https://www.cursor.sh/blog/rss.xml",           # Cursor Blog
    "https://windsurf.com/blog/rss.xml",            # Windsurf Blog
    "https://latent.space/feed",                    # Latent Space (Substack)
    "https://hnrss.org/newest?q=cursor+IDE",        # Hacker News keyword search
    "https://www.reddit.com/r/vibecoding/.rss",     # Reddit /r/vibecoding
    # GitHub repo search RSS (may require authentication or manual generation)
    "https://github.com/search?q=vibe+coding&type=repositories&format=rss",  # GitHub search
    # TODO: Add Claude Code/Anthropic (custom watcher on release notes)
    # TODO: Add GitHub Trending (API or scraping)
    # TODO: Add YouTube search (via RSSHub or 3rd-party RSS generator)
    # TODO: Add Google Alerts (via email-to-RSS or Zapier)
    # TODO: Add LinkedIn content (via RSSHub, scraping, or API)
]

# ---
# Delivery Options (choose one or extend):
# - Email (default, see send_email)
# - Slack (add integration/delivery function)
# - GitHub Issues (add integration/delivery function)
# ---


def fetch_feed_items():
    """Fetch items from RSS feeds.

    Returns:
        list: List of feed items
    """
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        items.extend(feed.entries[:3])
    return items[:10]


def summarize(text):
    """Generate a summary of the given text using OpenAI's API.

    Args:
        text (str): Text to summarize

    Returns:
        str: Generated summary
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "Summarize articles for a daily Vibe Coding digest."
            },
            {"role": "user", "content": text[:4000]}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def format_digest(summaries):
    """Format the digest into HTML.

    Args:
        summaries (list): List of summaries to include in the digest

    Returns:
        str: Formatted HTML digest
    """
    today = datetime.utcnow().strftime("%B %d, %Y")
    digest = f"<h2>🧠 Vibe Coding Digest – {today}</h2><ul>"
    for summary in summaries:
        digest += f"<li>{summary}</li>"
    digest += "</ul>"
    return digest


def send_email(html):
    """Send an email with the digest using SendGrid API.

    Args:
        html (str): HTML content to send in the email

    Raises:
        requests.exceptions.HTTPError: If the email fails to send
    """
    payload = {
        "personalizations": [{
            "to": [{"email": os.getenv("EMAIL_TO")}]
        }],
        "from": {"email": os.getenv("EMAIL_FROM")},
        "subject": "🧠 Daily Vibe Coding Digest",
        "content": [{"type": "text/html", "value": html}]
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        json=payload,
        headers=headers
    )
    response.raise_for_status()


def main():
    """Main function to fetch, summarize, and email the digest.

    This function orchestrates the entire process of fetching feed items,
    generating summaries, formatting them into an HTML digest, and sending
    the digest via email.
    """
    items = fetch_feed_items()
    summaries = [
        summarize(
            item.title + "\n" + item.link + "\n" + (item.get("summary", ""))
        )
        for item in items
    ]
    html = format_digest(summaries)
    send_email(html)


if __name__ == "__main__":
    main()
