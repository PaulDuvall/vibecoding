import openai
import logging
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import os


# Initialize OpenAI client once
_openai_client = None

def get_openai_client(api_key: str) -> openai.OpenAI:
    """Get or create OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = openai.OpenAI(api_key=api_key)
    return _openai_client


def _content_hash(text: str) -> str:
    """Generate hash for content caching."""
    return hashlib.md5(text.encode()).hexdigest()


# Simple in-memory cache for duplicate content
_summary_cache = {}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _make_openai_request(client: openai.OpenAI, messages: List[Dict], source_name: str) -> str:
    """Make OpenAI API request with retry logic."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            timeout=30  # Add explicit timeout
        )
        return response.choices[0].message.content.strip()
    except openai.RateLimitError as e:
        logging.warning(f"Rate limit hit for '{source_name}', retrying...")
        raise  # Let tenacity handle retries
    except (openai.APIConnectionError, openai.APITimeoutError) as e:
        logging.warning(f"Connection/timeout error for '{source_name}', retrying...")
        raise  # Let tenacity handle retries
    except openai.AuthenticationError as e:
        logging.error(f"Authentication error for '{source_name}': {e.message}")
        raise  # Don't retry auth errors
    except openai.InvalidRequestError as e:
        logging.error(f"Invalid request for '{source_name}': {e.message}")
        raise  # Don't retry invalid requests
    except Exception as e:
        logging.error(f"Unexpected OpenAI error for '{source_name}': {e}")
        raise


def summarize(text: str, source_name: str, source_url: str, openai_api_key: str) -> str:
    """
    Summarize text using OpenAI with caching and retry logic.
    
    Args:
        text: Content to summarize
        source_name: Name of the source
        source_url: URL of the source
        openai_api_key: OpenAI API key
        
    Returns:
        Summarized text or error message
    """
    # Truncate text for prompt to stay within token limits
    effective_text = text[:8000]
    
    # Check cache first
    content_hash = _content_hash(effective_text)
    cache_key = f"{content_hash}_{source_name}"
    if cache_key in _summary_cache:
        logging.debug(f"Using cached summary for {source_name}")
        return _summary_cache[cache_key]

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
    
    messages = [
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
    ]
    
    try:
        client = get_openai_client(openai_api_key)
        result = _make_openai_request(client, messages, source_name)
        
        # Cache the result
        _summary_cache[cache_key] = result
        
        # Limit cache size to prevent memory issues
        if len(_summary_cache) > 1000:
            # Remove oldest 100 entries
            keys_to_remove = list(_summary_cache.keys())[:100]
            for key in keys_to_remove:
                del _summary_cache[key]
        
        return result
        
    except openai.AuthenticationError:
        return f"[Summary unavailable for {source_name} - OpenAI Authentication Error]"
    except openai.InvalidRequestError:
        return f"[Summary unavailable for {source_name} - OpenAI Invalid Request Error]"
    except Exception as e:
        logging.error(f"Final error for '{source_name}': {type(e).__name__} - {e}")
        return f"[Summary unavailable for {source_name} - {type(e).__name__}]"


def summarize_concurrent(items: List[Tuple[str, str, str]], openai_api_key: str, max_workers: int = 5) -> List[Tuple[str, str, str]]:
    """
    Summarize multiple items concurrently with controlled concurrency.
    
    Args:
        items: List of (text, source_name, source_url) tuples
        openai_api_key: OpenAI API key
        max_workers: Maximum concurrent OpenAI requests
        
    Returns:
        List of (summary, source_name, source_url) tuples
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(summarize, text, source_name, source_url, openai_api_key): (source_name, source_url)
            for text, source_name, source_url in items
        }
        
        # Process completed tasks
        for future in as_completed(future_to_item):
            source_name, source_url = future_to_item[future]
            try:
                summary = future.result()
                results.append((summary, source_name, source_url))
                logging.info(f"Completed summary for {source_name}")
            except Exception as e:
                logging.error(f"Summary failed for {source_name}: {e}")
                results.append((f"[Summary unavailable for {source_name}]", source_name, source_url))
    
    return results


def batch_summarize(items: List[Tuple[str, str, str]], openai_api_key: str, batch_size: int = 3) -> List[str]:
    """
    Batch multiple articles into single OpenAI requests for efficiency.
    
    Args:
        items: List of (text, source_name, source_url) tuples
        openai_api_key: OpenAI API key
        batch_size: Number of articles per batch request
        
    Returns:
        List of summary strings
    """
    client = get_openai_client(openai_api_key)
    summaries = []
    
    # Process items in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Create batch prompt
        batch_content = "\n\n---ARTICLE SEPARATOR---\n\n".join([
            f"ARTICLE {idx + 1}:\nSource: {source_name} ({source_url})\nContent: {text[:4000]}"
            for idx, (text, source_name, source_url) in enumerate(batch)
        ])
        
        batch_prompt = (
            f"Summarize these {len(batch)} articles in Paul Duvall's style. "
            "For each article, provide a 2-3 sentence summary with appropriate emoji tags. "
            "Format: 'SUMMARY X: [content]' where X is the article number.\n\n"
            f"{batch_content}"
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are summarizing multiple articles efficiently in Paul Duvall's style."
                    },
                    {"role": "user", "content": batch_prompt}
                ],
                max_tokens=800,  # More tokens for multiple summaries
                temperature=0.7
            )
            
            # Parse batch response
            batch_result = response.choices[0].message.content.strip()
            
            # Split summaries (simple parsing - could be improved)
            batch_summaries = []
            for idx in range(len(batch)):
                start_marker = f"SUMMARY {idx + 1}:"
                if start_marker in batch_result:
                    start_idx = batch_result.index(start_marker) + len(start_marker)
                    end_marker = f"SUMMARY {idx + 2}:" if idx + 1 < len(batch) else None
                    end_idx = batch_result.index(end_marker) if end_marker and end_marker in batch_result else len(batch_result)
                    summary = batch_result[start_idx:end_idx].strip()
                    batch_summaries.append(summary)
                else:
                    batch_summaries.append(f"[Summary unavailable for article {idx + 1}]")
            
            summaries.extend(batch_summaries)
            
        except Exception as e:
            logging.error(f"Batch summarization failed: {e}")
            # Fallback to individual summaries
            for text, source_name, source_url in batch:
                summary = summarize(text, source_name, source_url, openai_api_key)
                summaries.append(summary)
    
    return summaries
