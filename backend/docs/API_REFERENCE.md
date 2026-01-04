# API Reference

> **FastAPI Backend - REST API Documentation**

## Base URL

```
Development: http://localhost/api
Production:  https://yourdomain.com/api
```

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status](#health--status)
3. [Image Conversion](#image-conversion)
4. [Job Management](#job-management)
5. [Error Responses](#error-responses)

---

## Authentication

Currently, the API is open for local use. For production deployment, implement JWT-based authentication.

### Future: Bearer Token (Coming Soon)

```http
Authorization: Bearer <your_token>
```

---

## Health & Status

### GET /health

Check API and GPU status.

**Request:**
```bash
curl http://localhost/api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "cuda_available": true,
  "timestamp": "2026-01-04T12:00:00.000Z",
  "version": "1.0.0"
}
```

---

## Image Conversion

### POST /convert

Convert a single image to specified format.

**Request:**

```http
POST /api/convert
Content-Type: multipart/form-data

Parameters:
- file (required): Image file to convert
- output_format (required): Target format (jpg, png, webp, avif, etc.)
- quality (optional): Compression quality 1-100 (default: 90)
- width (optional): Target width in pixels
- height (optional): Target height in pixels
- fit (optional): Resize mode: 'max' | 'fill' | 'stretch' (default: 'max')
- use_gpu (optional): Enable GPU acceleration (default: true)
- sharpen (optional): Apply sharpening filter (default: false)
- denoise (optional): Apply denoising filter (default: false)
- progressive (optional): Progressive JPEG (default: false)
- lossless (optional): Lossless compression for WebP/AVIF (default: false)
```

**Example using cURL:**

```bash
curl -X POST http://localhost/api/convert \
  -F "file=@/path/to/image.png" \
  -F "output_format=webp" \
  -F "quality=90" \
  -F "width=1920" \
  -F "height=1080" \
  -F "fit=max" \
  -F "use_gpu=true" \
  -F "sharpen=false" \
  -F "denoise=false"
```

**Example using JavaScript (Fetch):**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('output_format', 'webp');
formData.append('quality', '90');
formData.append('use_gpu', 'true');

const response = await fetch('http://localhost/api/convert', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
```

**Example using Python (requests):**

```python
import requests

files = {'file': open('image.png', 'rb')}
data = {
    'output_format': 'webp',
    'quality': 90,
    'use_gpu': True,
}

response = requests.post('http://localhost/api/convert', files=files, data=data)
result = response.json()
```

**Response (200 OK):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Conversion started",
  "filename": "image.png"
}
```

**Supported Formats:**

| Format | Input | Output | Notes |
|--------|-------|--------|-------|
| JPEG   | ✅    | ✅     | Progressive option available |
| PNG    | ✅    | ✅     | Supports transparency |
| WebP   | ✅    | ✅     | Modern format, best compression |
| AVIF   | ✅    | ✅     | Next-gen format, excellent quality |
| GIF    | ✅    | ✅     | Animation preserved |
| BMP    | ✅    | ✅     | Uncompressed format |
| TIFF   | ✅    | ✅     | Professional format |
| HEIC   | ✅    | ❌     | Input only (Apple format) |
| SVG    | ✅    | ❌     | Vector format, rasterized on load |
| PDF    | ❌    | ✅     | Output only |

---

### POST /batch-convert

Convert multiple images in a single batch.

**Request:**

```http
POST /api/batch-convert
Content-Type: multipart/form-data

Parameters:
- files (required): Array of image files (max 50)
- output_format (required): Target format for all images
- quality (optional): Compression quality 1-100 (default: 90)
```

**Example using cURL:**

```bash
curl -X POST http://localhost/api/batch-convert \
  -F "files=@image1.png" \
  -F "files=@image2.jpg" \
  -F "files=@image3.webp" \
  -F "output_format=avif" \
  -F "quality=85"
```

**Example using JavaScript:**

```javascript
const formData = new FormData();

// Add multiple files
for (const file of fileInput.files) {
  formData.append('files', file);
}

formData.append('output_format', 'webp');
formData.append('quality', '90');

const response = await fetch('http://localhost/api/batch-convert', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
```

**Response (200 OK):**

```json
{
  "job_id": "batch-550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "total_files": 10,
  "message": "Batch conversion started"
}
```

**Limitations:**

- Maximum 50 files per batch
- Maximum 100MB per file
- All files converted to same format

---

## Job Management

### GET /status/{job_id}

Get conversion job status and progress.

**Request:**

```bash
curl http://localhost/api/status/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK) - Pending:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "filename": "image.png",
  "created_at": "2026-01-04T12:00:00.000Z",
  "progress": 0
}
```

**Response (200 OK) - Processing:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "filename": "image.png",
  "created_at": "2026-01-04T12:00:00.000Z",
  "progress": 50
}
```

**Response (200 OK) - Completed:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "image.png",
  "created_at": "2026-01-04T12:00:00.000Z",
  "completed_at": "2026-01-04T12:00:02.543Z",
  "progress": 100,
  "download_url": "/downloads/550e8400-e29b-41d4-a716-446655440000_image.webp",
  "metadata": {
    "duration": 0.823,
    "input_size": 5242880,
    "output_size": 1048576,
    "compression_ratio": 0.2,
    "space_saved": 4194304,
    "space_saved_percent": 80.0,
    "original_dimensions": [1920, 1080],
    "output_dimensions": [1920, 1080],
    "format": "webp",
    "quality": 90,
    "gpu_used": true
  }
}
```

**Response (200 OK) - Failed:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "filename": "image.png",
  "created_at": "2026-01-04T12:00:00.000Z",
  "progress": 0,
  "error": "Unsupported image format"
}
```

---

### GET /downloads/{filename}

Download converted file.

**Request:**

```bash
curl -O http://localhost/api/downloads/550e8400-e29b-41d4-a716-446655440000_image.webp
```

**Response:**

Binary file download with appropriate `Content-Type` header.

**Example using JavaScript:**

```javascript
const downloadUrl = `http://localhost${job.download_url}`;

// Method 1: Direct download link
const link = document.createElement('a');
link.href = downloadUrl;
link.download = 'converted-image.webp';
link.click();

// Method 2: Fetch and create blob
const response = await fetch(downloadUrl);
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;
link.download = 'converted-image.webp';
link.click();
window.URL.revokeObjectURL(url);
```

---

### DELETE /jobs/{job_id}

Delete a conversion job and associated files.

**Request:**

```bash
curl -X DELETE http://localhost/api/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**

```json
{
  "message": "Job deleted",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

---

## Error Responses

### Standard Error Format

All errors follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

#### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "File too large (max 100MB)"
}
```

**Common causes:**
- File size exceeds limit
- Invalid format specified
- Missing required parameters
- Invalid quality value (must be 1-100)

#### 404 Not Found

Resource not found.

```json
{
  "detail": "Job not found"
}
```

**Common causes:**
- Invalid job ID
- Job expired (files cleaned up after 24 hours)
- Download file already deleted

#### 413 Payload Too Large

File or request body too large.

```json
{
  "detail": "Request entity too large"
}
```

#### 415 Unsupported Media Type

Invalid file type.

```json
{
  "detail": "Unsupported file type. Supported: jpg, png, webp, gif, bmp, tiff, svg, heic, avif"
}
```

#### 422 Unprocessable Entity

Validation error in request data.

```json
{
  "detail": [
    {
      "loc": ["body", "quality"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

#### 500 Internal Server Error

Server-side processing error.

```json
{
  "detail": "Internal server error: GPU processing failed"
}
```

**Common causes:**
- GPU out of memory
- Corrupted image file
- Unsupported image variant
- System resource exhaustion

#### 503 Service Unavailable

Service temporarily unavailable.

```json
{
  "detail": "Worker queue full, please try again later"
}
```

---

## Rate Limiting

**Current:** No rate limiting (local deployment)

**Future (Production):**
- 100 requests per minute per IP
- 1000 requests per hour per API key
- 10GB upload per day

---

## WebSocket Support (Coming Soon)

Real-time conversion progress updates via WebSocket.

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost/ws');

ws.onopen = () => {
  // Subscribe to job updates
  ws.send(JSON.stringify({
    action: 'subscribe',
    job_id: '550e8400-e29b-41d4-a716-446655440000'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
  // { status: 'processing', progress: 45, ... }
};
```

---

## Performance Metrics

### Expected Response Times

| Operation | GPU (RTX 4060) | CPU Only | Speedup |
|-----------|----------------|----------|---------|
| PNG → WebP (5MB) | 0.3s | 2.1s | 7x |
| JPEG → AVIF (10MB) | 0.8s | 5.4s | 6.75x |
| Batch 10 images (50MB) | 3.2s | 24.3s | 7.6x |
| Resize 4K image | 0.4s | 3.2s | 8x |
| Sharpen filter | 0.5s | 3.8s | 7.6x |

### Compression Ratios

| Format | Typical Compression | Quality Loss | Best For |
|--------|---------------------|--------------|----------|
| WebP   | 70-80% smaller      | Minimal      | Web images, general use |
| AVIF   | 75-85% smaller      | Minimal      | Next-gen web, best quality |
| JPEG   | 50-70% smaller      | Moderate     | Photos, legacy support |
| PNG    | Lossless            | None         | Graphics, transparency |

---

## Example Workflows

### Basic Conversion Workflow

```javascript
// 1. Upload and convert
const formData = new FormData();
formData.append('file', imageFile);
formData.append('output_format', 'webp');
formData.append('quality', '90');

const uploadResponse = await fetch('/api/convert', {
  method: 'POST',
  body: formData,
});

const { job_id } = await uploadResponse.json();

// 2. Poll for completion
const pollStatus = async () => {
  const statusResponse = await fetch(`/api/status/${job_id}`);
  const status = await statusResponse.json();

  if (status.status === 'completed') {
    // 3. Download result
    window.location.href = `/api${status.download_url}`;
  } else if (status.status === 'processing') {
    setTimeout(pollStatus, 1000);
  }
};

pollStatus();
```

### Batch Conversion with Progress

```javascript
async function batchConvert(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('output_format', 'avif');
  formData.append('quality', '85');

  // Start batch job
  const response = await fetch('/api/batch-convert', {
    method: 'POST',
    body: formData,
  });

  const { job_id, total_files } = await response.json();

  // Monitor progress
  const checkProgress = setInterval(async () => {
    const status = await fetch(`/api/status/${job_id}`);
    const data = await status.json();

    console.log(`Progress: ${data.progress}%`);

    if (data.status === 'completed') {
      clearInterval(checkProgress);
      console.log('Batch complete!');
    }
  }, 1000);
}
```

---

## SDK Examples

### Python SDK

```python
import requests
from pathlib import Path

class ImageConverterClient:
    def __init__(self, base_url='http://localhost/api'):
        self.base_url = base_url

    def convert(self, file_path, output_format='webp', quality=90, **kwargs):
        """Convert a single image."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'output_format': output_format,
                'quality': quality,
                **kwargs
            }
            response = requests.post(
                f'{self.base_url}/convert',
                files=files,
                data=data
            )
            return response.json()

    def get_status(self, job_id):
        """Get job status."""
        response = requests.get(f'{self.base_url}/status/{job_id}')
        return response.json()

    def download(self, download_url, output_path):
        """Download converted file."""
        response = requests.get(f'{self.base_url}{download_url}', stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# Usage
client = ImageConverterClient()

# Convert image
result = client.convert('photo.jpg', output_format='webp', quality=90)
job_id = result['job_id']

# Wait for completion
import time
while True:
    status = client.get_status(job_id)
    if status['status'] == 'completed':
        client.download(status['download_url'], 'photo.webp')
        break
    time.sleep(1)
```

### TypeScript SDK

```typescript
class ImageConverterAPI {
  constructor(private baseUrl = 'http://localhost/api') {}

  async convert(
    file: File,
    options: {
      outputFormat: string;
      quality?: number;
      width?: number;
      height?: number;
    }
  ) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);
    if (options.quality) formData.append('quality', String(options.quality));
    if (options.width) formData.append('width', String(options.width));
    if (options.height) formData.append('height', String(options.height));

    const response = await fetch(`${this.baseUrl}/convert`, {
      method: 'POST',
      body: formData,
    });

    return response.json();
  }

  async getStatus(jobId: string) {
    const response = await fetch(`${this.baseUrl}/status/${jobId}`);
    return response.json();
  }

  async waitForCompletion(jobId: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        const status = await this.getStatus(jobId);

        if (status.status === 'completed') {
          resolve(status);
        } else if (status.status === 'failed') {
          reject(new Error(status.error));
        } else {
          setTimeout(poll, 1000);
        }
      };

      poll();
    });
  }
}

// Usage
const api = new ImageConverterAPI();

const file = document.querySelector('input[type="file"]').files[0];
const result = await api.convert(file, {
  outputFormat: 'webp',
  quality: 90,
});

const completed = await api.waitForCompletion(result.job_id);
console.log('Download URL:', completed.download_url);
```

---

## Changelog

### v1.0.0 (2026-01-04)

- Initial release
- Single image conversion
- Batch conversion support
- GPU acceleration
- 10+ format support
- Real-time progress tracking
- Automatic file cleanup

---

**For more information, see:**
- [Implementation Guide](../../docs/IMPLEMENTATION_GUIDE.md)
- [Backend Guide](./BACKEND_GUIDE.md)
- [Frontend Guide](../../frontend/docs/FRONTEND_GUIDE.md)
