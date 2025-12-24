"""
Integration tests for ytplay_modules.normalize

Tests for audio normalization with mocked subprocess calls.
Target: 80%+ coverage
"""

import subprocess
from unittest.mock import MagicMock, patch

# Mock Windows-specific subprocess attributes for Linux testing
if not hasattr(subprocess, "STARTUPINFO"):
    subprocess.STARTUPINFO = MagicMock
    subprocess.STARTF_USESHOWWINDOW = 0x00000001
    subprocess.SW_HIDE = 0


class TestExtractLoudnormStats:
    """Tests for extract_loudnorm_stats function."""

    def test_extracts_valid_stats(self):
        """Should extract JSON stats from FFmpeg output."""
        from ytplay_modules.normalize import extract_loudnorm_stats

        ffmpeg_output = """
frame= 1000 fps=100 q=-1.0 Lsize=   10000kB time=00:00:30.00 bitrate=2730.7kbits/s speed=3.33x
[Parsed_loudnorm_0 @ 0x12345678]
{
    "input_i" : "-20.50",
    "input_tp" : "-5.00",
    "input_lra" : "8.20",
    "input_thresh" : "-30.50",
    "output_i" : "-14.00",
    "output_tp" : "-1.00",
    "output_lra" : "7.50",
    "output_thresh" : "-24.00",
    "normalization_type" : "dynamic",
    "target_offset" : "0.00"
}
        """

        stats = extract_loudnorm_stats(ffmpeg_output)

        assert stats is not None
        assert stats["input_i"] == "-20.50"
        assert stats["input_tp"] == "-5.00"
        assert stats["input_lra"] == "8.20"
        assert stats["input_thresh"] == "-30.50"
        assert stats["target_offset"] == "0.00"

    def test_returns_none_for_no_json(self):
        """Should return None when no JSON in output."""
        from ytplay_modules.normalize import extract_loudnorm_stats

        ffmpeg_output = "Some regular FFmpeg output without JSON"

        stats = extract_loudnorm_stats(ffmpeg_output)

        assert stats is None

    def test_returns_none_for_invalid_json(self):
        """Should return None for invalid JSON."""
        from ytplay_modules.normalize import extract_loudnorm_stats

        ffmpeg_output = "{not valid json{"

        stats = extract_loudnorm_stats(ffmpeg_output)

        assert stats is None

    def test_returns_none_for_missing_required_fields(self):
        """Should return None when required fields are missing."""
        from ytplay_modules.normalize import extract_loudnorm_stats

        ffmpeg_output = '{"input_i": "-20.50"}'  # Missing other required fields

        stats = extract_loudnorm_stats(ffmpeg_output)

        assert stats is None


class TestNormalizeAudio:
    """Tests for normalize_audio function."""

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_successful_normalization(self, mock_popen, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should normalize audio successfully."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        # Create input file
        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        # Mock first pass (analysis)
        analysis_stats = """
{
    "input_i" : "-20.50",
    "input_tp" : "-5.00",
    "input_lra" : "8.20",
    "input_thresh" : "-30.50",
    "target_offset" : "0.00"
}
        """
        mock_run.return_value = MagicMock(returncode=0, stderr=analysis_stats)

        output_file = tmp_path / "Test Song_Test Artist_video123_normalized.mp4"

        # Mock second pass (normalization) - need to create file during iteration
        class MockStderr:
            def __init__(self, output_file):
                self.output_file = output_file
                self.lines = iter(["frame=100 time=00:00:05.00", "frame=200 time=00:00:10.00"])

            def __iter__(self):
                return self

            def __next__(self):
                try:
                    return next(self.lines)
                except StopIteration:
                    # Create output file when iteration ends (simulating FFmpeg completion)
                    self.output_file.write_bytes(b"x" * 2048)
                    raise

        mock_process = MagicMock()
        mock_process.stderr = MockStderr(output_file)
        mock_process.returncode = 0
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        metadata = {"song": "Test Song", "artist": "Test Artist"}

        result = normalize_audio(str(input_file), "video123", metadata)

        assert result is not None
        assert "normalized" in result
        mock_run.assert_called_once()  # First pass
        mock_popen.assert_called_once()  # Second pass

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    def test_returns_existing_normalized_file(self, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return existing normalized file without re-processing."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        # Create already-normalized file
        output_file = tmp_path / "Song_Artist_video456_normalized.mp4"
        output_file.write_bytes(b"x" * 2048)

        metadata = {"song": "Song", "artist": "Artist"}

        result = normalize_audio("/path/to/input.mp4", "video456", metadata)

        assert result is not None
        assert str(output_file) == result
        mock_run.assert_not_called()  # Should not run FFmpeg

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    def test_handles_analysis_failure(self, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return None when analysis fails."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        # Create input file
        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        # Mock analysis failure
        mock_run.return_value = MagicMock(returncode=1, stderr="FFmpeg error: invalid input")

        metadata = {"song": "Test", "artist": "Artist"}

        result = normalize_audio(str(input_file), "video789", metadata)

        assert result is None

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    def test_handles_timeout(self, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return None on timeout."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=300)

        metadata = {"song": "Test", "artist": "Artist"}

        result = normalize_audio(str(input_file), "video_timeout", metadata)

        assert result is None

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    def test_gemini_failed_marker_in_filename(self, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should add _gf marker when gemini_failed is True."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        # Create the expected output file with _gf marker
        output_file = tmp_path / "Song_Artist_video_gf_normalized_gf.mp4"
        output_file.write_bytes(b"x" * 2048)

        metadata = {"song": "Song", "artist": "Artist"}

        result = normalize_audio("/path/to/input.mp4", "video_gf", metadata, gemini_failed=True)

        assert result is not None
        assert "_gf" in result

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("os.rename")
    def test_renames_existing_file_for_gemini_failure(self, mock_rename, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should rename non-gf file to gf version when gemini_failed."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        # Create existing non-gf file
        non_gf_file = tmp_path / "Song_Artist_video_rename_normalized.mp4"
        non_gf_file.write_bytes(b"x" * 2048)

        metadata = {"song": "Song", "artist": "Artist"}

        result = normalize_audio("/path/to/input.mp4", "video_rename", metadata, gemini_failed=True)

        # Should have renamed the file
        mock_rename.assert_called_once()


class TestNormalizeAudioEdgeCases:
    """Edge case tests for normalize_audio."""

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    def test_handles_exception(self, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return None on general exception."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        mock_run.side_effect = Exception("Unexpected error")

        metadata = {"song": "Test", "artist": "Artist"}

        result = normalize_audio(str(input_file), "video_error", metadata)

        assert result is None

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    def test_handles_failed_stats_extraction(self, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return None when stats extraction fails."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        # Return success but with no valid JSON stats
        mock_run.return_value = MagicMock(returncode=0, stderr="Some output without JSON stats")

        metadata = {"song": "Test", "artist": "Artist"}

        result = normalize_audio(str(input_file), "video_no_stats", metadata)

        assert result is None

    @patch("ytplay_modules.normalize.get_ffmpeg_path")
    @patch("ytplay_modules.normalize.get_cache_dir")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_handles_normalization_pass_failure(self, mock_popen, mock_run, mock_cache_dir, mock_ffmpeg_path, tmp_path):
        """Should return None when second pass fails."""
        from ytplay_modules.normalize import normalize_audio

        mock_ffmpeg_path.return_value = "/path/to/ffmpeg"
        mock_cache_dir.return_value = str(tmp_path)

        input_file = tmp_path / "input_temp.mp4"
        input_file.write_bytes(b"x" * 1024)

        # Mock successful first pass
        analysis_stats = '{"input_i":"-20","input_tp":"-5","input_lra":"8","input_thresh":"-30","target_offset":"0"}'
        mock_run.return_value = MagicMock(returncode=0, stderr=analysis_stats)

        # Mock failed second pass
        mock_process = MagicMock()
        mock_process.stderr = iter([])
        mock_process.returncode = 1
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        metadata = {"song": "Test", "artist": "Artist"}

        result = normalize_audio(str(input_file), "video_norm_fail", metadata)

        assert result is None
