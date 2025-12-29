"""Background worker for processing jobs."""

import asyncio
from pathlib import Path
from .queue_manager import QueueManager
from .ffmpeg_processor import FFmpegProcessor
from .whisper_wrapper_openai import WhisperWrapper
from ..models import JobStatus


class Worker:
    """Background worker that processes jobs from the queue."""

    def __init__(self, worker_id: int, queue_manager: QueueManager):
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.ffmpeg = FFmpegProcessor()
        self.whisper = None  # Lazy initialization
        self.running = False

    async def start(self):
        """Start worker loop."""
        self.running = True
        print(f"Worker {self.worker_id} started")

        while self.running:
            try:
                # Get job from queue (wait if empty)
                job_id = await self.queue_manager.job_queue.get()
                print(f"Worker {self.worker_id} picked up job {job_id}")
                await self.process_job(job_id)

            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(1)

    async def process_job(self, job_id: str):
        """Process a single job."""
        job = self.queue_manager.get_job(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return

        try:
            print(f"Worker {self.worker_id} processing job {job_id}")
            print(f"Video path: {job.video_path}")
            print(f"Video path exists: {Path(job.video_path).exists()}")

            # Stage 1: Extract audio (0-50%)
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.EXTRACTING_AUDIO,
                0,
                "Starting audio extraction",
                "Initializing FFmpeg..."
            )

            # Generate audio path in storage/audio directory
            audio_filename = Path(job.filename).stem + ".wav"
            audio_path = str(Path("storage/audio") / audio_filename)

            async def ffmpeg_progress(progress: float, message: str):
                # Map FFmpeg progress to 0-50%
                overall_progress = progress * 0.5
                await self.queue_manager.update_job_progress(
                    job_id,
                    JobStatus.EXTRACTING_AUDIO,
                    overall_progress,
                    "Extracting audio",
                    message
                )

            success = await self.ffmpeg.extract_audio(
                job.video_path,
                audio_path,
                ffmpeg_progress
            )

            if not success:
                raise Exception("Audio extraction failed")

            job.audio_path = audio_path

            # Stage 2: Transcribe (50-100%)
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.TRANSCRIBING,
                50,
                "Starting transcription",
                "Loading Whisper model..."
            )

            # Lazy initialize Whisper wrapper
            if self.whisper is None:
                try:
                    self.whisper = WhisperWrapper()
                    print(f"Worker {self.worker_id} initialized Whisper wrapper")
                except Exception as e:
                    raise Exception(f"Failed to initialize Whisper: {str(e)}")

            # Generate transcript path in storage/transcripts directory
            transcript_filename = Path(job.filename).stem + "_transcript.txt"
            transcript_path = str(Path("storage/transcripts") / transcript_filename)

            async def whisper_progress(progress: float, message: str):
                # Map Whisper progress to 50-100%
                overall_progress = 50 + (progress * 0.5)
                await self.queue_manager.update_job_progress(
                    job_id,
                    JobStatus.TRANSCRIBING,
                    overall_progress,
                    "Transcribing",
                    message
                )

            success = await self.whisper.transcribe_with_progress(
                audio_path,
                transcript_path,
                whisper_progress
            )

            if not success:
                raise Exception("Transcription failed")

            job.transcript_path = transcript_path

            # Complete
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.COMPLETED,
                100,
                "Completed",
                "Job completed successfully"
            )

            print(f"Worker {self.worker_id} completed job {job_id}")

        except Exception as e:
            error_msg = str(e)
            print(f"Worker {self.worker_id} failed job {job_id}: {error_msg}")
            job.error_message = error_msg
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.FAILED,
                job.progress,
                "Failed",
                f"Error: {error_msg}"
            )

    def stop(self):
        """Stop worker."""
        self.running = False
        print(f"Worker {self.worker_id} stopped")
