# Frontend Implementation Guide

> **Next.js 16 + TypeScript + Bun + shadcn/ui**

## Table of Contents

1. [Setup](#setup)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [API Integration](#api-integration)
5. [Real-time Updates](#real-time-updates)
6. [Docker Configuration](#docker-configuration)
7. [Testing](#testing)

---

## Setup

### Step 1: Initialize Next.js Project with Bun

```bash
cd frontend

# Create Next.js app with Bun
bun create next-app@latest . --typescript --tailwind --app --no-src-dir

# Answer prompts:
# ✔ Would you like to use ESLint? … Yes
# ✔ Would you like to use Turbopack? … Yes
# ✔ Would you like to customize the import alias? … No
```

### Step 2: Install Dependencies

```bash
# Core dependencies
bun add axios react-dropzone zustand @tanstack/react-query

# shadcn/ui setup
bun add -D @types/node

# Initialize shadcn/ui
bunx shadcn@latest init

# Add shadcn components
bunx shadcn@latest add button
bunx shadcn@latest add card
bunx shadcn@latest add badge
bunx shadcn@latest add progress
bunx shadcn@latest add select
bunx shadcn@latest add slider
bunx shadcn@latest add tabs
bunx shadcn@latest add toast
bunx shadcn@latest add dropdown-menu
bunx shadcn@latest add dialog

# Icons
bun add lucide-react
```

### Step 3: Project Structure

Create the following structure:

```bash
mkdir -p app/components
mkdir -p app/api/upload
mkdir -p components/ui
mkdir -p lib
mkdir -p public/icons
mkdir -p docs
```

Final structure:

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── components/
│   │   ├── ImageConverter.tsx
│   │   ├── ConversionQueue.tsx
│   │   ├── SettingsPanel.tsx
│   │   └── FileUploadZone.tsx
│   └── api/
│       └── upload/
│           └── route.ts
├── components/
│   └── ui/                    # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── progress.tsx
│       └── ...
├── lib/
│   ├── utils.ts
│   ├── api.ts
│   └── types.ts
├── public/
│   └── icons/
├── docs/
│   ├── FRONTEND_GUIDE.md
│   └── COMPONENT_REFERENCE.md
├── Dockerfile
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Core Components

### 1. Type Definitions

**lib/types.ts**

```typescript
export type ImageFormat =
  | 'jpg'
  | 'jpeg'
  | 'png'
  | 'webp'
  | 'gif'
  | 'bmp'
  | 'tiff'
  | 'avif'
  | 'pdf';

export type FitMode = 'max' | 'fill' | 'stretch';

export type ConversionStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ConversionOptions {
  outputFormat: ImageFormat;
  quality: number;
  width?: number;
  height?: number;
  fit?: FitMode;
  useGpu?: boolean;
  sharpen?: boolean;
  denoise?: boolean;
  progressive?: boolean;
  lossless?: boolean;
}

export interface ConversionJob {
  id: string;
  filename: string;
  status: ConversionStatus;
  progress: number;
  createdAt: string;
  completedAt?: string;
  downloadUrl?: string;
  metadata?: {
    duration: number;
    inputSize: number;
    outputSize: number;
    compressionRatio: number;
    spaceSaved: number;
    spaceSavedPercent: number;
    originalDimensions: [number, number];
    outputDimensions: [number, number];
    gpuUsed: boolean;
  };
  error?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
```

### 2. API Client

**lib/api.ts**

```typescript
import axios, { AxiosError } from 'axios';
import type { ConversionJob, ConversionOptions, ApiResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

export class ApiClient {
  private client = axios.create({
    baseURL: API_URL,
    timeout: 300000, // 5 minutes
    headers: {
      'Content-Type': 'application/json',
    },
  });

  /**
   * Upload and convert a single image
   */
  async convertImage(
    file: File,
    options: ConversionOptions
  ): Promise<ApiResponse<ConversionJob>> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('output_format', options.outputFormat);
      formData.append('quality', options.quality.toString());

      if (options.width) formData.append('width', options.width.toString());
      if (options.height) formData.append('height', options.height.toString());
      if (options.fit) formData.append('fit', options.fit);
      if (options.useGpu !== undefined) formData.append('use_gpu', options.useGpu.toString());
      if (options.sharpen) formData.append('sharpen', options.sharpen.toString());
      if (options.denoise) formData.append('denoise', options.denoise.toString());

      const response = await this.client.post('/convert', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get conversion job status
   */
  async getJobStatus(jobId: string): Promise<ApiResponse<ConversionJob>> {
    try {
      const response = await this.client.get(`/status/${jobId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Download converted file
   */
  getDownloadUrl(downloadPath: string): string {
    return `${API_URL}${downloadPath}`;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<ApiResponse<{ status: string; cudaAvailable: boolean }>> {
    try {
      const response = await this.client.get('/health');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Batch convert multiple images
   */
  async batchConvert(
    files: File[],
    options: ConversionOptions
  ): Promise<ApiResponse<{ jobId: string; totalFiles: number }>> {
    try {
      const formData = new FormData();

      files.forEach(file => {
        formData.append('files', file);
      });

      formData.append('output_format', options.outputFormat);
      formData.append('quality', options.quality.toString());

      const response = await this.client.post('/batch-convert', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  private handleError(error: unknown): ApiResponse {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      return {
        success: false,
        error: axiosError.response?.data?.detail || axiosError.message,
      };
    }

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Singleton instance
export const apiClient = new ApiClient();
```

### 3. Main Converter Component

**app/components/ImageConverter.tsx**

```typescript
'use client';

import { useState, useCallback } from 'react';
import { FileUploadZone } from './FileUploadZone';
import { SettingsPanel } from './SettingsPanel';
import { ConversionQueue } from './ConversionQueue';
import type { ConversionJob, ConversionOptions, ImageFormat } from '@/lib/types';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';

export function ImageConverter() {
  const [jobs, setJobs] = useState<ConversionJob[]>([]);
  const [outputFormat, setOutputFormat] = useState<ImageFormat>('webp');
  const [quality, setQuality] = useState(90);
  const [useGpu, setUseGpu] = useState(true);
  const [sharpen, setSharpen] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const { toast } = useToast();

  const handleFilesAdded = useCallback(async (files: File[]) => {
    if (files.length === 0) return;

    setIsUploading(true);

    const options: ConversionOptions = {
      outputFormat,
      quality,
      useGpu,
      sharpen,
      denoise,
    };

    try {
      for (const file of files) {
        const response = await apiClient.convertImage(file, options);

        if (response.success && response.data) {
          const newJob: ConversionJob = {
            id: response.data.job_id,
            filename: file.name,
            status: 'pending',
            progress: 0,
            createdAt: new Date().toISOString(),
          };

          setJobs(prev => [...prev, newJob]);

          // Start polling for this job
          pollJobStatus(response.data.job_id);

          toast({
            title: 'Conversion started',
            description: `${file.name} added to queue`,
          });
        } else {
          toast({
            title: 'Upload failed',
            description: response.error || 'Failed to upload file',
            variant: 'destructive',
          });
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Upload failed',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  }, [outputFormat, quality, useGpu, sharpen, denoise, toast]);

  const pollJobStatus = useCallback(async (jobId: string) => {
    const poll = async () => {
      const response = await apiClient.getJobStatus(jobId);

      if (response.success && response.data) {
        setJobs(prev =>
          prev.map(job =>
            job.id === jobId
              ? {
                  ...job,
                  status: response.data!.status,
                  progress: response.data!.progress || 0,
                  downloadUrl: response.data!.download_url,
                  metadata: response.data!.metadata,
                  error: response.data!.error,
                  completedAt:
                    response.data!.status === 'completed'
                      ? new Date().toISOString()
                      : undefined,
                }
              : job
          )
        );

        // Continue polling if not finished
        if (
          response.data.status === 'pending' ||
          response.data.status === 'processing'
        ) {
          setTimeout(poll, 1000);
        } else if (response.data.status === 'completed') {
          toast({
            title: 'Conversion complete',
            description: `${response.data.filename} is ready to download`,
          });
        } else if (response.data.status === 'failed') {
          toast({
            title: 'Conversion failed',
            description: response.data.error || 'Unknown error',
            variant: 'destructive',
          });
        }
      }
    };

    poll();
  }, [toast]);

  const handleRemoveJob = useCallback((jobId: string) => {
    setJobs(prev => prev.filter(job => job.id !== jobId));
  }, []);

  const handleClearCompleted = useCallback(() => {
    setJobs(prev => prev.filter(job => job.status !== 'completed'));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12 max-w-7xl">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
            GPU Image Converter
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300">
            Lightning-fast local image conversion powered by NVIDIA RTX 4060
          </p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-500">
            <span className="inline-flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              GPU Accelerated
            </span>
            <span>•</span>
            <span>100% Local Processing</span>
            <span>•</span>
            <span>No API Costs</span>
          </div>
        </div>

        {/* Settings Panel */}
        <Card className="mb-8 p-6">
          <SettingsPanel
            outputFormat={outputFormat}
            quality={quality}
            useGpu={useGpu}
            sharpen={sharpen}
            denoise={denoise}
            onOutputFormatChange={setOutputFormat}
            onQualityChange={setQuality}
            onUseGpuChange={setUseGpu}
            onSharpenChange={setSharpen}
            onDenoiseChange={setDenoise}
          />
        </Card>

        {/* Upload Zone */}
        <FileUploadZone
          onFilesAdded={handleFilesAdded}
          isUploading={isUploading}
        />

        {/* Conversion Queue */}
        {jobs.length > 0 && (
          <div className="mt-8">
            <ConversionQueue
              jobs={jobs}
              onRemoveJob={handleRemoveJob}
              onClearCompleted={handleClearCompleted}
            />
          </div>
        )}

        {/* Stats Footer */}
        {jobs.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {jobs.length}
              </div>
              <div className="text-sm text-slate-500">Total Jobs</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {jobs.filter(j => j.status === 'processing').length}
              </div>
              <div className="text-sm text-slate-500">Processing</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {jobs.filter(j => j.status === 'completed').length}
              </div>
              <div className="text-sm text-slate-500">Completed</div>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-red-600">
                {jobs.filter(j => j.status === 'failed').length}
              </div>
              <div className="text-sm text-slate-500">Failed</div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4. File Upload Zone Component

**app/components/FileUploadZone.tsx**

```typescript
'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileImage } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface FileUploadZoneProps {
  onFilesAdded: (files: File[]) => void;
  isUploading: boolean;
}

export function FileUploadZone({ onFilesAdded, isUploading }: FileUploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesAdded(acceptedFiles);
    },
    [onFilesAdded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.heic', '.avif'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true,
    disabled: isUploading,
  });

  return (
    <Card
      {...getRootProps()}
      className={`
        relative overflow-hidden cursor-pointer transition-all duration-200
        ${isDragActive
          ? 'border-2 border-blue-500 bg-blue-50 dark:bg-blue-950 scale-[1.02]'
          : 'border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
        }
        ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />

      <div className="p-16 text-center">
        <div className="flex justify-center mb-6">
          {isDragActive ? (
            <FileImage className="h-16 w-16 text-blue-500 animate-bounce" />
          ) : (
            <Upload className="h-16 w-16 text-slate-400 dark:text-slate-600" />
          )}
        </div>

        <h3 className="text-2xl font-semibold mb-2">
          {isDragActive
            ? 'Drop images here...'
            : isUploading
            ? 'Uploading...'
            : 'Drag & drop images here'}
        </h3>

        <p className="text-slate-500 dark:text-slate-400 mb-4">
          or click to browse your files
        </p>

        <div className="flex flex-wrap justify-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">PNG</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">JPEG</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">WebP</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">GIF</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">BMP</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">TIFF</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">HEIC</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">AVIF</span>
        </div>

        <p className="mt-4 text-sm text-slate-400">
          Maximum file size: 100MB per image
        </p>
      </div>
    </Card>
  );
}
```

See [COMPONENT_REFERENCE.md](./COMPONENT_REFERENCE.md) for complete component documentation.

---

## Docker Configuration

### Dockerfile

```dockerfile
# ============================================
# Multi-stage Dockerfile for Next.js with Bun
# ============================================

# Base stage with Bun
FROM oven/bun:1.0-slim AS base
WORKDIR /app

# Install dependencies stage
FROM base AS deps
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# Development stage
FROM base AS development
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=development
EXPOSE 3000
CMD ["bun", "run", "dev"]

# Build stage for production
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

# Production stage
FROM base AS production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["bun", "run", "server.js"]
```

### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  // Image optimization
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },

  // Disable telemetry
  telemetry: false,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
  },

  // Headers for CORS
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## Testing

### Example Test (using Vitest)

```bash
# Install testing dependencies
bun add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**tests/ImageConverter.test.tsx**

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageConverter } from '@/app/components/ImageConverter';

describe('ImageConverter', () => {
  it('renders the main heading', () => {
    render(<ImageConverter />);
    expect(screen.getByText('GPU Image Converter')).toBeInTheDocument();
  });

  it('shows settings panel', () => {
    render(<ImageConverter />);
    expect(screen.getByText(/output format/i)).toBeInTheDocument();
  });

  it('accepts file uploads', async () => {
    render(<ImageConverter />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });

    // Test file upload logic
    // ... test implementation
  });
});
```

Run tests:

```bash
bun test
```

---

**Next:** See [API Reference](../../backend/docs/API_REFERENCE.md) for backend endpoints
