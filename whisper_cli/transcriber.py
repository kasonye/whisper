"""Whisper model integration and transcription logic."""

from faster_whisper import WhisperModel
from .config import Config


class TranscriberError(Exception):
    """Custom exception for transcription errors."""
    pass


class WhisperTranscriber:
    """Handles Whisper model loading and transcription."""

    def __init__(self, device="auto", verbose=False):
        """
        Initialize the transcriber.

        Args:
            device: Device preference ("auto", "cpu", or "cuda")
            verbose: Enable verbose output
        """
        self.device = Config.detect_device(device)
        self.verbose = verbose
        self.model = None
        self._model_loaded = False

    def _load_model(self):
        """Load the Whisper model (lazy loading)."""
        if self._model_loaded:
            return

        if self.verbose:
            print(f"Loading Whisper {Config.MODEL_SIZE} model on {self.device}...")

        try:
            # Load model with faster-whisper
            # compute_type: "float16" for GPU, "int8" for CPU for better performance
            compute_type = "float16" if self.device == "cuda" else "int8"

            self.model = WhisperModel(
                Config.MODEL_SIZE,
                device=self.device,
                compute_type=compute_type,
                download_root=str(Config.get_cache_dir())
            )
            self._model_loaded = True

            if self.verbose:
                print(f"Model loaded successfully on {self.device}")

        except Exception as e:
            raise TranscriberError(f"Failed to load Whisper model: {str(e)}")

    def transcribe(self, audio_path):
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            str: Transcribed text

        Raises:
            TranscriberError: If transcription fails
        """
        # Load model if not already loaded
        self._load_model()

        if self.verbose:
            print(f"Transcribing: {audio_path}")

        try:
            # Transcribe the audio
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
                language=None,  # Auto-detect language
                task="transcribe"  # Transcribe (not translate)
            )

            # Collect all segments into a single text
            transcription = ""
            for segment in segments:
                transcription += segment.text

            # Clean up the transcription
            transcription = transcription.strip()

            if self.verbose:
                print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
                print(f"Duration: {info.duration:.2f} seconds")

            return transcription

        except Exception as e:
            raise TranscriberError(f"Transcription failed: {str(e)}")

    def get_device_info(self):
        """
        Get information about the device being used.

        Returns:
            dict: Device information
        """
        return {
            "device": self.device,
            "model_loaded": self._model_loaded,
            "model_size": Config.MODEL_SIZE
        }
