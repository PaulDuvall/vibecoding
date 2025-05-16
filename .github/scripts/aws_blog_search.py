import requests
import feedparser
from datetime import datetime

def fetch_aws_blog_posts(query="vibe coding", max_results=3):
    """
    Search the AWS Blog RSS feed for posts matching the query.
    Returns a list of dicts with 'title', 'link', 'summary', and 'published'.
    """
    # AWS Blog main feed
    rss_url = "https://aws.amazon.com/blogs/aws/feed/"
    feed = feedparser.parse(rss_url)
    results = []
    for entry in feed.entries:
        # Search title and summary for the query (case-insensitive)
        text = (entry.title + "\n" + entry.get("summary", "")).lower()
        if query.lower() in text or "agentic coding" in text or "amazon q developer" in text or "codewhisperer" in text:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
            })
        if len(results) >= max_results:
            break
    return results

if __name__ == "__main__":
    posts = fetch_aws_blog_posts()
    for post in posts:
        print(f"{post['title']}\n{post['link']}\n{post['summary']}\n---\n")
