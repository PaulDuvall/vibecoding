import re
import feedparser
from typing import List, Dict, Set


# Core AI Engineering search terms
AI_ENGINEERING_QUERIES = [
    # Core AI Engineering terms
    "AI engineer", "AI engineering", "LLM engineering",
    "prompt engineering", "RAG pipeline", "vector database",
    "LLMOps", "MLOps", "model evaluation",
    
    # AI-Assisted Development Tools
    "cursor ide", "windsurf ide", "claude code",
    "github copilot", "amazon q developer", "codewhisperer",
    "aider", "continue dev", "sourcegraph cody",
    "tabnine", "codeium", "amazon bedrock",
    
    # Frameworks & Platforms
    "langchain", "llamaindex", "autogen", "semantic kernel",
    "vercel ai sdk", "openai assistants", "anthropic claude",
    "hugging face", "crew ai", "dspy", "guidance ai",
    
    # AI Engineering Practices
    "prompt versioning", "prompt management", "prompt testing",
    "AI test driven development", "ATDD AI", "AI pair programming",
    "context engineering", "few shot learning", "chain of thought",
    "retrieval augmented generation", "fine tuning", "PEFT", "LoRA",
    
    # Infrastructure & Operations
    "vector embeddings", "embedding models", "inference optimization",
    "model serving", "model deployment", "token optimization",
    "context window", "semantic search", "hybrid search",
    
    # Specific Models & Providers
    "gpt-4", "claude 3", "llama 3", "deepseek", "gemini",
    "mistral", "qwen", "phi-3", "command r", "grok",
    
    # Curated High-Signal Agent Coding Terms
    "AI coding agents", "software development agents", "AI pair programmer",
    "autonomous coding agents", "AI programming assistant", "agentic software",
    "AI developer bots", "AI-powered code agents", "autonomous dev agents",
    
    # Coding with AI Terms
    "AI-assisted development", "copilot coding", "AI code generation",
    "prompt-based programming", "LLM coding", "generative coding",
    "AI-enhanced development", "natural language programming", "coding with language models",
    
    # Autonomous Software Engineering
    "self-coding AI", "autonomous programming", "end-to-end code generation",
    "AI-led development", "agentic software engineering", "closed-loop AI development",
    "autonomous software agents", "full-stack AI engineering", "intelligent code orchestration",
    
    # Autonomous Software Agents
    "AI dev agents", "software agents with reasoning", "agent-based software engineering",
    "autonomous developer agents", "multi-agent software systems", "LLM-powered agents",
    "self-directed AI agents", "cognitive software agents", "tool-using AI agents",
    "AI software builders",
    
    # High-Volume/Trending Terms
    "GPT engineering", "AI IDEs", "agentic workflows", "small language models",
    "AI copilots for developers", "code synthesis from prompts", "software 2.0",
    "prompt engineering for development", "reasoning agents", "autonomous IDEs"
]


def _calculate_relevance_score(text: str, matched_queries: Set[str]) -> float:
    """
    Calculate a relevance score based on matched queries and content quality indicators.
    """
    score = len(matched_queries) * 10  # Base score from number of matches
    
    # Boost for tool comparisons
    comparison_terms = ["vs", "versus", "compare", "comparison", "better than"]
    if any(term in text.lower() for term in comparison_terms):
        score += 5
    
    # Boost for practical content
    practical_terms = ["tutorial", "guide", "how to", "example", "implementation", "code"]
    if any(term in text.lower() for term in practical_terms):
        score += 3
    
    # Boost for benchmarks and performance
    performance_terms = ["benchmark", "performance", "speed", "cost", "pricing", "optimization"]
    if any(term in text.lower() for term in performance_terms):
        score += 3
    
    # Boost for recent/new content
    new_terms = ["announce", "release", "launch", "update", "new feature", "beta", "preview"]
    if any(term in text.lower() for term in new_terms):
        score += 2
    
    return score


def _is_query_match(text: str, query: str) -> bool:
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
        return all(
            re.search(r'\b{}\b'.format(re.escape(word)), text_lower)
            for word in words
        )


def search_ai_engineering_content(
    feed_urls: List[str], 
    custom_queries: List[str] = None,
    max_results: int = 50,
    min_relevance_score: float = 10.0
) -> List[Dict]:
    """
    Search multiple RSS feeds for AI engineering content.
    Returns a list of dicts with title, link, summary, published, source, and relevance_score.
    Results are sorted by relevance score.
    """
    queries = AI_ENGINEERING_QUERIES
    if custom_queries:
        queries = queries + custom_queries
    
    seen_links = set()
    results = []
    
    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)
            feed_name = feed.feed.get('title', feed_url)
            
            for entry in feed.entries:
                if entry.link in seen_links:
                    continue
                
                text_to_search = entry.title + "\n" + entry.get("summary", "")
                matched_queries = set()
                
                # Check which queries match this entry
                for query in queries:
                    if _is_query_match(text_to_search, query):
                        matched_queries.add(query)
                
                if matched_queries:
                    relevance_score = _calculate_relevance_score(text_to_search, matched_queries)
                    
                    if relevance_score >= min_relevance_score:
                        results.append({
                            "title": entry.title,
                            "link": entry.link,
                            "summary": entry.get("summary", ""),
                            "published": entry.get("published", ""),
                            "source": feed_name,
                            "relevance_score": relevance_score,
                            "matched_queries": list(matched_queries)
                        })
                        seen_links.add(entry.link)
                        
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            continue
    
    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Return top results
    return results[:max_results]


def fetch_aws_blog_posts(base_queries=None, max_results_per_query=5):
    """
    Enhanced AWS blog search focusing on AI engineering topics.
    """
    if base_queries is None:
        # Focus on AI engineering tools and practices at AWS
        queries = [
            "amazon q developer", "codewhisperer", "bedrock",
            "sagemaker", "AI engineering", "machine learning",
            "generative AI", "foundation models", "claude",
            "AI developer tools", "ML pipeline", "model deployment"
        ]
    else:
        queries = list(base_queries)
    
    # Add AI engineering specific queries
    queries += [
        "agentic coding", "prompt engineering aws", "rag aws",
        "vector database aws", "llm aws", "ai assistant aws"
    ]
    
    rss_url = "https://aws.amazon.com/blogs/aws/feed/"
    results = search_ai_engineering_content(
        [rss_url], 
        queries, 
        max_results=max_results_per_query * len(queries)
    )
    
    return results


if __name__ == "__main__":
    # Example usage
    ai_feeds = [
        "https://aws.amazon.com/blogs/aws/feed/",
        "https://openai.com/news/rss.xml",
        "https://www.anthropic.com/news/feed.xml"
    ]
    
    posts = search_ai_engineering_content(ai_feeds, max_results=10)
    
    print("Top AI Engineering Content:")
    print("-" * 80)
    
    for post in posts:
        print(f"Title: {post['title']}")
        print(f"Source: {post['source']}")
        print(f"Relevance Score: {post['relevance_score']}")
        print(f"Matched: {', '.join(post['matched_queries'][:3])}...")
        print(f"Link: {post['link']}")
        print("-" * 80)