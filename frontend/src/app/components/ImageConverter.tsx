'use client';

import { useState, useCallback } from 'react';
import { FileUploadZone } from './FileUploadZone';
import { SettingsPanel } from './SettingsPanel';
import { ConversionQueue } from './ConversionQueue';
import type { ConversionJob, ConversionOptions, ImageFormat } from '@/lib/types';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';

export function ImageConverter() {
  const [jobs, setJobs] = useState<ConversionJob[]>([]);
  const [outputFormat, setOutputFormat] = useState<ImageFormat>('webp');
  const [quality, setQuality] = useState(90);
  const [useGpu, setUseGpu] = useState(true);
  const [sharpen, setSharpen] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

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
          const jobId = (response.data as any).job_id || response.data.id;
          const newJob: ConversionJob = {
            id: jobId,
            filename: file.name,
            status: 'pending',
            progress: 0,
            createdAt: new Date().toISOString(),
          };

          setJobs(prev => [...prev, newJob]);

          // Start polling for this job
          pollJobStatus(jobId);

          toast.success('Conversion started', {
            description: `${file.name} added to queue`,
          });
        } else {
          toast.error('Upload failed', {
            description: response.error || 'Failed to upload file',
          });
        }
      }
    } catch (error) {
      toast.error('Error', {
        description: error instanceof Error ? error.message : 'Upload failed',
      });
    } finally {
      setIsUploading(false);
    }
  }, [outputFormat, quality, useGpu, sharpen, denoise]);

  const pollJobStatus = useCallback(async (jobId: string) => {
    const poll = async () => {
      const response = await apiClient.getJobStatus(jobId);

      if (response.success && response.data) {
        const data = response.data as any;
        setJobs(prev =>
          prev.map(job =>
            job.id === jobId
              ? {
                  ...job,
                  status: data.status,
                  progress: data.progress || 0,
                  downloadUrl: data.download_url || data.downloadUrl,
                  metadata: data.metadata,
                  error: data.error,
                  completedAt:
                    data.status === 'completed'
                      ? new Date().toISOString()
                      : undefined,
                }
              : job
          )
        );

        // Continue polling if not finished
        if (
          data.status === 'pending' ||
          data.status === 'processing'
        ) {
          setTimeout(poll, 1000);
        } else if (data.status === 'completed') {
          toast.success('Conversion complete', {
            description: `Conversion is ready to download`,
          });
        } else if (data.status === 'failed') {
          toast.error('Conversion failed', {
            description: data.error || 'Unknown error',
          });
        }
      }
    };

    poll();
  }, []);

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