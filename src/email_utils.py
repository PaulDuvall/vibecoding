import os
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


def send_email(html: str) -> None:
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
