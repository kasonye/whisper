"""Data models for the video transcription application."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    FORMATTING_LLM = "formatting_llm"
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
    transcript_raw_path: Optional[str] = None
    # LLM processing fields
    target_language: Optional[str] = None
    llm_model: Optional[str] = None
    llm_model_used: Optional[str] = None
    llm_processing_skipped: bool = False
    detected_language: Optional[str] = None

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


class OllamaConfig(BaseModel):
    """Ollama configuration model."""
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5:7b"
    timeout: int = 300
    chunk_size: Optional[int] = 4000
    chunk_overlap: Optional[int] = 200


class OllamaStatus(BaseModel):
    """Ollama status model."""
    available: bool
    url: str
    enabled: bool
    models_count: int
    error: Optional[str] = None


class SupportedLanguage(BaseModel):
    """Supported language model."""
    code: str
    name: str
    native_name: str


# Supported languages list
SUPPORTED_LANGUAGES: List[SupportedLanguage] = [
    SupportedLanguage(code="zh", name="Chinese", native_name="中文"),
    SupportedLanguage(code="en", name="English", native_name="English"),
    SupportedLanguage(code="ja", name="Japanese", native_name="日本語"),
    SupportedLanguage(code="ko", name="Korean", native_name="한국어"),
    SupportedLanguage(code="fr", name="French", native_name="Français"),
    SupportedLanguage(code="de", name="German", native_name="Deutsch"),
    SupportedLanguage(code="es", name="Spanish", native_name="Español"),
    SupportedLanguage(code="ru", name="Russian", native_name="Русский"),
    SupportedLanguage(code="pt", name="Portuguese", native_name="Português"),
    SupportedLanguage(code="it", name="Italian", native_name="Italiano"),
    SupportedLanguage(code="ar", name="Arabic", native_name="العربية"),
    SupportedLanguage(code="th", name="Thai", native_name="ไทย"),
    SupportedLanguage(code="vi", name="Vietnamese", native_name="Tiếng Việt"),
]
