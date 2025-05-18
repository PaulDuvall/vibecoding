import openai
import logging


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
