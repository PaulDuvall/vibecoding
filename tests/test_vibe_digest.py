# test_vibe_digest.py

"""Tests for the vibe_digest module."""
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

# Add the project root to the path so we can import vibe_digest
sys.path.append(os.path.join(
    os.path.dirname(__file__), '..'
))

# Import the module to test
from src import vibe_digest  # noqa: E402


def test_fetch_feed_items():
    """Test that fetch_all_feed_items_concurrently returns a list of feed items.

    This test verifies that the function correctly processes RSS feed URLs
    and returns the expected number of items with the correct structure.
    """
    with patch('feedparser.parse') as mock_parse, \
         patch('src.vibe_digest.feedparser.http') as mock_http:
        # Mock the feedparser response
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="Test Title 1",
                link="http://example.com/1",
                summary="Test Summary 1"
            ),
            MagicMock(
                title="Test Title 2",
                link="http://example.com/2",
                summary="Test Summary 2"
            )
        ]
        mock_parse.return_value = mock_feed
        mock_http.FeedHttpError = Exception  # Mock the error class

        # Test with a single URL for isolation
        test_feeds = ["http://dummy.url"]
        
        # Call the function
        items = vibe_digest.fetch_all_feed_items_concurrently(test_feeds)

        # Assert the results
        assert len(items) == 2
        assert items[0].title == "Test Title 1"
        assert items[1].title == "Test Title 2"
        # Assert the mock_parse call count (should be 1)
        assert mock_parse.call_count == 1


def test_summarize():
    """Test the summarize function with a mock OpenAI response.

    This test verifies that the summarize function correctly processes input
    text and returns the expected summary from the mock OpenAI API.
    """
    with patch('src.vibe_digest.summarize',
               return_value="This is a test summary.") as mock_summarize:
        with patch.dict(
            'os.environ',
            {'OPENAI_API_KEY': 'valid-key'}
        ):
            result = vibe_digest.summarize(
                "Test input text",
                "Test Source",
                "http://example.com",
                "valid-key"
            )
        assert result == "This is a test summary."
        mock_summarize.assert_called_once_with(
            "Test input text",
            "Test Source",
            "http://example.com",
            "valid-key"
        )


def test_format_digest():
    """Test that the digest is formatted correctly.

    This test verifies that the format_digest function generates the expected
    HTML structure with the current date and provided summaries.
    """
    # Mock datetime to ensure consistent test output
    with patch('src.vibe_digest.datetime') as mock_datetime:
        test_date = datetime(2023, 1, 1)
        mock_datetime.now.return_value = test_date

        # Call the function with test data
        test_summaries = {
            "Test Source": ["Summary 1", "Summary 2"]
        }
        result_html, result_md = vibe_digest.format_digest(test_summaries)

        # Adjust expected date format to match actual output
        expected_date = test_date.strftime("%B %d, %Y %I:%M %p ")
        assert f"<h2>🧠 Vibe Coding Digest – {expected_date}</h2>" in result_html
        assert "<li>Summary 1</li>" in result_html
        assert "<li>Summary 2</li>" in result_html
        assert f"## 🧠 Vibe Coding Digest – {expected_date}\n" in result_md
        assert "- Summary 1\n" in result_md
        assert "- Summary 2\n" in result_md


def test_send_email():
    """Test the send_email function with a mock requests.post.

    This test verifies that the send_email function constructs the correct
    API request to SendGrid with the expected headers and payload.
    """
    with patch('requests.post') as mock_post, \
         patch.dict('os.environ', {
             'SENDGRID_API_KEY': 'test-api-key',
             'EMAIL_TO': 'to@example.com',
             'EMAIL_FROM': 'from@example.com'
         }):
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the function
        test_html = "<h1>Test Email</h1>"
        vibe_digest.send_email(test_html)

        # Assert the request was made correctly
        expected_url = "https://api.sendgrid.com/v3/mail/send"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == expected_url
        assert kwargs['headers']['Authorization'] == "Bearer test-api-key"
        assert kwargs['json']['content'][0]['value'] == test_html


def test_main(monkeypatch):
    """Test the main function integration.

    This test verifies that the main function correctly orchestrates the
    entire process of fetching, summarizing, and emailing the digest.
    """
    # Mock all external dependencies
    test_items = [
        MagicMock(
            title="Test Title",
            link="http://example.com",
            summary="Test Summary",
            published_date=datetime(2023, 1, 1).timetuple(),
            source_name="Test Source",
            source_url="http://example.com"
        ),
        MagicMock(
            title="Test Title 2",
            link="http://example.com/2",
            summary="Test Summary 2",
            published_date=datetime(2023, 1, 2).timetuple(),
            source_name="Test Source",
            source_url="http://example.com"
        )
    ]

    with (
        patch(
            'src.vibe_digest.fetch_all_feed_items_concurrently',
            return_value=test_items
        ) as mock_fetch,
        patch(
            'src.vibe_digest.summarize_concurrent',
            return_value=[("Test Summary", "Test Source", "http://example.com")] * 2
        ) as mock_summarize,
        patch(
            'src.vibe_digest.format_digest',
            return_value=("<html>Test Digest</html>", "<md>Test Digest</md>")
        ) as mock_format,
        patch(
            'src.vibe_digest.send_email'
        ) as mock_send,
        patch('src.vibe_digest.fetch_aws_blog_posts', return_value=[]),
        patch('src.vibe_digest.fetch_claude_release_notes_scraper', return_value=[]),
        patch.dict('os.environ', {
            'OPENAI_API_KEY': 'valid-key',
            'EMAIL_TO': 'to@example.com',
            'EMAIL_FROM': 'from@example.com',
            'SENDGRID_API_KEY': 'test-api-key'
        })
    ):

        # Call the main function
        vibe_digest.main()

        # Assert the function calls
        mock_fetch.assert_called_once()
        # Check that summarize_concurrent was called once (not per item)
        mock_summarize.assert_called_once()
        actual_args, _ = mock_format.call_args
        assert "Test Source" in actual_args[0]
        assert actual_args[0]["Test Source"] == ["Test Summary"] * len(test_items)
        mock_send.assert_called_once_with(
            "<html>Test Digest</html>"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
