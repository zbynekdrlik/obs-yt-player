"""
Audio normalization for OBS YouTube Player.
Normalizes audio to -14 LUFS using FFmpeg.
"""

import subprocess
import os
import json
from pathlib import Path

from ytfast_modules.logger import log
from ytfast_modules.config import FFMPEG_FILENAME, TOOLS_SUBDIR, NORMALIZE_TIMEOUT
from ytfast_modules.state import get_cache_dir

def get_ffmpeg_path():
    """Get full path to FFmpeg executable."""
    return os.path.join(get_cache_dir(), TOOLS_SUBDIR, FFMPEG_FILENAME)

def analyze_loudness(input_path):
    """Analyze audio loudness using FFmpeg loudnorm filter."""
    ffmpeg_path = get_ffmpeg_path()
    
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-af', 'loudnorm=I=-14:LRA=11:TP=-1.5:print_format=json',
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=NORMALIZE_TIMEOUT
        )
        
        # Parse loudnorm output from stderr
        lines = result.stderr.split('\n')
        json_start = False
        json_data = []
        
        for line in lines:
            if '{' in line:
                json_start = True
            if json_start:
                json_data.append(line)
            if '}' in line and json_start:
                break
        
        if json_data:
            loudness_data = json.loads('\n'.join(json_data))
            return loudness_data
        else:
            log("No loudness data found in FFmpeg output")
            return None
            
    except subprocess.TimeoutExpired:
        log(f"Loudness analysis timed out after {NORMALIZE_TIMEOUT}s")
        return None
    except json.JSONDecodeError as e:
        log(f"Failed to parse loudness data: {e}")
        return None
    except Exception as e:
        log(f"Error analyzing loudness: {e}")
        return None

def normalize_audio(input_path, output_path):
    """Normalize audio to -14 LUFS using two-pass loudnorm."""
    ffmpeg_path = get_ffmpeg_path()
    
    # First pass: analyze
    log("Analyzing audio loudness...")
    loudness_data = analyze_loudness(input_path)
    
    if not loudness_data:
        log("Falling back to simple normalization")
        # Fallback to simple volume adjustment
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-c:v', 'copy',
            '-af', 'loudnorm=I=-14:LRA=11:TP=-1.5',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
    else:
        # Second pass: normalize with measured values
        measured_I = loudness_data.get('input_i', '-70.0')
        measured_LRA = loudness_data.get('input_lra', '0.0')
        measured_TP = loudness_data.get('input_tp', '-1.5')
        measured_thresh = loudness_data.get('input_thresh', '-70.0')
        target_offset = loudness_data.get('target_offset', '0.0')
        
        log(f"Normalizing: Input I={measured_I} LUFS")
        
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-c:v', 'copy',
            '-af', f'loudnorm=I=-14:LRA=11:TP=-1.5:measured_I={measured_I}:measured_LRA={measured_LRA}:measured_TP={measured_TP}:measured_thresh={measured_thresh}:offset={target_offset}:linear=true',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
    
    try:
        # Run normalization
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=NORMALIZE_TIMEOUT
        )
        
        if result.returncode == 0:
            log("Audio normalization complete")
            return True
        else:
            log(f"FFmpeg normalization failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"Normalization timed out after {NORMALIZE_TIMEOUT}s")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        return False
    except Exception as e:
        log(f"Error during normalization: {e}")
        return False