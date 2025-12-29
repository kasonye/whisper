"""Download Whisper large-v3 model."""

import os
from pathlib import Path
from faster_whisper import WhisperModel

def get_cache_dir():
    """Get the cache directory for model storage."""
    if os.name == 'nt':  # Windows
        cache_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'whisper-cli'
    else:  # Unix-like
        cache_dir = Path.home() / '.cache' / 'whisper-cli'

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def download_model():
    """Download the Whisper large-v3 model."""
    print("Downloading Whisper large-v3 model...")
    print("This may take a few minutes (model size: ~3GB)")
    print()

    cache_dir = get_cache_dir()
    print(f"Model will be saved to: {cache_dir}")
    print()

    try:
        # Load model - this will trigger download if not cached
        model = WhisperModel(
            "large-v3",
            device="cpu",  # Use CPU for download to avoid GPU memory issues
            compute_type="int8",
            download_root=str(cache_dir)
        )

        print()
        print("✓ Model downloaded successfully!")
        print(f"✓ Model location: {cache_dir}")
        print()
        print("You can now use the model with whisper-cli or the web application.")

    except Exception as e:
        print(f"✗ Error downloading model: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Make sure you have enough disk space (~5GB)")
        print("3. Try running the script again")

if __name__ == "__main__":
    download_model()
