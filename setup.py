from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="whisper-cli",
    version="1.0.0",
    author="Whisper CLI",
    description="Audio transcription tool using Whisper-large-v3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "faster-whisper>=0.10.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "whisper-cli=whisper_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
