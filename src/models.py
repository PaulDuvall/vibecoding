"""
Data models for vibe_digest and related scripts.
"""
from typing import Optional, Any
import time


class DigestItem:
    """Standardized structure for a digest item."""

    def __init__(
        self,
        title: str,
        link: str,
        summary: str,
        source_name: str,
        source_url: str,
        published_date: Optional[time.struct_time] = None,
        author: Optional[str] = None
    ) -> None:
        self.title = title
        self.link = link
        self.summary = summary
        self.source_name = source_name
        self.source_url = source_url
        self.published_date = published_date
        self.author = author

    def __hash__(self) -> int:
        return hash((self.title, self.link))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DigestItem):
            return False
        return (self.title, self.link) == (other.title, other.link)
