import feedparser


def _is_query_match(text, query):
    """
    Checks if a query matches the given text (case-insensitive).
    Considers exact phrase match and all words present for multi-word queries.
    """
    text_lower = text.lower()
    query_lower = query.lower()

    # Exact phrase match
    if query_lower in text_lower:
        return True

    # All words present match for multi-word queries
    query_words = query_lower.split()
    if len(query_words) > 1:
        if all(word in text_lower for word in query_words):
            return True
    return False


def fetch_aws_blog_posts(base_queries=None, max_results_per_query=3):
    """
    Search the AWS Blog RSS feed for posts matching any of the queries.
    Returns a list of dicts with 'title', 'link', 'summary', and
    'published'.
    """
    if base_queries is None:
        base_queries = ["vibe coding", "security engineering", "vibe coding security"]
    #  Always include these related terms
    all_queries = base_queries + [
        "agentic coding", "amazon q developer", "codewhisperer",
        "vibe coding security engineering", "vibe coding security"
    ]
    rss_url = "https://aws.amazon.com/blogs/aws/feed/"
    feed = feedparser.parse(rss_url)
    seen_links = set()
    results = []
    for query in all_queries:
        count = 0
        for entry in feed.entries:
            text_to_search = entry.title + "\n" + entry.get("summary", "")
            if _is_query_match(text_to_search, query) and entry.link not in seen_links:
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
        print(
            f"{post['title']}\n{post['link']}\n{post['summary']}\n---\n"
        )
