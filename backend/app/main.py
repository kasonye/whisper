"""FastAPI main application."""

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import asyncio
import logging
from typing import List
from contextlib import asynccontextmanager

from .core.queue_manager import QueueManager
from .core.worker import Worker
from .models import Job

# Setup logging
logger = logging.getLogger(__name__)

# Global queue manager and workers
queue_manager = QueueManager(max_workers=2)
workers = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Starting up application...", flush=True)

    # Create storage directories
    Path("storage/uploads").mkdir(parents=True, exist_ok=True)
    Path("storage/audio").mkdir(parents=True, exist_ok=True)
    Path("storage/transcripts").mkdir(parents=True, exist_ok=True)
    print("Storage directories created", flush=True)

    # Start workers
    for i in range(queue_manager.max_workers):
        worker = Worker(i, queue_manager)
        workers.append(worker)
        asyncio.create_task(worker.start())
    print(f"Started {queue_manager.max_workers} workers", flush=True)

    yield

    # Shutdown
    print("Shutting down application...", flush=True)
    for worker in workers:
        worker.stop()
    print("Workers stopped", flush=True)


app = FastAPI(
    title="Video Transcription API",
    description="API for video transcription using FFmpeg and Whisper",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Video Transcription API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload",
            "jobs": "GET /api/jobs",
            "job": "GET /api/jobs/{job_id}",
            "download": "GET /api/download/{job_id}",
            "websocket": "WS /ws",
            "status": "GET /api/status"
        }
    }


@app.get("/api/status")
async def get_status():
    """Get system status including worker information."""
    return {
        "workers": {
            "count": len(workers),
            "max_workers": queue_manager.max_workers,
            "running": [w.running for w in workers],
            "worker_ids": [w.worker_id for w in workers]
        },
        "queue": {
            "size": queue_manager.get_queue_size(),
            "total_jobs": len(queue_manager.jobs)
        },
        "jobs": {
            "total": len(queue_manager.jobs),
            "queued": len([j for j in queue_manager.jobs.values() if j.status.value == "queued"]),
            "processing": len([j for j in queue_manager.jobs.values() if j.status.value in ["extracting_audio", "transcribing"]]),
            "completed": len([j for j in queue_manager.jobs.values() if j.status.value == "completed"]),
            "failed": len([j for j in queue_manager.jobs.values() if j.status.value == "failed"])
        }
    }


@app.post("/api/upload", response_model=Job)
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and add to processing queue."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file extension
    allowed_extensions = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file
    video_path = Path("storage/uploads") / file.filename
    try:
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Add to queue
    job = await queue_manager.add_job(
        filename=file.filename,
        file_size=video_path.stat().st_size,
        video_path=str(video_path)
    )

    return job


@app.get("/api/jobs", response_model=List[Job])
async def get_jobs():
    """Get all jobs."""
    return queue_manager.get_all_jobs()


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get specific job by ID."""
    job = queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/download/{job_id}")
async def download_transcript(job_id: str):
    """Download transcript file."""
    job = queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.transcript_path or not Path(job.transcript_path).exists():
        raise HTTPException(status_code=404, detail="Transcript not found")

    return FileResponse(
        job.transcript_path,
        media_type="text/plain",
        filename=f"{Path(job.filename).stem}_transcript.txt"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time job updates."""
    await queue_manager.websocket_manager.connect(websocket)
    try:
        # Send current jobs on connect
        jobs = queue_manager.get_all_jobs()
        for job in jobs:
            await websocket.send_json(job.model_dump(mode='json'))

        # Keep connection alive and listen for messages
        while True:
            # Receive messages (ping/pong to keep connection alive)
            data = await websocket.receive_text()
            # Echo back for debugging
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        queue_manager.websocket_manager.disconnect(websocket)
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        queue_manager.websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

