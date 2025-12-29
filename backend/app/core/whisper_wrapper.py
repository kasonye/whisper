"""Whisper wrapper for transcription with progress tracking."""

import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional

# Add parent directory to path to import whisper_cli
# Get the project root (4 levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from whisper_cli.transcriber import WhisperTranscriber, TranscriberError
    import librosa
except ImportError as e:
    print(f"Warning: Failed to import whisper dependencies: {e}")
    print(f"Project root: {project_root}")
    print(f"sys.path: {sys.path}")
    # Re-raise to make the error visible
    raise


class WhisperWrapper:
    """Handles Whisper transcription with progress tracking."""

    def __init__(self, device: str = "auto"):
        self.transcriber = WhisperTranscriber(device=device, verbose=False)
        self._cancel_flag = False

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
            # Load model (this happens once)
            self.transcriber._load_model()

            if progress_callback:
                await progress_callback(5, "Model loaded, starting transcription...")

            # Estimate duration for progress calculation
            duration = await self._get_audio_duration(audio_path)
            estimated_segments = max(int(duration / 5), 1)  # ~5 seconds per segment
            print(f"Audio duration: {duration:.2f}s, estimated segments: {estimated_segments}")

            # Run transcription in thread pool (blocking operation)
            loop = asyncio.get_event_loop()

            # Create a wrapper to track segments
            segments_processed = [0]  # Use list to allow modification in nested function
            transcription_text = [""]

            def transcribe_sync():
                """Synchronous transcription function."""
                try:
                    segments, info = self.transcriber.model.transcribe(
                        str(audio_path),
                        beam_size=5,
                        language=None,
                        task="transcribe"
                    )

                    # Process segments with progress tracking
                    for segment in segments:
                        if self._cancel_flag:
                            raise TranscriberError("Transcription cancelled")

                        transcription_text[0] += segment.text
                        segments_processed[0] += 1

                        # Calculate progress (5% for loading, 95% for transcription)
                        progress = 5 + (segments_processed[0] / estimated_segments) * 95
                        progress = min(progress, 99)  # Cap at 99% until complete

                        # Schedule callback in async context
                        if progress_callback:
                            asyncio.run_coroutine_threadsafe(
                                progress_callback(
                                    progress,
                                    f"Transcribing: segment {segments_processed[0]}/{estimated_segments}"
                                ),
                                loop
                            )

                    return transcription_text[0].strip()

                except Exception as e:
                    print(f"Transcription error in sync function: {e}")
                    raise

            # Run in executor
            transcription = await loop.run_in_executor(None, transcribe_sync)

            # Save transcript
            Path(output_path).write_text(transcription, encoding='utf-8')

            if progress_callback:
                await progress_callback(100, "Transcription complete")

            print(f"Transcription saved: {output_path}")
            return True

        except Exception as e:
            print(f"Transcription error: {e}")
            return False

    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using librosa."""
        try:
            loop = asyncio.get_event_loop()
            duration = await loop.run_in_executor(
                None,
                lambda: librosa.get_duration(path=audio_path)
            )
            return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 60.0  # Default estimate

    def cancel(self):
        """Cancel transcription."""
        self._cancel_flag = True
        print("Transcription cancellation requested")
