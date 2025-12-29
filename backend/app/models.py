"""Data models for the video transcription application."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Model for creating a new job."""
    filename: str
    file_size: int


class Job(BaseModel):
    """Job model representing a transcription job."""
    id: str
    filename: str
    file_size: int
    status: JobStatus
    progress: float  # 0-100
    current_stage: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    video_path: str
    audio_path: Optional[str] = None
    transcript_path: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProgressUpdate(BaseModel):
    """Model for progress update messages."""
    job_id: str
    status: JobStatus
    progress: float
    current_stage: str
    message: str
