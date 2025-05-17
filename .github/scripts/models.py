# models.py
"""
Data models for vibe_digest and related scripts.
"""


class DigestItem:
    """Standardized structure for a digest item."""
    def __init__(self, title, link, summary, source_name, source_url,
                 published_date=None, author=None):
        self.title = title
        self.link = link
        self.summary = summary
        self.source_name = source_name
        self.source_url = source_url
        self.published_date = published_date
        self.author = author

    def __hash__(self):
        return hash((self.title, self.link))

    def __eq__(self, other):
        if not isinstance(other, DigestItem):
            return False
        return (self.title, self.link) == (other.title, other.link)
