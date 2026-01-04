# Backend Implementation Guide

> **FastAPI + Celery + GPU Image Processing**

## Table of Contents

1. [Setup](#setup)
2. [Project Structure](#project-structure)
3. [GPU Converter Implementation](#gpu-converter-implementation)
4. [FastAPI Endpoints](#fastapi-endpoints)
5. [Celery Worker](#celery-worker)
6. [Docker Configuration](#docker-configuration)
7. [Testing](#testing)

---

## Setup

### Step 1: Create Backend Structure

```bash
cd backend

# Create folder structure
mkdir -p app tests docs

# Create initial files
touch app/__init__.py
touch app/main.py
touch app/worker.py
touch app/converter.py
touch app/models.py
touch app/utils.py
touch tests/__init__.py
touch tests/test_converter.py
touch tests/test_api.py
```

### Step 2: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
# ============================================
# Web Framework
# ============================================
fastapi==0.109.2
uvicorn[standard]==0.27.1
python-multipart==0.0.9
aiofiles==23.2.1

# ============================================
# Task Queue
# ============================================
celery==5.3.6
redis==5.0.1

# ============================================
# Image Processing - Core
# ============================================
pillow==10.2.0
pillow-simd==10.2.0
pyvips==2.2.1
opencv-python-headless==4.9.0.80
imageio==2.34.0

# ============================================
# GPU Computing
# ============================================
torch==2.2.0+cu121
torchvision==0.17.0+cu121
cupy-cuda12x==13.0.0

# ============================================
# Data Validation
# ============================================
pydantic==2.6.1
pydantic-settings==2.1.0

# ============================================
# Utilities
# ============================================
python-jose[cryptography]==3.3.0
python-dotenv==1.0.1
websockets==12.0
EOF
```

### System prerequisites (local development)

If you're developing or running the backend locally (outside Docker), you need the `pyvips` Python package and the `libvips` native library. On Debian/Ubuntu the simplest way is:

```bash
sudo apt update
sudo apt install -y libvips libvips-dev libvips-tools
# create and activate a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate
# install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
# verify pyvips is importable
python -c "import pyvips; print('pyvips', pyvips.__version__)"
```

Notes:
- If you don't have root access, install `libvips` via your package manager or use the Docker image included in this repo which already contains the native dependencies.
- On macOS use `brew install vips` before installing Python dependencies.

### Step 3: Create pyproject.toml

```bash
cat > pyproject.toml << 'EOF'
[project]
name = "gpu-image-converter"
version = "1.0.0"
description = "GPU-accelerated image converter backend"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "celery>=5.3.0",
    "redis>=5.0.0",
    "pyvips>=2.2.0",
    "pillow>=10.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=app --cov-report=term-missing"
EOF
```

### Step 4: Create Dockerfile

```bash
cat > Dockerfile << 'EOF'
# ============================================
# GPU Image Converter - Backend Dockerfile
# ============================================
FROM nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    # Image processing libraries
    libvips-dev \
    libvips-tools \
    imagemagick \
    ffmpeg \
    libopencv-dev \
    # NVIDIA tools
    nvidia-cuda-toolkit \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install GPU-accelerated libraries
RUN pip3 install --no-cache-dir \
    pyvips \
    opencv-python-headless \
    pillow-simd \
    cupy-cuda12x

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir \
    torch==2.2.0+cu121 \
    torchvision==0.17.0+cu121 \
    --extra-index-url https://download.pytorch.org/whl/cu121

# Copy application code
COPY . .

# Create directories for uploads and outputs
RUN mkdir -p /app/uploads /app/outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### Step 5: Create .dockerignore

```bash
cat > .dockerignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.pytest_cache/
.coverage
htmlcov/
*.log
.git/
.gitignore
README.md
tests/
docs/
*.md
.env
.env.*
uploads/
outputs/
EOF
```

---

## GPU Converter Implementation

### app/converter.py

This is the core GPU image processing module:

```python
import pyvips
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class GPUImageConverter:
    """
    GPU-accelerated image converter using libvips and OpenCV CUDA.

    Features:
    - Hardware-accelerated image processing
    - Support for 10+ image formats
    - Resize, crop, and filter operations
    - Batch processing support
    """

    SUPPORTED_FORMATS = {
        'input': [
            'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp',
            'tiff', 'tif', 'svg', 'heic', 'avif'
        ],
        'output': [
            'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp',
            'tiff', 'avif', 'pdf'
        ]
    }

    def __init__(self):
        """Initialize the converter and configure libvips."""
        # Configure libvips for optimal performance
        pyvips.cache_set_max(0)  # Disable cache to save memory
        pyvips.cache_set_max_mem(1024 * 1024 * 500)  # 500MB cache
        pyvips.concurrency_set(4)  # Utilize 4 CPU cores

        # Test CUDA availability
        try:
            self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
            if self.cuda_available:
                logger.info(f"CUDA devices available: {cv2.cuda.getCudaEnabledDeviceCount()}")
        except Exception as e:
            logger.warning(f"CUDA check failed: {e}")
            self.cuda_available = False

        logger.info(f"GPU Image Converter initialized (CUDA: {self.cuda_available})")

    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        quality: int = 90,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fit: str = 'max',
        use_gpu: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert image with optional GPU acceleration.

        Args:
            input_path: Source image file path
            output_path: Destination file path
            output_format: Target format (jpg, png, webp, etc.)
            quality: Compression quality (1-100)
            width: Target width in pixels (None = keep original)
            height: Target height in pixels (None = keep original)
            fit: Resize mode ('max', 'fill', 'stretch')
            use_gpu: Enable GPU acceleration for filters
            **kwargs: Additional format-specific options

        Returns:
            Dict containing conversion metadata and stats
        """
        try:
            start_time = time.time()

            # Validate input file
            if not Path(input_path).exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Load image with libvips (fastest loader)
            logger.info(f"Loading image: {input_path}")
            image = pyvips.Image.new_from_file(input_path, access='sequential')

            original_size = (image.width, image.height)
            original_file_size = Path(input_path).stat().st_size

            logger.info(
                f"Loaded: {original_size[0]}x{original_size[1]}, "
                f"{original_file_size / 1024 / 1024:.2f}MB, "
                f"format: {image.interpretation}"
            )

            # Resize if requested
            if width or height:
                image = self._resize_image(image, width, height, fit)
                logger.info(f"Resized to: {image.width}x{image.height}")

            # Apply GPU-accelerated filters if available and requested
            if self.cuda_available and use_gpu and kwargs.get('sharpen') or kwargs.get('denoise'):
                logger.info("Applying GPU filters...")
                image = self._apply_gpu_filters(image, kwargs)

            # Get format-specific save options
            save_options = self._get_save_options(output_format, quality, kwargs)

            # Save converted image
            logger.info(f"Saving to: {output_path}")
            image.write_to_file(output_path, **save_options)

            # Calculate statistics
            end_time = time.time()
            elapsed = end_time - start_time
            output_file_size = Path(output_path).stat().st_size
            compression_ratio = output_file_size / original_file_size

            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'input_size': original_file_size,
                'output_size': output_file_size,
                'compression_ratio': round(compression_ratio, 3),
                'space_saved': original_file_size - output_file_size,
                'space_saved_percent': round((1 - compression_ratio) * 100, 2),
                'duration': round(elapsed, 3),
                'original_dimensions': original_size,
                'output_dimensions': (image.width, image.height),
                'format': output_format,
                'quality': quality,
                'gpu_used': self.cuda_available and use_gpu
            }

            logger.info(
                f"Conversion complete: {elapsed:.3f}s, "
                f"{compression_ratio*100:.1f}% of original size"
            )

            return result

        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path
            }

    def _resize_image(
        self,
        image: pyvips.Image,
        width: Optional[int],
        height: Optional[int],
        fit: str = 'max'
    ) -> pyvips.Image:
        """
        Resize image with aspect ratio handling.

        Args:
            image: Source vips image
            width: Target width (None = auto)
            height: Target height (None = auto)
            fit: Resize mode ('max', 'fill', 'stretch')

        Returns:
            Resized vips image
        """
        if not width and not height:
            return image

        current_width = image.width
        current_height = image.height

        if fit == 'max':
            # Fit within bounds, maintain aspect ratio
            if width and height:
                scale = min(width / current_width, height / current_height)
            elif width:
                scale = width / current_width
            else:
                scale = height / current_height

            return image.resize(scale)

        elif fit == 'fill':
            # Fill bounds, may crop (thumbnail)
            if width and height:
                return image.thumbnail_image(width, height=height, crop='centre')
            elif width:
                scale = width / current_width
                return image.resize(scale)
            else:
                scale = height / current_height
                return image.resize(scale)

        else:  # stretch
            # Exact dimensions, ignore aspect ratio
            scale_x = width / current_width if width else 1
            scale_y = height / current_height if height else 1
            return image.resize(scale_x, vscale=scale_y)

    def _apply_gpu_filters(
        self,
        image: pyvips.Image,
        options: Dict
    ) -> pyvips.Image:
        """
        Apply GPU-accelerated filters using OpenCV CUDA.

        Args:
            image: Source vips image
            options: Filter options (sharpen, denoise, etc.)

        Returns:
            Filtered vips image
        """
        if not self.cuda_available:
            logger.warning("GPU not available, skipping filters")
            return image

        try:
            # Convert vips image to numpy array
            np_array = np.ndarray(
                buffer=image.write_to_memory(),
                dtype=np.uint8,
                shape=[image.height, image.width, image.bands]
            )

            # Upload to GPU
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(np_array)

            # Apply sharpening filter on GPU
            if options.get('sharpen'):
                kernel = np.array([
                    [-1, -1, -1],
                    [-1,  9, -1],
                    [-1, -1, -1]
                ], dtype=np.float32)

                gpu_filter = cv2.cuda.createLinearFilter(
                    cv2.CV_8UC3, cv2.CV_8UC3, kernel
                )
                gpu_image = gpu_filter.apply(gpu_image)

            # Apply denoising on GPU
            if options.get('denoise'):
                denoiser = cv2.cuda.createFastNlMeansDenoisingColored()
                gpu_image = denoiser.apply(gpu_image)

            # Download from GPU
            result = gpu_image.download()

            # Convert back to vips image
            return pyvips.Image.new_from_memory(
                result.tobytes(),
                image.width,
                image.height,
                image.bands,
                image.format
            )

        except Exception as e:
            logger.error(f"GPU filter failed: {e}, falling back to original image")
            return image

    def _get_save_options(
        self,
        format: str,
        quality: int,
        options: Dict
    ) -> Dict:
        """
        Get format-specific save options for libvips.

        Args:
            format: Output format (jpg, png, webp, etc.)
            quality: Quality setting (1-100)
            options: Additional format options

        Returns:
            Dict of save options for vips.write_to_file()
        """
        format = format.lower()
        base_options = {'Q': quality}

        if format in ['jpg', 'jpeg']:
            return {
                **base_options,
                'strip': True,  # Remove EXIF metadata
                'optimize_coding': True,
                'interlace': options.get('progressive', False),
                'subsample_mode': 'auto'
            }

        elif format == 'png':
            return {
                'compression': options.get('compression', 6),
                'interlace': options.get('interlace', False),
                'strip': True
            }

        elif format == 'webp':
            return {
                **base_options,
                'lossless': options.get('lossless', False),
                'strip': True,
                'effort': options.get('effort', 4),  # 0-6
                'smart_subsample': True
            }

        elif format == 'avif':
            return {
                **base_options,
                'speed': options.get('speed', 6),  # 0-8
                'lossless': options.get('lossless', False)
            }

        elif format == 'tiff':
            return {
                **base_options,
                'compression': options.get('compression', 'jpeg'),
                'tile': options.get('tile', False)
            }

        else:
            return base_options

    def batch_convert(
        self,
        files: list,
        output_dir: str,
        output_format: str,
        **options
    ) -> list:
        """
        Convert multiple files in batch.

        Args:
            files: List of input file paths
            output_dir: Output directory path
            output_format: Target format for all files
            **options: Conversion options

        Returns:
            List of conversion results
        """
        results = []
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        for file_path in files:
            try:
                input_file = Path(file_path)
                output_file = output_dir_path / f"{input_file.stem}.{output_format}"

                result = self.convert(
                    input_path=str(input_file),
                    output_path=str(output_file),
                    output_format=output_format,
                    **options
                )

                results.append({
                    'input': str(input_file),
                    'output': str(output_file),
                    **result
                })

            except Exception as e:
                logger.error(f"Batch conversion failed for {file_path}: {e}")
                results.append({
                    'input': file_path,
                    'success': False,
                    'error': str(e)
                })

        return results


# Singleton instance
_converter_instance = None


def get_converter() -> GPUImageConverter:
    """Get or create singleton converter instance."""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = GPUImageConverter()
    return _converter_instance
```

See [API_REFERENCE.md](./API_REFERENCE.md) for complete FastAPI endpoint documentation.

---

## Celery Worker

### app/worker.py

```python
from celery import Celery
from celery.utils.log import get_task_logger
from .converter import get_converter
import os
from pathlib import Path
from datetime import datetime, timedelta

logger = get_task_logger(__name__)

# Initialize Celery with Redis backend
celery_app = Celery(
    'gpu_image_converter',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    result_expires=3600,  # 1 hour
)

# Get converter instance
converter = get_converter()


@celery_app.task(bind=True, name='convert_image')
def convert_image_task(
    self,
    job_id: str,
    input_path: str,
    output_path: str,
    output_format: str,
    options: dict
):
    """
    Celery task for GPU-accelerated image conversion.

    Args:
        job_id: Unique job identifier
        input_path: Source file path
        output_path: Destination file path
        output_format: Target format
        options: Conversion options (quality, resize, filters, etc.)
    """
    try:
        # Update task state to processing
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Converting image...',
                'progress': 10,
                'current': 'loading'
            }
        )

        logger.info(f"[{job_id}] Starting conversion: {input_path} -> {output_format}")

        # Perform GPU conversion
        result = converter.convert(
            input_path=input_path,
            output_path=output_path,
            output_format=output_format,
            **options
        )

        if not result['success']:
            raise Exception(result.get('error', 'Conversion failed'))

        # Update state to success
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Conversion complete',
                'progress': 100,
                'result': result
            }
        )

        logger.info(
            f"[{job_id}] Completed in {result['duration']}s, "
            f"size: {result['output_size'] / 1024 / 1024:.2f}MB"
        )

        return result

    except Exception as e:
        logger.error(f"[{job_id}] Conversion failed: {str(e)}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={
                'status': f'Error: {str(e)}',
                'progress': 0,
                'error': str(e)
            }
        )
        raise


@celery_app.task(name='batch_convert')
def batch_convert_task(
    job_id: str,
    files: list,
    output_dir: str,
    output_format: str,
    options: dict
):
    """
    Batch conversion task for multiple images.

    Args:
        job_id: Batch job identifier
        files: List of input file paths
        output_dir: Output directory
        output_format: Target format
        options: Conversion options
    """
    results = []
    total = len(files)

    logger.info(f"[{job_id}] Starting batch conversion: {total} files")

    for idx, file_path in enumerate(files, 1):
        try:
            output_path = Path(output_dir) / f"{Path(file_path).stem}.{output_format}"

            result = converter.convert(
                input_path=file_path,
                output_path=str(output_path),
                output_format=output_format,
                **options
            )

            results.append(result)

            # Update batch progress
            progress = int((idx / total) * 100)
            celery_app.backend.set(
                f'batch_progress:{job_id}',
                progress,
                ex=3600  # Expire in 1 hour
            )

            logger.info(f"[{job_id}] Progress: {idx}/{total} ({progress}%)")

        except Exception as e:
            logger.error(f"[{job_id}] Failed {file_path}: {str(e)}")
            results.append({
                'success': False,
                'input_path': file_path,
                'error': str(e)
            })

    logger.info(f"[{job_id}] Batch complete: {len(results)} files processed")
    return results


@celery_app.task(name='cleanup_old_files')
def cleanup_old_files():
    """
    Scheduled task to clean up files older than configured hours.
    """
    try:
        upload_dir = Path(os.getenv('UPLOAD_DIR', '/app/uploads'))
        output_dir = Path(os.getenv('OUTPUT_DIR', '/app/outputs'))
        hours = int(os.getenv('CLEANUP_AFTER_HOURS', '24'))

        threshold = datetime.now() - timedelta(hours=hours)
        deleted_count = 0

        for directory in [upload_dir, output_dir]:
            if not directory.exists():
                continue

            for file_path in directory.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < threshold:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(
                            f"Deleted old file: {file_path.name} "
                            f"({file_size / 1024 / 1024:.2f}MB)"
                        )

        logger.info(f"Cleanup complete: {deleted_count} files deleted")
        return {'deleted': deleted_count, 'threshold_hours': hours}

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'cleanup_old_files',
        'schedule': 3600.0,  # Every hour
    },
}
```

---

## Testing

### tests/test_converter.py

```python
import pytest
from pathlib import Path
from app.converter import GPUImageConverter


@pytest.fixture
def converter():
    return GPUImageConverter()


@pytest.fixture
def sample_image(tmp_path):
    """Create a simple test image."""
    from PIL import Image

    img = Image.new('RGB', (800, 600), color='red')
    img_path = tmp_path / "test.png"
    img.save(img_path)
    return str(img_path)


def test_converter_initialization(converter):
    """Test converter initializes properly."""
    assert converter is not None
    assert isinstance(converter.cuda_available, bool)


def test_png_to_webp_conversion(converter, sample_image, tmp_path):
    """Test basic PNG to WebP conversion."""
    output_path = tmp_path / "output.webp"

    result = converter.convert(
        input_path=sample_image,
        output_path=str(output_path),
        output_format='webp',
        quality=90
    )

    assert result['success'] is True
    assert Path(output_path).exists()
    assert result['format'] == 'webp'
    assert result['output_size'] > 0


def test_resize_image(converter, sample_image, tmp_path):
    """Test image resizing."""
    output_path = tmp_path / "resized.jpg"

    result = converter.convert(
        input_path=sample_image,
        output_path=str(output_path),
        output_format='jpg',
        width=400,
        height=300,
        fit='max'
    )

    assert result['success'] is True
    assert result['output_dimensions'] == (400, 300)


def test_batch_conversion(converter, tmp_path):
    """Test batch conversion."""
    from PIL import Image

    # Create multiple test images
    files = []
    for i in range(3):
        img = Image.new('RGB', (100, 100), color='blue')
        img_path = tmp_path / f"test_{i}.png"
        img.save(img_path)
        files.append(str(img_path))

    output_dir = tmp_path / "output"

    results = converter.batch_convert(
        files=files,
        output_dir=str(output_dir),
        output_format='webp',
        quality=80
    )

    assert len(results) == 3
    assert all(r['success'] for r in results)
```

Run tests:

```bash
cd backend
python -m pytest tests/ -v --cov=app
```

---

**Next:** Continue with [Frontend Implementation](../../frontend/docs/FRONTEND_GUIDE.md)
