"""
Integration tests for ytplay_modules.tools

Tests for tool download, extraction, and verification.
Uses mocked subprocess and urllib for testing.
"""

import os
import subprocess
from unittest.mock import MagicMock, patch

# Mock Windows-specific subprocess attributes for Linux testing
if not hasattr(subprocess, "STARTUPINFO"):
    subprocess.STARTUPINFO = MagicMock
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0


class TestDownloadFile:
    """Tests for download_file function."""

    @patch("urllib.request.urlretrieve")
    def test_successful_download(self, mock_urlretrieve, tmp_path):
        """Should download file successfully."""
        from ytplay_modules.tools import download_file

        dest = str(tmp_path / "test_file.exe")

        result = download_file("http://example.com/file.exe", dest, "test file")

        assert result is True
        mock_urlretrieve.assert_called_once()

    @patch("urllib.request.urlretrieve")
    def test_download_creates_parent_directory(self, mock_urlretrieve, tmp_path):
        """Should create parent directory if it doesn't exist."""
        from ytplay_modules.tools import download_file

        dest = str(tmp_path / "subdir" / "test_file.exe")

        download_file("http://example.com/file.exe", dest, "test file")

        # Parent directory should have been created
        assert os.path.exists(str(tmp_path / "subdir"))

    @patch("urllib.request.urlretrieve")
    def test_download_handles_exception(self, mock_urlretrieve):
        """Should return False on download error."""
        from ytplay_modules.tools import download_file

        mock_urlretrieve.side_effect = Exception("Network error")

        result = download_file("http://example.com/file.exe", "/tmp/test.exe", "test")

        assert result is False


class TestExtractFfmpeg:
    """Tests for extract_ffmpeg function."""

    def test_extracts_ffmpeg_from_archive(self, tmp_path):
        """Should extract ffmpeg.exe from zip archive."""
        import zipfile

        from ytplay_modules.config import FFMPEG_FILENAME
        from ytplay_modules.tools import extract_ffmpeg

        # Create a test zip file with ffmpeg.exe
        archive_path = tmp_path / "ffmpeg.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            # Use path that ends with ffmpeg.exe to match the check
            zf.writestr("ffmpeg-release/bin/ffmpeg.exe", b"fake ffmpeg content")

        result = extract_ffmpeg(str(archive_path), str(tmp_path))

        assert result is True
        # Check for the configured filename
        assert (tmp_path / FFMPEG_FILENAME).exists()

    def test_returns_false_when_ffmpeg_not_found(self, tmp_path):
        """Should return False when ffmpeg.exe not in archive."""
        import zipfile

        from ytplay_modules.tools import extract_ffmpeg

        # Create a zip without ffmpeg.exe
        archive_path = tmp_path / "other.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("other_file.txt", b"some content")

        result = extract_ffmpeg(str(archive_path), str(tmp_path))

        assert result is False

    def test_handles_invalid_archive(self, tmp_path):
        """Should return False for invalid archive."""
        from ytplay_modules.tools import extract_ffmpeg

        # Create a non-zip file
        bad_archive = tmp_path / "bad.zip"
        bad_archive.write_bytes(b"not a zip file")

        result = extract_ffmpeg(str(bad_archive), str(tmp_path))

        assert result is False


class TestVerifyTool:
    """Tests for verify_tool function."""

    @patch("subprocess.run")
    def test_verifies_working_tool(self, mock_run):
        """Should return True for working tool."""
        from ytplay_modules.tools import verify_tool

        mock_run.return_value = MagicMock(returncode=0)

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is True

    @patch("subprocess.run")
    def test_returns_false_for_failing_tool(self, mock_run):
        """Should return False when tool returns non-zero."""
        from ytplay_modules.tools import verify_tool

        mock_run.return_value = MagicMock(returncode=1)

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is False

    @patch("subprocess.run")
    def test_handles_timeout(self, mock_run):
        """Should return False on timeout."""
        from ytplay_modules.tools import verify_tool

        mock_run.side_effect = subprocess.TimeoutExpired("tool", 5)

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is False

    @patch("subprocess.run")
    def test_handles_exception(self, mock_run):
        """Should return False on exception."""
        from ytplay_modules.tools import verify_tool

        mock_run.side_effect = Exception("Error running tool")

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is False


class TestDownloadYtdlp:
    """Tests for download_ytdlp function."""

    @patch("ytplay_modules.tools.verify_tool")
    @patch("os.path.exists")
    def test_skips_if_already_exists_and_works(self, mock_exists, mock_verify):
        """Should skip download if yt-dlp already exists and works."""
        from ytplay_modules.tools import download_ytdlp

        mock_exists.return_value = True
        mock_verify.return_value = True

        result = download_ytdlp("/path/to/tools")

        assert result is True

    @patch("ytplay_modules.tools.download_file")
    @patch("ytplay_modules.tools.verify_tool")
    @patch("os.path.exists")
    def test_downloads_when_missing(self, mock_exists, mock_verify, mock_download):
        """Should download yt-dlp when missing."""
        from ytplay_modules.tools import download_ytdlp

        mock_exists.return_value = False
        mock_download.return_value = True

        result = download_ytdlp("/path/to/tools")

        assert result is True
        mock_download.assert_called_once()


class TestDownloadFfmpeg:
    """Tests for download_ffmpeg function."""

    @patch("ytplay_modules.tools.verify_tool")
    @patch("os.path.exists")
    def test_skips_if_already_exists_and_works(self, mock_exists, mock_verify):
        """Should skip download if FFmpeg already exists and works."""
        from ytplay_modules.tools import download_ffmpeg

        mock_exists.return_value = True
        mock_verify.return_value = True

        result = download_ffmpeg("/path/to/tools")

        assert result is True

    @patch("ytplay_modules.tools.extract_ffmpeg")
    @patch("ytplay_modules.tools.download_file")
    @patch("ytplay_modules.tools.verify_tool")
    @patch("os.path.exists")
    def test_downloads_and_extracts_when_missing(self, mock_exists, mock_verify, mock_download, mock_extract):
        """Should download and extract FFmpeg when missing."""
        from ytplay_modules.tools import download_ffmpeg

        mock_exists.return_value = False
        mock_download.return_value = True
        mock_extract.return_value = True

        result = download_ffmpeg("/path/to/tools")

        assert result is True


class TestSetupTools:
    """Tests for setup_tools function."""

    @patch("ytplay_modules.tools.download_ffmpeg")
    @patch("ytplay_modules.tools.download_ytdlp")
    @patch("ytplay_modules.tools.get_tools_path")
    @patch("os.makedirs")
    def test_successful_setup(self, mock_makedirs, mock_tools_path, mock_ytdlp, mock_ffmpeg):
        """Should set tools ready when all downloads succeed."""
        from ytplay_modules.state import is_tools_ready, set_tools_ready
        from ytplay_modules.tools import setup_tools

        mock_tools_path.return_value = "/path/to/tools"
        mock_ytdlp.return_value = True
        mock_ffmpeg.return_value = True
        set_tools_ready(False)

        result = setup_tools()

        assert result is True
        assert is_tools_ready() is True

    @patch("ytplay_modules.tools.download_ytdlp")
    @patch("ytplay_modules.tools.get_tools_path")
    @patch("os.makedirs")
    def test_fails_when_ytdlp_fails(self, mock_makedirs, mock_tools_path, mock_ytdlp):
        """Should return False when yt-dlp download fails."""
        from ytplay_modules.tools import setup_tools

        mock_tools_path.return_value = "/path/to/tools"
        mock_ytdlp.return_value = False

        result = setup_tools()

        assert result is False

    @patch("ytplay_modules.tools.download_ffmpeg")
    @patch("ytplay_modules.tools.download_ytdlp")
    @patch("ytplay_modules.tools.get_tools_path")
    @patch("os.makedirs")
    def test_fails_when_ffmpeg_fails(self, mock_makedirs, mock_tools_path, mock_ytdlp, mock_ffmpeg):
        """Should return False when FFmpeg download fails."""
        from ytplay_modules.tools import setup_tools

        mock_tools_path.return_value = "/path/to/tools"
        mock_ytdlp.return_value = True
        mock_ffmpeg.return_value = False

        result = setup_tools()

        assert result is False
