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