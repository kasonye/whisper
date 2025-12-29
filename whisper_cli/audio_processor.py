"""Audio file processing and validation."""

import os
from pathlib import Path
from .config import Config


class AudioProcessorError(Exception):
    """Custom exception for audio processing errors."""
    pass


class AudioProcessor:
    """Handles audio file validation and preprocessing."""

    @staticmethod
    def validate_file(file_path):
        """
        Validate that the audio file exists and is in a supported format.

        Args:
            file_path: Path to the audio file

        Returns:
            Path: Validated file path

        Raises:
            AudioProcessorError: If file doesn't exist or format is unsupported
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise AudioProcessorError(f"File not found: {file_path}")

        # Check if it's a file (not a directory)
        if not path.is_file():
            raise AudioProcessorError(f"Path is not a file: {file_path}")

        # Check if file is readable
        if not os.access(path, os.R_OK):
            raise AudioProcessorError(f"File is not readable: {file_path}")

        # Check if format is supported
        if not Config.is_supported_format(path):
            supported = ", ".join(sorted(Config.SUPPORTED_FORMATS))
            raise AudioProcessorError(
                f"Unsupported audio format: {path.suffix}\n"
                f"Supported formats: {supported}"
            )

        # Check if file is not empty
        if path.stat().st_size == 0:
            raise AudioProcessorError(f"File is empty: {file_path}")

        return path

    @staticmethod
    def get_file_info(file_path):
        """
        Get basic information about the audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            dict: File information (name, size, format)
        """
        path = Path(file_path)
        size_mb = path.stat().st_size / (1024 * 1024)

        return {
            "name": path.name,
            "size_mb": round(size_mb, 2),
            "format": path.suffix.lower(),
            "path": str(path.absolute())
        }
