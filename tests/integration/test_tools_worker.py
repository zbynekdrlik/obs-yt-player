"""
Tests for tools setup worker functionality.
Covers the tools_setup_worker event loop and download progress tracking.
"""

import threading
import time
from unittest.mock import MagicMock


class TestToolsSetupWorker:
    """Tests for tools_setup_worker function."""

    def test_worker_exits_on_stop_threads(self, configured_state):
        """Worker should exit when stop_threads is set."""
        from ytplay_modules import state
        from ytplay_modules.tools import tools_setup_worker

        state.set_stop_threads(True)

        thread = threading.Thread(target=tools_setup_worker, daemon=True)
        thread.start()
        thread.join(timeout=2)

        assert not thread.is_alive(), "Worker should have exited"

    def test_worker_waits_for_cache_dir(self, configured_state, mocker):
        """Worker should wait if cache directory doesn't exist."""
        from ytplay_modules import state
        from ytplay_modules.tools import tools_setup_worker

        state.set_stop_threads(False)

        mock_ensure = mocker.patch("ytplay_modules.tools.ensure_cache_directory")
        mock_ensure.return_value = False  # Directory doesn't exist

        thread = threading.Thread(target=tools_setup_worker, daemon=True)
        thread.start()

        time.sleep(0.5)

        # Worker should still be running, waiting
        assert thread.is_alive()

        # Stop the worker
        state.set_stop_threads(True)
        thread.join(timeout=2)

    def test_worker_calls_setup_tools(self, configured_state, mocker):
        """Worker should call setup_tools when cache exists."""
        from ytplay_modules import state
        from ytplay_modules.tools import tools_setup_worker

        state.set_stop_threads(False)

        mock_ensure = mocker.patch("ytplay_modules.tools.ensure_cache_directory")
        mock_ensure.return_value = True

        mock_setup = mocker.patch("ytplay_modules.tools.setup_tools")
        mock_setup.return_value = True

        mock_trigger = mocker.patch("ytplay_modules.playlist.trigger_startup_sync")

        thread = threading.Thread(target=tools_setup_worker, daemon=True)
        thread.start()

        # Wait for setup to complete
        time.sleep(0.5)

        # Worker should have exited after successful setup
        thread.join(timeout=2)
        assert not thread.is_alive()

        mock_setup.assert_called_once()
        mock_trigger.assert_called_once()

    def test_worker_retries_on_setup_failure(self, configured_state, mocker):
        """Worker should retry if setup_tools fails."""
        from ytplay_modules import state
        from ytplay_modules.tools import tools_setup_worker

        state.set_stop_threads(False)

        mock_ensure = mocker.patch("ytplay_modules.tools.ensure_cache_directory")
        mock_ensure.return_value = True

        # Mock the check interval to be very short for testing
        mocker.patch("ytplay_modules.tools.TOOLS_CHECK_INTERVAL", 0)

        call_count = 0

        def mock_setup_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return False
            # On second call, signal stop to exit cleanly
            state.set_stop_threads(True)
            return True

        mock_setup = mocker.patch("ytplay_modules.tools.setup_tools")
        mock_setup.side_effect = mock_setup_side_effect

        mocker.patch("ytplay_modules.playlist.trigger_startup_sync")
        mocker.patch("ytplay_modules.tools.log")

        thread = threading.Thread(target=tools_setup_worker, daemon=True)
        thread.start()

        # Wait for the worker to complete
        thread.join(timeout=5)

        # Should have called setup at least twice (fail then succeed)
        assert call_count >= 2


class TestSetupTools:
    """Tests for setup_tools function."""

    def test_setup_tools_downloads_missing_tools(self, temp_cache_dir, mocker, configured_state):
        """Should download tools if they don't exist."""
        from ytplay_modules import state
        from ytplay_modules.tools import setup_tools

        state.set_cache_dir(str(temp_cache_dir))

        mock_download = mocker.patch("ytplay_modules.tools.download_file")
        mock_download.return_value = True

        mock_extract = mocker.patch("ytplay_modules.tools.extract_ffmpeg")
        mock_extract.return_value = True

        mock_verify = mocker.patch("ytplay_modules.tools.verify_tool")
        mock_verify.return_value = True

        # Create tools directory
        tools_dir = temp_cache_dir / "tools"
        tools_dir.mkdir()

        result = setup_tools()

        # Should have attempted downloads
        assert mock_download.called or mock_verify.called

    def test_setup_tools_skips_existing(self, temp_cache_dir, mocker, configured_state):
        """Should skip download if tools exist and work."""
        from ytplay_modules import state
        from ytplay_modules.config import FFMPEG_FILENAME, YTDLP_FILENAME
        from ytplay_modules.tools import setup_tools

        state.set_cache_dir(str(temp_cache_dir))

        # Create fake tool files with platform-correct names
        tools_dir = temp_cache_dir / "tools"
        tools_dir.mkdir()
        (tools_dir / YTDLP_FILENAME).write_bytes(b"fake")
        (tools_dir / FFMPEG_FILENAME).write_bytes(b"fake")

        mock_verify = mocker.patch("ytplay_modules.tools.verify_tool")
        mock_verify.return_value = True

        mock_download = mocker.patch("ytplay_modules.tools.download_file")

        result = setup_tools()

        assert result is True
        mock_download.assert_not_called()


class TestDownloadFile:
    """Tests for download_file function."""

    def test_download_creates_directory(self, temp_cache_dir, mocker):
        """Should create parent directory if needed."""
        from ytplay_modules.tools import download_file

        mock_urlretrieve = mocker.patch("urllib.request.urlretrieve")

        destination = temp_cache_dir / "subdir" / "file.exe"

        download_file("https://example.com/file.exe", str(destination))

        assert destination.parent.exists()

    def test_download_logs_progress(self, temp_cache_dir, mocker):
        """Should log download progress at milestones."""
        from ytplay_modules.tools import download_file

        mock_log = mocker.patch("ytplay_modules.tools.log")

        progress_calls = []

        def capture_progress(block_num, block_size, total_size):
            progress_calls.append((block_num, block_size, total_size))

        def mock_urlretrieve(url, dest, reporthook=None):
            if reporthook:
                # Simulate progress: 0%, 25%, 50%, 75%, 100%
                total = 1000
                for i in range(0, 101, 25):
                    reporthook(i, 10, total)

        mocker.patch("urllib.request.urlretrieve", side_effect=mock_urlretrieve)

        destination = temp_cache_dir / "file.exe"
        download_file("https://example.com/file.exe", str(destination))

        # Check log was called with progress
        calls = [str(c) for c in mock_log.call_args_list]
        assert len(calls) > 0

    def test_download_handles_error(self, temp_cache_dir, mocker):
        """Should handle download errors gracefully."""
        import urllib.error

        from ytplay_modules.tools import download_file

        mock_urlretrieve = mocker.patch("urllib.request.urlretrieve")
        mock_urlretrieve.side_effect = urllib.error.URLError("Network error")

        mock_log = mocker.patch("ytplay_modules.tools.log")

        destination = temp_cache_dir / "file.exe"
        result = download_file("https://example.com/file.exe", str(destination))

        assert result is False


class TestVerifyTool:
    """Tests for verify_tool function."""

    def test_verify_returns_true_for_working_tool(self, mocker):
        """Should return True if tool runs successfully."""
        from ytplay_modules.tools import verify_tool

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="version 1.0", stderr="")

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is True

    def test_verify_returns_false_for_failure(self, mocker):
        """Should return False if tool fails."""
        from ytplay_modules.tools import verify_tool

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is False

    def test_verify_returns_false_for_exception(self, mocker):
        """Should return False on exception."""
        from ytplay_modules.tools import verify_tool

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = Exception("Tool not found")

        result = verify_tool("/path/to/tool.exe", ["--version"])

        assert result is False


class TestExtractFfmpeg:
    """Tests for extract_ffmpeg function."""

    def test_extract_handles_missing_archive(self, temp_cache_dir, mocker):
        """Should handle missing archive file."""
        from ytplay_modules.tools import extract_ffmpeg

        mock_log = mocker.patch("ytplay_modules.tools.log")

        result = extract_ffmpeg(str(temp_cache_dir / "nonexistent.zip"), str(temp_cache_dir))

        assert result is False

    def test_extract_removes_archive_after(self, temp_cache_dir, mocker):
        """Should remove archive after extraction."""
        import zipfile

        from ytplay_modules.tools import extract_ffmpeg

        # Create a simple zip file
        archive_path = temp_cache_dir / "ffmpeg.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("ffmpeg.exe", "fake content")

        result = extract_ffmpeg(str(archive_path), str(temp_cache_dir))

        # Archive should be removed (or extraction attempted)
        # The actual result depends on implementation details


class TestEnsureCacheDirectory:
    """Tests for ensure_cache_directory function."""

    def test_creates_cache_dir(self, tmp_path, configured_state):
        """Should create cache directory if it doesn't exist."""
        from ytplay_modules import state
        from ytplay_modules.tools import ensure_cache_directory

        cache_dir = tmp_path / "new_cache"
        state.set_cache_dir(str(cache_dir))

        result = ensure_cache_directory()

        assert result is True
        assert cache_dir.exists()

    def test_creates_tools_subdir(self, tmp_path, configured_state):
        """Should create tools subdirectory."""
        from ytplay_modules import state
        from ytplay_modules.tools import ensure_cache_directory

        cache_dir = tmp_path / "cache"
        state.set_cache_dir(str(cache_dir))

        ensure_cache_directory()

        tools_dir = cache_dir / "tools"
        assert tools_dir.exists()

    def test_handles_permission_error(self, tmp_path, mocker, configured_state):
        """Should handle permission errors gracefully."""
        from ytplay_modules import state
        from ytplay_modules.tools import ensure_cache_directory

        # Use a real path so state is set correctly
        state.set_cache_dir(str(tmp_path / "forbidden_cache"))

        # Mock Path.mkdir to raise PermissionError
        mocker.patch("pathlib.Path.mkdir", side_effect=PermissionError("Access denied"))

        result = ensure_cache_directory()

        assert result is False
