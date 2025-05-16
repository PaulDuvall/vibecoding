# .github/scripts/vibe_digest.py
import os
import feedparser
import openai
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from aws_blog_search import fetch_aws_blog_posts


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
    # --- Core AI/Dev Feeds ---
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714",  # Google Alerts: Vibe Coding
    "https://www.cursor.sh/blog/rss.xml",           # Cursor Blog
    "https://windsurf.com/blog/rss.xml",            # Windsurf Blog
    "https://latent.space/feed",                    # Latent Space (Substack)
    "https://hnrss.org/newest?q=cursor+IDE",        # Hacker News keyword search
    "https://www.reddit.com/r/vibecoding/.rss",     # Reddit /r/vibecoding
    "https://github.com/search?q=vibe+coding&type=repositories&format=rss",  # GitHub search
    # --- GitHub Copilot related ---
    "https://hnrss.org/newest?q=github+copilot",    # Hacker News: GitHub Copilot
    "https://www.reddit.com/search.rss?q=github+copilot",  # Reddit search: GitHub Copilot
    "https://github.blog/feed/",                    # GitHub Blog
    # --- Recommended Additional Feeds ---
    # Claude Code / Anthropic Release Notes (via RSSHub)
    # "https://rsshub.app/anthropic/claude/release-notes",    # Claude Release Notes (RSSHub) - currently not working
    # GitHub Trending (via unofficial API)
    "https://github-trending-api.now.sh/repositories?language=python&since=daily", # GitHub Trending (Python, daily)
    # YouTube AI/ML Channels
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew",  # YouTube: Yannic Kilcher
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg",  # YouTube: Two Minute Papers
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCLB7AzTwc6VFZrBsO2ucBMg",  # YouTube: OpenAI
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCm5mt-A4w61lknZ9lCsZtBw",  # YouTube: Latent Space Podcast
    # YouTube search for "AI coding" (via RSSHub)
    # "https://rsshub.app/youtube/search/ai%20coding",  # YouTube search: AI coding (RSSHub) - currently not working
    # Google Alerts (user must set up and supply their own RSS for privacy)
    # "https://www.google.com/alerts/feeds/xxxx/xxxx",  # Google Alerts: AI coding (placeholder)
    # Product Hunt – AI Tools
    "https://www.producthunt.com/topics/artificial-intelligence.rss",                # Product Hunt AI
    # Reddit – Broader AI Communities
    "https://www.reddit.com/r/MachineLearning/.rss",  # Reddit: MachineLearning
    "https://www.reddit.com/r/artificial/.rss",       # Reddit: Artificial Intelligence
    "https://www.reddit.com/r/programming/.rss",      # Reddit: Programming
    # Official Blogs
    "https://openai.com/blog/rss",                    # OpenAI Blog
    "https://www.anthropic.com/news/feed.xml",        # Anthropic Blog
    "https://ai.googleblog.com/feeds/posts/default",  # Google AI Blog
]


# Mapping from feed URL to human-friendly source name
FEED_SOURCES = {
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714": "Google Alerts: Vibe Coding",
    # --- Core AI/Dev Feeds ---
    "https://www.cursor.sh/blog/rss.xml": "Cursor Blog",
    "https://windsurf.com/blog/rss.xml": "Windsurf Blog",
    "https://latent.space/feed": "Latent Space (Substack)",
    "https://hnrss.org/newest?q=cursor+IDE": "Hacker News (Cursor IDE)",
    "https://www.reddit.com/r/vibecoding/.rss": "Reddit /r/vibecoding",
    "https://github.com/search?q=vibe+coding&type=repositories&format=rss": "GitHub Search (Vibe Coding)",
    # --- GitHub Copilot related ---
    "https://hnrss.org/newest?q=github+copilot": "Hacker News (GitHub Copilot)",
    "https://www.reddit.com/search.rss?q=github+copilot": "Reddit Search (GitHub Copilot)",
    "https://github.blog/feed/": "GitHub Blog",
    # --- Recommended Additional Feeds ---
    # "https://rsshub.app/anthropic/claude/release-notes": "Claude Release Notes (RSSHub)",
    "https://github-trending-api.now.sh/repositories?language=python&since=daily": "GitHub Trending (Python, daily)",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew": "YouTube: Yannic Kilcher",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg": "YouTube: Two Minute Papers",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCLB7AzTwc6VFZrBsO2ucBMg": "YouTube: OpenAI",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCm5mt-A4w61lknZ9lCsZtBw": "YouTube: Latent Space Podcast",
    # "https://rsshub.app/youtube/search/ai%20coding": "YouTube Search: AI coding (RSSHub)",
    # Google Alerts placeholder (user-supplied)
    # "https://www.google.com/alerts/feeds/xxxx/xxxx": "Google Alerts: AI coding",
    "https://www.producthunt.com/topics/artificial-intelligence.rss": "Product Hunt: AI",
    "https://www.reddit.com/r/MachineLearning/.rss": "Reddit: MachineLearning",
    "https://www.reddit.com/r/vibecoding/.rss": "Reddit: Vibe Coding",
    "https://www.reddit.com/r/artificial/.rss": "Reddit: Artificial Intelligence",
    "https://www.reddit.com/r/programming/.rss": "Reddit: Programming",
    "https://openai.com/blog/rss": "OpenAI Blog",
    "https://www.anthropic.com/news/feed.xml": "Anthropic Blog",
    "https://ai.googleblog.com/feeds/posts/default": "Google AI Blog",
}



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


def summarize(text, source_name, source_url):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = (
        f"Source: {source_name} ({source_url})\n"
        f"Article:\n{text[:4000]}\n"
        "\nSummarize in the tone and clarity of a high-signal AI newsletter like 'The Vibe'.\n"
        "Write in the voice of Paul Duvall. Prioritize clarity, precision, and relevance to experienced software engineers.\n"
        "Focus on the big idea, highlight any tool or trend, tag it appropriately (e.g., \U0001f4c8 trend, \U0001f9ea tool, \U0001f512 security), and end with a useful takeaway.\n"
        "Use 3–4 short, data-rich sentences. Avoid fluff."
    )
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an editorial assistant summarizing AI-assisted software development articles in the style of Paul Duvall."
                    " Start with 'Source: [source name] ([source URL])', then summarize concisely."
                    " Mimic Paul Duvall's clarity, structure, and engineering precision. Tag summaries with appropriate emojis."
                )
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def format_digest(summaries):
    """Format the digest into HTML and Markdown.

    Args:
        summaries (list): List of summaries to include in the digest

    Returns:
        tuple: Formatted HTML and Markdown digest
    """
    eastern = ZoneInfo('America/New_York')
    now_et = datetime.now(tz=eastern)
    now_str = now_et.strftime('%B %d, %Y %-I:%M %p %Z')
    digest_html = f"<h2>🧠 Vibe Coding Digest – {now_str}</h2><ul>"
    digest_md = f"## 🧠 Vibe Coding Digest – {now_str}\n"

    for summary in summaries:
        digest_html += f"<li>{summary}</li>"
        digest_md += f"- {summary}\n"

    digest_html += "</ul>"
    return digest_html, digest_md


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
        "subject": f"🧠 Daily Vibe Coding Digest – {datetime.now(ZoneInfo('America/New_York')).strftime('%B %d, %Y %-I:%M %p %Z')}",
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
    # --- Inject AWS Blog search results as synthetic feed items ---
    aws_blog_posts = fetch_aws_blog_posts()
    for post in aws_blog_posts:
        items.append({
            'title': post['title'],
            'link': post['link'],
            'summary': post['summary'],
            'feed': {'href': 'https://aws.amazon.com/blogs/aws/feed/'},
            '_synthetic_source_name': 'AWS Blog',
            '_synthetic_source_url': 'https://aws.amazon.com/blogs/aws/',
        })
    summaries = []
    for item in items:
        # Use synthetic source if present
        if '_synthetic_source_name' in item:
            source_name = item['_synthetic_source_name']
            source_url = item['_synthetic_source_url']
        else:
            source_url = item.get('feedburner_origlink', None) or getattr(item, 'href', None) or getattr(item, 'feed', {}).get('href', None)
            # fallback: use item.feed if available, otherwise try to match by link prefix
            if not source_url:
                for feed_url in FEEDS:
                    if item.link.startswith(feed_url.split('/rss')[0]):
                        source_url = feed_url
                        break
            # fallback: use feed_url from FEEDS if present in item's feed
            if not source_url and hasattr(item, 'feed') and hasattr(item.feed, 'href'):
                source_url = item.feed.href
            # fallback: try to match by domain
            if not source_url:
                for feed_url in FEEDS:
                    if feed_url.split('/')[2] in item.link:
                        source_url = feed_url
                        break
            # fallback: just use the first FEEDS url
            if not source_url:
                source_url = FEEDS[0]
            source_name = FEED_SOURCES.get(source_url, 'Unknown Source')
        text = item['title'] + "\n" + item['link'] + "\n" + (item.get("summary", ""))
        summaries.append(
            summarize(text, source_name, source_url)
        )
    digest_html, digest_md = format_digest(summaries)
    send_email(digest_html)


if __name__ == "__main__":
    main()
