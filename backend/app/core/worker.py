"""Background worker for processing jobs."""

import asyncio
from pathlib import Path
from .queue_manager import QueueManager
from .ffmpeg_processor import FFmpegProcessor
from .whisper_wrapper_openai import WhisperWrapper
from .ollama_service import ollama_service
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
            print(f"Target language: {job.target_language}, LLM model: {job.llm_model}")

            # Stage 1: Extract audio (0-40%)
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
                # Map FFmpeg progress to 0-40%
                overall_progress = progress * 0.4
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

            # Stage 2: Transcribe (40-70%)
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.TRANSCRIBING,
                40,
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

            # Generate raw transcript path in storage/transcripts directory
            raw_transcript_filename = Path(job.filename).stem + "_raw_transcript.txt"
            raw_transcript_path = str(Path("storage/transcripts") / raw_transcript_filename)

            async def whisper_progress(progress: float, message: str):
                # Map Whisper progress to 40-70%
                overall_progress = 40 + (progress * 0.3)
                await self.queue_manager.update_job_progress(
                    job_id,
                    JobStatus.TRANSCRIBING,
                    overall_progress,
                    "Transcribing",
                    message
                )

            success = await self.whisper.transcribe_with_progress(
                audio_path,
                raw_transcript_path,
                whisper_progress
            )

            if not success:
                raise Exception("Transcription failed")

            job.transcript_raw_path = raw_transcript_path

            # Stage 3: LLM Processing (70-100%)
            # Check if LLM processing is needed
            if job.target_language and job.llm_model:
                await self.process_with_llm(job_id, job, raw_transcript_path)
            else:
                # No LLM processing, use raw transcript as final
                job.transcript_path = raw_transcript_path
                job.llm_processing_skipped = True

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

    async def process_with_llm(self, job_id: str, job, raw_transcript_path: str):
        """Process transcript with LLM for formatting and/or translation."""
        await self.queue_manager.update_job_progress(
            job_id,
            JobStatus.FORMATTING_LLM,
            70,
            "LLM Processing",
            "Checking Ollama service..."
        )

        # Check if Ollama is available
        status = await ollama_service.check_status()
        if not status["available"]:
            print(f"Ollama service not available: {status.get('error')}")
            job.transcript_path = raw_transcript_path
            job.llm_processing_skipped = True
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.FORMATTING_LLM,
                95,
                "LLM Processing",
                "Ollama unavailable, using raw transcript"
            )
            return

        # Read raw transcript
        with open(raw_transcript_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        if not raw_text.strip():
            job.transcript_path = raw_transcript_path
            job.llm_processing_skipped = True
            return

        # Detect source language
        await self.queue_manager.update_job_progress(
            job_id,
            JobStatus.FORMATTING_LLM,
            75,
            "LLM Processing",
            "Detecting source language..."
        )

        detected_lang = await ollama_service.detect_language(raw_text, job.llm_model)
        job.detected_language = detected_lang
        print(f"Detected language: {detected_lang}, Target language: {job.target_language}")

        # Generate final transcript path
        final_transcript_filename = Path(job.filename).stem + "_transcript.txt"
        final_transcript_path = str(Path("storage/transcripts") / final_transcript_filename)

        # Progress callback for LLM operations
        async def llm_progress(progress: float, message: str):
            # Map LLM progress to 80-95%
            overall_progress = 80 + (progress * 0.15)
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.FORMATTING_LLM,
                overall_progress,
                "LLM Processing",
                message
            )

        # Determine if translation is needed
        if detected_lang and detected_lang == job.target_language:
            # Same language, just format
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.FORMATTING_LLM,
                80,
                "LLM Processing",
                "Source and target language match, formatting only..."
            )
            processed_text = await ollama_service.format_transcript(
                raw_text,
                job.llm_model,
                llm_progress
            )
        else:
            # Different language, translate and format
            await self.queue_manager.update_job_progress(
                job_id,
                JobStatus.FORMATTING_LLM,
                80,
                "LLM Processing",
                f"Translating to {job.target_language}..."
            )
            processed_text = await ollama_service.translate_and_format(
                raw_text,
                job.target_language,
                job.llm_model,
                llm_progress
            )

        # Save processed transcript
        if processed_text:
            with open(final_transcript_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            job.transcript_path = final_transcript_path
            job.llm_model_used = job.llm_model
        else:
            # LLM processing failed, fall back to raw transcript
            job.transcript_path = raw_transcript_path
            job.llm_processing_skipped = True
            print(f"LLM processing failed for job {job_id}, using raw transcript")

        await self.queue_manager.update_job_progress(
            job_id,
            JobStatus.FORMATTING_LLM,
            95,
            "LLM Processing",
            "LLM processing complete"
        )

    def stop(self):
        """Stop worker."""
        self.running = False
        print(f"Worker {self.worker_id} stopped")
