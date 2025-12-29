"""Configuration management for Whisper CLI."""

import os
import torch
from pathlib import Path


class Config:
    """Configuration settings for Whisper CLI."""

    # Model settings
    MODEL_SIZE = "large-v3"

    # Device settings
    DEVICE_AUTO = "auto"
    DEVICE_CPU = "cpu"
    DEVICE_CUDA = "cuda"

    # Supported audio formats
    SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".webm"}

    @staticmethod
    def detect_device(device_preference="auto"):
        """
        Detect the best available device for inference.

        Args:
            device_preference: User's device preference ("auto", "cpu", or "cuda")

        Returns:
            str: Device to use ("cuda" or "cpu")
        """
        if device_preference == "cpu":
            return "cpu"

        if device_preference == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            else:
                print("Warning: CUDA requested but not available. Falling back to CPU.")
                return "cpu"

        # Auto detection
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @staticmethod
    def get_cache_dir():
        """
        Get the cache directory for model storage.

        Returns:
            Path: Cache directory path
        """
        # Use user's cache directory
        if os.name == 'nt':  # Windows
            cache_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'whisper-cli'
        else:  # Unix-like
            cache_dir = Path.home() / '.cache' / 'whisper-cli'

        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @staticmethod
    def is_supported_format(file_path):
        """
        Check if the audio file format is supported.

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if format is supported
        """
        return Path(file_path).suffix.lower() in Config.SUPPORTED_FORMATS
