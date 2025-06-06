import openai
import logging


def summarize(text: str, source_name: str, source_url: str, openai_api_key: str) -> str:
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
    except openai.RateLimitError as e:
        logging.error(
            f"OpenAI RateLimitError for '{source_name}': HTTP Status: {e.status_code}, "
            f"Response: {e.response.text if e.response else 'N/A'}"
            f" Message: {e.message}"
        )
        return f"[Summary unavailable for {source_name} - OpenAI Rate Limit Error]"
    except openai.AuthenticationError as e:
        logging.error(
            f"OpenAI AuthenticationError for '{source_name}': "
            f"HTTP Status: {e.status_code}, "
            f"Response: {e.response.text if e.response else 'N/A'}, "
            f"Message: {e.message}"
        )
        return f"[Summary unavailable for {source_name} - OpenAI Authentication Error]"
    except openai.APIConnectionError as e:
        logging.error(
            f"OpenAI APIConnectionError for '{source_name}': "
            f"Message: {e.message}"
        )
        return f"[Summary unavailable for {source_name} - OpenAI Connection Error]"
    except openai.APITimeoutError as e:
        logging.error(
            f"OpenAI APITimeoutError for '{source_name}': "
            f"Message: {e.message}"
        )
        return f"[Summary unavailable for {source_name} - OpenAI Timeout Error]"
    except openai.InvalidRequestError as e:
        logging.error(
            f"OpenAI InvalidRequestError for '{source_name}': "
            f"HTTP Status: {e.status_code if hasattr(e, 'status_code') else 'N/A'}, "
            f"Message: {e.message}, "
            f"Param: {e.param if hasattr(e, 'param') else 'N/A'}"
        )
        return (
            f"[Summary unavailable for {source_name} - OpenAI Invalid "
            f"Request Error. Please check the request and try again.]"
        )
    except openai.APIError as e:  # General API error
        logging.error(
            f"OpenAI APIError for '{source_name}': HTTP Status: {e.status_code}, "
            f"Response: {e.response.text if e.response else 'N/A'}, "
            f"Message: {e.message}"
        )
        return (
            f"[Summary unavailable for {source_name} - OpenAI API "
            f"Error. Please check the API and try again.]"
        )
    except Exception as e:  # Catch-all for other errors
        logging.error(
            f"Unexpected error during OpenAI API call for '{source_name}': "
            f"{type(e).__name__} - {e}"
        )
        return f"[Summary unavailable for {source_name} - Internal Error]"
