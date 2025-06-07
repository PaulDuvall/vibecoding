import openai
import logging
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import re

# Import tiktoken for token optimization
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    logging.warning("tiktoken not available - token optimization disabled")

from src.config import get_config


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

# Token usage tracking
_token_usage = {
    'prompt_tokens': 0,
    'completion_tokens': 0,
    'total_cost': 0.0
}

# Model pricing (per 1K tokens)
MODEL_PRICING = {
    'gpt-4o': {'prompt': 0.005, 'completion': 0.015},
    'gpt-4o-mini': {'prompt': 0.00015, 'completion': 0.0006},
    'gpt-3.5-turbo': {'prompt': 0.0015, 'completion': 0.002},
}


def _get_encoding(model: str = "gpt-4o"):
    """Get tiktoken encoding for the model."""
    if not HAS_TIKTOKEN:
        return None
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        return tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text."""
    if not HAS_TIKTOKEN:
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    encoding = _get_encoding(model)
    if encoding:
        return len(encoding.encode(text))
    return len(text) // 4


def _optimize_content_for_tokens(content: str, max_tokens: int = 2000, model: str = "gpt-4o") -> str:
    """Intelligently truncate content to optimize token usage."""
    current_tokens = _count_tokens(content, model)
    
    if current_tokens <= max_tokens:
        return content
    
    # Strategy 1: Remove extra whitespace and formatting
    cleaned = re.sub(r'\s+', ' ', content).strip()
    current_tokens = _count_tokens(cleaned, model)
    
    if current_tokens <= max_tokens:
        return cleaned
    
    # Strategy 2: Split into paragraphs and prioritize
    paragraphs = content.split('\n\n')
    if len(paragraphs) > 2:
        # Keep first and last paragraphs (usually most important)
        intro = paragraphs[0]
        conclusion = paragraphs[-1]
        intro_tokens = _count_tokens(intro, model)
        conclusion_tokens = _count_tokens(conclusion, model)
        
        remaining_tokens = max_tokens - intro_tokens - conclusion_tokens - 20  # Buffer
        
        if remaining_tokens > 0:
            # Fill with middle content
            middle_content = '\n\n'.join(paragraphs[1:-1])
            if HAS_TIKTOKEN:
                encoding = _get_encoding(model)
                if encoding:
                    middle_tokens = encoding.encode(middle_content)
                    truncated_middle = encoding.decode(middle_tokens[:remaining_tokens])
                    return f"{intro}\n\n{truncated_middle}...\n\n{conclusion}"
            
            # Fallback: character-based truncation
            char_ratio = remaining_tokens * 4  # Rough approximation
            truncated_middle = middle_content[:char_ratio]
            return f"{intro}\n\n{truncated_middle}...\n\n{conclusion}"
        else:
            # Just use intro if no room for conclusion
            return intro[:max_tokens * 4] + "..."
    
    # Strategy 3: Simple truncation with sentence boundaries
    if HAS_TIKTOKEN:
        encoding = _get_encoding(model)
        if encoding:
            tokens = encoding.encode(content)
            truncated_tokens = tokens[:max_tokens]
            truncated_text = encoding.decode(truncated_tokens)
            
            # Try to end at sentence boundary
            last_period = truncated_text.rfind('.')
            if last_period > len(truncated_text) * 0.8:  # Keep if we retain >80%
                return truncated_text[:last_period + 1]
            
            return truncated_text + "..."
    
    # Final fallback
    return content[:max_tokens * 4] + "..."


def _select_optimal_model(content: str, source: str = "") -> str:
    """Select the most cost-effective model based on content characteristics."""
    config = get_config()
    content_length = len(content)
    token_count = _count_tokens(content)
    
    # For very short content, use cheaper model
    if content_length < 300 or token_count < 100:
        return "gpt-3.5-turbo"
    
    # For medium content, use mini model
    if content_length < 1500 or token_count < 500:
        return "gpt-4o-mini"
    
    # For long or complex content, use full model
    return config.openai_model


def _track_token_usage(prompt_tokens: int, completion_tokens: int, model: str):
    """Track token usage and costs."""
    
    _token_usage['prompt_tokens'] += prompt_tokens
    _token_usage['completion_tokens'] += completion_tokens
    
    # Calculate cost
    if model in MODEL_PRICING:
        pricing = MODEL_PRICING[model]
        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']
        _token_usage['total_cost'] += prompt_cost + completion_cost


def get_token_usage_report() -> Dict:
    """Get current token usage statistics."""
    total_tokens = _token_usage['prompt_tokens'] + _token_usage['completion_tokens']
    
    return {
        'prompt_tokens': _token_usage['prompt_tokens'],
        'completion_tokens': _token_usage['completion_tokens'],
        'total_tokens': total_tokens,
        'estimated_cost': f"${_token_usage['total_cost']:.4f}",
        'average_tokens_per_request': total_tokens // max(1, len(_summary_cache))
    }


def summarize_with_streaming(text: str, source_name: str, source_url: str,
                             openai_api_key: str, callback=None) -> str:
    """
    Summarize with streaming response for better perceived performance.
    
    Args:
        text: Content to summarize
        source_name: Name of the source
        source_url: URL of the source
        openai_api_key: OpenAI API key
        callback: Optional callback function to handle streaming chunks
        
    Returns:
        Complete summary text
    """
    # Check cache first
    config = get_config()
    effective_text = text[:config.max_text_length]
    content_hash = _content_hash(effective_text)
    cache_key = f"{content_hash}_{source_name}"
    
    if cache_key in _summary_cache:
        logging.debug(f"Using cached summary for {source_name}")
        return _summary_cache[cache_key]
    
    # Select optimal model
    optimal_model = _select_optimal_model(effective_text, source_name)
    
    # Optimize content
    optimized_content = _optimize_content_for_tokens(
        effective_text, 
        max_tokens=1500, 
        model=optimal_model
    )
    
    prompt = (
        f"Source: {source_name} ({source_url})\n"
        f"Article:\n{optimized_content}\n\n"
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
        
        # Adjust max_tokens based on model
        max_tokens = config.openai_max_tokens
        if optimal_model == "gpt-3.5-turbo":
            max_tokens = min(max_tokens, 150)
        elif optimal_model == "gpt-4o-mini":
            max_tokens = min(max_tokens, 200)
        
        # Create streaming request
        stream = client.chat.completions.create(
            model=optimal_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=config.openai_temperature,
            timeout=config.openai_timeout,
            stream=True
        )
        
        # Collect streamed response
        summary_parts = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                summary_parts.append(content_chunk)
                
                # Call callback if provided (for real-time display)
                if callback:
                    callback(content_chunk)
        
        result = "".join(summary_parts).strip()
        
        # Cache the result
        _summary_cache[cache_key] = result
        
        # Limit cache size
        if len(_summary_cache) > config.cache_size_limit:
            oldest_keys = list(_summary_cache.keys())[:config.cache_cleanup_size]
            for key in oldest_keys:
                del _summary_cache[key]
        
        logging.info(f"Streaming summary completed for '{source_name}' using model '{optimal_model}'")
        return result
        
    except Exception as e:
        logging.error(f"Streaming summarization failed for {source_name}: {e}")
        # Fallback to regular summarization
        return summarize(text, source_name, source_url, openai_api_key)


@retry(
    stop=stop_after_attempt(get_config().openai_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _make_openai_request(client: openai.OpenAI, messages: List[Dict], source_name: str,
                         content: str = "") -> str:
    """Make OpenAI API request with retry logic and optimizations."""
    try:
        config = get_config()
        
        # Select optimal model based on content
        optimal_model = _select_optimal_model(content, source_name)
        
        # Optimize content for token usage
        optimized_messages = []
        for msg in messages:
            if msg['role'] == 'user' and 'content' in msg:
                # Optimize the user content
                optimized_content = _optimize_content_for_tokens(
                    msg['content'], 
                    max_tokens=1500,  # Leave room for system message and response
                    model=optimal_model
                )
                optimized_messages.append({
                    'role': msg['role'],
                    'content': optimized_content
                })
            else:
                optimized_messages.append(msg)
        
        # Adjust max_tokens based on model
        max_tokens = config.openai_max_tokens
        if optimal_model == "gpt-3.5-turbo":
            max_tokens = min(max_tokens, 150)  # Shorter for cheaper model
        elif optimal_model == "gpt-4o-mini":
            max_tokens = min(max_tokens, 200)
        
        response = client.chat.completions.create(
            model=optimal_model,
            messages=optimized_messages,
            max_tokens=max_tokens,
            temperature=config.openai_temperature,
            timeout=config.openai_timeout
        )
        
        # Track token usage
        if hasattr(response, 'usage') and response.usage:
            try:
                _track_token_usage(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    optimal_model
                )
            except (TypeError, AttributeError):
                # Handle mocked responses in tests
                pass
        
        result = response.choices[0].message.content.strip()
        logging.info(f"Summary completed for '{source_name}' using model '{optimal_model}'")
        return result
        
    except openai.RateLimitError:
        logging.warning(f"Rate limit hit for '{source_name}', retrying...")
        raise  # Let tenacity handle retries
    except (openai.APIConnectionError, openai.APITimeoutError):
        logging.warning(f"Connection/timeout error for '{source_name}', retrying...")
        raise  # Let tenacity handle retries
    except openai.AuthenticationError as e:
        logging.error(f"Authentication error for '{source_name}': {e}")
        raise  # Don't retry auth errors
    except openai.BadRequestError as e:
        logging.error(f"Invalid request for '{source_name}': {e}")
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
    config = get_config()
    effective_text = text[:config.max_text_length]
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
        result = _make_openai_request(client, messages, source_name, effective_text)

        # Cache the result
        _summary_cache[cache_key] = result

        # Limit cache size to prevent memory issues
        if len(_summary_cache) > config.cache_size_limit:
            # Remove oldest entries
            keys_to_remove = list(_summary_cache.keys())[:config.cache_cleanup_size]
            for key in keys_to_remove:
                del _summary_cache[key]

        return result
    except openai.AuthenticationError:
        return f"[Summary unavailable for {source_name} - OpenAI Authentication Error]"
    except openai.BadRequestError:
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
            messages = [
                {
                    "role": "system",
                    "content": "You are summarizing multiple articles efficiently in Paul Duvall's style."
                },
                {"role": "user", "content": batch_prompt}
            ]
            
            # Use optimized request function
            batch_result = _make_openai_request(
                client, 
                messages, 
                f"batch_{i//batch_size + 1}", 
                batch_content
            )

            # Parse batch response - batch_result already contains the content
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
