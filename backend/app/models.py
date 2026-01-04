from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional, List
from datetime import datetime


class ImageFormat(str, Enum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    AVIF = "avif"
    PDF = "pdf"


class FitMode(str, Enum):
    MAX = "max"      # Fit within bounds
    FILL = "fill"    # Fill bounds, may crop
    STRETCH = "stretch"  # Ignore aspect ratio


class ConversionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionOptions(BaseModel):
    """Image conversion options"""
    output_format: ImageFormat
    quality: int = Field(default=90, ge=1, le=100)
    width: Optional[int] = Field(default=None, gt=0, le=10000)
    height: Optional[int] = Field(default=None, gt=0, le=10000)
    fit: FitMode = FitMode.MAX
    use_gpu: bool = True
    sharpen: bool = False
    denoise: bool = False
    progressive: bool = False  # For JPEG
    lossless: bool = False  # For WEBP/AVIF

    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v):
        if v and v > 10000:
            raise ValueError('Dimension cannot exceed 10000 pixels')
        return v


class ConversionJob(BaseModel):
    """Conversion job model"""
    id: str
    filename: str
    status: ConversionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    input_path: str
    output_path: Optional[str] = None
    options: ConversionOptions
    result: Optional[dict] = None
    error: Optional[str] = None


class ConversionResponse(BaseModel):
    """API response for conversion"""
    job_id: str
    status: ConversionStatus
    message: str
    filename: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    cuda_available: bool
    timestamp: datetime
    version: str = "1.0.0"
