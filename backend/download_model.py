#!/usr/bin/env python3
"""Download Whisper model"""

from faster_whisper import WhisperModel
import sys

print("Downloading Whisper large-v3 model...")
print("This may take a few minutes (model size: ~3GB)")
print()

try:
    # Download model with GPU support
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    print()
    print("✓ Model downloaded successfully!")
    print("✓ GPU support enabled")

except Exception as e:
    print(f"Error downloading model: {e}")
    print()
    print("Trying CPU version...")
    try:
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")
        print()
        print("✓ Model downloaded successfully!")
        print("✓ CPU mode enabled")
    except Exception as e2:
        print(f"Error: {e2}")
        sys.exit(1)

print()
print("You can now use the video transcription system!")
