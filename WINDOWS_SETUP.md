# Windows 系统安装指南

本指南专门针对 Windows 系统用户，解决常见的安装和运行问题。

## 必需组件

### 1. Visual C++ Redistributable（必需）

**为什么需要？**
PyTorch 在 Windows 上依赖 Microsoft Visual C++ 运行库。如果没有安装，会出现 DLL 加载错误。

**安装方法：**

**方法 1: 使用 winget（推荐）**
```bash
winget install Microsoft.VCRedist.2015+.x64
```

**方法 2: 使用 Chocolatey**
```bash
choco install vcredist-all
```

**方法 3: 手动下载**
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
- 双击安装

**验证安装：**
安装完成后，重新启动命令行窗口，然后测试：
```bash
cd backend
venv\Scripts\python -c "import torch; print('Success!')"
```

### 2. FFmpeg

**安装方法：**

**使用 Chocolatey（推荐）：**
```bash
choco install ffmpeg
```

**手动安装：**
1. 下载：https://www.gyan.dev/ffmpeg/builds/
2. 解压到 `C:\ffmpeg`
3. 添加到 PATH：
   - 右键"此电脑" → 属性 → 高级系统设置
   - 环境变量 → 系统变量 → Path → 编辑
   - 新建 → 输入 `C:\ffmpeg\bin`
   - 确定

**验证安装：**
```bash
ffmpeg -version
```

### 3. Python 3.8+

**下载：**
https://www.python.org/downloads/

**安装注意事项：**
- ✅ 勾选 "Add Python to PATH"
- ✅ 选择 "Install for all users"

**验证安装：**
```bash
python --version
pip --version
```

### 4. Node.js 14+

**下载：**
https://nodejs.org/

**验证安装：**
```bash
node --version
npm --version
```

## GPU 支持（可选）

### 检查 GPU

```bash
nvidia-smi
```

如果看到 GPU 信息和 CUDA 版本，说明驱动已正确安装。

### 安装 GPU 版本的 PyTorch

**重要**: 必须先安装 GPU 版本的 PyTorch，再安装其他依赖。

```bash
cd backend
venv\Scripts\activate

# 检查 CUDA 版本（从 nvidia-smi 输出中查看）
# CUDA 12.4 或更高
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证 GPU 是否可用
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

# 安装其他依赖
pip install -r requirements.txt
```

## 常见问题

### 问题 1: PyTorch DLL 加载错误

**错误信息：**
```
OSError: [WinError 1114] 动态链接库(DLL)初始化例程失败
Error loading "C:\...\torch\lib\c10.dll" or one of its dependencies
```

**原因：**
缺少 Visual C++ Redistributable

**解决方法：**
```bash
# 安装 Visual C++ Redistributable
winget install Microsoft.VCRedist.2015+.x64

# 重新启动命令行窗口
# 重新启动后端服务器
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### 问题 2: FFmpeg 未找到

**错误信息：**
```
FileNotFoundError: [WinError 2] 系统找不到指定的文件。
```

**解决方法：**
```bash
# 安装 FFmpeg
choco install ffmpeg

# 或手动添加到 PATH
# 验证
ffmpeg -version
```

### 问题 3: GPU 不可用

**检查步骤：**

1. 验证 NVIDIA 驱动：
```bash
nvidia-smi
```

2. 检查 PyTorch 版本：
```bash
cd backend
venv\Scripts\activate
python -c "import torch; print(torch.__version__)"
```

如果版本号包含 `+cpu`，说明安装的是 CPU 版本。

3. 重新安装 GPU 版本：
```bash
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

4. 验证：
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

### 问题 4: 端口被占用

**错误信息：**
```
OSError: [WinError 10048] 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

**解决方法：**

查找占用端口的进程：
```bash
netstat -ano | findstr :8000
```

终止进程：
```bash
taskkill /PID <进程ID> /F
```

或使用不同端口：
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### 问题 5: 虚拟环境激活失败

**错误信息：**
```
无法加载文件 venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决方法（PowerShell）：**
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**或使用 CMD 而不是 PowerShell：**
```bash
# 在 CMD 中
venv\Scripts\activate.bat
```

### 问题 6: npm 安装失败

**错误信息：**
```
npm ERR! network timeout
```

**解决方法：**
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 重新安装
cd frontend
npm install
```

## 完整安装流程（Windows）

### 步骤 1: 安装必需软件

```bash
# 安装 Visual C++ Redistributable
winget install Microsoft.VCRedist.2015+.x64

# 安装 FFmpeg
choco install ffmpeg

# 验证 Python 和 Node.js
python --version
node --version
```

### 步骤 2: 克隆或下载项目

```bash
cd C:\Users\YourName\Desktop
# 假设项目已在 Whisper 目录
cd Whisper
```

### 步骤 3: 设置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装 GPU 版本的 PyTorch（如果有 NVIDIA GPU）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 安装其他依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

### 步骤 4: 设置前端

```bash
cd ..\frontend

# 安装依赖
npm install
```

### 步骤 5: 启动应用

**方法 1: 使用启动脚本**
```bash
cd ..
start.bat
```

**方法 2: 手动启动**

终端 1（后端）：
```bash
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

终端 2（前端）：
```bash
cd frontend
npm start
```

### 步骤 6: 访问应用

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 性能优化建议

### GPU 加速

如果有 NVIDIA GPU：
- 确保安装了 GPU 版本的 PyTorch
- 转录速度可提升 10-20 倍
- 1 小时视频约 5-8 分钟完成

### CPU 模式

如果没有 GPU：
- 系统会自动使用 CPU
- 转录速度约 1-3 倍实时速度
- 1 小时视频约 30-60 分钟完成

## 卸载

### 卸载后端

```bash
cd backend
rmdir /s /q venv
```

### 卸载前端

```bash
cd frontend
rmdir /s /q node_modules
```

### 卸载依赖软件

```bash
# 卸载 FFmpeg
choco uninstall ffmpeg

# Visual C++ Redistributable 建议保留，其他软件可能需要
```

## 技术支持

如果遇到其他问题：

1. 检查后端控制台日志
2. 检查浏览器控制台（F12）
3. 确认所有必需软件已正确安装
4. 尝试重新创建虚拟环境

## 系统要求

**最低配置：**
- Windows 10/11
- 8GB RAM
- 10GB 可用磁盘空间
- 双核 CPU

**推荐配置：**
- Windows 10/11
- 16GB+ RAM
- 20GB+ 可用磁盘空间
- NVIDIA GPU（8GB+ 显存）
- 四核+ CPU

## 首次运行注意事项

1. **模型下载**：首次运行会自动下载 Whisper-large-v3 模型（约 3GB），需要稳定的网络连接
2. **防火墙**：可能需要允许 Python 和 Node.js 通过防火墙
3. **杀毒软件**：某些杀毒软件可能会误报，需要添加信任
4. **磁盘空间**：确保有足够空间存储上传的视频和生成的文件

## 更新项目

```bash
# 更新后端依赖
cd backend
venv\Scripts\activate
pip install -r requirements.txt --upgrade

# 更新前端依赖
cd ..\frontend
npm update
```

## 许可证

MIT License
