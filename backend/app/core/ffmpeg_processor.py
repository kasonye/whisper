"""FFmpeg processor for audio extraction with progress tracking."""

import asyncio
import subprocess
import re
from pathlib import Path
from typing import Callable, Optional


class FFmpegProcessor:
    """Handles FFmpeg audio extraction with progress tracking."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    async def extract_audio(
        self,
        video_path: str,
        audio_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Extract audio from video using FFmpeg with progress tracking.

        Args:
            video_path: Path to input video
            audio_path: Path to output audio
            progress_callback: Async callback(progress_percent, message)

        Returns:
            bool: True if successful
        """
        try:
            # First, get video duration
            duration = await self._get_duration(video_path)
            print(f"Video duration: {duration:.2f} seconds")

            # FFmpeg command to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # WAV codec
                '-ar', '16000',  # Sample rate (Whisper recommended)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                audio_path
            ]

            def run_ffmpeg():
                """Run FFmpeg in a thread."""
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                stderr_output = []
                if process.stderr:
                    for line in process.stderr:
                        stderr_output.append(line)

                process.wait()
                return process.returncode, stderr_output

            # Run FFmpeg in thread pool
            returncode, stderr_lines = await asyncio.to_thread(run_ffmpeg)

            # Parse progress from stderr
            for line in stderr_lines:
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                if time_match and duration > 0:
                    hours, minutes, seconds = time_match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    progress = min((current_time / duration) * 100, 100)

                    if progress_callback:
                        await progress_callback(
                            progress,
                            f"Extracting audio: {progress:.1f}%"
                        )

            if returncode == 0:
                if progress_callback:
                    await progress_callback(100, "Audio extraction complete")
                print(f"Audio extracted successfully: {audio_path}")
                return True
            else:
                print(f"FFmpeg failed with return code: {returncode}")
                return False

        except Exception as e:
            print(f"FFmpeg error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _get_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        try:
            import os
            import subprocess

            def run_ffprobe():
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                return result.returncode, result.stdout, result.stderr

            # Run subprocess in thread pool to avoid blocking
            returncode, stdout, stderr = await asyncio.to_thread(run_ffprobe)

            if returncode != 0:
                print(f"ffprobe failed with return code {returncode}: {stderr}")
                return 0.0

            duration_str = stdout.strip()
            if not duration_str:
                print("ffprobe returned empty duration")
                return 0.0

            return float(duration_str)

        except Exception as e:
            print(f"Error getting duration: {e}")
            import traceback
            traceback.print_exc()
            return 0.0

    def cancel(self):
        """Cancel current FFmpeg process."""
        if self.process:
            self.process.terminate()
            print("FFmpeg process terminated")
