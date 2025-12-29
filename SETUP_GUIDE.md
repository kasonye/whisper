# 视频转录 Web 应用 - 启动指南

## 项目概述

这是一个完整的全栈 Web 应用，可以上传视频文件，自动提取音频并使用 Whisper AI 进行转录，支持实时进度显示。

### 技术栈
- **后端**: FastAPI + Python
- **前端**: React + TypeScript + Ant Design
- **实时通信**: WebSocket
- **处理**: FFmpeg + Whisper-large-v3

## 前置要求

### 1. Python 环境
- Python 3.8 或更高版本
- pip 包管理器

### 2. Node.js 环境
- Node.js 14 或更高版本
- npm 包管理器

### 3. FFmpeg
必须安装 FFmpeg 和 ffprobe：

**Windows 安装：**
```bash
# 使用 Chocolatey
choco install ffmpeg

# 或手动下载：https://www.gyan.dev/ffmpeg/builds/
```

**验证安装：**
```bash
ffmpeg -version
ffprobe -version
```

### 4. Visual C++ Redistributable（Windows 必需）
**重要**: Windows 系统必须安装 Microsoft Visual C++ Redistributable 才能运行 PyTorch。

**安装方法：**

使用 winget（推荐）：
```bash
winget install Microsoft.VCRedist.2015+.x64
```

或使用 Chocolatey：
```bash
choco install vcredist-all
```

或手动下载安装：
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

### 5. GPU 支持（可选）
如需 GPU 加速，需要：
- NVIDIA GPU（支持 CUDA）
- CUDA Toolkit 11.8 或 12.x（驱动自带）
- 支持 CUDA 的 PyTorch

## 安装步骤

### 后端安装

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
```

3. 激活虚拟环境：
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. 安装依赖：

**重要**: 如需 GPU 加速，请先安装 GPU 版本的 PyTorch，再安装其他依赖。

**GPU 版本（推荐，需要 NVIDIA GPU）：**
```bash
# 检查 CUDA 版本
nvidia-smi

# 根据 CUDA 版本安装 PyTorch
# CUDA 12.4 或更高
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证 GPU 是否可用
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# 安装其他依赖
pip install -r requirements.txt
```

**CPU 版本（无 GPU 或 GPU 不可用）：**
```bash
pip install -r requirements.txt
```

**注意**: 如果遇到 PyTorch DLL 加载错误，请确保已安装 Visual C++ Redistributable（见前置要求第 4 项）。

### 前端安装

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

## 启动应用

### 1. 启动后端服务器

在 `backend` 目录下：

```bash
# 确保虚拟环境已激活
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 启动

API 文档：http://localhost:8000/docs

### 2. 启动前端开发服务器

在 `frontend` 目录下：

```bash
cd frontend
npm start
```

前端将在 http://localhost:3000 启动，浏览器会自动打开

## 使用说明

### 1. 上传视频
- 在浏览器中打开 http://localhost:3000
- 点击或拖拽视频文件到上传区域
- 支持格式：MP4, AVI, MKV, MOV, WEBM, FLV, WMV
- 最大文件大小：2GB

### 2. 查看进度
- 上传后，视频会自动加入处理队列
- 实时显示两个阶段的进度：
  - 阶段 1 (0-50%): FFmpeg 提取音频
  - 阶段 2 (50-100%): Whisper 转录
- 可以同时上传多个视频，系统会按顺序处理

### 3. 下载转录文本
- 处理完成后，点击"下载转录文本"按钮
- 文本文件格式：`{视频文件名}_transcript.txt`

### 4. 筛选任务
使用顶部的筛选按钮查看：
- 全部任务
- 处理中的任务
- 已完成的任务
- 失败的任务

## 项目结构

```
C:\Users\Kason\Desktop\Whisper\
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 主应用
│   │   ├── models.py            # 数据模型
│   │   ├── core/                # 核心处理逻辑
│   │   │   ├── queue_manager.py
│   │   │   ├── worker.py
│   │   │   ├── ffmpeg_processor.py
│   │   │   └── whisper_wrapper.py
│   │   └── utils/               # 工具类
│   │       └── websocket_manager.py
│   ├── storage/                 # 文件存储
│   │   ├── uploads/            # 上传的视频
│   │   ├── audio/              # 提取的音频
│   │   └── transcripts/        # 生成的转录文本
│   └── requirements.txt
│
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── App.tsx             # 主组件
│   │   ├── components/         # UI 组件
│   │   ├── hooks/              # 自定义 Hooks
│   │   └── types/              # TypeScript 类型
│   └── package.json
│
└── whisper_cli/                # Whisper CLI（原有）
    ├── transcriber.py
    └── ...
```

## 故障排除

### 后端问题

**1. PyTorch DLL 加载错误（Windows）**
```
OSError: [WinError 1114] 动态链接库(DLL)初始化例程失败
Error loading "torch\lib\c10.dll" or one of its dependencies
```

**解决方法：**
```bash
# 安装 Visual C++ Redistributable
winget install Microsoft.VCRedist.2015+.x64

# 或使用 Chocolatey
choco install vcredist-all

# 安装后重新启动后端服务器
```

**2. 模块导入错误**
```bash
# 确保在 backend 目录下运行
cd backend
python -m uvicorn app.main:app --reload
```

**3. FFmpeg 未找到**
```bash
# 验证 FFmpeg 安装
ffmpeg -version

# Windows: 确保 FFmpeg 在 PATH 中
```

**4. GPU 不可用**
```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"

# 如果返回 False，检查：
# 1. 是否安装了 GPU 版本的 PyTorch
# 2. NVIDIA 驱动是否正确安装
# 3. 使用 nvidia-smi 检查 GPU 状态

# 如果 GPU 不可用，系统会自动使用 CPU 模式
```

**5. 端口被占用**
```bash
# 使用不同端口
uvicorn app.main:app --reload --port 8001

# 同时修改前端 API_URL 和 WS_URL
```

**6. 虚拟环境问题**
```bash
# 如果遇到依赖冲突，重新创建虚拟环境
cd backend
rm -rf venv  # Windows: rmdir /s venv
python -m venv venv
venv\Scripts\activate
# 然后重新安装依赖
```

### 前端问题

**1. 无法连接后端**
- 确保后端服务器正在运行
- 检查 CORS 设置
- 查看浏览器控制台错误信息

**2. WebSocket 连接失败**
- 确认后端 WebSocket 端点正常
- 检查防火墙设置
- 查看浏览器控制台 WebSocket 错误

**3. 上传失败**
- 检查文件格式是否支持
- 确认文件大小不超过 2GB
- 查看后端日志

## 性能优化

### GPU 加速
- 使用 NVIDIA GPU 可将转录速度提升 10-20 倍
- 确保安装了支持 CUDA 的 PyTorch
- 首次运行会下载 Whisper 模型（约 3GB）

### 并发处理
- 默认配置：2 个并发 Worker
- 可在 `backend/app/main.py` 中修改：
```python
queue_manager = QueueManager(max_workers=2)  # 修改此值
```

### 存储管理
- 定期清理 `storage/` 目录下的临时文件
- 音频文件可在转录完成后删除
- 考虑实现自动清理机制

## API 端点

### REST API
- `POST /api/upload` - 上传视频文件
- `GET /api/jobs` - 获取所有任务
- `GET /api/jobs/{job_id}` - 获取特定任务
- `GET /api/download/{job_id}` - 下载转录文本

### WebSocket
- `WS /ws` - 实时任务更新

完整 API 文档：http://localhost:8000/docs

## 开发说明

### 后端开发
```bash
cd backend
# 启用热重载
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
# 启动开发服务器
npm start
```

### 生产部署
```bash
# 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run build
# 将 build/ 目录部署到 Web 服务器
```

## 常见问题

**Q: 首次运行很慢？**
A: 首次运行会下载 Whisper-large-v3 模型（约 3GB），需要稳定的网络连接。

**Q: 可以同时处理多少个视频？**
A: 默认 2 个并发 Worker，可根据硬件配置调整。

**Q: 支持哪些语言？**
A: Whisper 支持 99 种语言，会自动检测语言。

**Q: 转录准确率如何？**
A: 使用 Whisper-large-v3 模型，准确率较高，但取决于音频质量。

**Q: 可以取消正在处理的任务吗？**
A: 当前版本不支持取消，可在后续版本中添加此功能。

## 技术支持

如遇问题，请检查：
1. 后端控制台日志
2. 浏览器控制台错误
3. 网络连接状态
4. FFmpeg 和 Python 环境

## 许可证

MIT License
