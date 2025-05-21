import sys
import os
import unittest
from unittest.mock import patch, MagicMock, ANY
import logging # For checking log calls
import openai # For exception types

# Add the scripts directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts')))

from summarize import summarize # Target for testing

# Disable logging for tests to keep output clean, we will check calls to logging.error directly
logging.disable(logging.CRITICAL)

class TestSummarizeScript(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.source_name = "Test Source"
        self.source_url = "http://example.com/test"
        self.text_to_summarize = "This is a long text that needs summarization."
        self.mock_openai_patch = patch('summarize.openai.chat.completions.create')
        self.mock_openai_create = self.mock_openai_patch.start()
        self.mock_logging_error_patch = patch('summarize.logging.error')
        self.mock_logging_error = self.mock_logging_error_patch.start()

    def tearDown(self):
        self.mock_openai_patch.stop()
        self.mock_logging_error_patch.stop()

    def test_successful_summarization(self):
        expected_summary = "This is a summary."
        mock_choice = MagicMock()
        mock_choice.message.content = expected_summary
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        self.mock_openai_create.return_value = mock_response

        summary = summarize(self.text_to_summarize, self.source_name, self.source_url, self.api_key)

        self.assertEqual(summary, expected_summary)
        self.mock_openai_create.assert_called_once()
        # Check that openai.api_key was set
        self.assertEqual(openai.api_key, self.api_key)
        self.mock_logging_error.assert_not_called()

    def _test_openai_error_scenario(self, error_class, error_message_contains, expected_return_message, include_response_in_error=True):
        if include_response_in_error:
            mock_response = MagicMock()
            mock_response.text = "Error details from API"
            error_instance = error_class("Mocked error message", response=mock_response, status_code=500)
            if hasattr(error_instance, 'param'): # For InvalidRequestError
                 error_instance.param = "test_param"
        else: # For errors like APIConnectionError, APITimeoutError that might not have a response object
            error_instance = error_class("Mocked error message")


        self.mock_openai_create.side_effect = error_instance

        summary = summarize(self.text_to_summarize, self.source_name, self.source_url, self.api_key)

        self.assertEqual(summary, f"[Summary unavailable for {self.source_name} - {expected_return_message}]")
        self.mock_openai_create.assert_called_once()
        self.mock_logging_error.assert_called_once()
        # Check that the log message contains specific parts of the error
        args, _ = self.mock_logging_error.call_args
        log_message = args[0]
        self.assertIn(error_class.__name__, log_message)
        self.assertIn(self.source_name, log_message)
        if hasattr(error_instance, 'status_code') and error_instance.status_code:
             self.assertIn(str(error_instance.status_code), log_message)
        if hasattr(error_instance, 'message') and error_instance.message:
             self.assertIn(error_instance.message, log_message)


    def test_rate_limit_error(self):
        self._test_openai_error_scenario(openai.RateLimitError, "RateLimitError", "OpenAI Rate Limit Error")

    def test_authentication_error(self):
        self._test_openai_error_scenario(openai.AuthenticationError, "AuthenticationError", "OpenAI Authentication Error")

    def test_api_connection_error(self):
        self._test_openai_error_scenario(openai.APIConnectionError, "APIConnectionError", "OpenAI Connection Error", include_response_in_error=False)
        
    def test_api_timeout_error(self):
        self._test_openai_error_scenario(openai.APITimeoutError, "APITimeoutError", "OpenAI Timeout Error", include_response_in_error=False)

    def test_invalid_request_error(self):
        self._test_openai_error_scenario(openai.InvalidRequestError, "InvalidRequestError", "OpenAI Invalid Request Error")

    def test_generic_api_error(self):
        self._test_openai_error_scenario(openai.APIError, "APIError", "OpenAI API Error")

    def test_generic_exception(self):
        # For generic Exception, the structure of error_instance and logging might differ
        error_instance = Exception("Generic test error")
        self.mock_openai_create.side_effect = error_instance

        summary = summarize(self.text_to_summarize, self.source_name, self.source_url, self.api_key)

        self.assertEqual(summary, f"[Summary unavailable for {self.source_name} - Internal Error]")
        self.mock_openai_create.assert_called_once()
        self.mock_logging_error.assert_called_once()
        args, _ = self.mock_logging_error.call_args
        log_message = args[0]
        self.assertIn("Unexpected error", log_message)
        self.assertIn(self.source_name, log_message)
        self.assertIn("Exception - Generic test error", log_message) # Check type and message

if __name__ == '__main__':
    unittest.main()
