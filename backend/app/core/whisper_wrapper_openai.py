"""Whisper wrapper using OpenAI Whisper (not faster-whisper)."""

import asyncio
import whisper
from pathlib import Path
from typing import Callable, Optional
import threading
import time


class WhisperWrapper:
    """Handles Whisper transcription with progress tracking using OpenAI Whisper."""

    def __init__(self, device: str = "auto"):
        """Initialize wrapper.

        Args:
            device: "auto", "cpu", or "cuda"
        """
        import torch

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = None
        self._cancel_flag = False
        self._transcription_progress = 0
        self._transcription_running = False
        print(f"WhisperWrapper initialized for device: {self.device}")

    async def transcribe_with_progress(
        self,
        audio_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Transcribe audio with progress tracking.

        Args:
            audio_path: Path to audio file
            output_path: Path to save transcript
            progress_callback: Async callback(progress_percent, message)

        Returns:
            bool: True if successful
        """
        try:
            # Load model
            if progress_callback:
                await progress_callback(5, "Loading Whisper model...")

            if self.model is None:
                print(f"Loading Whisper large-v3 model on {self.device}...")
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None,
                    lambda: whisper.load_model("large-v3", device=self.device)
                )
                print(f"Model loaded on {self.device}")

            if progress_callback:
                await progress_callback(10, "Model loaded, starting transcription...")

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()

            print(f"Transcribing: {audio_path}")

            # Start progress monitoring
            self._transcription_running = True
            self._transcription_progress = 10

            # Start a background task to provide progress updates
            async def monitor_progress():
                last_progress = 10
                while self._transcription_running:
                    await asyncio.sleep(3)  # Update every 3 seconds
                    # Gradually increment progress, but slow down as we approach 95%
                    if last_progress < 95:
                        # Increment by smaller amounts as we get closer to completion
                        if last_progress < 50:
                            increment = 5
                        elif last_progress < 70:
                            increment = 3
                        elif last_progress < 85:
                            increment = 2
                        else:
                            increment = 1

                        last_progress = min(last_progress + increment, 95)
                        self._transcription_progress = last_progress
                        if progress_callback:
                            await progress_callback(
                                last_progress,
                                f"Transcribing... ({int(last_progress)}%)"
                            )

            # Start monitoring task
            monitor_task = asyncio.create_task(monitor_progress())

            # Transcribe
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_path,
                    language=None,  # Auto-detect
                    task="transcribe",
                    verbose=True  # Enable verbose for progress tracking
                )
            )

            # Stop progress monitoring
            self._transcription_running = False
            await monitor_task

            if progress_callback:
                await progress_callback(90, "Transcription complete, saving...")

            # Extract and format text with smart segmentation
            from .text_formatter import format_segments_with_pauses, format_text_simple

            segments = result.get("segments", [])
            if segments:
                # Use smart formatting with pause detection
                transcription = format_segments_with_pauses(segments)
            else:
                # Fallback to simple formatting
                transcription = format_text_simple(result["text"])

            # Save transcript
            Path(output_path).write_text(transcription, encoding='utf-8')

            if progress_callback:
                await progress_callback(100, "Done")

            print(f"Transcription saved: {output_path}")
            print(f"Detected language: {result.get('language', 'unknown')}")

            return True

        except Exception as e:
            print(f"Transcription error: {e}")
            self._transcription_running = False
            import traceback
            traceback.print_exc()
            return False

    def cancel(self):
        """Cancel transcription."""
        self._cancel_flag = True
        print("Transcription cancellation requested")
