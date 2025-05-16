import requests
import feedparser
from datetime import datetime

def fetch_aws_blog_posts(queries=None, max_results_per_query=3):
    """
    Search the AWS Blog RSS feed for posts matching any of the queries.
    Returns a list of dicts with 'title', 'link', 'summary', and 'published'.
    """
    if queries is None:
        queries = ["vibe coding", "security engineering", "vibe coding security"]
    # Always include these related terms
    queries += ["agentic coding", "amazon q developer", "codewhisperer", "vibe coding security engineering", "vibe coding security"]
    rss_url = "https://aws.amazon.com/blogs/aws/feed/"
    feed = feedparser.parse(rss_url)
    seen_links = set()
    results = []
    for query in queries:
        count = 0
        for entry in feed.entries:
            text = (entry.title + "\n" + entry.get("summary", "")).lower()
            query_match = query.lower() in text
            # For multi-word queries, also match if all words present
            if not query_match and len(query.split()) > 1:
                query_match = all(word in text for word in query.lower().split())
            if query_match and entry.link not in seen_links:
                results.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                })
                seen_links.add(entry.link)
                count += 1
            if count >= max_results_per_query:
                break
    return results

if __name__ == "__main__":
    posts = fetch_aws_blog_posts()
    for post in posts:
        print(f"{post['title']}\n{post['link']}\n{post['summary']}\n---\n")
