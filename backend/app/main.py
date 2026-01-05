"""FastAPI main application."""

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import asyncio
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from .core.queue_manager import QueueManager
from .core.worker import Worker
from .core.llm_service import llm_service
from .models import (
    Job, OllamaConfig, OllamaStatus, OpenRouterConfig, OpenRouterStatus,
    LLMConfig, LLMStatus, LLMProvider, SupportedLanguage, SUPPORTED_LANGUAGES
)

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
            "download_raw": "GET /api/download/{job_id}/raw",
            "websocket": "WS /ws",
            "status": "GET /api/status",
            "llm_config": "GET/PUT /api/config/llm",
            "llm_status": "GET /api/llm/status",
            "llm_models": "GET /api/llm/models",
            "ollama_config": "GET/PUT /api/config/ollama (legacy)",
            "ollama_status": "GET /api/ollama/status",
            "ollama_models": "GET /api/ollama/models",
            "openrouter_status": "GET /api/openrouter/status",
            "openrouter_models": "GET /api/openrouter/models",
            "languages": "GET /api/languages"
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
async def upload_video(
    file: UploadFile = File(...),
    target_language: Optional[str] = Form(None),
    llm_model: Optional[str] = Form(None)
):
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

    # Validate target_language if provided
    if target_language:
        valid_codes = [lang.code for lang in SUPPORTED_LANGUAGES]
        if target_language not in valid_codes:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language. Allowed: {', '.join(valid_codes)}"
            )

    # Save uploaded file
    video_path = Path("storage/uploads") / file.filename
    try:
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Add to queue with language and model info
    job = await queue_manager.add_job(
        filename=file.filename,
        file_size=video_path.stat().st_size,
        video_path=str(video_path),
        target_language=target_language,
        llm_model=llm_model
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


@app.get("/api/download/{job_id}/raw")
async def download_raw_transcript(job_id: str):
    """Download raw (unformatted) transcript file."""
    job = queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.transcript_raw_path or not Path(job.transcript_raw_path).exists():
        raise HTTPException(status_code=404, detail="Raw transcript not found")

    return FileResponse(
        job.transcript_raw_path,
        media_type="text/plain",
        filename=f"{Path(job.filename).stem}_raw_transcript.txt"
    )


# ============== LLM API Endpoints ==============

@app.get("/api/config/llm")
async def get_llm_config():
    """Get unified LLM configuration."""
    return llm_service.get_config()


@app.put("/api/config/llm")
async def update_llm_config(config: LLMConfig):
    """Update unified LLM configuration."""
    updated_config = llm_service.update_config(config.model_dump())
    return {"message": "Configuration updated", "config": updated_config}


@app.get("/api/llm/status")
async def get_llm_status():
    """Get unified LLM status."""
    status = await llm_service.check_status()
    return status


@app.get("/api/llm/models")
async def get_llm_models(provider: Optional[str] = None):
    """Get available models for the specified or current provider."""
    models = await llm_service.list_models(provider)
    return {"models": models}


# ============== Ollama API Endpoints (Legacy) ==============

@app.get("/api/config/ollama")
async def get_ollama_config():
    """Get Ollama configuration (legacy, returns from unified config)."""
    config = llm_service.get_config()
    ollama_config = config.get("ollama", {})
    ollama_config["enabled"] = config.get("enabled", True) and config.get("provider") == "ollama"
    return ollama_config


@app.put("/api/config/ollama")
async def update_ollama_config(config: OllamaConfig):
    """Update Ollama configuration (legacy)."""
    current_config = llm_service.get_config()
    current_config["ollama"] = config.model_dump()
    if config.enabled:
        current_config["provider"] = "ollama"
    updated_config = llm_service.update_config(current_config)
    return {"message": "Configuration updated", "config": updated_config.get("ollama", {})}


@app.get("/api/ollama/status", response_model=OllamaStatus)
async def get_ollama_status():
    """Get Ollama service status."""
    status = await llm_service.check_ollama_status()
    return status


@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get available Ollama models."""
    status = await llm_service.check_ollama_status()
    if not status["available"]:
        raise HTTPException(
            status_code=503,
            detail=status.get("error", "Ollama service not available")
        )
    models = await llm_service.list_models("ollama")
    return {"models": models}


# ============== OpenRouter API Endpoints ==============

@app.get("/api/openrouter/status", response_model=OpenRouterStatus)
async def get_openrouter_status():
    """Get OpenRouter service status."""
    status = await llm_service.check_openrouter_status()
    return status


@app.get("/api/openrouter/models")
async def get_openrouter_models():
    """Get available OpenRouter models."""
    models = await llm_service.list_models("openrouter")
    return {"models": models}


@app.get("/api/languages", response_model=List[SupportedLanguage])
async def get_supported_languages():
    """Get list of supported languages."""
    return SUPPORTED_LANGUAGES


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

