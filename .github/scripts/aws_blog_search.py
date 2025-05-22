import feedparser


import re

def _is_query_match(text, query):
    """
    Checks if a query matches the given text (case-insensitive).
    For single-word queries, matches only whole words.
    For multi-word queries, matches if all words are present, regardless of order.
    """
    text_lower = text.lower()
    query_lower = query.lower()
    words = query_lower.split()
    if len(words) == 1:
        # Single word: match only whole word
        pattern = r'\b{}\b'.format(re.escape(query_lower))
        return re.search(pattern, text_lower) is not None
    else:
        # Multi-word: match if all words are present, regardless of order
        return all(re.search(r'\b{}\b'.format(re.escape(word)), text_lower) for word in words)



def fetch_aws_blog_posts(base_queries=None, max_results_per_query=3):
    """
    Search the AWS Blog RSS feed for posts matching any of the queries.
    Returns a list of dicts with 'title', 'link', 'summary', and
    'published'.
    """
    if base_queries is None:
        queries = ["vibe coding", "security engineering", "vibe coding security"]
    else:
        queries = list(base_queries)
    # Always include these related terms
    queries += [
        "agentic coding", "amazon q developer", "codewhisperer",
        "vibe coding security engineering", "vibe coding security"
    ]
    rss_url = "https://aws.amazon.com/blogs/aws/feed/"
    feed = feedparser.parse(rss_url)
    seen_links = set()
    results = []
    for query in queries:
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
