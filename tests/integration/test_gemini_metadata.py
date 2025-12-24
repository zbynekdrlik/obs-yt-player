"""
Integration tests for ytplay_modules.gemini_metadata

Tests for Gemini API integration with mocked HTTP responses.
Target: 80%+ coverage
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import urllib.error


class TestExtractMetadataWithGemini:
    """Tests for extract_metadata_with_gemini function."""

    def test_returns_none_without_api_key(self):
        """Should return None, None when no API key provided."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        artist, song = extract_metadata_with_gemini(
            video_id="dQw4w9WgXcQ",
            video_title="Test Title",
            api_key=None
        )

        assert artist is None
        assert song is None

    def test_returns_none_with_empty_api_key(self):
        """Should return None, None when API key is empty."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        artist, song = extract_metadata_with_gemini(
            video_id="dQw4w9WgXcQ",
            video_title="Test Title",
            api_key=""
        )

        assert artist is None
        assert song is None

    @patch("urllib.request.urlopen")
    def test_successful_extraction(self, mock_urlopen):
        """Should extract artist and song from valid Gemini response."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        # Create mock response
        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"artist": "Rick Astley", "song": "Never Gonna Give You Up"}'
                    }]
                }
            }]
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="dQw4w9WgXcQ",
            video_title="Rick Astley - Never Gonna Give You Up",
            api_key="test_api_key"
        )

        assert artist == "Rick Astley"
        assert song == "Never Gonna Give You Up"

    @patch("urllib.request.urlopen")
    def test_handles_json_in_markdown_code_block(self, mock_urlopen):
        """Should handle JSON wrapped in markdown code blocks."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```json\n{"artist": "Elevation Worship", "song": "The Blessing"}\n```'
                    }]
                }
            }]
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="The Blessing | Elevation Worship",
            api_key="test_api_key"
        )

        assert artist == "Elevation Worship"
        assert song == "The Blessing"

    @patch("urllib.request.urlopen")
    def test_handles_song_only_response(self, mock_urlopen):
        """Should handle response with song but no artist."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"artist": "", "song": "Unknown Song Title"}'
                    }]
                }
            }]
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Some Video",
            api_key="test_api_key"
        )

        assert artist is None  # Empty string becomes None
        assert song == "Unknown Song Title"

    @patch("urllib.request.urlopen")
    def test_returns_none_on_http_error(self, mock_urlopen):
        """Should return None, None on HTTP error."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        mock_error = urllib.error.HTTPError(
            url="http://test.com",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=MagicMock()
        )
        mock_error.read = MagicMock(return_value=b'{"error": "test"}')
        mock_urlopen.side_effect = mock_error

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        assert artist is None
        assert song is None

    @patch("urllib.request.urlopen")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_rate_limit_retry_with_backoff(self, mock_sleep, mock_urlopen):
        """Should retry with exponential backoff on rate limit (429)."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        # First call fails with 429, second succeeds
        mock_error = urllib.error.HTTPError(
            url="http://test.com",
            code=429,
            msg="Rate Limited",
            hdrs={},
            fp=MagicMock()
        )
        mock_error.read = MagicMock(return_value=b'{"error": "rate limited"}')

        success_response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"artist": "Artist", "song": "Song"}'
                    }]
                }
            }]
        }

        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps(success_response_data).encode('utf-8')
        mock_success.__enter__ = MagicMock(return_value=mock_success)
        mock_success.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [mock_error, mock_success]

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        # Should have succeeded on retry
        assert artist == "Artist"
        assert song == "Song"
        # Sleep should have been called for backoff
        mock_sleep.assert_called()

    @patch("urllib.request.urlopen")
    def test_returns_none_on_url_error(self, mock_urlopen):
        """Should return None, None on URL/network error."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        assert artist is None
        assert song is None

    @patch("urllib.request.urlopen")
    def test_handles_invalid_json_response(self, mock_urlopen):
        """Should handle invalid JSON in response text."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Not valid JSON at all"
                    }]
                }
            }]
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        assert artist is None
        assert song is None

    @patch("urllib.request.urlopen")
    def test_handles_empty_candidates(self, mock_urlopen):
        """Should handle response with no candidates."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        response_data = {
            "candidates": []
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        assert artist is None
        assert song is None

    @patch("urllib.request.urlopen")
    def test_handles_missing_song_in_response(self, mock_urlopen):
        """Should handle response missing song field."""
        from ytplay_modules.gemini_metadata import extract_metadata_with_gemini

        response_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"artist": "Some Artist"}'
                    }]
                }
            }]
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        artist, song = extract_metadata_with_gemini(
            video_id="test123",
            video_title="Test Title",
            api_key="test_api_key"
        )

        # Song is required, so should return None
        assert artist is None
        assert song is None


class TestGeminiFailureTracking:
    """Tests for Gemini failure tracking functions."""

    def test_clear_gemini_failures(self):
        """Should clear the failure set."""
        from ytplay_modules.gemini_metadata import (
            clear_gemini_failures, is_gemini_failed, _gemini_failures
        )

        # Add a failure manually
        _gemini_failures.add("test_video")

        clear_gemini_failures()

        assert not is_gemini_failed("test_video")

    def test_remove_gemini_failure(self):
        """Should remove specific video from failures."""
        from ytplay_modules.gemini_metadata import (
            remove_gemini_failure, is_gemini_failed, _gemini_failures,
            clear_gemini_failures
        )

        clear_gemini_failures()
        _gemini_failures.add("video_to_remove")

        assert is_gemini_failed("video_to_remove")

        remove_gemini_failure("video_to_remove")

        assert not is_gemini_failed("video_to_remove")

    def test_remove_nonexistent_failure(self):
        """Should handle removing nonexistent video gracefully."""
        from ytplay_modules.gemini_metadata import remove_gemini_failure

        # Should not raise
        remove_gemini_failure("nonexistent_video")

    def test_is_gemini_failed(self):
        """Should check if video has failed."""
        from ytplay_modules.gemini_metadata import (
            is_gemini_failed, _gemini_failures, clear_gemini_failures
        )

        clear_gemini_failures()
        _gemini_failures.add("failed_video")

        assert is_gemini_failed("failed_video") is True
        assert is_gemini_failed("other_video") is False


class TestCleanGeminiSongTitle:
    """Tests for clean_gemini_song_title function."""

    def test_returns_song_unchanged(self):
        """Should return song title unchanged (cleaning handled elsewhere)."""
        from ytplay_modules.gemini_metadata import clean_gemini_song_title

        result = clean_gemini_song_title("My Song Title")
        assert result == "My Song Title"
