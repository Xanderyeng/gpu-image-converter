# WSL2 Development Setup Guide

> **Complete guide for setting up GPU-accelerated development in WSL2**

## 🎯 Why WSL2?

For GPU development with Docker and NVIDIA CUDA, **WSL2 is essential** because:

✅ **Native GPU Support** - NVIDIA drivers work seamlessly
✅ **Docker Integration** - Docker Desktop GPU access
✅ **Better Performance** - Native Linux filesystem is 2-5x faster
✅ **Production Parity** - Matches your Docker container environment
✅ **Linux Tooling** - Access to apt, native Python builds, etc.

---

## 🚀 Step-by-Step Setup

### Step 1: Verify WSL2 is Installed

```powershell
# In PowerShell (Windows), check WSL version
wsl --list --verbose

# You should see:
#   NAME      STATE   VERSION
# * Ubuntu    Running    2
```

If WSL2 isn't installed:

```powershell
# Install WSL2
wsl --install

# Set default version to WSL2
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu-22.04

# Restart your computer
```

### Step 2: Copy Project to WSL2 (Recommended)

For **much better performance**, copy your project to WSL2's native filesystem:

```bash
# Open WSL2 terminal (run 'wsl' in PowerShell or open Ubuntu app)
wsl

# Create workspace
mkdir -p ~/projects
cd ~/projects

# Copy project from Windows to WSL2
cp -r /mnt/c/Users/alexa/Documents/personal/gpu-image-converter ./

# Navigate to the project
cd gpu-image-converter

# Verify copy
ls -la
```

**⚠️ Important:** You can still access these files from Windows at:
```
\\wsl$\Ubuntu\home\<your-username>\projects\gpu-image-converter
```

### Step 3: Update System Packages

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    software-properties-common
```

### Step 4: Install Python 3.11

```bash
# Add deadsnakes PPA for Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and development packages
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip

# Verify installation
python3.11 --version
# Should show: Python 3.11.x

# Set Python 3.11 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Step 5: Install System Dependencies for Image Processing

```bash
# Install libvips and image processing libraries
sudo apt install -y \
    libvips-dev \
    libvips-tools \
    imagemagick \
    ffmpeg \
    libopencv-dev \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev

# Verify libvips installation
vips --version
# Should show: vips-8.x.x
```

### Step 6: Set Up Python Virtual Environment

```bash
# Navigate to backend folder
cd ~/projects/gpu-image-converter/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should now see (venv) in your prompt:
# (venv) user@hostname:~/projects/gpu-image-converter/backend$

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel
```

### Step 7: Install Python Dependencies

```bash
# Make sure you're in the backend folder with venv activated
cd ~/projects/gpu-image-converter/backend
source venv/bin/activate

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# This will take 5-10 minutes, be patient!
```

**Note:** PyTorch and CUDA libraries are large downloads (~2GB). The installation includes:
- FastAPI and web framework
- Celery and Redis for task queuing
- Image processing libraries (Pillow, pyvips, OpenCV)
- GPU libraries (PyTorch with CUDA, CuPy)

### Step 8: Verify Installation

```bash
# Test Python imports
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import celery; print('Celery:', celery.__version__)"
python -c "import pyvips; print('PyVips:', pyvips.__version__)"

# Test PyTorch (CPU only for now, GPU needs Docker)
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
```

### Step 9: Create Required Directories

```bash
# Create upload and output directories
mkdir -p uploads outputs

# Verify structure
ls -la
# You should see: app/, tests/, docs/, uploads/, outputs/, venv/
```

### Step 10: Set Up Environment Variables

```bash
# Copy the .env file if not already there
# The .env file should already exist from Windows

# Verify .env exists
cat .env

# If not, create it:
cat > .env << 'EOF'
# Backend
REDIS_URL=redis://redis:6379/0
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs
MAX_FILE_SIZE=104857600
ALLOWED_FORMATS=jpg,jpeg,png,webp,gif,bmp,tiff,svg,avif,heic
SECRET_KEY=dev-secret-key-change-in-production
MAX_CONCURRENT_JOBS=4
CLEANUP_AFTER_HOURS=24
DEFAULT_QUALITY=90

# GPU
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
EOF
```

---

## 🧪 Testing the Backend (Without Docker)

### Option 1: Test Individual Components

```bash
# Activate venv
cd ~/projects/gpu-image-converter/backend
source venv/bin/activate

# Test converter module (without GPU, just validation)
python -c "from app.converter import GPUImageConverter; c = GPUImageConverter(); print('Converter initialized')"

# Test models
python -c "from app.models import ConversionOptions, ImageFormat; print('Models imported successfully')"

# Test utilities
python -c "from app.utils import format_bytes, get_gpu_info; print(format_bytes(1024**3)); print(get_gpu_info())"
```

### Option 2: Run FastAPI Development Server

**⚠️ Note:** Redis and Celery won't work without Docker, but you can test the API structure:

```bash
# Start FastAPI dev server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

Open another WSL2 terminal and test:

```bash
# Test health endpoint
curl http://localhost:8000/health

# View API docs
curl http://localhost:8000/api/docs
```

Or from Windows browser: `http://localhost:8000/api/docs`

---

## 🐳 Docker Setup (Full GPU Testing)

For full GPU support, you'll need Docker:

### Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/
2. Install and restart
3. Open Docker Desktop settings:
   - Enable "Use WSL 2 based engine"
   - Enable "WSL Integration" with your Ubuntu distribution

### Step 2: Verify Docker in WSL2

```bash
# In WSL2 terminal
docker --version
docker compose version

# Test Docker works
docker run hello-world
```

### Step 3: Test GPU Access in Docker

```bash
# Test NVIDIA GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# You should see your RTX 4060 listed!
```

### Step 4: Build and Run with Docker

```bash
# Navigate to project root
cd ~/projects/gpu-image-converter

# Build all services
docker compose build

# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Test API
curl http://localhost/api/health
```

---

## 🛠️ Development Workflow

### Daily Development Routine

```bash
# 1. Open WSL2 terminal
wsl

# 2. Navigate to project
cd ~/projects/gpu-image-converter/backend

# 3. Activate virtual environment
source venv/bin/activate

# 4. Make your code changes in VS Code or your editor

# 5. Run tests
pytest tests/ -v

# 6. Run development server
uvicorn app.main:app --reload

# 7. When done, deactivate venv
deactivate
```

### Using VS Code with WSL2

1. Install "Remote - WSL" extension in VS Code
2. Open WSL2 terminal
3. Navigate to project: `cd ~/projects/gpu-image-converter`
4. Open in VS Code: `code .`
5. VS Code will open connected to WSL2!

### Git Workflow in WSL2

```bash
# Configure git (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Normal git workflow
git status
git add .
git commit -m "Your commit message"
git push
```

---

## 📝 Important Notes

### File System Performance

- **WSL2 native** (`~/projects/`): **Fast** ✅
- **Windows mount** (`/mnt/c/`): **Slow** ❌

Always work from `~/` in WSL2 for best performance!

### Accessing Files

- **From Windows to WSL2**: `\\wsl$\Ubuntu\home\<username>\projects\`
- **From WSL2 to Windows**: `/mnt/c/Users/alexa/Documents/`

### Virtual Environment

- Always activate venv before installing packages or running code
- Your prompt should show `(venv)` when active
- Deactivate with: `deactivate`

### GPU Access

- GPU access **only works in Docker containers** on WSL2
- Native Python in WSL2 can access GPU if CUDA is installed in WSL2 (advanced)
- For this project, we use Docker for GPU access

---

## 🐛 Troubleshooting

### "python3.11: command not found"

```bash
sudo apt update
sudo apt install -y python3.11
```

### "pip: command not found"

```bash
sudo apt install -y python3-pip
```

### "venv activation doesn't work"

```bash
# Make sure you're in backend folder
cd ~/projects/gpu-image-converter/backend

# Try with full path
source ./venv/bin/activate
```

### "Docker not found in WSL2"

1. Make sure Docker Desktop is running
2. Check WSL2 integration in Docker Desktop settings
3. Restart WSL2: `wsl --shutdown` then open Ubuntu again

### "Permission denied" errors

```bash
# Fix ownership
sudo chown -R $USER:$USER ~/projects/gpu-image-converter
```

### Package installation fails

```bash
# Update pip
pip install --upgrade pip

# Install wheel
pip install wheel

# Try again
pip install -r requirements.txt
```

---

## ✅ Verification Checklist

Before continuing, verify:

- [ ] WSL2 is installed and running
- [ ] Project copied to `~/projects/gpu-image-converter`
- [ ] Python 3.11 installed: `python3.11 --version`
- [ ] Virtual environment created and activated
- [ ] All requirements installed: `pip list | grep fastapi`
- [ ] Can import modules: `python -c "import fastapi"`
- [ ] Docker Desktop installed and running
- [ ] GPU accessible in Docker: `docker run --gpus all nvidia/cuda:12.2.0-base nvidia-smi`

---

## 🎯 Next Steps

Once setup is complete:

1. ✅ **Backend is ready** - You can now develop in WSL2
2. 📝 **Implement features** - Add endpoints, improve converter
3. 🧪 **Write tests** - Run `pytest tests/`
4. 🐳 **Test with Docker** - Full GPU testing with `docker compose up`
5. 🎨 **Frontend setup** - Move to frontend development

---

**You're now ready to develop!** 🚀

Return to [Implementation Guide](./IMPLEMENTATION_GUIDE.md) to continue with Phase 2.
