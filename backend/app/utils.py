import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def format_bytes(bytes: int, decimals: int = 2) -> str:
    """
    Format bytes to human-readable string.

    Args:
        bytes: Number of bytes
        decimals: Decimal places

    Returns:
        Formatted string (e.g., "1.23 MB")
    """
    if bytes == 0:
        return "0 Bytes"

    k = 1024
    dm = decimals if decimals >= 0 else 0
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']

    i = 0
    size = float(bytes)

    while size >= k and i < len(sizes) - 1:
        size /= k
        i += 1

    return f"{size:.{dm}f} {sizes[i]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1.23s" or "2m 15s")
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"

    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def validate_image_format(filename: str, allowed_formats: list) -> bool:
    """
    Validate if file has allowed image format.

    Args:
        filename: File name to validate
        allowed_formats: List of allowed extensions (e.g., ['jpg', 'png'])

    Returns:
        True if format is allowed, False otherwise
    """
    ext = Path(filename).suffix.lower().lstrip('.')
    return ext in allowed_formats


def get_file_extension(filename: str) -> str:
    """
    Get file extension without dot.

    Args:
        filename: File name

    Returns:
        Extension string (e.g., "jpg")
    """
    return Path(filename).suffix.lower().lstrip('.')


def ensure_directory(path: str | Path) -> Path:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_old_files(directory: Path, max_age_hours: int = 24) -> int:
    """
    Clean up files older than specified hours.

    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours

    Returns:
        Number of files deleted
    """
    from datetime import datetime, timedelta

    if not directory.exists():
        return 0

    threshold = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0

    for file_path in directory.glob('*'):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < threshold:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

    return deleted_count


def get_gpu_info() -> dict:
    """
    Get GPU information if available.

    Returns:
        Dictionary with GPU info or error message
    """
    try:
        import torch
        import cv2

        cuda_available = torch.cuda.is_available()
        cv_cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0

        if cuda_available:
            return {
                "available": True,
                "device_name": torch.cuda.get_device_name(0),
                "cuda_version": torch.version.cuda,
                "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB",
                "opencv_cuda": cv_cuda_available
            }
        else:
            return {
                "available": False,
                "message": "CUDA not available"
            }

    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
