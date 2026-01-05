import pyvips
import cv2
import numpy as np
import torch
import torch.nn.functional as F
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
        # Configure libvips for optimal performance. Some pyvips
        # installations expose different helper functions depending
        # on version / build (or may wrap the libvips C API differently).
        # Call these functions guarded so importing the module won't
        # raise AttributeError on older/newer pyvips installs.
        def _safe_pyvips_call(name, *args, **kwargs):
            func = getattr(pyvips, name, None)
            if callable(func):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"pyvips.{name} call failed: {e}")

            # Some pyvips builds expose the underlying vips module
            # as `pyvips.vips` with similar helper functions.
            vips_mod = getattr(pyvips, "vips", None)
            func2 = getattr(vips_mod, name, None) if vips_mod is not None else None
            if callable(func2):
                try:
                    return func2(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"pyvips.vips.{name} call failed: {e}")

            logger.warning(f"pyvips.{name} not available; skipping")
            return None

        # Disable cache to save memory (if supported)
        _safe_pyvips_call("cache_set_max", 0)
        # Try to set a reasonable max memory cache
        _safe_pyvips_call("cache_set_max_mem", 1024 * 1024 * 500)  # 500MB cache
        # Try to set concurrency (number of worker threads)
        _safe_pyvips_call("concurrency_set", 4)  # Utilize 4 CPU cores

        # Test CUDA availability using PyTorch
        try:
            self.cuda_available = torch.cuda.is_available()
            if self.cuda_available:
                self.device = torch.device('cuda:0')
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA available: {device_name}")
            else:
                self.device = torch.device('cpu')
                logger.info("CUDA not available, using CPU")
        except Exception as e:
            logger.warning(f"CUDA check failed: {e}")
            self.cuda_available = False
            self.device = torch.device('cpu')

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
        Apply GPU-accelerated filters using PyTorch.

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

            # Convert to PyTorch tensor and move to GPU
            # Shape: [H, W, C] -> [1, C, H, W] for PyTorch
            tensor = torch.from_numpy(np_array).float().permute(2, 0, 1).unsqueeze(0) / 255.0
            tensor = tensor.to(self.device)

            # Apply sharpening filter on GPU
            if options.get('sharpen'):
                # Sharpen kernel
                kernel = torch.tensor([
                    [[-1, -1, -1],
                     [-1,  9, -1],
                     [-1, -1, -1]]
                ], dtype=torch.float32).unsqueeze(0).to(self.device)

                # Apply convolution to each channel
                channels = []
                for i in range(tensor.shape[1]):
                    channel = tensor[:, i:i+1, :, :]
                    sharpened = F.conv2d(channel, kernel, padding=1)
                    channels.append(sharpened)
                tensor = torch.cat(channels, dim=1)
                tensor = torch.clamp(tensor, 0, 1)

            # Apply denoising on GPU (simple bilateral-like filter)
            if options.get('denoise'):
                # Use average pooling as a simple denoise
                tensor = F.avg_pool2d(tensor, kernel_size=3, stride=1, padding=1)

            # Convert back to numpy
            result = (tensor.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)

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