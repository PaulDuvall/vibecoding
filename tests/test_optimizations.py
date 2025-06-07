"""
Tests for OpenAI usage optimizations.
"""

import os
import time
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor

from src.summarize import (
    summarize, summarize_concurrent, batch_summarize, 
    get_openai_client, _content_hash, _summary_cache,
    summarize_async, summarize_concurrent_async, 
    batch_summarize_async, create_smart_batches,
    get_performance_report, AdaptiveRateLimiter
)


class TestOpenAIOptimizations(unittest.TestCase):
    """Test cases for OpenAI usage optimizations."""

    def setUp(self):
        """Set up test environment."""
        # Clear cache before each test
        _summary_cache.clear()

    def test_client_singleton(self):
        """Test that OpenAI client is created once and reused."""
        api_key = "test-key"
        
        client1 = get_openai_client(api_key)
        client2 = get_openai_client(api_key)
        
        # Should return the same instance
        self.assertIs(client1, client2)

    def test_content_caching(self):
        """Test that identical content is cached and reused."""
        content_hash1 = _content_hash("This is test content")
        content_hash2 = _content_hash("This is test content")
        content_hash3 = _content_hash("This is different content")
        
        # Same content should have same hash
        self.assertEqual(content_hash1, content_hash2)
        # Different content should have different hash
        self.assertNotEqual(content_hash1, content_hash3)

    @patch('src.summarize._make_openai_request')
    @patch('src.summarize.get_openai_client')
    def test_summary_caching(self, mock_client, mock_request):
        """Test that summaries are cached to avoid duplicate API calls."""
        mock_client.return_value = Mock()
        mock_request.return_value = "Test summary"
        
        text = "Test content for caching"
        source_name = "Test Source"
        source_url = "https://example.com"
        api_key = "test-key"
        
        # First call
        result1 = summarize(text, source_name, source_url, api_key)
        
        # Second call with same content
        result2 = summarize(text, source_name, source_url, api_key)
        
        # Should return same result
        self.assertEqual(result1, result2)
        
        # OpenAI should only be called once (first time)
        mock_request.assert_called_once()

    @patch('src.summarize.summarize')
    def test_concurrent_processing(self, mock_summarize):
        """Test that concurrent processing calls summarize for each item."""
        mock_summarize.return_value = "Test summary"
        
        items = [
            ("Content 1", "Source 1", "URL 1"),
            ("Content 2", "Source 2", "URL 2"),
            ("Content 3", "Source 3", "URL 3")
        ]
        
        results = summarize_concurrent(items, "test-key", max_workers=2)
        
        # Should process all items
        self.assertEqual(len(results), 3)
        
        # Should call summarize for each item
        self.assertEqual(mock_summarize.call_count, 3)
        
        # Verify results format
        for summary, source_name, source_url in results:
            self.assertEqual(summary, "Test summary")
            self.assertIn(source_name, ["Source 1", "Source 2", "Source 3"])

    @patch('src.summarize.get_openai_client')
    def test_batch_processing(self, mock_client):
        """Test that batch processing combines multiple items."""
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        # Mock batch response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "SUMMARY 1: First article summary\n"
            "SUMMARY 2: Second article summary\n"
            "SUMMARY 3: Third article summary"
        )
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        items = [
            ("Content 1", "Source 1", "URL 1"),
            ("Content 2", "Source 2", "URL 2"),
            ("Content 3", "Source 3", "URL 3")
        ]
        
        results = batch_summarize(items, "test-key", batch_size=3)
        
        # Should return summaries for all items
        self.assertEqual(len(results), 3)
        
        # Should make only one OpenAI call for the batch
        mock_openai_client.chat.completions.create.assert_called_once()
        
        # Verify batch request parameters
        call_args = mock_openai_client.chat.completions.create.call_args
        self.assertGreater(call_args[1]['max_tokens'], 100)  # Should have reasonable token limit
        
        # Verify batch content format
        user_message = call_args[1]['messages'][1]['content']
        self.assertIn("ARTICLE 1:", user_message)
        self.assertIn("ARTICLE 2:", user_message)
        self.assertIn("ARTICLE 3:", user_message)

    @patch('src.summarize.get_openai_client')
    def test_retry_logic(self, mock_client):
        """Test that retry logic works for transient failures."""
        # Mock the client and its method directly to avoid import issues
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        # First two calls fail with rate limit, third succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success summary"
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # Simulate rate limit error
                from openai import RateLimitError
                raise RateLimitError("Rate limit", response=Mock(), body="")
            return mock_response
        
        mock_openai_client.chat.completions.create.side_effect = side_effect
        
        result = summarize("Test content", "Test Source", "https://example.com", "test-key")
        
        # Should eventually succeed
        self.assertEqual(result, "Success summary")
        
        # Should have retried 3 times total
        self.assertEqual(call_count, 3)

    @patch('src.summarize.get_openai_client')
    def test_error_handling(self, mock_client):
        """Test that authentication errors are handled properly."""
        # Mock the client directly
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        # Simulate authentication error
        from openai import AuthenticationError
        mock_openai_client.chat.completions.create.side_effect = AuthenticationError(
            "Invalid API key", response=Mock(), body=""
        )
        
        result = summarize("Test content", "Test Source", "https://example.com", "test-key")
        
        # Should return error message
        self.assertIn("Authentication Error", result)
        self.assertIn("Test Source", result)

    @patch('src.summarize._make_openai_request')
    @patch('src.summarize.get_openai_client')
    def test_cache_size_limit(self, mock_client, mock_request):
        """Test that cache size is limited to prevent memory issues."""
        mock_client.return_value = Mock()
        mock_request.return_value = "Test summary"
        
        # Clear cache first
        _summary_cache.clear()
        
        # Fill cache beyond limit by calling summarize many times
        for i in range(1005):  # More than the 1000 limit
            summarize(f"Content {i}", f"Source {i}", f"URL {i}", "test-key")
        
        # Cache should be trimmed to reasonable size
        self.assertLessEqual(len(_summary_cache), 1000)

    @patch('src.summarize.summarize')
    def test_concurrent_error_handling(self, mock_summarize):
        """Test that concurrent processing handles individual item failures."""
        # First item succeeds, second fails, third succeeds
        mock_summarize.side_effect = [
            "Success summary 1",
            Exception("API Error"),
            "Success summary 3"
        ]
        
        items = [
            ("Content 1", "Source 1", "URL 1"),
            ("Content 2", "Source 2", "URL 2"),
            ("Content 3", "Source 3", "URL 3")
        ]
        
        results = summarize_concurrent(items, "test-key", max_workers=2)
        
        # Should return results for all items (including error fallbacks)
        self.assertEqual(len(results), 3)
        
        # Check that successful items have proper summaries
        success_results = [r for r in results if not r[0].startswith("[Summary unavailable")]
        self.assertEqual(len(success_results), 2)

    def test_performance_metrics(self):
        """Test that performance improvements can be measured."""
        import time
        
        # Simulate time measurement
        start_time = time.time()
        
        # Simulate concurrent processing (mocked)
        with patch('src.summarize.summarize') as mock_summarize:
            mock_summarize.return_value = "Fast summary"
            
            items = [("Content", "Source", "URL")] * 5
            results = summarize_concurrent(items, "test-key", max_workers=3)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Concurrent processing should be reasonably fast
        self.assertLess(processing_time, 1.0)  # Should complete in under 1 second
        self.assertEqual(len(results), 5)

    def test_smart_batching(self):
        """Test that smart batching groups similar content."""
        items = [
            ("Content 1", "Source 1", "https://aws.amazon.com/blog/post1"),
            ("Content 2", "Source 2", "https://aws.amazon.com/blog/post2"),
            ("Content 3", "Source 3", "https://openai.com/blog/post1"),
            ("Content 4", "Source 4", "https://openai.com/blog/post2"),
        ]
        
        batches = create_smart_batches(items, batch_size=2)
        
        # Should group by domain
        self.assertEqual(len(batches), 2)  # Two domains
        
        # Each batch should have items from same domain
        for batch in batches:
            domains = set(item[2].split('/')[2] for item in batch)  # Extract domain
            self.assertEqual(len(domains), 1)  # All items in batch from same domain

    def test_performance_monitor(self):
        """Test performance monitoring functionality."""
        report = get_performance_report()
        
        # Should return all expected metrics
        expected_keys = [
            'cache_hit_rate', 'avg_cost_per_summary', 'avg_tokens_per_summary',
            'avg_latency_ms', 'error_rate', 'total_runtime', 
            'total_api_calls', 'total_cost'
        ]
        
        for key in expected_keys:
            self.assertIn(key, report)

    def test_adaptive_rate_limiter(self):
        """Test adaptive rate limiting functionality."""
        limiter = AdaptiveRateLimiter(base_rpm=60)
        
        # Test header updates
        headers = {
            'x-ratelimit-remaining': '45',
            'x-ratelimit-reset': str(int(time.time()) + 3600)
        }
        
        limiter.update_from_response_headers(headers)
        # Test that headers are stored (the update is checked in acquire method)
        self.assertEqual(limiter.last_headers, headers)

    async def test_async_summarize(self):
        """Test async summarization function."""
        with patch('src.summarize.get_async_openai_client') as mock_client:
            mock_openai_client = AsyncMock()
            mock_client.return_value = mock_openai_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Async test summary"
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            
            mock_openai_client.chat.completions.create.return_value = mock_response
            
            result = await summarize_async(
                "Test content", "Test Source", "https://example.com", "test-key"
            )
            
            self.assertEqual(result, "Async test summary")
            mock_openai_client.chat.completions.create.assert_called_once()

    async def test_async_concurrent_summarization(self):
        """Test async concurrent summarization."""
        with patch('src.summarize.summarize_async') as mock_async_summarize:
            mock_async_summarize.return_value = "Async summary"
            
            items = [
                ("Content 1", "Source 1", "URL 1"),
                ("Content 2", "Source 2", "URL 2"),
                ("Content 3", "Source 3", "URL 3")
            ]
            
            results = await summarize_concurrent_async(items, "test-key", max_concurrent=2)
            
            # Should process all items
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_async_summarize.call_count, 3)
            
            # Verify results format
            for summary, source_name, source_url in results:
                self.assertEqual(summary, "Async summary")

    async def test_async_batch_summarization(self):
        """Test async batch summarization."""
        with patch('src.summarize.get_async_openai_client') as mock_client:
            mock_openai_client = AsyncMock()
            mock_client.return_value = mock_openai_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = (
                "SUMMARY 1: First async summary\n"
                "SUMMARY 2: Second async summary"
            )
            
            mock_openai_client.chat.completions.create.return_value = mock_response
            
            items = [
                ("Content 1", "Source 1", "URL 1"),
                ("Content 2", "Source 2", "URL 2")
            ]
            
            results = await batch_summarize_async(items, "test-key", batch_size=2)
            
            self.assertEqual(len(results), 2)
            mock_openai_client.chat.completions.create.assert_called_once()

    def test_async_integration(self):
        """Integration test for async functions."""
        # Test that async functions are importable and have correct signatures
        from src.summarize import summarize_async, summarize_concurrent_async, batch_summarize_async
        
        # Check function signatures
        import inspect
        
        # summarize_async should be async
        self.assertTrue(inspect.iscoroutinefunction(summarize_async))
        
        # summarize_concurrent_async should be async
        self.assertTrue(inspect.iscoroutinefunction(summarize_concurrent_async))
        
        # batch_summarize_async should be async
        self.assertTrue(inspect.iscoroutinefunction(batch_summarize_async))


if __name__ == '__main__':
    unittest.main()