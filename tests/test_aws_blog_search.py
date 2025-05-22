import sys
import os

# Ensure the scripts directory is in the path BEFORE importing aws_blog_search
_project_root_scripts_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../.github/scripts'
    )
)
if _project_root_scripts_path not in sys.path:
    sys.path.insert(0, _project_root_scripts_path)
import unittest
from unittest.mock import patch, MagicMock
from aws_blog_search import _is_query_match, fetch_aws_blog_posts

class FeedEntry(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class TestAwsBlogSearch(unittest.TestCase):

    # Tests for _is_query_match

    def test_is_query_match_single_word_case_insensitive(self):
        self.assertTrue(_is_query_match("Hello World", "hello"))
        self.assertTrue(_is_query_match("Hello World", "WORLD"))

    def test_is_query_match_exact_phrase_case_insensitive(self):
        self.assertTrue(_is_query_match("This is a test phrase", "test phrase"))
        # Should match all words
        self.assertTrue(
            _is_query_match("This is a test phrase", "THIS IS A TEST")
        )

    def test_is_query_match_all_words_present_case_insensitive_different_order(self):
        self.assertTrue(_is_query_match("Find these words here", "words find here"))
        self.assertTrue(_is_query_match("Find these WORDS here", "HERE find WoRdS"))

    def test_is_query_match_no_match(self):
        self.assertFalse(_is_query_match("Hello World", "goodbye"))
        # "there" is not in text
        self.assertFalse(
            _is_query_match("Hello World", "hello there world")
        )

    def test_is_query_match_query_with_mixed_casing(self):
        self.assertTrue(_is_query_match("Test with Mixed Case", "MiXeD CaSe"))

    def test_is_query_match_text_with_mixed_casing(self):
        self.assertTrue(_is_query_match("TeSt WiTh MiXeD CaSe", "mixed case"))

    def test_is_query_match_partial_word_should_not_match(self):
        self.assertFalse(_is_query_match("Partial words should not match", "part"))
        self.assertFalse(_is_query_match("Partial words should not match", "shoulder"))
        # All words present, any order, should match (True)
        self.assertTrue(
            _is_query_match(
                "Partial words should not match",
                "words match partial"
            )
        )

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_default_queries(self, mock_is_query_match,
                                                  mock_parse):
        # Simulate feed entries
        mock_entry1 = FeedEntry({
            "title": "Test Post 1",
            "link": "http://example.com/1",
            "summary": "Summary about vibe coding"
        })
        mock_entry2 = FeedEntry({
            "title": "Test Post 2",
            "link": "http://example.com/2",
            "summary": "Another post on security engineering"
        })
        mock_entry3 = FeedEntry({
            "title": "Test Post 3",
            "link": "http://example.com/3",
            "summary": "DevOps and agentic coding"
        })
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry1, mock_entry2, mock_entry3]
        mock_parse.return_value = mock_feed

        # Simulate _is_query_match returning True for specific calls
        # Default queries: "vibe coding", "security engineering",
        # "vibe coding security"
        # Always include: "agentic coding", "amazon q developer", "codewhisperer",
        # "vibe coding security engineering", "vibe coding security"

        def side_effect_is_query_match(text, query):
            print(f"_is_query_match called with text: '{text}', query: '{query}'")
            # Mimic all-words-present logic
            words = query.lower().split()
            text_lower = text.lower()
            return all(word in text_lower for word in words)

        mock_is_query_match.side_effect = side_effect_is_query_match

        results = fetch_aws_blog_posts(max_results_per_query=1)

        # Expect one for each matching query that _is_query_match handles
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['title'], "Test Post 1")
        self.assertEqual(results[1]['title'], "Test Post 2")
        self.assertEqual(results[2]['title'], "Test Post 3")

        # Check a subset of calls involving the matched entries
        mock_is_query_match.assert_any_call(
            mock_entry1.title + "\n" + mock_entry1.summary,
            "vibe coding"
        )
        mock_is_query_match.assert_any_call(
            mock_entry2.title + "\n" + mock_entry2.summary,
            "security engineering"
        )
        mock_is_query_match.assert_any_call(
            mock_entry3.title + "\n" + mock_entry3.summary,
            "agentic coding"
        )

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_provided_queries_and_max_results(
        self, mock_is_query_match, mock_parse
    ):
        mock_entry1 = FeedEntry({
            "title": "Custom Query Post 1",
            "link": "http://custom.com/1",
            "summary": "About custom1"
        })
        mock_entry2 = FeedEntry({
            "title": "Custom Query Post 2",
            "link": "http://custom.com/2",
            "summary": "More on custom1"
        })
        mock_entry3 = FeedEntry({
            "title": "Another Query Post",
            "link": "http://custom.com/3",
            "summary": "About custom2"
        })
        mock_entry4 = FeedEntry({
            "title": "Always Included Post",
            "link": "http://custom.com/4",
            "summary": "Topic: codewhisperer"
        })

        mock_feed = MagicMock()
        mock_feed.entries = [
            mock_entry1,
            mock_entry2,
            mock_entry3,
            mock_entry4
        ]
        mock_parse.return_value = mock_feed

        # Simulate _is_query_match
        def side_effect_is_query_match(text, query):
            # Mimic all-words-present logic
            words = query.lower().split()
            text_lower = text.lower()
            return all(word in text_lower for word in words)

        mock_is_query_match.side_effect = side_effect_is_query_match

        base_queries = ["custom1", "custom2"]
        results = fetch_aws_blog_posts(
            base_queries=base_queries, max_results_per_query=1
        )

        # Expected: one for "custom1", one for "custom2",
        # one for "codewhisperer" (always included)
        self.assertEqual(len(results), 3)
        titles = [r['title'] for r in results]
        # From custom1
        self.assertIn("Custom Query Post 1", titles)
        # From custom2
        self.assertIn("Another Query Post", titles)
        # From codewhisperer
        self.assertIn("Always Included Post", titles)

        # Check that _is_query_match was called with base and
        # always-included queries
        mock_is_query_match.assert_any_call(
            mock_entry1.title + "\n" + mock_entry1.summary,
            "custom1"
        )
        mock_is_query_match.assert_any_call(
            mock_entry3.title + "\n" + mock_entry3.summary,
            "custom2"
        )
        mock_is_query_match.assert_any_call(
            mock_entry4.title + "\n" + mock_entry4.summary,
            "codewhisperer"
        )

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_max_results_logic(self, mock_is_query_match,
                                                    mock_parse):
        # Create more entries than max_results_per_query to test limiting
        mock_entries = []
        for i in range(5):
            mock_entries.append(
                MagicMock(
                    title=f"Post {i}",
                    link=f"http://example.com/{i}",
                    summary=f"Topic: testquery item {i}"
                )
            )
        mock_feed = MagicMock()
        mock_feed.entries = mock_entries
        mock_parse.return_value = mock_feed

        # To make it precise, let's refine the side_effect
        def side_effect_is_query_match_max_results(text, query):
            if query == "testquery":
                return True
            # Let's assume always-included queries don't match for this
            # specific test to isolate the max_results_per_query for
            # "testquery".
            if query in [
                "agentic coding",
                "amazon q developer",
                "codewhisperer",
                "vibe coding security engineering",
                "vibe coding security"
            ]:
                return False
            return False  # Default to False if not one of the above

        mock_is_query_match.side_effect = side_effect_is_query_match_max_results

        results = fetch_aws_blog_posts(
            base_queries=["testquery"], max_results_per_query=2
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], "Post 0")
        self.assertEqual(results[1]['title'], "Post 1")

    @patch('aws_blog_search.feedparser.parse')
    @patch('aws_blog_search._is_query_match')
    def test_fetch_aws_blog_posts_always_include_queries_are_added(
            self, mock_is_query_match, mock_parse):
        mock_entry_base = FeedEntry({
            "title": "Base Query Item",
            "link": "http://example.com/base",
            "summary": "Content for base_query"
        })
        mock_entry_always = FeedEntry({
            "title": "Always Query Item",
            "link": "http://example.com/always",
            "summary": "Content for agentic coding"
        })

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry_base, mock_entry_always]
        mock_parse.return_value = mock_feed

        def side_effect_always_include(text, query):
            print(f"_is_query_match called with text: '{text}', query: '{query}'")
            # Mimic all-words-present logic
            words = query.lower().split()
            text_lower = text.lower()
            return all(word in text_lower for word in words)
        mock_is_query_match.side_effect = side_effect_always_include

        results = fetch_aws_blog_posts(
            base_queries=["base_query"], max_results_per_query=1
        )
        # One from base_query, one from "agentic coding"
        self.assertEqual(len(results), 2)
        titles = [r['title'] for r in results]
        self.assertIn("Base Query Item", titles)
        self.assertIn("Always Query Item", titles)
        # Verify that _is_query_match was called for both types of queries
        mock_is_query_match.assert_any_call(
            mock_entry_base.title + "\n" + mock_entry_base.summary,
            "base_query"
        )
        mock_is_query_match.assert_any_call(
            mock_entry_always.title + "\n" + mock_entry_always.summary,
            "agentic coding"
        )


if __name__ == '__main__':
    unittest.main()

# This is the last line of text.
