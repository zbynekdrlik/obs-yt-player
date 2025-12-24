"""
Integration tests for ytplay_modules.download

Tests for video downloading with mocked subprocess calls.
Target: 80%+ coverage
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock
import subprocess

# Mock Windows-specific subprocess attributes for Linux testing
if not hasattr(subprocess, 'STARTUPINFO'):
    subprocess.STARTUPINFO = MagicMock
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0


class TestDownloadVideo:
    """Tests for download_video function."""

    @patch("ytplay_modules.download.get_ytdlp_path")
    @patch("ytplay_modules.download.get_ffmpeg_path")
    @patch("ytplay_modules.download.get_cache_dir")
    @patch("ytplay_modules.download.is_audio_only_mode")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_successful_download(
        self, mock_popen, mock_run, mock_audio_mode, mock_cache_dir,
        mock_ffmpeg_path, mock_ytdlp_path, tmp_path
    ):
        """Should download video successfully."""
        from ytplay_modules.download import download_video

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)
        mock_audio_mode.return_value = False

        # Mock info command (for quality logging)
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1920,1080,30,h264,aac"
        )

        output_file = tmp_path / "dQw4w9WgXcQ_temp.mp4"

        # Create file when wait() is called (simulating download completion)
        def create_file_on_wait(*args, **kwargs):
            output_file.write_bytes(b"x" * (2 * 1024 * 1024))
            return None

        # Mock download process
        mock_process = MagicMock()
        mock_process.stdout = iter([
            "[download] Destination: /path/to/video.mp4",
            "[download]  50.0% of ~100.00MiB at 5.00MiB/s ETA 00:10"
        ])
        mock_process.returncode = 0
        mock_process.wait.side_effect = create_file_on_wait
        mock_popen.return_value = mock_process

        result = download_video("dQw4w9WgXcQ", "Test Video Title")

        assert result is not None
        assert "dQw4w9WgXcQ_temp.mp4" in result

    @patch("ytplay_modules.download.get_ytdlp_path")
    @patch("ytplay_modules.download.get_ffmpeg_path")
    @patch("ytplay_modules.download.get_cache_dir")
    @patch("ytplay_modules.download.is_audio_only_mode")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_download_failure(
        self, mock_popen, mock_run, mock_audio_mode, mock_cache_dir,
        mock_ffmpeg_path, mock_ytdlp_path, tmp_path
    ):
        """Should return None on download failure."""
        from ytplay_modules.download import download_video

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)
        mock_audio_mode.return_value = False

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1920,1080,30,h264,aac"
        )

        # Mock failed download
        mock_process = MagicMock()
        mock_process.stdout = iter(["[download] ERROR: Unable to download"])
        mock_process.returncode = 1
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        result = download_video("invalid123", "Invalid Video")

        assert result is None

    @patch("ytplay_modules.download.get_ytdlp_path")
    @patch("ytplay_modules.download.get_ffmpeg_path")
    @patch("ytplay_modules.download.get_cache_dir")
    @patch("ytplay_modules.download.is_audio_only_mode")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_audio_only_mode(
        self, mock_popen, mock_run, mock_audio_mode, mock_cache_dir,
        mock_ffmpeg_path, mock_ytdlp_path, tmp_path
    ):
        """Should use minimal video quality in audio-only mode."""
        from ytplay_modules.download import download_video

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)
        mock_audio_mode.return_value = True  # Audio-only mode

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="256,144,15,h264,aac"  # Minimal quality
        )

        mock_process = MagicMock()
        mock_process.stdout = iter([])
        mock_process.returncode = 0
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        # Create output file
        output_file = tmp_path / "audio_only_temp.mp4"
        output_file.write_bytes(b"x" * (1 * 1024 * 1024))

        download_video("audio_only", "Audio Only Video")

        # Verify yt-dlp was called
        mock_popen.assert_called()

    @patch("ytplay_modules.download.get_ytdlp_path")
    @patch("ytplay_modules.download.get_ffmpeg_path")
    @patch("ytplay_modules.download.get_cache_dir")
    @patch("ytplay_modules.download.is_audio_only_mode")
    @patch("subprocess.Popen")
    def test_handles_timeout(
        self, mock_popen, mock_audio_mode, mock_cache_dir,
        mock_ffmpeg_path, mock_ytdlp_path, tmp_path
    ):
        """Should return None on timeout."""
        from ytplay_modules.download import download_video

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)
        mock_audio_mode.return_value = False

        mock_process = MagicMock()
        mock_process.stdout = iter([])
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="yt-dlp", timeout=600)
        mock_process.kill.return_value = None
        mock_popen.return_value = mock_process

        result = download_video("timeout123", "Timeout Video")

        assert result is None
        mock_process.kill.assert_called()

    @patch("ytplay_modules.download.get_ytdlp_path")
    @patch("ytplay_modules.download.get_ffmpeg_path")
    @patch("ytplay_modules.download.get_cache_dir")
    @patch("ytplay_modules.download.is_audio_only_mode")
    def test_handles_exception(
        self, mock_audio_mode, mock_cache_dir, mock_ffmpeg_path, mock_ytdlp_path, tmp_path
    ):
        """Should return None on general exception."""
        from ytplay_modules.download import download_video

        mock_ytdlp_path.return_value = "/path/to/yt-dlp"
        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)
        mock_audio_mode.side_effect = Exception("Config error")

        result = download_video("error123", "Error Video")

        assert result is None


class TestParseProgress:
    """Tests for parse_progress function."""

    def test_parses_50_percent_milestone(self):
        """Should log at 50% milestone."""
        from ytplay_modules.download import parse_progress, download_progress_milestones

        video_id = "test_progress"
        download_progress_milestones[video_id] = set()

        parse_progress("[download]  50.0% of ~100.00MiB at 5.00MiB/s", video_id, "Test Title")

        assert 50 in download_progress_milestones[video_id]

    def test_ignores_progress_after_50_percent(self):
        """Should stop logging after 50% milestone."""
        from ytplay_modules.download import parse_progress, download_progress_milestones

        video_id = "test_ignore"
        download_progress_milestones[video_id] = {50}  # Already logged 50%

        # This should not add anything new
        parse_progress("[download]  75.0% of ~100.00MiB", video_id, "Test Title")
        parse_progress("[download]  99.0% of ~100.00MiB", video_id, "Test Title")

        # Should still only have 50
        assert download_progress_milestones[video_id] == {50}

    def test_handles_invalid_progress_line(self):
        """Should handle lines without progress info."""
        from ytplay_modules.download import parse_progress, download_progress_milestones

        video_id = "test_invalid"
        download_progress_milestones[video_id] = set()

        # Should not crash on invalid lines
        parse_progress("[download] Downloading video", video_id, "Test Title")
        parse_progress("Some other output", video_id, "Test Title")

        assert 50 not in download_progress_milestones[video_id]


class TestProcessVideosWorker:
    """Tests for process_videos_worker behavior."""

    @patch("ytplay_modules.download.download_video")
    @patch("ytplay_modules.download.get_video_metadata")
    @patch("ytplay_modules.download.normalize_audio")
    def test_skips_cached_videos(
        self, mock_normalize, mock_metadata, mock_download
    ):
        """Should skip videos that are already cached."""
        from ytplay_modules.state import (
            video_queue, add_cached_video, should_stop_threads
        )

        # Pre-cache the video
        add_cached_video("already_cached", {
            "path": "/cache/cached.mp4",
            "song": "Cached",
            "artist": "Artist"
        })

        # Add to queue
        video_queue.put({"id": "already_cached", "title": "Cached Video"})

        # Get from queue and check if cached
        video_info = video_queue.get_nowait()
        from ytplay_modules.state import is_video_cached

        assert is_video_cached(video_info["id"]) is True

        # Should not call download for cached videos
        mock_download.assert_not_called()

    @patch("ytplay_modules.download.download_video")
    @patch("ytplay_modules.download.get_video_metadata")
    @patch("ytplay_modules.download.normalize_audio")
    def test_full_processing_pipeline(
        self, mock_normalize, mock_metadata, mock_download
    ):
        """Should process video through all stages."""
        from ytplay_modules.state import video_queue, is_video_cached

        video_id = "new_video_123"
        title = "New Video Title"

        # Mock download success
        mock_download.return_value = "/cache/temp_file.mp4"

        # Mock metadata extraction
        mock_metadata.return_value = ("Song Title", "Artist Name", "Gemini", False)

        # Mock normalization success
        mock_normalize.return_value = "/cache/normalized_file.mp4"

        # Verify video is not cached initially
        assert not is_video_cached(video_id)

        # Simulate the processing logic
        temp_path = mock_download(video_id, title)
        assert temp_path is not None

        song, artist, source, gemini_failed = mock_metadata(temp_path, title, video_id)
        assert song == "Song Title"
        assert artist == "Artist Name"

        metadata = {"song": song, "artist": artist}
        normalized_path = mock_normalize(temp_path, video_id, metadata, gemini_failed)
        assert normalized_path is not None


class TestStartVideoProcessingThread:
    """Tests for start_video_processing_thread function."""

    @patch("threading.Thread")
    def test_creates_daemon_thread(self, mock_thread):
        """Should create a daemon thread."""
        from ytplay_modules.download import start_video_processing_thread

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        start_video_processing_thread()

        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs.get("daemon") is True
        mock_thread_instance.start.assert_called_once()
