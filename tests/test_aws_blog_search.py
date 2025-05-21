import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call
import pytest

# Add the scripts directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts')))

from aws_blog_search import _is_query_match, fetch_aws_blog_posts

class TestAwsBlogSearch(unittest.TestCase):

    # Tests for _is_query_match
    def test_is_query_match_single_word_case_insensitive(self):
        self.assertTrue(_is_query_match("Hello World", "hello"))
        self.assertTrue(_is_query_match("Hello World", "WORLD"))

    def test_is_query_match_exact_phrase_case_insensitive(self):
        self.assertTrue(_is_query_match("This is a test phrase", "test phrase"))
        self.assertTrue(_is_query_match("This is a test phrase", "THIS IS A TEST")) # Should match all words

    def test_is_query_match_all_words_present_case_insensitive_different_order(self):
        self.assertTrue(_is_query_match("Find these words here", "words find here"))
        self.assertTrue(_is_query_match("Find these WORDS here", "HERE find WoRdS"))

    def test_is_query_match_no_match(self):
        self.assertFalse(_is_query_match("Hello World", "goodbye"))
        self.assertFalse(_is_query_match("Hello World", "hello there world")) # "there" is not in text

    def test_is_query_match_query_with_mixed_casing(self):
        self.assertTrue(_is_query_match("Test with Mixed Case", "MiXeD CaSe"))

    def test_is_query_match_text_with_mixed_casing(self):
        self.assertTrue(_is_query_match("TeSt WiTh MiXeD CaSe", "mixed case"))

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_default_queries(self, mock_is_query_match, mock_parse):
        # Simulate feed entries
        mock_entry1 = MagicMock(title="Test Post 1", link="http://example.com/1", summary="Summary about vibe coding")
        mock_entry2 = MagicMock(title="Test Post 2", link="http://example.com/2", summary="Another post on security engineering")
        mock_entry3 = MagicMock(title="Test Post 3", link="http://example.com/3", summary="DevOps and agentic coding")
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry1, mock_entry2, mock_entry3]
        mock_parse.return_value = mock_feed

        # Simulate _is_query_match returning True for specific calls
        # Default queries: "vibe coding", "security engineering", "vibe coding security"
        # Always include: "agentic coding", "amazon q developer", "codewhisperer", "vibe coding security engineering", "vibe coding security"
        def side_effect_is_query_match(text, query):
            text_lower = text.lower()
            if query == "vibe coding" and "vibe coding" in text_lower: return True
            if query == "security engineering" and "security engineering" in text_lower: return True
            if query == "agentic coding" and "agentic coding" in text_lower: return True
            return False

        mock_is_query_match.side_effect = side_effect_is_query_match

        results = fetch_aws_blog_posts(max_results_per_query=1)

        self.assertEqual(len(results), 3) # Expect one for each matching query that _is_query_match handles
        self.assertEqual(results[0]['title'], "Test Post 1")
        self.assertEqual(results[1]['title'], "Test Post 2")
        self.assertEqual(results[2]['title'], "Test Post 3")

        expected_calls = [
            call(mock_entry1.title + "\n" + mock_entry1.summary, "vibe coding"),
            call(mock_entry2.title + "\n" + mock_entry2.summary, "vibe coding"), # no match based on side_effect
            call(mock_entry3.title + "\n" + mock_entry3.summary, "vibe coding"), # no match
            call(mock_entry1.title + "\n" + mock_entry1.summary, "security engineering"), # no match
            call(mock_entry2.title + "\n" + mock_entry2.summary, "security engineering"),
            call(mock_entry3.title + "\n" + mock_entry3.summary, "security engineering"), # no match
            call(mock_entry1.title + "\n" + mock_entry1.summary, "vibe coding security"), # no match
            call(mock_entry2.title + "\n" + mock_entry2.summary, "vibe coding security"), # no match
            call(mock_entry3.title + "\n" + mock_entry3.summary, "vibe coding security"), # no match
            call(mock_entry1.title + "\n" + mock_entry1.summary, "agentic coding"), # no match
            call(mock_entry2.title + "\n" + mock_entry2.summary, "agentic coding"), # no match
            call(mock_entry3.title + "\n" + mock_entry3.summary, "agentic coding"),
        ]
        # Check a subset of calls involving the matched entries
        mock_is_query_match.assert_any_call(mock_entry1.title + "\n" + mock_entry1.summary, "vibe coding")
        mock_is_query_match.assert_any_call(mock_entry2.title + "\n" + mock_entry2.summary, "security engineering")
        mock_is_query_match.assert_any_call(mock_entry3.title + "\n" + mock_entry3.summary, "agentic coding")


    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_provided_queries_and_max_results(self, mock_is_query_match, mock_parse):
        mock_entry1 = MagicMock(title="Custom Query Post 1", link="http://custom.com/1", summary="About custom1")
        mock_entry2 = MagicMock(title="Custom Query Post 2", link="http://custom.com/2", summary="More on custom1")
        mock_entry3 = MagicMock(title="Another Query Post", link="http://custom.com/3", summary="About custom2")
        mock_entry4 = MagicMock(title="Always Included Post", link="http://custom.com/4", summary="Topic: codewhisperer")

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry1, mock_entry2, mock_entry3, mock_entry4]
        mock_parse.return_value = mock_feed

        # Simulate _is_query_match
        def side_effect_is_query_match(text, query):
            text_lower = text.lower()
            if query == "custom1" and "custom1" in text_lower: return True
            if query == "custom2" and "custom2" in text_lower: return True
            if query == "codewhisperer" and "codewhisperer" in text_lower: return True
            return False
        mock_is_query_match.side_effect = side_effect_is_query_match

        base_queries = ["custom1", "custom2"]
        results = fetch_aws_blog_posts(base_queries=base_queries, max_results_per_query=1)

        # Expected: one for "custom1", one for "custom2", one for "codewhisperer" (always included)
        self.assertEqual(len(results), 3)
        titles = [r['title'] for r in results]
        self.assertIn("Custom Query Post 1", titles) # From custom1
        self.assertIn("Another Query Post", titles)  # From custom2
        self.assertIn("Always Included Post", titles) # From codewhisperer

        # Check that _is_query_match was called with base and always-included queries
        mock_is_query_match.assert_any_call(mock_entry1.title + "\n" + mock_entry1.summary, "custom1")
        mock_is_query_match.assert_any_call(mock_entry3.title + "\n" + mock_entry3.summary, "custom2")
        mock_is_query_match.assert_any_call(mock_entry4.title + "\n" + mock_entry4.summary, "codewhisperer")

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_max_results_logic(self, mock_is_query_match, mock_parse):
        # Create more entries than max_results_per_query to test limiting
        mock_entries = []
        for i in range(5):
            mock_entries.append(MagicMock(title=f"Post {i}", link=f"http://example.com/{i}", summary=f"Topic: testquery item {i}"))
        
        mock_feed = MagicMock()
        mock_feed.entries = mock_entries
        mock_parse.return_value = mock_feed

        mock_is_query_match.return_value = True # Match all for simplicity

        results = fetch_aws_blog_posts(base_queries=["testquery"], max_results_per_query=2)
        
        # Should be 2 from "testquery" + number of always-included queries that find matches (assuming they also match)
        # For simplicity, let's assume only "testquery" matches.
        # If always-included queries also match, this count would be higher.
        # To make it precise, let's refine the side_effect
        def side_effect_is_query_match_max_results(text, query):
            if query == "testquery": return True
            # Let's assume always-included queries don't match for this specific test
            # to isolate the max_results_per_query for "testquery".
            if query in ["agentic coding", "amazon q developer", "codewhisperer", "vibe coding security engineering", "vibe coding security"]:
                return False
            return False
        mock_is_query_match.side_effect = side_effect_is_query_match_max_results
        
        results = fetch_aws_blog_posts(base_queries=["testquery"], max_results_per_query=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], "Post 0")
        self.assertEqual(results[1]['title'], "Post 1")

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_always_include_queries_are_added(self, mock_is_query_match, mock_parse):
        mock_entry_base = MagicMock(title="Base Query Item", link="http://example.com/base", summary="Content for base_query")
        mock_entry_always = MagicMock(title="Always Query Item", link="http://example.com/always", summary="Content for agentic coding")
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry_base, mock_entry_always]
        mock_parse.return_value = mock_feed

        def side_effect_always_include(text, query):
            if query == "base_query" and "base_query" in text: return True
            if query == "agentic coding" and "agentic coding" in text: return True
            return False
        mock_is_query_match.side_effect = side_effect_always_include

        results = fetch_aws_blog_posts(base_queries=["base_query"], max_results_per_query=1)
        
        self.assertEqual(len(results), 2) # One from base_query, one from "agentic coding"
        titles = [r['title'] for r in results]
        self.assertIn("Base Query Item", titles)
        self.assertIn("Always Query Item", titles)
        
        # Verify that _is_query_match was called for both types of queries
        mock_is_query_match.assert_any_call(mock_entry_base.title + "\n" + mock_entry_base.summary, "base_query")
        mock_is_query_match.assert_any_call(mock_entry_always.title + "\n" + mock_entry_always.summary, "agentic coding")


if __name__ == '__main__':
    unittest.main()
