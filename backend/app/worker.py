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