"""Queue manager for job processing."""

import asyncio
from typing import Dict, Optional, List
from uuid import uuid4
from datetime import datetime
from ..models import Job, JobStatus, ProgressUpdate
from ..utils.websocket_manager import WebSocketManager


class QueueManager:
    """Manages job queue and state."""

    def __init__(self, max_workers: int = 2):
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, Job] = {}
        self.max_workers = max_workers
        self.websocket_manager = WebSocketManager()

    async def add_job(self, filename: str, file_size: int, video_path: str) -> Job:
        """Add a new job to the queue."""
        job_id = str(uuid4())
        job = Job(
            id=job_id,
            filename=filename,
            file_size=file_size,
            status=JobStatus.QUEUED,
            progress=0.0,
            current_stage="Queued",
            created_at=datetime.now(),
            completed_at=None,
            error_message=None,
            video_path=video_path,
            audio_path=None,
            transcript_path=None
        )

        self.jobs[job_id] = job
        await self.job_queue.put(job_id)
        await self.broadcast_update(job)
        print(f"Job {job_id} added to queue: {filename}")
        return job

    async def update_job_progress(
        self,
        job_id: str,
        status: JobStatus,
        progress: float,
        current_stage: str,
        message: str = ""
    ):
        """Update job progress and broadcast to clients."""
        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]
        job.status = status
        job.progress = progress
        job.current_stage = current_stage

        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.now()
        elif status == JobStatus.FAILED:
            job.error_message = message

        await self.broadcast_update(job)

    async def broadcast_update(self, job: Job):
        """Broadcast job update to all WebSocket clients."""
        await self.websocket_manager.broadcast(job.model_dump(mode='json'))

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[Job]:
        """Get all jobs."""
        return list(self.jobs.values())

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.job_queue.qsize()
