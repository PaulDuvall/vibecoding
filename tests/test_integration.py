"""
Integration tests for the full vibe_digest pipeline.
"""
import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models import DigestItem
from src.feeds import fetch_all_feed_items_concurrently
from src.summarize import summarize
from src.email_utils import send_email
from src import vibe_digest


class TestDigestIntegration:
    """Integration tests for the complete digest pipeline."""

    @patch('src.vibe_digest.send_email')
    @patch('src.vibe_digest.summarize')
    @patch('src.vibe_digest.fetch_all_feed_items_concurrently')
    @patch('src.vibe_digest.fetch_aws_blog_posts')
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'EMAIL_TO': 'test@example.com',
        'EMAIL_FROM': 'from@example.com',
        'SENDGRID_API_KEY': 'test-sendgrid-key'
    })
    def test_full_digest_pipeline(self, mock_aws_fetch, mock_feed_fetch, 
                                  mock_summarize, mock_send_email):
        """Test the complete digest pipeline from feed fetch to email send."""
        # Setup mock data
        test_items = [
            DigestItem(
                title="Test Article 1",
                link="https://example.com/1",
                summary="Test summary 1",
                source_name="Test Source 1",
                source_url="https://feed1.com",
                published_date=None,
                author="Test Author"
            ),
            DigestItem(
                title="Test Article 2", 
                link="https://example.com/2",
                summary="Test summary 2",
                source_name="Test Source 2",
                source_url="https://feed2.com",
                published_date=None,
                author=None
            )
        ]
        
        # Configure mocks
        mock_feed_fetch.return_value = test_items
        mock_aws_fetch.return_value = []
        mock_summarize.return_value = "Mocked summary content"
        mock_send_email.return_value = None
        
        # Run the main digest function
        vibe_digest.main()
        
        # Verify the pipeline executed correctly
        mock_feed_fetch.assert_called_once()
        assert mock_summarize.call_count == len(test_items)
        mock_send_email.assert_called_once()
        
        # Verify summarize was called with correct parameters
        for item in test_items:
            expected_text = (
                f"Title: {item.title}\n"
                f"Link: {item.link}\n"
                f"Source: {item.source_name}\n"
                f"Published: {item.published_date or 'N/A'}\n"
                f"Author: {item.author or 'N/A'}\n"
                f"Content: {item.summary}"
            )
            mock_summarize.assert_any_call(
                expected_text,
                item.source_name,
                item.link,
                'test-key'
            )

    @patch.dict('os.environ', {}, clear=True)
    def test_environment_validation_fails(self):
        """Test that missing environment variables cause validation to fail."""
        with pytest.raises(SystemExit):
            vibe_digest.validate_environment()

    @patch('src.vibe_digest.logging')
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'EMAIL_TO': '',  # Missing value
        'EMAIL_FROM': 'from@example.com',
        'SENDGRID_API_KEY': 'test-sendgrid-key'
    })
    def test_environment_validation_logs_missing_vars(self, mock_logging):
        """Test that missing environment variables are logged."""
        with pytest.raises(SystemExit):
            vibe_digest.validate_environment()
        
        mock_logging.error.assert_called_with(
            "Missing required environment variable: EMAIL_TO"
        )

    def test_digest_item_deduplication(self):
        """Test that duplicate items are properly removed."""
        # Create duplicate items
        item1 = DigestItem(
            title="Same Title",
            link="https://example.com/same",
            summary="Summary 1",
            source_name="Source 1",
            source_url="https://feed1.com"
        )
        item2 = DigestItem(
            title="Same Title",
            link="https://example.com/same",  # Same link
            summary="Summary 2",  # Different summary
            source_name="Source 2",
            source_url="https://feed2.com"
        )
        item3 = DigestItem(
            title="Different Title",
            link="https://example.com/different",
            summary="Summary 3",
            source_name="Source 3",
            source_url="https://feed3.com"
        )
        
        items = [item1, item2, item3]
        unique_items = vibe_digest.dedupe_and_sort_items(items)
        
        # Should only have 2 unique items (item1 and item3)
        assert len(unique_items) == 2
        assert item1 in unique_items
        assert item3 in unique_items
        # item2 should be deduplicated since it has same title/link as item1

    @patch('src.vibe_digest.datetime')
    def test_format_digest_structure(self, mock_datetime):
        """Test that digest formatting produces correct HTML and Markdown."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # Mock datetime for consistent output
        test_date = datetime(2023, 6, 15, 10, 30, 0, tzinfo=ZoneInfo("America/New_York"))
        mock_datetime.now.return_value = test_date
        
        test_summaries = {
            "Test Source 1": ["Summary 1", "Summary 2"],
            "Test Source 2": ["Summary 3"]
        }
        
        html, md = vibe_digest.format_digest(test_summaries)
        
        # Check HTML structure
        assert "<h2>🧠 Vibe Coding Digest" in html
        assert "<h3>Test Source 1</h3>" in html
        assert "<li>Summary 1</li>" in html
        assert "<li>Summary 2</li>" in html
        assert "<h3>Test Source 2</h3>" in html
        assert "<li>Summary 3</li>" in html
        
        # Check Markdown structure  
        assert "## 🧠 Vibe Coding Digest" in md
        assert "### Test Source 1" in md
        assert "- Summary 1" in md
        assert "- Summary 2" in md
        assert "### Test Source 2" in md
        assert "- Summary 3" in md


if __name__ == "__main__":
    pytest.main([__file__, "-v"])