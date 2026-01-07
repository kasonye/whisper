# 视频转录系统 (Video Transcription System)

一个完整的全栈 Web 应用，支持视频上传、音频提取和 AI 转录，带实时进度显示。

## 项目包含

1. **Whisper CLI** - 命令行音频转录工具
2. **Web 应用** - 基于 React + FastAPI 的视频转录 Web 界面

---

# Web 应用使用指南

## 快速开始

### 前置要求
1. Python 3.8+
2. Node.js 14+
3. FFmpeg
4. **Visual C++ Redistributable（Windows 必需）**
5. NVIDIA GPU（可选，用于 GPU 加速）

### 一键启动（Windows）
双击运行 `start.bat` 文件，脚本会自动：
- 检查依赖
- 安装所需包
- 启动后端和前端服务器

**注意**: 首次运行前，请确保已安装：
- Visual C++ Redistributable: `winget install Microsoft.VCRedist.2015+.x64`
- FFmpeg: `choco install ffmpeg`

### 手动启动
- **Windows 用户**: 详细步骤请查看 [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- **通用指南**: 详细步骤请查看 [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 功能特性

- ✅ 拖拽上传视频文件
- ✅ 自动提取音频（FFmpeg）
- ✅ AI 转录（Whisper-large-v3）
- ✅ 实时进度显示（WebSocket）
- ✅ 队列处理多个视频
- ✅ 一键下载转录文本
- ✅ GPU 加速支持
- ✅ **LLM 智能文本处理**（NEW）
  - 支持 Ollama（本地）和 OpenRouter（云端 API）
  - 自动标点符号添加和段落分段
  - 多语言翻译支持（13+ 语言）
  - 可配置的 LLM 提供商切换

## 技术栈

- **前端**: React + TypeScript + Ant Design
- **后端**: FastAPI + Python
- **实时通信**: WebSocket
- **AI 模型**: Whisper-large-v3
- **音频处理**: FFmpeg
- **LLM 支持**: Ollama / OpenRouter (GPT-4o, Claude, Gemini, Qwen 等)

## 项目结构

```
Whisper/
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
├── whisper_cli/      # CLI 工具
├── start.bat         # 一键启动脚本
└── SETUP_GUIDE.md    # 详细安装指南
```

## 访问地址

- 前端界面: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## LLM 配置

转录完成后，可使用 LLM 对文本进行智能格式化和翻译处理。

### 方式一：Ollama（本地，免费）

1. 安装 Ollama: https://ollama.ai
2. 下载推荐模型：
   ```bash
   ollama pull qwen2.5:7b    # 中文推荐
   ollama pull llama3        # 英文推荐
   ```
3. 在前端"LLM 设置"中配置 Ollama

### 方式二：OpenRouter（云端 API）

1. 注册 OpenRouter: https://openrouter.ai
2. 获取 API Key
3. 在前端"LLM 设置"中配置 OpenRouter API Key
4. 选择模型（推荐：gpt-4o-mini、claude-3-haiku）

### 支持的翻译语言

中文、英文、日语、韩语、法语、德语、西班牙语、俄语、葡萄牙语、意大利语、阿拉伯语、泰语、越南语

---

# Whisper CLI 工具

命令行音频转录工具，使用 OpenAI 的 Whisper-large-v3 模型。

## Features

- Fast transcription using faster-whisper (4x faster than original implementation)
- Automatic GPU detection with CPU fallback
- Support for multiple audio formats (WAV, MP3, FLAC, M4A, OGG, OPUS, WEBM)
- Clean command-line interface with progress indicators
- Output to stdout or file

## Requirements

- Python 3.8 or higher
- 4GB+ RAM (8GB+ recommended)
- 5GB+ disk space for model storage
- Optional: CUDA-compatible GPU for faster inference

## Installation

1. Create a virtual environment:
```bash
python -m venv whisper_env
```

2. Activate the virtual environment:
```bash
# Windows
whisper_env\Scripts\activate

# Linux/Mac
source whisper_env/bin/activate
```

3. Install the package:
```bash
pip install -e .
```

On first run, the Whisper-large-v3 model (~3GB) will be automatically downloaded.

## Usage

### Basic Usage

Transcribe an audio file and print to stdout:
```bash
whisper-cli audio.wav
```

### Save to File

Save transcription to a text file:
```bash
whisper-cli audio.mp3 -o transcript.txt
```

### Force CPU Usage

Use CPU even if GPU is available:
```bash
whisper-cli audio.wav --device cpu
```

### Verbose Output

Enable detailed output with file info and language detection:
```bash
whisper-cli audio.wav --verbose
```

### Get Help

Display all available options:
```bash
whisper-cli --help
```

## Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- M4A (.m4a)
- OGG (.ogg)
- OPUS (.opus)
- WEBM (.webm)

## Examples

```bash
# Basic transcription
whisper-cli interview.wav

# Save to file with verbose output
whisper-cli podcast.mp3 -o transcript.txt --verbose

# Use CPU only
whisper-cli lecture.m4a --device cpu

# Multiple files (using shell loop)
for file in *.wav; do whisper-cli "$file" -o "${file%.wav}.txt"; done
```

## Performance

- **GPU (CUDA)**: Recommended for best performance
  - Typical speed: 10-20x real-time
  - Example: 1 hour audio transcribed in 3-6 minutes

- **CPU**: Slower but still functional
  - Typical speed: 1-3x real-time
  - Example: 1 hour audio transcribed in 20-60 minutes

## Troubleshooting

### CUDA Out of Memory

If you encounter GPU memory errors, try using CPU:
```bash
whisper-cli audio.wav --device cpu
```

### Model Download Issues

If model download fails, check your internet connection and try again. The model is cached after the first successful download.

### Unsupported Audio Format

Convert your audio to a supported format using ffmpeg:
```bash
ffmpeg -i input.avi -vn -acodec libmp3lame output.mp3
```

## Project Structure

```
whisper_cli/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface
├── transcriber.py       # Whisper model integration
├── audio_processor.py   # Audio file validation
└── config.py            # Configuration management
```

## Dependencies

- faster-whisper: Fast Whisper inference
- click: Command-line interface framework
- rich: Terminal formatting and progress bars
- librosa: Audio processing
- soundfile: Audio file I/O
- torch: PyTorch backend
- torchaudio: Audio utilities

## License

MIT License

## Acknowledgments

- OpenAI for the Whisper model
- faster-whisper for the optimized implementation
