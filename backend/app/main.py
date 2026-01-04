from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import aiofiles
import os
import uuid
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime

from .models import (
    ConversionOptions, ConversionJob, ConversionStatus,
    ConversionResponse, ImageFormat, HealthResponse, FitMode
)
from .worker import convert_image_task, batch_convert_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="GPU Image Converter",
    description="High-performance local image converter with GPU acceleration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
# Default to relative paths for local development, /app/* for Docker
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DEFAULT_UPLOAD_DIR = BASE_DIR / "uploads"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', str(DEFAULT_UPLOAD_DIR)))
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', str(DEFAULT_OUTPUT_DIR)))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Mount output directory for downloads
app.mount("/downloads", StaticFiles(directory=OUTPUT_DIR), name="downloads")

# In-memory job store (use Redis in production)
jobs_store = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "GPU Image Converter",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from .converter import get_converter

    try:
        converter = get_converter()
        return HealthResponse(
            status="healthy",
            cuda_available=converter.cuda_available,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(500, f"Health check failed: {str(e)}")


@app.post("/convert", response_model=ConversionResponse)
async def convert_image(
    file: UploadFile = File(...),
    output_format: ImageFormat = Form(...),
    quality: int = Form(90),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    fit: FitMode = Form(FitMode.MAX),
    use_gpu: bool = Form(True),
    sharpen: bool = Form(False),
    denoise: bool = Form(False),
    progressive: bool = Form(False),
    lossless: bool = Form(False)
):
    """
    Convert a single image to specified format.

    - **file**: Image file to convert
    - **output_format**: Target format (jpg, png, webp, avif, etc.)
    - **quality**: Compression quality 1-100 (default: 90)
    - **width**: Target width in pixels (optional)
    - **height**: Target height in pixels (optional)
    - **fit**: Resize mode: 'max' | 'fill' | 'stretch' (default: 'max')
    - **use_gpu**: Enable GPU acceleration (default: true)
    - **sharpen**: Apply sharpening filter (default: false)
    - **denoise**: Apply denoising filter (default: false)
    - **progressive**: Progressive JPEG (default: false)
    - **lossless**: Lossless compression for WebP/AVIF (default: false)
    """
    try:
        # Validate file size
        max_size = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(400, f"File too large (max {max_size / 1024 / 1024}MB)")

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Save uploaded file
        input_filename = f"{job_id}_{file.filename}"
        input_path = UPLOAD_DIR / input_filename

        async with aiofiles.open(input_path, 'wb') as f:
            await f.write(content)

        logger.info(f"[{job_id}] Saved upload: {file.filename} ({len(content)} bytes)")

        # Prepare output path
        output_filename = f"{job_id}_{Path(file.filename).stem}.{output_format.value}"
        output_path = OUTPUT_DIR / output_filename

        # Create conversion options
        options = ConversionOptions(
            output_format=output_format,
            quality=quality,
            width=width,
            height=height,
            fit=fit,
            use_gpu=use_gpu,
            sharpen=sharpen,
            denoise=denoise,
            progressive=progressive,
            lossless=lossless
        )

        # Create job record
        job = ConversionJob(
            id=job_id,
            filename=file.filename,
            status=ConversionStatus.PENDING,
            created_at=datetime.utcnow(),
            input_path=str(input_path),
            output_path=str(output_path),
            options=options
        )
        jobs_store[job_id] = job

        # Submit to Celery
        task = convert_image_task.apply_async(
            args=[
                job_id,
                str(input_path),
                str(output_path),
                output_format.value,
                options.model_dump()
            ],
            task_id=job_id
        )

        logger.info(f"[{job_id}] Submitted conversion task")

        return ConversionResponse(
            job_id=job_id,
            status=ConversionStatus.PENDING,
            message="Conversion started",
            filename=file.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversion job: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to create conversion: {str(e)}")


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get conversion job status and progress"""
    from celery.result import AsyncResult

    if job_id not in jobs_store:
        raise HTTPException(404, "Job not found")

    job = jobs_store[job_id]
    task = AsyncResult(job_id)

    # Update job status from Celery
    if task.state == 'PENDING':
        job.status = ConversionStatus.PENDING
    elif task.state == 'PROCESSING':
        job.status = ConversionStatus.PROCESSING
    elif task.state == 'SUCCESS':
        job.status = ConversionStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = task.result
    elif task.state == 'FAILURE':
        job.status = ConversionStatus.FAILED
        job.error = str(task.info)

    response = {
        "job_id": job.id,
        "status": job.status.value,
        "filename": job.filename,
        "created_at": job.created_at.isoformat(),
        "progress": task.info.get('progress', 0) if isinstance(task.info, dict) else 0
    }

    if job.status == ConversionStatus.COMPLETED:
        response["completed_at"] = job.completed_at.isoformat() if job.completed_at else None
        response["download_url"] = f"/downloads/{Path(job.output_path).name}"
        response["metadata"] = job.result
    elif job.status == ConversionStatus.FAILED:
        response["error"] = job.error

    return response


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download converted file"""
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@app.post("/batch-convert")
async def batch_convert(
    files: List[UploadFile] = File(...),
    output_format: ImageFormat = Form(...),
    quality: int = Form(90),
    use_gpu: bool = Form(True)
):
    """Convert multiple images in batch"""
    if len(files) > 50:
        raise HTTPException(400, "Maximum 50 files per batch")

    job_id = str(uuid.uuid4())
    file_paths = []

    try:
        # Save all uploaded files
        for file in files:
            content = await file.read()
            input_filename = f"{job_id}_{file.filename}"
            input_path = UPLOAD_DIR / input_filename

            async with aiofiles.open(input_path, 'wb') as f:
                await f.write(content)

            file_paths.append(str(input_path))

        logger.info(f"[{job_id}] Batch upload: {len(files)} files")

        # Submit batch job
        task = batch_convert_task.apply_async(
            args=[
                job_id,
                file_paths,
                str(OUTPUT_DIR),
                output_format.value,
                {'quality': quality, 'use_gpu': use_gpu}
            ]
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "total_files": len(files),
            "message": "Batch conversion started"
        }

    except Exception as e:
        logger.error(f"Batch conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(500, str(e))


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, background_tasks: BackgroundTasks):
    """Delete job and associated files"""
    if job_id not in jobs_store:
        raise HTTPException(404, "Job not found")

    job = jobs_store[job_id]

    # Delete files in background
    def cleanup_files():
        try:
            Path(job.input_path).unlink(missing_ok=True)
            if job.output_path:
                Path(job.output_path).unlink(missing_ok=True)
            logger.info(f"[{job_id}] Cleaned up files")
        except Exception as e:
            logger.error(f"[{job_id}] Cleanup failed: {e}")

    background_tasks.add_task(cleanup_files)
    del jobs_store[job_id]

    return {"message": "Job deleted", "job_id": job_id}


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("GPU Image Converter API started")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Test GPU availability
    try:
        from .converter import get_converter
        converter = get_converter()
        logger.info(f"GPU acceleration: {'enabled' if converter.cuda_available else 'disabled'}")
    except Exception as e:
        logger.warning(f"GPU check failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("GPU Image Converter API shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
