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