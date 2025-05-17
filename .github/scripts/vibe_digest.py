import os
import sys
import logging
import feedparser
import openai
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from tenacity import retry, wait_exponential, stop_after_attempt
from feeds import FEED_SOURCES, FEEDS, fetch_all_feed_items_concurrently
from models import DigestItem

# Assume aws_blog_search.py exists and works
try:
    from aws_blog_search import fetch_aws_blog_posts
except ImportError:
    logging.warning(
        "aws_blog_search.py not found. AWS blog posts will not be included."
    )
    fetch_aws_blog_posts = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
def fetch_single_feed(url):
    """Fetches and parses a single RSS/Atom feed."""
    digest_items = []
    try:
        logging.info(f"Fetching feed: {url}")
        feed = feedparser.parse(url)

        if feed.bozo:
            # Check for common bozo exceptions that might be retriable
            if isinstance(feed.bozo_exception, (feedparser.http.FeedHttpError,)):
                logging.warning(
                    f"Retriable feed parse error for {url}: "
                    f"{feed.bozo_exception}"
                )
                raise Exception("Retriable feed parse error")

        source_name = FEED_SOURCES.get(url, 'Unknown Source')
        # Limit to 3 entries per feed to keep digest concise
        for entry in feed.entries[:3]:
            link = entry.get('feedburner_origlink', entry.link) \
                if hasattr(entry, 'link') else None
            summary = entry.get('summary', entry.get('description', ''))
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            published_date = getattr(entry, 'published_parsed', None)
            author = getattr(entry, 'author', None)

            if not link:
                logging.warning(
                    f"Skipping entry from {source_name} "
                    f"due to missing link: {title}"
                )
                continue

            digest_items.append(
                DigestItem(
                    title, link, summary, source_name, url, published_date, author
                )
            )
        logging.info(
            f"Successfully fetched {len(digest_items)} items from "
            f"{source_name} ({url})"
        )
    except Exception as e:
        logging.error(f"Exception fetching or parsing feed {url}: {e}")
    return digest_items


def fetch_claude_release_notes_scraper():
    """
    A placeholder function to demonstrate a basic web scraper for Claude Release Notes.
    This would require more robust implementation for a production system,
    including handling of dynamic content, rate limits, and structural changes.
    """
    url = "https://docs.anthropic.com/claude/docs/claude-release-notes"
    try:
        logging.info(f"Attempting to scrape Claude Release Notes from: {url}")
        # This is a very basic example. A real scraper would use BeautifulSoup
        # to parse HTML and extract specific elements.
        # For demonstration, we'll just return a mock item.
        if "Claude 3.5 Sonnet" in "":  # Example check
            title = "Anthropic: Claude 3.5 Sonnet Released!"
            summary = (
                "Anthropic released Claude 3.5 Sonnet, their fastest and most "
                "cost-effective model yet, setting new industry benchmarks for "
                "intelligence. It excels in vision, code, and reasoning "
                "tasks."
            )
            return [DigestItem(
                title=title,
                link=url,
                summary=summary,
                source_name="Claude Release Notes (Scraper)",
                source_url=url,
                published_date=datetime.now(ZoneInfo('UTC')).timetuple()  # Mock date
            )]
    except Exception as e:
        logging.error(f"Error scraping Claude Release Notes from {url}: {e}")
    return []


def summarize(text, source_name, source_url, openai_api_key):
    openai.api_key = openai_api_key
    # Truncate text for prompt to stay within token limits and focus on main content
    effective_text = text[:8000]

    prompt = (
        f"Source: {source_name} ({source_url})\n"
        f"Article:\n{effective_text}\n\n"
        "Summarize in the tone and clarity of a high-signal AI newsletter like "
        "'The Vibe'. Write in the voice of Paul Duvall. Prioritize clarity, "
        "precision, and relevance to experienced software engineers.\n"
        "Focus on the big idea, highlight any tool or trend, tag it appropriately "
        "(e.g., 📈 trend, 🛠️ tool, 🔒 security, 🔬 research, 🚀 release), "
        "and end with a useful takeaway.\n"
        "Use 3–4 short, data-rich sentences. Avoid fluff."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o for potentially better performance/cost
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an editorial assistant summarizing AI-assisted"
                        " software development articles in the style of Paul Duvall."
                        " Start with 'Source: [source name] ([source URL])', then"
                        " summarize concisely. Mimic Paul Duvall's clarity, structure,"
                        " and engineering precision. Tag summaries with appropriate"
                        " emojis. Include the original article link prominently in"
                        " the summary."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        logging.error(
            f"OpenAI API error for '{source_name}' (HTTP {e.status_code}): "
            f"{e.response.text}"
        )
        return f"[Summary unavailable for {source_name} - OpenAI API Error]"
    except Exception as e:
        logging.error(
            f"Unexpected error during OpenAI API call for '{source_name}': {e}"
        )
        return f"[Summary unavailable for {source_name} - Internal Error]"


def format_digest(summaries_by_source):
    """Format the digest into HTML and Markdown, grouped by source."""
    eastern = ZoneInfo('America/New_York')
    now_et = datetime.now(tz=eastern)
    now_str = now_et.strftime('%B %d, %Y %-I:%M %p %Z')

    digest_html = f"<h2>🧠 Vibe Coding Digest – {now_str}</h2>"
    digest_md = f"## 🧠 Vibe Coding Digest – {now_str}\n"

    for source_name, summaries in summaries_by_source.items():
        digest_html += f"<h3>{source_name}</h3><ul>"
        digest_md += f"\n### {source_name}\n"
        for summary in summaries:
            digest_html += f"<li>{summary}</li>"
            digest_md += f"- {summary}\n"
        digest_html += "</ul>"

    return digest_html, digest_md


def send_email(html):
    """Send an email with the digest using SendGrid API."""
    email_to = os.getenv("EMAIL_TO")
    email_from = os.getenv("EMAIL_FROM")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    if not email_to or not email_from or not sendgrid_api_key:
        logging.error(
            "Missing EMAIL_TO, EMAIL_FROM, or SENDGRID_API_KEY environment variable."
        )
        raise EnvironmentError("Required email environment variables not set.")

    now_in_eastern = datetime.now(ZoneInfo('America/New_York'))
    now_et_formatted = now_in_eastern.strftime(
        '%B %d, %Y %-I:%M %p %Z'
    )
    subject = f"🧠 Daily Vibe Coding Digest – {now_et_formatted}"

    payload = {
        "personalizations": [{"to": [{"email": email_to}]}],
        "from": {"email": email_from},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}]
    }
    headers = {
        "Authorization": f"Bearer {sendgrid_api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        logging.info("Digest email sent successfully.")
    except requests.exceptions.HTTPError as e:
        logging.error(
            f"SendGrid API error: {e}\nResponse: "
            f"{getattr(e.response, 'text', None)}"
        )
        raise
    except Exception as e:
        logging.error(f"Unexpected error sending email: {e}")
        raise


def main():
    """Main function to fetch, summarize, and email the digest."""
    # Validate required environment variables early
    openai_api_key = os.getenv("OPENAI_API_KEY")
    required_vars = {
        "OPENAI_API_KEY": openai_api_key,
        "EMAIL_TO": os.getenv("EMAIL_TO"),
        "EMAIL_FROM": os.getenv("EMAIL_FROM"),
        "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY")
    }
    for var_name, value in required_vars.items():
        if not value:
            logging.error(f"Missing required environment variable: {var_name}")
            sys.exit(1)

    all_raw_items = []
    # Fetch RSS feeds concurrently
    all_raw_items.extend(fetch_all_feed_items_concurrently(FEEDS))

    # --- Inject AWS Blog search results as synthetic feed items ---
    if fetch_aws_blog_posts:
        try:
            aws_blog_posts = fetch_aws_blog_posts()
            for post in aws_blog_posts:
                all_raw_items.append(DigestItem(
                    title=post['title'],
                    link=post['link'],
                    summary=post['summary'],
                    source_name='AWS Blog',
                    source_url='https://aws.amazon.com/blogs/aws/',
                    published_date=None
                ))
            logging.info(f"Added {len(aws_blog_posts)} items from AWS Blog.")
        except Exception as e:
            logging.error(f"Error fetching AWS Blog posts: {e}")

    # --- Inject Claude Release Notes from custom scraper (if applicable) ---
    try:
        claude_items = fetch_claude_release_notes_scraper()
        if claude_items:
            all_raw_items.extend(claude_items)
            logging.info(
                f"Added {len(claude_items)} items from Claude Release Notes scraper."
            )
    except Exception as e:
        logging.error(f"Error fetching Claude Release Notes via scraper: {e}")

    # Deduplicate items based on title and link
    unique_items = list(dict.fromkeys(all_raw_items))
    logging.info(
        f"Deduped to {len(unique_items)} unique items from "
        f"{len(all_raw_items)} raw items."
    )

    # Sort items by published date, newest first (if available)
    # Items without a published_date will be at the end.
    unique_items.sort(
        key=lambda x: x.published_date if x.published_date else
        (0, 0, 0, 0, 0, 0, 0, 0, 0),  # earliest possible time.struct_time
        reverse=True
    )

    summaries_by_source = {}
    for item in unique_items:
        try:
            published_str = 'N/A'
            if item.published_date:
                # feedparser.struct_time can be converted to datetime
                dt_published_date = datetime(
                    item.published_date.tm_year, item.published_date.tm_mon,
                    item.published_date.tm_mday, item.published_date.tm_hour,
                    item.published_date.tm_min, item.published_date.tm_sec
                )
                published_str = dt_published_date.strftime('%Y-%m-%d %H:%M:%S')
                # Note: item.published_date often lacks TZ info.
                # For UTC, ensure original data has it or handle explicitly.

            full_text_for_llm = (
                f"Title: {item.title}\n"
                f"Link: {item.link}\n"
                f"Source: {item.source_name}\n"
                f"Published: {published_str}\n"
                f"Author: {item.author if item.author else 'N/A'}\n"
                f"Content: {item.summary}"
            )
            # Prioritize summarizing the first 10 *sources* for a concise digest
            if len(summaries_by_source) < 10 or \
               item.source_name in summaries_by_source:
                summary_content = summarize(
                    full_text_for_llm, item.source_name, item.link, openai_api_key
                )
                summaries_by_source.setdefault(
                    item.source_name, []
                ).append(summary_content)
            else:
                logging.info(
                    f"Skipping summarization for {item.title} from "
                    f"{item.source_name} due to summary limit (10 sources)."
                )
        except Exception as e:
            logging.error(
                f"Error processing item '{item.title}' from "
                f"'{item.source_name}': {e}"
            )
            summaries_by_source.setdefault(item.source_name, []).append(
                f"[Summary unavailable for {item.title}]"
            )

    # Final HTML/Markdown generation
    digest_html, digest_md = format_digest(summaries_by_source)

    # Output to console for debugging/verification
    logging.info("\n--- Generated Markdown Digest ---\n")
    logging.info(digest_md)
    logging.info("\n--- End Markdown Digest ---")

    try:
        send_email(digest_html)
    except Exception as e:
        logging.error(f"Failed to send digest email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
